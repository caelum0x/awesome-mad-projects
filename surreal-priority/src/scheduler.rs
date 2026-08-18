//! A tiny, deterministic priority-scheduler *simulation*.
//!
//! This touches nothing in the real operating system. It is a pure in-memory
//! model: a bag of tasks, each carrying a surreal [`Priority`] and an amount of
//! remaining work. On every tick the scheduler picks the highest-priority
//! runnable task, "runs" it for one quantum, and records the choice.
//!
//! Because priorities are surreal, we can express strictly dominant behaviour:
//! a task with priority `omega` outranks *every* finite task, so it starves
//! them until it finishes; a task with priority `1/omega` is below every
//! positive finite task, so it only runs once nothing else is runnable.

use crate::surreal::Priority;

/// A schedulable unit of work.
#[derive(Clone, Debug)]
pub struct Task {
    /// Human-readable identifier.
    pub name: String,
    /// Surreal priority governing selection order.
    pub priority: Priority,
    /// Work units still to do. The task is runnable while this is `> 0`.
    pub remaining: u32,
    /// Work units consumed per quantum.
    pub quantum: u32,
}

impl Task {
    /// Create a task. `quantum` is clamped to at least 1 so progress is
    /// guaranteed and the run loop always terminates.
    pub fn new(name: &str, priority: Priority, work: u32, quantum: u32) -> Task {
        Task {
            name: name.to_string(),
            priority,
            remaining: work,
            quantum: quantum.max(1),
        }
    }

    /// A task is runnable while it still has work left.
    pub fn is_runnable(&self) -> bool {
        self.remaining > 0
    }
}

/// One recorded scheduling decision.
#[derive(Clone, Debug)]
pub struct ScheduleEntry {
    /// Global tick index, starting at 0.
    pub tick: u32,
    /// Name of the task that ran this tick.
    pub task: String,
    /// The surreal priority it ran with (rendered for the log).
    pub priority: String,
    /// Work actually consumed this tick.
    pub ran: u32,
    /// Work left for that task after the tick.
    pub remaining_after: u32,
}

/// The scheduler owns its tasks and produces an immutable schedule log.
pub struct Scheduler {
    tasks: Vec<Task>,
    log: Vec<ScheduleEntry>,
    tick: u32,
}

impl Scheduler {
    /// Build a scheduler from an initial task set.
    pub fn new(tasks: Vec<Task>) -> Scheduler {
        Scheduler {
            tasks,
            log: Vec::new(),
            tick: 0,
        }
    }

    /// Index of the runnable task with the greatest surreal priority.
    ///
    /// Ties are broken deterministically by original task order (the earlier
    /// task wins), so runs are fully reproducible.
    fn pick(&self) -> Option<usize> {
        let mut best: Option<usize> = None;
        for (i, task) in self.tasks.iter().enumerate() {
            if !task.is_runnable() {
                continue;
            }
            match best {
                None => best = Some(i),
                Some(b) => {
                    if task.priority > self.tasks[b].priority {
                        best = Some(i);
                    }
                }
            }
        }
        best
    }

    /// Advance one tick. Returns `false` when nothing is runnable (done).
    pub fn step(&mut self) -> bool {
        let idx = match self.pick() {
            Some(i) => i,
            None => return false,
        };

        // Compute the new task state immutably, then swap it in. No task is
        // mutated in place; we replace it with an updated copy.
        let ran = self.tasks[idx].quantum.min(self.tasks[idx].remaining);
        let updated = Task {
            remaining: self.tasks[idx].remaining - ran,
            ..self.tasks[idx].clone()
        };

        self.log.push(ScheduleEntry {
            tick: self.tick,
            task: updated.name.clone(),
            priority: format!("{}", updated.priority),
            ran,
            remaining_after: updated.remaining,
        });

        self.tasks[idx] = updated;
        self.tick += 1;
        true
    }

    /// Run until every task is complete, capped at `max_ticks` for safety.
    /// Returns the full schedule log.
    pub fn run(&mut self, max_ticks: u32) -> &[ScheduleEntry] {
        while self.tick < max_ticks && self.step() {}
        &self.log
    }

    /// Read-only view of the recorded schedule.
    pub fn log(&self) -> &[ScheduleEntry] {
        &self.log
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dyadic::Dyadic;

    #[test]
    fn omega_task_starves_finite_tasks_until_done() {
        let tasks = vec![
            Task::new("infinite", Priority::omega(Dyadic::ONE), 3, 1),
            Task::new("finite", Priority::integer(5), 2, 1),
        ];
        let mut sched = Scheduler::new(tasks);
        let log = sched.run(100).to_vec();

        // The first three ticks must all belong to the omega task.
        assert_eq!(log[0].task, "infinite");
        assert_eq!(log[1].task, "infinite");
        assert_eq!(log[2].task, "infinite");
        // Only after it finishes does the finite task get to run.
        assert_eq!(log[3].task, "finite");
    }

    #[test]
    fn inv_omega_task_runs_last() {
        let tasks = vec![
            Task::new("idle", Priority::inv_omega(Dyadic::ONE), 1, 1),
            Task::new("normal", Priority::integer(1), 2, 1),
        ];
        let mut sched = Scheduler::new(tasks);
        let log = sched.run(100).to_vec();

        // The finite "normal" task drains completely first.
        assert_eq!(log[0].task, "normal");
        assert_eq!(log[1].task, "normal");
        // The infinitesimal task only runs once nothing else is runnable.
        assert_eq!(log[2].task, "idle");
    }

    #[test]
    fn all_work_completes() {
        let tasks = vec![
            Task::new("a", Priority::omega(Dyadic::ONE), 2, 1),
            Task::new("b", Priority::integer(3), 3, 2),
            Task::new("c", Priority::inv_omega(Dyadic::ONE), 1, 1),
        ];
        let mut sched = Scheduler::new(tasks);
        sched.run(100);
        assert!(sched.tasks.iter().all(|t| t.remaining == 0));
    }

    #[test]
    fn run_terminates_at_cap() {
        // A never-shrinking cap check: even with plenty of work the loop
        // respects max_ticks.
        let tasks = vec![Task::new("x", Priority::integer(1), 1000, 1)];
        let mut sched = Scheduler::new(tasks);
        sched.run(5);
        assert_eq!(sched.log().len(), 5);
    }
}
