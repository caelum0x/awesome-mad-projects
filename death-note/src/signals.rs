//! Mapping from a "cause of death" (as written in the Death Note) to the actual
//! POSIX signal we send — ONLY ever to one of our own verified sandbox
//! processes.

/// A resolved cause: the signal name to pass to `kill -s`, a human label, and
/// whether it is lethal (STOP merely pauses; it is not a death by itself).
pub struct Cause {
    pub signal: &'static str,
    pub human: &'static str,
    pub lethal: bool,
}

pub const DEFAULT_CAUSE: &str = "heart_attack";

/// Resolve a cause string. Unknown causes fall back to the default heart attack,
/// mirroring the canon: without a specified cause, the target dies of a heart
/// attack.
pub fn resolve(cause: &str) -> Cause {
    match cause.trim().to_lowercase().as_str() {
        "heart_attack" | "heartattack" | "heart" | "" => Cause {
            signal: "TERM",
            human: "heart attack (SIGTERM)",
            lethal: true,
        },
        "accident" | "sigkill" | "kill" => Cause {
            signal: "KILL",
            human: "accident (SIGKILL)",
            lethal: true,
        },
        "coma" | "sigstop" | "stop" | "sleep" => Cause {
            signal: "STOP",
            human: "coma (SIGSTOP — paused, not dead; cleaned up later)",
            lethal: false,
        },
        // We CANNOT and WILL NOT actually exhaust memory. "oom" is simulated as
        // a plain SIGKILL, clearly labelled as such.
        "oom" | "starvation" => Cause {
            signal: "KILL",
            human: "OOM-style kill (SIGKILL — SIMULATED, no real memory pressure)",
            lethal: true,
        },
        // Anything unrecognised => default heart attack (canon behaviour).
        _ => Cause {
            signal: "TERM",
            human: "heart attack (SIGTERM, default — unrecognised cause)",
            lethal: true,
        },
    }
}

/// Deliver a signal by name to a specific pid using `kill -s`.
///
/// SAFETY: callers MUST have passed `safety::verify_owned` for this pid first.
/// This function is a thin wrapper and does no verification of its own.
pub fn send(pid: u32, signal: &str) -> Result<(), String> {
    let out = std::process::Command::new("kill")
        .arg("-s")
        .arg(signal)
        .arg(pid.to_string())
        .output()
        .map_err(|e| format!("failed to run kill: {e}"))?;
    if out.status.success() {
        Ok(())
    } else {
        let err = String::from_utf8_lossy(&out.stderr).trim().to_string();
        Err(format!("kill -s {signal} {pid} failed: {err}"))
    }
}
