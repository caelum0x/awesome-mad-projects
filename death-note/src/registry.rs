//! The session state: the set of owned sandbox processes and the misspelling
//! counters. Persisted as a tiny tab-separated file so the `spawn`, `write`,
//! `watch` and `demo` sub-commands can share state across invocations.
//!
//! We deliberately avoid a real serialization crate to keep this prototype
//! dependency-free. The format is line based:
//!
//!   PROC \t name \t pid \t startsig \t token \t state \t cause \t due_epoch
//!   MISS \t rawname \t count
//!
//! `startsig` may contain spaces (it is a date), but never a tab, so TSV is
//! safe.

use std::fs;
use std::path::{Path, PathBuf};

/// Lifecycle state of an owned sandbox process.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum State {
    /// Spawned, no valid Death Note entry yet.
    Alive,
    /// A valid name was written; scheduled to die at `due`.
    Condemned,
    /// Signal delivered; it is gone (or paused, for a coma).
    Reaped,
    /// Verification failed at reap time; we refused to signal.
    Void,
}

impl State {
    fn as_str(&self) -> &'static str {
        match self {
            State::Alive => "ALIVE",
            State::Condemned => "CONDEMNED",
            State::Reaped => "REAPED",
            State::Void => "VOID",
        }
    }
    fn parse(s: &str) -> State {
        match s {
            "CONDEMNED" => State::Condemned,
            "REAPED" => State::Reaped,
            "VOID" => State::Void,
            _ => State::Alive,
        }
    }
}

/// One owned sandbox process.
#[derive(Clone, Debug)]
pub struct Proc {
    pub name: String,
    pub pid: u32,
    /// Process start signature captured at spawn time (PID-reuse guard).
    pub startsig: String,
    /// argv[0] token we tried to set (best-effort ownership marker).
    pub token: String,
    pub state: State,
    /// Cause written in the note (empty until condemned).
    pub cause: String,
    /// Epoch second at which the process is scheduled to die (0 if not set).
    pub due: u64,
}

/// The whole session.
#[derive(Clone, Debug, Default)]
pub struct Session {
    pub procs: Vec<Proc>,
    /// rawname -> number of misspelled attempts.
    pub misses: Vec<(String, u32)>,
}

impl Session {
    pub fn find(&self, name: &str) -> Option<&Proc> {
        self.procs.iter().find(|p| p.name == name)
    }

    pub fn miss_count(&self, name: &str) -> u32 {
        self.misses
            .iter()
            .find(|(n, _)| n == name)
            .map(|(_, c)| *c)
            .unwrap_or(0)
    }

    pub fn bump_miss(&mut self, name: &str) -> u32 {
        if let Some(entry) = self.misses.iter_mut().find(|(n, _)| n == name) {
            entry.1 += 1;
            entry.1
        } else {
            self.misses.push((name.to_string(), 1));
            1
        }
    }
}

fn registry_path(home: &Path) -> PathBuf {
    home.join("session.tsv")
}

/// Load the session (empty if the file does not exist).
pub fn load(home: &Path) -> Session {
    let path = registry_path(home);
    let Ok(text) = fs::read_to_string(&path) else {
        return Session::default();
    };
    let mut session = Session::default();
    for line in text.lines() {
        let cols: Vec<&str> = line.split('\t').collect();
        match cols.first() {
            Some(&"PROC") if cols.len() >= 8 => {
                session.procs.push(Proc {
                    name: cols[1].to_string(),
                    pid: cols[2].parse().unwrap_or(0),
                    startsig: cols[3].to_string(),
                    token: cols[4].to_string(),
                    state: State::parse(cols[5]),
                    cause: cols[6].to_string(),
                    due: cols[7].parse().unwrap_or(0),
                });
            }
            Some(&"MISS") if cols.len() >= 3 => {
                session
                    .misses
                    .push((cols[1].to_string(), cols[2].parse().unwrap_or(0)));
            }
            _ => {}
        }
    }
    session
}

/// Persist the session atomically-ish (write then rename).
pub fn save(home: &Path, session: &Session) -> Result<(), String> {
    fs::create_dir_all(home).map_err(|e| format!("cannot create {home:?}: {e}"))?;
    let mut out = String::new();
    for p in &session.procs {
        out.push_str(&format!(
            "PROC\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n",
            p.name,
            p.pid,
            p.startsig,
            p.token,
            p.state.as_str(),
            p.cause,
            p.due
        ));
    }
    for (n, c) in &session.misses {
        out.push_str(&format!("MISS\t{n}\t{c}\n"));
    }
    let path = registry_path(home);
    let tmp = path.with_extension("tmp");
    fs::write(&tmp, out).map_err(|e| format!("cannot write session: {e}"))?;
    fs::rename(&tmp, &path).map_err(|e| format!("cannot commit session: {e}"))?;
    Ok(())
}

/// Append a human-readable line to the ledger.
pub fn ledger_append(home: &Path, line: &str) {
    let _ = fs::create_dir_all(home);
    let path = home.join("ledger.log");
    use std::io::Write;
    if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(f, "[{}] {}", crate::clock::now(), line);
    }
}

pub fn ledger_read(home: &Path) -> String {
    fs::read_to_string(home.join("ledger.log")).unwrap_or_default()
}
