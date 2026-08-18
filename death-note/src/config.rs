//! Runtime configuration. All timings are SCALED DOWN from the canon so the
//! demo finishes in seconds instead of the canonical 40 seconds.

use std::path::PathBuf;

/// Canonical Death Note delay is "40 seconds". We scale it down by default so
/// the demo is quick; override with env vars for the full experience.
pub struct Config {
    /// Directory holding this session's registry + ledger.
    pub home: PathBuf,
    /// Seconds between writing a name and the process dying. Canon: 40s.
    pub delay: u64,
    /// Seconds after writing a name in which a specific cause may still be
    /// written. Canon: 40s (6m40s for extra details). Here it defaults to the
    /// same as `delay`.
    pub window: u64,
    /// How long a freshly spawned sandbox `sleep` lives if never noted.
    pub life: u64,
}

impl Config {
    pub fn load() -> Self {
        let home = std::env::var("DEATHNOTE_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from(".deathnote_session"));
        let delay = env_u64("DEATHNOTE_DELAY", 4);
        let window = env_u64("DEATHNOTE_WINDOW", delay);
        let life = env_u64("DEATHNOTE_LIFE", 300);
        Config {
            home,
            delay,
            window,
            life,
        }
    }
}

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

/// Max number of times a wrong (unregistered) name may be written before it is
/// PERMANENTLY voided — the canonical "misspelling" rule.
pub const MAX_MISSPELLINGS: u32 = 3;
