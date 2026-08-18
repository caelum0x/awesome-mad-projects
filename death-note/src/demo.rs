//! Scripted end-to-end demo: spawn a few owned processes, write a mix of valid,
//! invalid and duplicate entries, then watch the valid ones get reaped on
//! schedule while the invalid/duplicate ones do nothing.

use crate::config::Config;
use crate::ops::{self, WriteOutcome};
use crate::registry::{self, State};
use crate::safety;
use std::thread::sleep;
use std::time::Duration;

pub fn run(cfg: &Config) -> Result<(), String> {
    let our_uid = safety::current_uid()?;

    // Fresh session so the demo is reproducible.
    let _ = std::fs::remove_file(cfg.home.join("session.tsv"));
    let _ = std::fs::remove_file(cfg.home.join("ledger.log"));

    banner();

    // 1. Spawn three harmless OWNED sandbox processes.
    println!("== Spawning owned sandbox processes (harmless `sleep`) ==");
    for name in ["Alpha", "Bravo", "Charlie"] {
        let p = ops::spawn(cfg, name)?;
        println!("  spawned '{}' -> pid {} (owned, tracked)", p.name, p.pid);
    }
    println!();

    // 2. Write entries into the Death Note.
    println!("== Writing Death Note entries ==");

    // Valid, default cause (heart attack / SIGTERM).
    report_write("Alpha (valid, default heart attack)", ops::write(cfg, "Alpha", None)?);

    // Valid, explicit cause (accident / SIGKILL).
    report_write(
        "Bravo (valid, cause=accident/SIGKILL)",
        ops::write(cfg, "Bravo", Some("accident"))?,
    );

    // Invalid name: not one of our processes. Written a few times => no effect,
    // then permanently void.
    for _ in 0..4 {
        report_write("Nobody (misspelling, unregistered)", ops::write(cfg, "Nobody", None)?);
    }

    // Duplicate: Alpha is already condemned => void.
    report_write("Alpha again (duplicate)", ops::write(cfg, "Alpha", Some("accident"))?);

    // Charlie is intentionally left un-noted: it should SURVIVE and be cleaned
    // up at the end, proving we only reap what was validly written.
    println!("  (Charlie deliberately left un-noted — it should survive)\n");

    // 3. Watch the reaper enforce the schedule.
    println!("== Watching the reaper (valid entries die on schedule) ==");
    let deadline = crate::clock::now() + cfg.delay + 15;
    loop {
        for ev in ops::tick(cfg, our_uid)? {
            println!("  {ev}");
        }
        let session = registry::load(&cfg.home);
        if !ops::has_pending(&session) || crate::clock::now() > deadline {
            break;
        }
        sleep(Duration::from_millis(400));
    }
    println!();

    // 4. Final state (let signals settle so liveness is accurate).
    sleep(Duration::from_millis(400));
    println!("== Final state ==");
    let session = registry::load(&cfg.home);
    for p in &session.procs {
        let alive = crate::proccheck::is_alive(p.pid);
        println!(
            "  {:<8} pid={:<7} state={:<10} alive={}",
            p.name,
            p.pid,
            format!("{:?}", p.state),
            alive
        );
    }
    println!();

    // 5. Clean up any survivors (only our own, verified).
    println!("== Cleanup (only our own verified processes) ==");
    for ev in ops::cleanup(cfg, our_uid)? {
        println!("  {ev}");
    }

    // Confirm nothing of ours is left running.
    sleep(Duration::from_millis(400));
    let session = registry::load(&cfg.home);
    let survivors: Vec<_> = session
        .procs
        .iter()
        .filter(|p| crate::proccheck::is_alive(p.pid))
        .collect();
    println!();
    if survivors.is_empty() {
        println!("All owned sandbox processes accounted for. Nothing stray left behind.");
    } else {
        for p in survivors {
            println!("  NOTE: '{}' pid {} still alive", p.name, p.pid);
        }
    }

    println!("\n== Ledger ==");
    print!("{}", registry::ledger_read(&cfg.home));
    Ok(())
}

fn report_write(label: &str, outcome: WriteOutcome) {
    match outcome {
        WriteOutcome::Condemned { pid, cause, .. } => {
            println!("  '{label}' -> CONDEMNED pid={pid} cause='{cause}'");
        }
        WriteOutcome::VoidMisspelled { count, permanent } => {
            if permanent {
                println!("  '{label}' -> NO EFFECT (permanently void after {count} misspellings)");
            } else {
                println!("  '{label}' -> NO EFFECT (misspelling #{count})");
            }
        }
        WriteOutcome::VoidAlreadyUsed => {
            println!("  '{label}' -> VOID (a name cannot be killed twice)");
        }
    }
}

fn banner() {
    // Keep the safety framing loud, even in the demo output.
    let _ = State::Alive;
    println!("┌────────────────────────────────────────────────────────────┐");
    println!("│  DEATH NOTE — SAFE SANDBOX PROCESS REAPER                   │");
    println!("│  Reaps ONLY the harmless `sleep` processes it spawned.      │");
    println!("│  Never targets arbitrary PIDs. Never runs as root.         │");
    println!("└────────────────────────────────────────────────────────────┘\n");
}
