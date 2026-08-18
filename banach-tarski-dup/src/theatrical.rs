//! Theatrical "file duplication" mode --- CLEARLY LABELLED AS NOT REAL.
//!
//! HONESTY NOTICE
//! ==============
//! Banach-Tarski does NOT let you duplicate matter, bytes, energy, or disk
//! blocks for free. The real theorem duplicates an abstract measure-zero set of
//! points using the Axiom of Choice, and it is impossible for physical objects.
//!
//! The only *real*, *constructive* content in this project lives in
//! `word.rs` / `decomp.rs`: the paradoxical decomposition of the FREE GROUP F2.
//! That combinatorial paradox is genuine and fully verified by the tests.
//!
//! This module is pure theatre. It makes a "second copy" of a file by creating
//! a hard link (or a plain reference note). A hard link is just a second
//! directory entry pointing at the *same* inode --- the same bytes on disk. No
//! new matter is created; both names share one body, exactly like the two
//! translated pieces of F2 share the one underlying group. We spell this out
//! loudly so nobody mistakes stagecraft for physics.

use std::fs;
use std::io;
use std::path::{Path, PathBuf};

/// Outcome of the theatrical duplication.
#[derive(Debug)]
pub struct TheatricalResult {
    pub original: PathBuf,
    pub copy: PathBuf,
    pub method: &'static str,
    pub shares_bytes_with_original: bool,
    pub disclaimer: &'static str,
}

const DISCLAIMER: &str =
    "THEATRE ONLY: no bytes were duplicated. The 'copy' is a hard link sharing \
     the SAME inode / the SAME bytes as the original, mirroring how the two \
     translated pieces of F2 share one underlying group. Banach-Tarski cannot \
     duplicate real matter; only the free-group combinatorics are real here.";

/// "Duplicate" a file, theatrically. Tries a hard link first (same bytes, two
/// names). If hard-linking is unsupported, falls back to writing a small text
/// pointer file that references the original --- again, no real duplication.
pub fn theatrical_duplicate(original: &Path, copy: &Path) -> io::Result<TheatricalResult> {
    if !original.exists() {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("original file not found: {}", original.display()),
        ));
    }
    // Never clobber an existing target.
    if copy.exists() {
        return Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            format!("target already exists: {}", copy.display()),
        ));
    }

    match fs::hard_link(original, copy) {
        Ok(()) => Ok(TheatricalResult {
            original: original.to_path_buf(),
            copy: copy.to_path_buf(),
            method: "hard link (same inode, same bytes)",
            shares_bytes_with_original: true,
            disclaimer: DISCLAIMER,
        }),
        Err(_) => {
            // Fallback: a plain-text reference note. Still not real duplication.
            let note = format!(
                "REFERENCE ONLY (theatrical Banach-Tarski copy)\n\
                 This is not a real duplicate. It points at:\n{}\n\n{}\n",
                original.display(),
                DISCLAIMER
            );
            fs::write(copy, note)?;
            Ok(TheatricalResult {
                original: original.to_path_buf(),
                copy: copy.to_path_buf(),
                method: "reference note (hard link unsupported here)",
                shares_bytes_with_original: false,
                disclaimer: DISCLAIMER,
            })
        }
    }
}
