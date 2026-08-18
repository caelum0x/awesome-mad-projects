//! The simulated process type. Everything here is plain in-memory data.

use std::collections::VecDeque;

use crate::stand::Stand;

/// Lifecycle state of a simulated process.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProcState {
    /// Has work queued and is eligible to run.
    Ready,
    /// Ran during the most recent tick.
    Running,
    /// No work left in its queue.
    Idle,
    /// Frozen by "The World"; will not advance for `frozen_ticks` more ticks.
    Frozen,
    /// Removed from scheduling but still visible in the last log line.
    Terminated,
}

impl ProcState {
    pub fn glyph(self) -> &'static str {
        match self {
            ProcState::Ready => "READY",
            ProcState::Running => "RUN  ",
            ProcState::Idle => "IDLE ",
            ProcState::Frozen => "FROZEN",
            ProcState::Terminated => "DEAD ",
        }
    }
}

/// A single unit of simulated work sitting in a process's queue.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Task {
    pub label: String,
}

impl Task {
    pub fn new(label: impl Into<String>) -> Self {
        Task { label: label.into() }
    }
}

/// A simulated process. This is NOT an OS process — it is an in-memory actor
/// owned entirely by the [`crate::scheduler::Scheduler`].
#[derive(Debug, Clone)]
pub struct SimProcess {
    pub pid: u64,
    pub name: String,
    /// Scheduler lane / namespace the process lives in.
    pub lane: String,
    pub state: ProcState,
    /// Pending work items.
    pub queue: VecDeque<Task>,
    /// Remaining ticks during which the process is frozen by "The World".
    pub frozen_ticks: u32,
    /// Total work items completed so far (progress counter).
    pub work_done: u32,
    /// Bound Stand ability, if any.
    pub stand: Option<Stand>,
    /// Set by Killer Queen: the next signal terminates this process.
    pub primed: bool,
}

impl SimProcess {
    pub fn new(pid: u64, name: impl Into<String>, lane: impl Into<String>, tasks: Vec<Task>) -> Self {
        let queue: VecDeque<Task> = tasks.into();
        let state = if queue.is_empty() { ProcState::Idle } else { ProcState::Ready };
        SimProcess {
            pid,
            name: name.into(),
            lane: lane.into(),
            state,
            queue,
            frozen_ticks: 0,
            work_done: 0,
            stand: None,
            primed: false,
        }
    }

    pub fn is_frozen(&self) -> bool {
        self.frozen_ticks > 0
    }

    pub fn is_alive(&self) -> bool {
        self.state != ProcState::Terminated
    }

    /// Advance one step: pop and complete a single task if possible.
    /// Returns the label of the completed task, if any.
    pub fn step(&mut self) -> Option<String> {
        if let Some(task) = self.queue.pop_front() {
            self.work_done += 1;
            self.state = if self.queue.is_empty() { ProcState::Idle } else { ProcState::Running };
            Some(task.label)
        } else {
            self.state = ProcState::Idle;
            None
        }
    }
}
