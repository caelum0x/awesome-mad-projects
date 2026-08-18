//! Read-only process inspection helpers.
//!
//! Everything here is NON-destructive. `is_alive` uses `kill -0`, which sends
//! NO signal — it only asks the kernel "does this pid exist?". The `ps` calls
//! read metadata only. None of these functions can harm a process.

use std::process::Command;

/// True if the pid currently exists AND is not a zombie/defunct.
///
/// `kill -0` delivers no signal — it only checks existence. A process we have
/// already reaped may briefly linger as a zombie (state 'Z') until the OS
/// cleans it up; for our purposes that is dead.
pub fn is_alive(pid: u32) -> bool {
    if !exists(pid) {
        return false;
    }
    match ps_field(pid, "state=") {
        Some(state) => !state.starts_with('Z'),
        None => true,
    }
}

/// Does the pid exist at all? `kill -0` sends no signal. Exit is failure for
/// both "no such process" and "permission denied"; the latter still means the
/// process EXISTS (it just belongs to someone else), so we distinguish via
/// stderr. This lets `verify_owned` reach the uid check and refuse with an
/// accurate "owned by another uid" message. Output is captured (never leaked).
fn exists(pid: u32) -> bool {
    match Command::new("kill").arg("-0").arg(pid.to_string()).output() {
        Ok(out) if out.status.success() => true,
        Ok(out) => {
            let err = String::from_utf8_lossy(&out.stderr).to_lowercase();
            err.contains("permit") || err.contains("permission")
        }
        Err(_) => false,
    }
}

/// Process start time string (e.g. "Tue Aug 18 10:11:12 2026").
/// Used as a PID-reuse guard: it is effectively unique per process instance.
pub fn start_signature(pid: u32) -> Option<String> {
    ps_field(pid, "lstart=")
}

/// Full command line of the process (argv), for our sandbox-marker check.
pub fn command_of(pid: u32) -> Option<String> {
    ps_field(pid, "command=")
}

/// Numeric owner uid of the process.
pub fn uid_of(pid: u32) -> Option<u32> {
    ps_field(pid, "uid=").and_then(|s| s.parse().ok())
}

fn ps_field(pid: u32, field: &str) -> Option<String> {
    let out = Command::new("ps")
        .args(["-p", &pid.to_string(), "-o", field])
        .output()
        .ok()?;
    let s = String::from_utf8_lossy(&out.stdout).trim().to_string();
    if s.is_empty() {
        None
    } else {
        Some(s)
    }
}
