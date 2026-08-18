//! ============================================================================
//!  ██  SAFETY CORE — READ THIS BEFORE ANYTHING ELSE  ██
//! ============================================================================
//!
//!  This program is a SANDBOX toy. It is NOT a system process killer.
//!
//!  The ONLY processes it is ever allowed to touch are the harmless
//!  `sleep` processes that IT ITSELF spawned in a previous `spawn` command.
//!  Those processes:
//!    * are owned by the current (non-root) user,
//!    * do nothing but sleep,
//!    * are recorded in the session registry together with a PID-reuse
//!      "start signature" and an ownership token.
//!
//!  HARD RULES ENFORCED IN CODE (see `verify_owned` + the reaper):
//!    1. It NEVER accepts an arbitrary system PID from the user. The Death Note
//!       is written with a NAME (a label you assigned to one of OUR processes),
//!       never a raw PID.
//!    2. Before sending ANY signal it re-verifies that the target PID:
//!         - is present in OUR session registry (we spawned it),
//!         - is still alive,
//!         - is owned by OUR uid,
//!         - still looks like our sandbox `sleep` process, and
//!         - has the SAME process start signature we recorded at spawn time
//!           (this defeats PID reuse — if the PID was recycled by the OS into
//!            some other program, verification FAILS and we refuse).
//!    3. It REFUSES to run as root.
//!    4. No kernel modules. No eBPF. No `unsafe`. No ptrace. Nothing privileged.
//!       Signals are delivered with the ordinary `kill(1)` command, restricted
//!       to PIDs that passed every check above.
//!
//!  If ANY check fails, the entry is voided and NO signal is sent. By design,
//!  there is no code path that can target a process this tool did not create.
//! ============================================================================

use crate::proccheck;
use crate::registry::Proc;
use std::process::Command;

/// Marker embedded into every spawned sandbox process' argv[0] (best effort).
pub const SANDBOX_TOKEN: &str = "deathnote_sandbox";

/// Refuse to run with root privileges. Loud and non-negotiable.
pub fn ensure_not_root() -> Result<(), String> {
    let uid = current_uid()?;
    if uid == 0 {
        return Err(
            "SAFETY REFUSAL: this sandbox must NEVER run as root (uid 0). Aborting.".to_string(),
        );
    }
    Ok(())
}

/// Read the current user's uid via `id -u` (no `unsafe`, no libc).
pub fn current_uid() -> Result<u32, String> {
    let out = Command::new("id")
        .arg("-u")
        .output()
        .map_err(|e| format!("cannot determine uid: {e}"))?;
    String::from_utf8_lossy(&out.stdout)
        .trim()
        .parse::<u32>()
        .map_err(|e| format!("cannot parse uid: {e}"))
}

/// The single gate every reap must pass through.
///
/// Returns Ok only if the process is provably one of OURS and unchanged since
/// we spawned it. Any doubt => Err => the caller must refuse to signal.
pub fn verify_owned(proc: &Proc, our_uid: u32) -> Result<(), String> {
    // 1. It must still be alive (kill -0 sends NO signal, only checks existence).
    if !proccheck::is_alive(proc.pid) {
        return Err(format!("pid {} is not alive", proc.pid));
    }

    // 2. It must be owned by US, not some other user / not a system daemon.
    match proccheck::uid_of(proc.pid) {
        Some(uid) if uid == our_uid => {}
        Some(uid) => {
            return Err(format!(
                "pid {} is owned by uid {}, not us ({}) — REFUSING",
                proc.pid, uid, our_uid
            ))
        }
        None => return Err(format!("cannot read owner of pid {}", proc.pid)),
    }

    // 3. PID-reuse guard: the OS may recycle a PID into a totally different
    //    program. If the recorded start signature no longer matches, this is
    //    NOT our original process anymore. Refuse hard.
    match proccheck::start_signature(proc.pid) {
        Some(sig) if sig == proc.startsig => {}
        Some(sig) => {
            return Err(format!(
                "pid {} start signature changed (recorded='{}', now='{}') — possible PID reuse, REFUSING",
                proc.pid, proc.startsig, sig
            ))
        }
        None => return Err(format!("cannot read start signature of pid {}", proc.pid)),
    }

    // 4. It must still look like our harmless sandbox sleep process.
    match proccheck::command_of(proc.pid) {
        Some(cmd) => {
            let ours = cmd.contains(SANDBOX_TOKEN) || cmd.contains("sleep");
            if !ours {
                return Err(format!(
                    "pid {} no longer looks like our sandbox process (cmd='{}') — REFUSING",
                    proc.pid, cmd
                ));
            }
        }
        None => return Err(format!("cannot read command line of pid {}", proc.pid)),
    }

    Ok(())
}
