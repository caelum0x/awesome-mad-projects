//! ============================================================================
//!  DEATH NOTE — a SAFE, sandboxed process reaper.
//!
//!  SAFETY (see src/safety.rs for the enforced guarantees):
//!    * It only ever reaps the harmless `sleep` processes it spawned itself.
//!    * You write a NAME (a label for one of OUR processes), never a raw PID.
//!    * Every reap re-verifies ownership (uid + PID-reuse guard + our marker).
//!    * It refuses to run as root. No unsafe. No kernel modules. No eBPF.
//! ============================================================================

mod clock;
mod config;
mod demo;
mod ops;
mod proccheck;
mod registry;
mod safety;
mod signals;

use config::Config;
use std::thread::sleep;
use std::time::Duration;

fn main() {
    if let Err(e) = real_main() {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}

fn real_main() -> Result<(), String> {
    // SAFETY: never proceed as root, for any sub-command.
    safety::ensure_not_root()?;

    let cfg = Config::load();
    let args: Vec<String> = std::env::args().skip(1).collect();
    let cmd = args.first().map(String::as_str).unwrap_or("help");

    match cmd {
        "spawn" => cmd_spawn(&cfg, &args),
        "write" => cmd_write(&cfg, &args),
        "cause" => cmd_cause(&cfg, &args),
        "list" | "ls" => cmd_list(&cfg),
        "watch" => cmd_watch(&cfg, &args),
        "reap" | "tick" => cmd_tick(&cfg),
        "cleanup" | "reset" => cmd_cleanup(&cfg),
        "ledger" => {
            print!("{}", registry::ledger_read(&cfg.home));
            Ok(())
        }
        "demo" => demo::run(&cfg),
        "rules" => {
            print_rules();
            Ok(())
        }
        "help" | "-h" | "--help" => {
            print_help();
            Ok(())
        }
        other => Err(format!("unknown command '{other}' (try `help`)")),
    }
}

fn cmd_spawn(cfg: &Config, args: &[String]) -> Result<(), String> {
    let name = args.get(1).ok_or("usage: spawn <name>")?;
    let p = ops::spawn(cfg, name)?;
    println!(
        "spawned owned sandbox process '{}' pid={} (harmless sleep, lives {}s if un-noted)",
        p.name, p.pid, cfg.life
    );
    Ok(())
}

fn cmd_write(cfg: &Config, args: &[String]) -> Result<(), String> {
    let name = args.get(1).ok_or("usage: write <name> [--cause CAUSE]")?;
    let cause = flag(args, "--cause");
    match ops::write(cfg, name, cause.as_deref())? {
        ops::WriteOutcome::Condemned { pid, cause, due } => {
            let secs = due.saturating_sub(clock::now());
            println!("'{name}' (pid {pid}) CONDEMNED — cause '{cause}', dies in ~{secs}s. Run `watch`.");
        }
        ops::WriteOutcome::VoidMisspelled { count, permanent } => {
            if permanent {
                println!("'{name}' has NO EFFECT — permanently void after {count} misspellings.");
            } else {
                println!("'{name}' has NO EFFECT — not one of our processes (misspelling #{count}).");
            }
        }
        ops::WriteOutcome::VoidAlreadyUsed => {
            println!("'{name}' is VOID — a name cannot be killed twice.");
        }
    }
    Ok(())
}

fn cmd_cause(cfg: &Config, args: &[String]) -> Result<(), String> {
    let name = args.get(1).ok_or("usage: cause <name> <CAUSE>")?;
    let cause = args.get(2).ok_or("usage: cause <name> <CAUSE>")?;
    if ops::set_cause(cfg, name, cause)? {
        println!("cause for '{name}' set to '{cause}'.");
    } else {
        println!("cause for '{name}' REJECTED — outside the allowed window.");
    }
    Ok(())
}

fn cmd_list(cfg: &Config) -> Result<(), String> {
    let session = registry::load(&cfg.home);
    if session.procs.is_empty() {
        println!("(no owned sandbox processes; try `spawn <name>` or `demo`)");
        return Ok(());
    }
    println!("{:<10} {:<8} {:<10} {:<8} cause", "NAME", "PID", "STATE", "ALIVE");
    for p in &session.procs {
        println!(
            "{:<10} {:<8} {:<10} {:<8} {}",
            p.name,
            p.pid,
            format!("{:?}", p.state),
            proccheck::is_alive(p.pid),
            p.cause
        );
    }
    Ok(())
}

fn cmd_watch(cfg: &Config, args: &[String]) -> Result<(), String> {
    let our_uid = safety::current_uid()?;
    let once = args.iter().any(|a| a == "--once");
    let deadline = clock::now() + cfg.delay + 30;
    loop {
        for ev in ops::tick(cfg, our_uid)? {
            println!("{ev}");
        }
        let session = registry::load(&cfg.home);
        if once || !ops::has_pending(&session) || clock::now() > deadline {
            break;
        }
        sleep(Duration::from_millis(400));
    }
    println!("watch: nothing left pending.");
    Ok(())
}

fn cmd_tick(cfg: &Config) -> Result<(), String> {
    let our_uid = safety::current_uid()?;
    let events = ops::tick(cfg, our_uid)?;
    if events.is_empty() {
        println!("reap: nothing due yet.");
    } else {
        for ev in events {
            println!("{ev}");
        }
    }
    Ok(())
}

fn cmd_cleanup(cfg: &Config) -> Result<(), String> {
    let our_uid = safety::current_uid()?;
    for ev in ops::cleanup(cfg, our_uid)? {
        println!("{ev}");
    }
    println!("cleanup: done (only our own verified processes were touched).");
    Ok(())
}

/// Extract `--flag value` from args.
fn flag(args: &[String], name: &str) -> Option<String> {
    let pos = args.iter().position(|a| a == name)?;
    args.get(pos + 1).cloned()
}

fn print_help() {
    println!(
        "Death Note — SAFE sandbox process reaper\n\
\n\
USAGE:\n\
  deathnote <command> [args]\n\
\n\
COMMANDS:\n\
  spawn <name>              Spawn a harmless OWNED sandbox `sleep` process.\n\
  write <name> [--cause C]  Write a name into the note. Valid names die after\n\
                            the delay. Cause C: heart_attack (default),\n\
                            accident (SIGKILL), coma (SIGSTOP), oom (simulated).\n\
  cause <name> <C>          Amend the cause within the allowed window.\n\
  list                      Show owned processes and their state.\n\
  watch                     Run the reaper until nothing is pending.\n\
  reap                      Run one reaper tick.\n\
  cleanup                   Terminate any surviving OWNED processes.\n\
  ledger                    Print the session ledger.\n\
  demo                      Run the full scripted demonstration.\n\
  rules                     Print the enforced Death Note rules.\n\
\n\
ENV (scaled-down timings for the demo):\n\
  DEATHNOTE_DELAY   seconds until death (default 4; canon is 40)\n\
  DEATHNOTE_WINDOW  seconds a cause may still be written (default = delay)\n\
  DEATHNOTE_LIFE    seconds a spawned sleep lives if un-noted (default 300)\n\
  DEATHNOTE_HOME    session directory (default ./.deathnote_session)\n\
\n\
SAFETY: only reaps processes THIS TOOL spawned; never a raw PID; never root.\n\
Try:  deathnote demo"
    );
}

fn print_rules() {
    println!(
        "Enforced Death Note rules (faithful, scaled for the demo):\n\
  1. Writing the NAME of one of our owned processes kills it after the delay.\n\
  2. If a specific cause is written within the window, it is applied;\n\
     otherwise the target dies of the default 'heart attack' (SIGTERM).\n\
  3. A name that does not match a registered owned process has NO effect;\n\
     after a few misspellings that name is PERMANENTLY void.\n\
  4. The same name cannot be killed twice — re-entries are void.\n\
  SAFETY OVERRIDE: any entry that fails ownership verification at reap time\n\
  is voided and NO signal is sent."
    );
}
