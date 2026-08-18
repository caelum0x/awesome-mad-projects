//! A small command interface for driving the simulation. Commands are plain
//! data; [`Command::apply`] executes one against a [`Scheduler`]. This keeps the
//! demo (and any future REPL) decoupled from the engine internals.

use crate::process::Task;
use crate::scheduler::Scheduler;
use crate::stand::Stand;

/// A single instruction to the simulation engine.
#[derive(Debug, Clone)]
pub enum Command {
    /// Create a process in a lane with a list of task labels.
    Spawn { name: String, lane: String, tasks: Vec<String> },
    /// Bind a Stand to a process.
    AssignStand { pid: u64, stand: Stand },
    /// Advance the simulation by `n` ticks.
    Tick { n: u64 },
    /// The World: freeze others for `ticks`.
    TheWorld { caster: u64, ticks: u32 },
    /// Killer Queen: prime a target.
    KillerQueenMark { caster: u64, target: u64 },
    /// Deliver a signal (may detonate a primed target).
    Signal { pid: u64, signal: String },
    /// King Crimson: erase `ticks_back` ticks.
    KingCrimsonErase { caster: u64, ticks_back: u64 },
    /// Sticky Fingers: zip a process to a new lane.
    StickyFingersZip { caster: u64, target: u64, new_lane: String },
}

impl Command {
    /// Execute this command. Returns the new pid for `Spawn`, else `None`.
    /// Engine errors are surfaced into the scheduler log rather than panicking.
    pub fn apply(self, sched: &mut Scheduler) -> Option<u64> {
        match self {
            Command::Spawn { name, lane, tasks } => {
                let tasks = tasks.into_iter().map(Task::new).collect();
                return Some(sched.spawn(&name, &lane, tasks));
            }
            Command::AssignStand { pid, stand } => {
                let r = sched.assign_stand(pid, stand);
                log_err(sched, r);
            }
            Command::Tick { n } => {
                for _ in 0..n {
                    sched.tick();
                }
            }
            Command::TheWorld { caster, ticks } => {
                let r = sched.the_world(caster, ticks);
                log_err(sched, r);
            }
            Command::KillerQueenMark { caster, target } => {
                let r = sched.killer_queen_mark(caster, target);
                log_err(sched, r);
            }
            Command::Signal { pid, signal } => {
                let r = sched.send_signal(pid, &signal);
                log_err(sched, r);
            }
            Command::KingCrimsonErase { caster, ticks_back } => {
                let r = sched.king_crimson_erase(caster, ticks_back);
                log_err(sched, r);
            }
            Command::StickyFingersZip { caster, target, new_lane } => {
                let r = sched.sticky_fingers_zip(caster, target, &new_lane);
                log_err(sched, r);
            }
        }
        None
    }
}

fn log_err(sched: &mut Scheduler, r: Result<(), String>) {
    if let Err(e) = r {
        sched.log.push(format!("[t{}] ERROR: {e}", sched.tick));
    }
}
