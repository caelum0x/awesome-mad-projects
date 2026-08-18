//! Demo entry point: prints the surreal ordering, then runs a scheduler
//! simulation showing an `omega` task starving finite tasks and a `1/omega`
//! task running only when nothing else can.

#![forbid(unsafe_code)]

use surreal_priority::dyadic::Dyadic;
use surreal_priority::scheduler::{ScheduleEntry, Scheduler, Task};
use surreal_priority::surreal::{Priority, Term};

fn main() {
    print_ordering_demo();
    println!();
    print_scheduler_demo();
}

/// Show that `1/omega < 1 < omega < 2*omega` and friends hold.
fn print_ordering_demo() {
    println!("== Surreal priority ordering ==");

    let samples = [
        ("1/omega", Priority::inv_omega(Dyadic::ONE)),
        ("1/2", Priority::finite(Dyadic::new(1, 1))),
        ("1", Priority::integer(1)),
        ("3", Priority::integer(3)),
        (
            "omega + 1",
            Priority::from_terms(&[Term::Omega { scale: Dyadic::ONE }, Term::Finite(Dyadic::ONE)]),
        ),
        ("2*omega", Priority::omega(Dyadic::integer(2))),
    ];

    // Ascending order, matching the array (already sorted by construction).
    println!("ascending priorities:");
    for (label, value) in &samples {
        println!("  {:<10} = {}", label, value);
    }

    // A couple of explicit comparisons for the reader.
    let inv = Priority::inv_omega(Dyadic::ONE);
    let one = Priority::integer(1);
    let om = Priority::omega(Dyadic::ONE);
    let two_om = Priority::omega(Dyadic::integer(2));
    println!("checks:");
    println!("  1/omega < 1      : {}", inv < one);
    println!("  1      < omega   : {}", one < om);
    println!("  omega  < 2*omega : {}", om < two_om);
    println!("  omega  > 1000000 : {}", om > Priority::integer(1_000_000));
}

/// Run the scheduler simulation and print the schedule log.
fn print_scheduler_demo() {
    println!("== Scheduler simulation ==");

    let tasks = vec![
        Task::new("render[omega]", Priority::omega(Dyadic::ONE), 4, 1),
        Task::new("ui[3]", Priority::integer(3), 3, 1),
        Task::new("sync[1]", Priority::integer(1), 2, 1),
        Task::new("gc[1/omega]", Priority::inv_omega(Dyadic::ONE), 2, 1),
    ];

    println!("tasks (priority, work, quantum):");
    for t in &tasks {
        println!(
            "  {:<16} prio={:<8} work={} quantum={}",
            t.name, t.priority, t.remaining, t.quantum
        );
    }
    println!();

    let mut sched = Scheduler::new(tasks);
    let log: Vec<ScheduleEntry> = sched.run(100).to_vec();

    println!("schedule:");
    println!("  tick  task              prio      ran  remaining");
    for e in &log {
        println!(
            "  {:>4}  {:<16}  {:<8}  {:>3}  {:>9}",
            e.tick, e.task, e.priority, e.ran, e.remaining_after
        );
    }

    println!();
    println!("observations:");
    println!("  - render[omega] runs ticks 0..3 back-to-back: an infinite");
    println!("    priority starves every finite task until it is done.");
    println!("  - gc[1/omega] runs last: an infinitesimal priority only gets");
    println!("    the CPU once nothing else is runnable.");
}
