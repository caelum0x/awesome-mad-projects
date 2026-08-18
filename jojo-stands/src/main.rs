//! Demo runner for the JoJo Stand System.
//!
//! SAFETY: This binary runs a purely in-memory simulation. It does not touch
//! real OS processes, PIDs, signals, or the kernel. See README.md.

use jojo_stands::{Command, Scheduler, Stand};

fn banner(title: &str) {
    println!("\n============================================================");
    println!("  {title}");
    println!("============================================================");
}

fn drain_log(sched: &mut Scheduler) {
    for line in sched.log.drain(..) {
        println!("{line}");
    }
}

fn main() {
    banner("JoJo Stand System — in-memory process simulation");
    println!("Nothing here touches your OS. Every 'process' is a struct in a HashMap.");

    // Remember up to 8 ticks of history for King Crimson.
    let mut sched = Scheduler::new(8);

    // ---- Set up the simulated process table -------------------------------
    let jotaro = Command::Spawn {
        name: "jotaro".into(),
        lane: "main".into(),
        tasks: vec!["ora-1".into(), "ora-2".into(), "ora-3".into(), "ora-4".into(), "ora-5".into()],
    }
    .apply(&mut sched)
    .unwrap();

    let josuke = Command::Spawn {
        name: "josuke".into(),
        lane: "main".into(),
        tasks: vec!["heal-1".into(), "heal-2".into(), "heal-3".into(), "heal-4".into()],
    }
    .apply(&mut sched)
    .unwrap();

    let giorno = Command::Spawn {
        name: "giorno".into(),
        lane: "main".into(),
        tasks: vec!["muda-1".into(), "muda-2".into(), "muda-3".into(), "muda-4".into()],
    }
    .apply(&mut sched)
    .unwrap();

    let koichi = Command::Spawn {
        name: "koichi".into(),
        lane: "workers".into(),
        tasks: vec!["echoes-1".into(), "echoes-2".into(), "echoes-3".into()],
    }
    .apply(&mut sched)
    .unwrap();

    // Bind Stands.
    for cmd in [
        Command::AssignStand { pid: jotaro, stand: Stand::TheWorld },
        Command::AssignStand { pid: josuke, stand: Stand::KillerQueen },
        Command::AssignStand { pid: giorno, stand: Stand::KingCrimson },
        Command::AssignStand { pid: koichi, stand: Stand::StickyFingers },
    ] {
        cmd.apply(&mut sched);
    }
    drain_log(&mut sched);
    println!("\nInitial table:\n{}", sched.table());

    // ---- Phase 1: run a few normal ticks ----------------------------------
    banner("Phase 1: run 2 normal ticks");
    Command::Tick { n: 2 }.apply(&mut sched);
    drain_log(&mut sched);
    println!("\nTable after t{}:\n{}", sched.tick, sched.table());

    // ---- Phase 2: THE WORLD -----------------------------------------------
    banner("Phase 2: jotaro casts THE WORLD (freeze others for 2 ticks)");
    Command::TheWorld { caster: jotaro, ticks: 2 }.apply(&mut sched);
    // Two ticks pass: only jotaro advances, the rest stay frozen.
    Command::Tick { n: 2 }.apply(&mut sched);
    drain_log(&mut sched);
    println!("\nTable after time-stop (note only jotaro's work_done grew):\n{}", sched.table());

    // ---- Phase 3: KILLER QUEEN --------------------------------------------
    banner("Phase 3: josuke's Killer Queen primes giorno, then a signal detonates it");
    Command::KillerQueenMark { caster: josuke, target: giorno }.apply(&mut sched);
    Command::Signal { pid: giorno, signal: "SIGUSR1".into() }.apply(&mut sched);
    drain_log(&mut sched);
    println!("\nTable after detonation (giorno removed from sim table):\n{}", sched.table());

    // ---- Phase 4: KING CRIMSON --------------------------------------------
    banner("Phase 4: run 2 ticks, then Giorno... wait, Giorno is gone — koichi is our survivor");
    Command::Tick { n: 2 }.apply(&mut sched);
    drain_log(&mut sched);
    let before = sched.get(jotaro).map(|p| p.work_done).unwrap_or(0);
    println!("\nTable BEFORE King Crimson (jotaro work_done={before}, tick=t{}):\n{}", sched.tick, sched.table());

    // Re-assign King Crimson to a survivor (its original wielder detonated).
    banner("Phase 5: KING CRIMSON — erase the last 2 ticks (rollback)");
    Command::AssignStand { pid: jotaro, stand: Stand::KingCrimson }.apply(&mut sched);
    Command::KingCrimsonErase { caster: jotaro, ticks_back: 2 }.apply(&mut sched);
    drain_log(&mut sched);
    let after = sched.get(jotaro).map(|p| p.work_done).unwrap_or(0);
    println!(
        "\nTable AFTER King Crimson (jotaro work_done rolled {before} -> {after}, tick=t{}):\n{}",
        sched.tick,
        sched.table()
    );

    // ---- Phase 6: STICKY FINGERS ------------------------------------------
    banner("Phase 6: koichi's Sticky Fingers ZIPS jotaro from 'main' to 'isolated'");
    Command::StickyFingersZip { caster: koichi, target: jotaro, new_lane: "isolated".into() }.apply(&mut sched);
    drain_log(&mut sched);
    println!("\nFinal table:\n{}", sched.table());

    banner("Simulation complete — no real processes were harmed");
}
