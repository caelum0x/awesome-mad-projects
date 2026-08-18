//! The tick-based simulation engine and Stand ability implementations.
//!
//! SAFETY: The scheduler only ever mutates its own in-memory `processes` map.
//! It never spawns OS processes, never sends OS signals, and never references
//! real PIDs. "Terminate" means `HashMap::remove`. "Signal" is a string routed
//! through the sim.

use std::collections::HashMap;
use std::collections::VecDeque;

use crate::process::{ProcState, SimProcess, Task};
use crate::stand::Stand;

/// An immutable snapshot of the whole simulated table at the end of a tick.
/// King Crimson "erases time" by restoring one of these.
#[derive(Debug, Clone)]
struct Snapshot {
    tick: u64,
    processes: HashMap<u64, SimProcess>,
    order: Vec<u64>,
}

/// The simulation engine.
pub struct Scheduler {
    pub tick: u64,
    next_pid: u64,
    processes: HashMap<u64, SimProcess>,
    /// Stable scheduling order of pids.
    order: Vec<u64>,
    /// Ring buffer of recent snapshots (oldest at front).
    history: VecDeque<Snapshot>,
    max_history: usize,
    /// Human-readable event log (also the tick-by-tick trace).
    pub log: Vec<String>,
}

impl Scheduler {
    /// Create an engine that remembers up to `max_history` past ticks for King
    /// Crimson rollbacks.
    pub fn new(max_history: usize) -> Self {
        Scheduler {
            tick: 0,
            next_pid: 1,
            processes: HashMap::new(),
            order: Vec::new(),
            history: VecDeque::new(),
            max_history: max_history.max(1),
            log: Vec::new(),
        }
    }

    fn record(&mut self, line: impl Into<String>) {
        self.log.push(line.into());
    }

    // ---- table access -----------------------------------------------------

    pub fn get(&self, pid: u64) -> Option<&SimProcess> {
        self.processes.get(&pid)
    }

    pub fn alive_pids(&self) -> Vec<u64> {
        self.order.iter().copied().filter(|p| self.processes.contains_key(p)).collect()
    }

    /// Spawn a new simulated process in `lane` seeded with `tasks`.
    pub fn spawn(&mut self, name: &str, lane: &str, tasks: Vec<Task>) -> u64 {
        let pid = self.next_pid;
        self.next_pid += 1;
        let proc = SimProcess::new(pid, name, lane, tasks);
        self.processes.insert(pid, proc);
        self.order.push(pid);
        self.record(format!("[t{}] spawn  pid={pid} \"{name}\" in lane '{lane}'", self.tick));
        pid
    }

    /// Bind a Stand ability to a process.
    pub fn assign_stand(&mut self, pid: u64, stand: Stand) -> Result<(), String> {
        let tick = self.tick;
        let proc = self.processes.get_mut(&pid).ok_or_else(|| format!("no such pid {pid}"))?;
        proc.stand = Some(stand);
        let line = format!(
            "[t{tick}] stand  pid={pid} \"{}\" <= {} ({}) — user: {}",
            proc.name,
            stand,
            stand.ability(),
            stand.user()
        );
        self.record(line);
        Ok(())
    }

    // ---- tick engine ------------------------------------------------------

    /// Advance the simulation by one tick.
    ///
    /// Frozen processes decrement their freeze counter and do NOT advance.
    /// Every other alive process steps once. A snapshot is stored afterwards so
    /// King Crimson can roll back to this point.
    pub fn tick(&mut self) {
        self.tick += 1;
        let tick = self.tick;
        self.record(format!("[t{tick}] --- tick begins ---"));

        for pid in self.order.clone() {
            let Some(proc) = self.processes.get_mut(&pid) else { continue };
            if !proc.is_alive() {
                continue;
            }
            if proc.is_frozen() {
                proc.frozen_ticks -= 1;
                proc.state = if proc.frozen_ticks > 0 { ProcState::Frozen } else { ProcState::Ready };
                let remaining = proc.frozen_ticks;
                let name = proc.name.clone();
                self.record(format!(
                    "[t{tick}]   pid={pid} \"{name}\" FROZEN (no advance, {remaining} tick(s) left)"
                ));
                continue;
            }
            let name = proc.name.clone();
            match proc.step() {
                Some(label) => {
                    let done = proc.work_done;
                    self.record(format!(
                        "[t{tick}]   pid={pid} \"{name}\" ran task '{label}' (work_done={done})"
                    ));
                }
                None => {
                    self.record(format!("[t{tick}]   pid={pid} \"{name}\" idle (empty queue)"));
                }
            }
        }

        self.snapshot();
    }

    fn snapshot(&mut self) {
        let snap = Snapshot { tick: self.tick, processes: self.processes.clone(), order: self.order.clone() };
        self.history.push_back(snap);
        while self.history.len() > self.max_history {
            self.history.pop_front();
        }
    }

    // ---- Stand abilities --------------------------------------------------

    /// The World / Star Platinum: freeze every OTHER alive process for
    /// `ticks` ticks. The caster keeps running.
    pub fn the_world(&mut self, caster: u64, ticks: u32) -> Result<(), String> {
        self.require_stand(caster, Stand::TheWorld)?;
        let tick = self.tick;
        let caster_name = self.processes.get(&caster).map(|p| p.name.clone()).unwrap_or_default();
        self.record(format!(
            "[t{tick}] ABILITY \"{caster_name}\" (pid={caster}) casts THE WORLD — toki wo tomare! Freezing others for {ticks} tick(s)."
        ));
        for pid in self.order.clone() {
            if pid == caster {
                continue;
            }
            if let Some(proc) = self.processes.get_mut(&pid) {
                if proc.is_alive() {
                    proc.frozen_ticks = ticks;
                    proc.state = ProcState::Frozen;
                }
            }
        }
        Ok(())
    }

    /// Killer Queen: prime a target so the next signal it receives detonates it.
    pub fn killer_queen_mark(&mut self, caster: u64, target: u64) -> Result<(), String> {
        self.require_stand(caster, Stand::KillerQueen)?;
        let tick = self.tick;
        let proc = self.processes.get_mut(&target).ok_or_else(|| format!("no such target pid {target}"))?;
        proc.primed = true;
        let name = proc.name.clone();
        self.record(format!(
            "[t{tick}] ABILITY Killer Queen (pid={caster}) touches pid={target} \"{name}\" — primed. Next signal detonates it."
        ));
        Ok(())
    }

    /// Deliver a signal to a process within the sim. If the process was primed
    /// by Killer Queen, it detonates (is removed from the table).
    pub fn send_signal(&mut self, pid: u64, signal: &str) -> Result<(), String> {
        let tick = self.tick;
        let proc = self.processes.get_mut(&pid).ok_or_else(|| format!("no such pid {pid}"))?;
        let name = proc.name.clone();
        if proc.primed {
            proc.state = ProcState::Terminated;
            self.processes.remove(&pid);
            self.record(format!(
                "[t{tick}] SIGNAL '{signal}' -> pid={pid} \"{name}\": BOOM. Killer Queen detonates it. Removed from sim table."
            ));
        } else {
            self.record(format!("[t{tick}] SIGNAL '{signal}' -> pid={pid} \"{name}\": delivered (no effect)."));
        }
        Ok(())
    }

    /// King Crimson: erase the last `ticks_back` ticks by restoring the snapshot
    /// taken that many ticks ago. The caster must exist in that snapshot.
    pub fn king_crimson_erase(&mut self, caster: u64, ticks_back: u64) -> Result<(), String> {
        self.require_stand(caster, Stand::KingCrimson)?;
        let target_tick = self.tick.checked_sub(ticks_back).ok_or_else(|| "cannot erase past t0".to_string())?;
        let snap = self
            .history
            .iter()
            .find(|s| s.tick == target_tick)
            .cloned()
            .ok_or_else(|| format!("no snapshot for tick {target_tick} (outside history window)"))?;

        let from = self.tick;
        self.processes = snap.processes;
        self.order = snap.order;
        self.tick = snap.tick;
        // Drop any snapshots that are now in the "erased" future.
        while self.history.back().map(|s| s.tick > self.tick).unwrap_or(false) {
            self.history.pop_back();
        }
        self.record(format!(
            "[t{from}] ABILITY King Crimson (pid={caster}) ERASES TIME: rolled back {ticks_back} tick(s) to t{target_tick}. State restored."
        ));
        Ok(())
    }

    /// Sticky Fingers: zip a process (and its queue, which travels with it) into
    /// a different scheduler lane / namespace.
    pub fn sticky_fingers_zip(&mut self, caster: u64, target: u64, new_lane: &str) -> Result<(), String> {
        self.require_stand(caster, Stand::StickyFingers)?;
        let tick = self.tick;
        let proc = self.processes.get_mut(&target).ok_or_else(|| format!("no such target pid {target}"))?;
        let old_lane = proc.lane.clone();
        let name = proc.name.clone();
        let qlen = proc.queue.len();
        proc.lane = new_lane.to_string();
        self.record(format!(
            "[t{tick}] ABILITY Sticky Fingers (pid={caster}) ZIPS pid={target} \"{name}\" (+{qlen} queued tasks) from lane '{old_lane}' -> '{new_lane}'."
        ));
        Ok(())
    }

    fn require_stand(&self, pid: u64, stand: Stand) -> Result<(), String> {
        match self.processes.get(&pid) {
            None => Err(format!("no such caster pid {pid}")),
            Some(p) if p.stand == Some(stand) => Ok(()),
            Some(p) => Err(format!(
                "pid {pid} \"{}\" is not wielding {stand} (has {:?})",
                p.name, p.stand
            )),
        }
    }

    // ---- reporting --------------------------------------------------------

    /// A compact one-line-per-process status table.
    pub fn table(&self) -> String {
        let mut out = String::new();
        out.push_str("  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND\n");
        for pid in &self.order {
            let Some(p) = self.processes.get(pid) else { continue };
            let stand = p.stand.map(|s| s.to_string()).unwrap_or_else(|| "-".into());
            out.push_str(&format!(
                "  {:<3}  {}  {:<6}  {:<12}  {:<4}  {:<5}  {}\n",
                p.pid,
                p.state.glyph(),
                p.frozen_ticks,
                p.lane,
                p.work_done,
                p.queue.len(),
                stand
            ));
        }
        out
    }
}
