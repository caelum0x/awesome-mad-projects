//! High-level operations shared by the CLI sub-commands and the scripted demo.

use crate::clock;
use crate::config::{Config, MAX_MISSPELLINGS};
use crate::registry::{self, Proc, Session, State};
use crate::safety::{self, SANDBOX_TOKEN};
use crate::signals;
use std::process::Command;

/// Names are LABELS you assign to our processes — never PIDs. Reject anything
/// that is not a tidy label, and loudly reject bare numbers (a common attempt
/// to sneak a PID in through the name field).
pub fn validate_name(name: &str) -> Result<(), String> {
    if name.is_empty() || name.len() > 64 {
        return Err("name must be 1..=64 characters".into());
    }
    if name.chars().all(|c| c.is_ascii_digit()) {
        return Err(
            "names are LABELS, not PIDs. This tool never targets a raw PID (safety).".into(),
        );
    }
    if !name
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
    {
        return Err("name may only contain [A-Za-z0-9_-]".into());
    }
    Ok(())
}

/// Spawn a harmless owned sandbox `sleep` process and register it under `name`.
pub fn spawn(cfg: &Config, name: &str) -> Result<Proc, String> {
    validate_name(name)?;
    let mut session = registry::load(&cfg.home);
    if session.find(name).is_some() {
        return Err(format!("a process named '{name}' already exists"));
    }

    // Best effort: set argv[0] to our token so `ps` shows we own it. If the
    // shell lacks `exec -a`, the child simply runs plain `sleep` and our other
    // guards (registry membership + uid + start signature) still hold.
    let argv0 = format!("{SANDBOX_TOKEN}_{name}");
    let script = format!("exec -a '{argv0}' sleep {}", cfg.life);
    let child = Command::new("/bin/sh")
        .arg("-c")
        .arg(&script)
        .spawn()
        .map_err(|e| format!("failed to spawn sandbox process: {e}"))?;
    let pid = child.id();

    // Give the OS a moment, then capture the start signature (PID-reuse guard).
    std::thread::sleep(std::time::Duration::from_millis(120));
    let startsig = crate::proccheck::start_signature(pid).unwrap_or_default();

    let proc = Proc {
        name: name.to_string(),
        pid,
        startsig,
        token: argv0,
        state: State::Alive,
        cause: String::new(),
        due: 0,
    };
    session.procs.push(proc.clone());
    registry::save(&cfg.home, &session)?;
    registry::ledger_append(
        &cfg.home,
        &format!("SPAWN name='{name}' pid={pid} (harmless owned sleep)"),
    );
    Ok(proc)
}

/// Outcome of writing a name into the Death Note.
pub enum WriteOutcome {
    Condemned { pid: u32, cause: String, due: u64 },
    VoidMisspelled { count: u32, permanent: bool },
    VoidAlreadyUsed,
}

/// Write a NAME (and optional cause) into the Death Note.
///
/// Canonical rules enforced here:
///  * a valid, still-ALIVE name is condemned to die after `delay`;
///  * a wrong name has NO effect, and after MAX_MISSPELLINGS is permanently void;
///  * a name that is already condemned/reaped cannot be killed again (void).
pub fn write(cfg: &Config, name: &str, cause: Option<&str>) -> Result<WriteOutcome, String> {
    validate_name(name)?;
    let mut session = registry::load(&cfg.home);

    // Permanently-void misspellings never do anything again.
    if session.miss_count(name) >= MAX_MISSPELLINGS {
        registry::ledger_append(
            &cfg.home,
            &format!("WRITE name='{name}' -> VOID (permanently misspelled)"),
        );
        return Ok(WriteOutcome::VoidMisspelled {
            count: session.miss_count(name),
            permanent: true,
        });
    }

    // Look the name up among OUR processes. No match => misspelling, no effect.
    let Some(idx) = session.procs.iter().position(|p| p.name == name) else {
        let count = session.bump_miss(name);
        registry::save(&cfg.home, &session)?;
        let permanent = count >= MAX_MISSPELLINGS;
        registry::ledger_append(
            &cfg.home,
            &format!("WRITE name='{name}' -> NO EFFECT (misspelling {count}/{MAX_MISSPELLINGS})"),
        );
        return Ok(WriteOutcome::VoidMisspelled { count, permanent });
    };

    // The same name cannot be killed twice.
    if session.procs[idx].state != State::Alive {
        registry::ledger_append(
            &cfg.home,
            &format!("WRITE name='{name}' -> VOID (already used; cannot kill twice)"),
        );
        return Ok(WriteOutcome::VoidAlreadyUsed);
    }

    // Condemn it. Cause defaults to heart attack; a specific cause may still be
    // amended within the window via `set_cause`.
    let cause = cause.unwrap_or(signals::DEFAULT_CAUSE).to_string();
    let due = clock::now() + cfg.delay;
    session.procs[idx].state = State::Condemned;
    session.procs[idx].cause = cause.clone();
    session.procs[idx].due = due;
    let pid = session.procs[idx].pid;
    registry::save(&cfg.home, &session)?;
    registry::ledger_append(
        &cfg.home,
        &format!("WRITE name='{name}' pid={pid} cause='{cause}' -> CONDEMNED (dies in {}s)", cfg.delay),
    );
    Ok(WriteOutcome::Condemned { pid, cause, due })
}

/// Amend the cause of an already-condemned name, allowed only within the window
/// (`due - window .. due`). Mirrors the canon: the cause must be added shortly
/// after the name.
pub fn set_cause(cfg: &Config, name: &str, cause: &str) -> Result<bool, String> {
    let mut session = registry::load(&cfg.home);
    let Some(idx) = session.procs.iter().position(|p| p.name == name) else {
        return Err(format!("no owned process named '{name}'"));
    };
    if session.procs[idx].state != State::Condemned {
        return Err(format!("'{name}' is not currently condemned"));
    }
    let now = clock::now();
    let due = session.procs[idx].due;
    let window_start = due.saturating_sub(cfg.window);
    if now < window_start || now > due {
        registry::ledger_append(
            &cfg.home,
            &format!("CAUSE name='{name}' cause='{cause}' -> REJECTED (outside window)"),
        );
        return Ok(false);
    }
    session.procs[idx].cause = cause.to_string();
    registry::save(&cfg.home, &session)?;
    registry::ledger_append(
        &cfg.home,
        &format!("CAUSE name='{name}' cause='{cause}' -> applied"),
    );
    Ok(true)
}

/// One reaper tick: reap every condemned process whose time has come, each one
/// only after passing the full ownership verification. Returns event lines.
pub fn tick(cfg: &Config, our_uid: u32) -> Result<Vec<String>, String> {
    let mut session = registry::load(&cfg.home);
    let now = clock::now();
    let mut events = Vec::new();

    for i in 0..session.procs.len() {
        if session.procs[i].state != State::Condemned {
            continue;
        }
        if session.procs[i].due > now {
            continue; // not yet
        }

        let proc = session.procs[i].clone();

        // THE SAFETY GATE. No signal is sent unless this passes.
        if let Err(reason) = safety::verify_owned(&proc, our_uid) {
            session.procs[i].state = State::Void;
            let msg = format!(
                "REFUSED to reap '{}' (pid {}): {} — entry voided",
                proc.name, proc.pid, reason
            );
            registry::ledger_append(&cfg.home, &msg);
            events.push(msg);
            continue;
        }

        let cause = signals::resolve(&proc.cause);
        match signals::send(proc.pid, cause.signal) {
            Ok(()) => {
                session.procs[i].state = State::Reaped;
                let msg = format!(
                    "REAPED '{}' (pid {}) via {}{}",
                    proc.name,
                    proc.pid,
                    cause.human,
                    if cause.lethal { "" } else { " [still paused]" }
                );
                registry::ledger_append(&cfg.home, &msg);
                events.push(msg);
            }
            Err(e) => {
                session.procs[i].state = State::Void;
                let msg = format!("FAILED to signal '{}' (pid {}): {e}", proc.name, proc.pid);
                registry::ledger_append(&cfg.home, &msg);
                events.push(msg);
            }
        }
    }

    registry::save(&cfg.home, &session)?;
    Ok(events)
}

/// True while any process is still condemned and waiting to be reaped.
pub fn has_pending(session: &Session) -> bool {
    session
        .procs
        .iter()
        .any(|p| p.state == State::Condemned)
}

/// Clean up: terminate every still-living OWNED sandbox process (verified) and
/// leave nothing stray behind. Only ever touches our own processes.
pub fn cleanup(cfg: &Config, our_uid: u32) -> Result<Vec<String>, String> {
    let mut session = registry::load(&cfg.home);
    let mut events = Vec::new();
    for i in 0..session.procs.len() {
        let st = session.procs[i].state;
        if st == State::Reaped || st == State::Void {
            // Reaped-by-coma processes are only paused; make sure they are gone.
            let proc = session.procs[i].clone();
            if st == State::Reaped && crate::proccheck::is_alive(proc.pid) {
                if safety::verify_owned(&proc, our_uid).is_ok() {
                    let _ = signals::send(proc.pid, "CONT");
                    let _ = signals::send(proc.pid, "KILL");
                    events.push(format!("cleanup: finished paused '{}'", proc.name));
                }
            }
            continue;
        }
        let proc = session.procs[i].clone();
        if !crate::proccheck::is_alive(proc.pid) {
            continue;
        }
        match safety::verify_owned(&proc, our_uid) {
            Ok(()) => {
                let _ = signals::send(proc.pid, "TERM");
                session.procs[i].state = State::Reaped;
                events.push(format!("cleanup: terminated owned '{}'", proc.name));
            }
            Err(reason) => {
                events.push(format!(
                    "cleanup: REFUSED to touch '{}': {reason}",
                    proc.name
                ));
            }
        }
    }
    registry::save(&cfg.home, &session)?;
    Ok(events)
}
