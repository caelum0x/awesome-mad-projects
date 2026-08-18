//! The vault: a single sandbox directory this crate is allowed to touch.
//!
//! SAFETY-CRITICAL DESIGN
//! ----------------------
//! Every filesystem operation goes through [`Vault`], which:
//!   * stores objects only under `<root>/objects/`,
//!   * validates every object name with [`crate::name::validate`],
//!   * re-checks, after joining, that the resulting path is still inside the
//!     objects directory (defence in depth against traversal).
//!
//! There is no API on `Vault` that accepts an arbitrary path, so the crate
//! can never read, write, or delete anything outside the vault it manages.

use std::fs;
use std::path::{Path, PathBuf};

use crate::error::{ExchangeError, Result};
use crate::name;

/// A managed sandbox directory.
#[derive(Debug, Clone)]
pub struct Vault {
    root: PathBuf,
}

impl Vault {
    /// Open (creating if necessary) a vault rooted at `root`.
    ///
    /// Creates `root/objects/` and an empty `root/ledger.log` on first use.
    pub fn open(root: impl AsRef<Path>) -> Result<Vault> {
        let root = root.as_ref().to_path_buf();
        let vault = Vault { root };
        fs::create_dir_all(vault.objects_dir())?;
        if !vault.ledger_path().exists() {
            fs::write(vault.ledger_path(), b"")?;
        }
        Ok(vault)
    }

    /// The vault root directory.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Directory that holds object data files.
    pub fn objects_dir(&self) -> PathBuf {
        self.root.join("objects")
    }

    /// Path to the append-only ledger file.
    pub fn ledger_path(&self) -> PathBuf {
        self.root.join("ledger.log")
    }

    /// Resolve a *validated* object name to its on-disk path, guaranteeing the
    /// result stays inside `objects/`.
    fn object_path(&self, raw_name: &str) -> Result<PathBuf> {
        let safe = name::validate(raw_name)?;
        let objects = self.objects_dir();
        let candidate = objects.join(safe);

        // Defence in depth: the joined path's parent must be exactly objects/.
        // Because `safe` contains no separators this always holds, but we assert
        // it explicitly so any future change cannot silently open an escape.
        match candidate.parent() {
            Some(parent) if parent == objects => Ok(candidate),
            _ => Err(ExchangeError::InvalidName(raw_name.to_string())),
        }
    }

    /// Whether an object currently exists.
    pub fn exists(&self, name: &str) -> Result<bool> {
        Ok(self.object_path(name)?.is_file())
    }

    /// Size in bytes of an existing object.
    pub fn size_of(&self, name: &str) -> Result<u64> {
        let path = self.object_path(name)?;
        let meta = fs::metadata(&path)
            .map_err(|_| ExchangeError::ObjectNotFound(name.to_string()))?;
        Ok(meta.len())
    }

    /// Create a new object of exactly `bytes` length, filled with a
    /// deterministic pattern derived from its name. Fails if it already exists.
    pub fn create(&self, name: &str, bytes: u64) -> Result<()> {
        let path = self.object_path(name)?;
        if path.exists() {
            return Err(ExchangeError::ObjectExists(name.to_string()));
        }
        let content = synth_content(name, bytes);
        fs::write(&path, &content)?;
        Ok(())
    }

    /// Delete (sacrifice) an existing object. Fails if it does not exist.
    pub fn remove(&self, name: &str) -> Result<()> {
        let path = self.object_path(name)?;
        if !path.is_file() {
            return Err(ExchangeError::ObjectNotFound(name.to_string()));
        }
        fs::remove_file(&path)?;
        Ok(())
    }

    /// List all objects as `(name, bytes)`, sorted by name.
    pub fn list(&self) -> Result<Vec<(String, u64)>> {
        let mut out = Vec::new();
        for entry in fs::read_dir(self.objects_dir())? {
            let entry = entry?;
            if !entry.file_type()?.is_file() {
                continue;
            }
            let file_name = entry.file_name();
            let name = match file_name.to_str() {
                Some(s) => s.to_string(),
                None => continue, // skip non-UTF8 names; we never create them
            };
            let bytes = entry.metadata()?.len();
            out.push((name, bytes));
        }
        out.sort_by(|a, b| a.0.cmp(&b.0));
        Ok(out)
    }

    /// Total bytes currently stored across all objects.
    pub fn total_mass(&self) -> Result<u64> {
        Ok(self.list()?.iter().map(|(_, b)| *b).sum())
    }

    /// Append one raw line to the ledger, adding the trailing newline.
    pub fn append_ledger_line(&self, line: &str) -> Result<()> {
        use std::io::Write;
        let mut f = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(self.ledger_path())?;
        writeln!(f, "{line}")?;
        Ok(())
    }

    /// Read the raw ledger body.
    pub fn read_ledger(&self) -> Result<String> {
        Ok(fs::read_to_string(self.ledger_path()).unwrap_or_default())
    }
}

/// Produce `bytes` bytes of deterministic, human-recognisable filler so that
/// created objects are real files with real content, not sparse holes.
fn synth_content(name: &str, bytes: u64) -> Vec<u8> {
    let seed = name.as_bytes();
    if seed.is_empty() {
        return vec![b'.'; bytes as usize];
    }
    (0..bytes as usize)
        .map(|i| {
            // Rotate through printable ASCII derived from the name + position.
            let base = seed[i % seed.len()] as u32;
            let shift = (i as u32) % 26;
            let v = 33 + ((base + shift) % 94); // printable range 33..=126
            v as u8
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp() -> PathBuf {
        let mut p = std::env::temp_dir();
        let uniq = format!(
            "eqx-vault-test-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        );
        p.push(uniq);
        p
    }

    #[test]
    fn create_size_remove_roundtrip() {
        let dir = tmp();
        let v = Vault::open(&dir).unwrap();
        v.create("gold", 100).unwrap();
        assert!(v.exists("gold").unwrap());
        assert_eq!(v.size_of("gold").unwrap(), 100);
        assert_eq!(v.total_mass().unwrap(), 100);
        v.remove("gold").unwrap();
        assert!(!v.exists("gold").unwrap());
        fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn rejects_unsafe_names_without_touching_disk() {
        let dir = tmp();
        let v = Vault::open(&dir).unwrap();
        assert!(v.create("../escape", 10).is_err());
        assert!(v.exists("../escape").is_err());
        fs::remove_dir_all(&dir).ok();
    }
}
