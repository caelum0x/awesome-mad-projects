//! Object-name validation.
//!
//! SAFETY-CRITICAL: object names become file names inside the vault. To
//! guarantee we never escape the sandbox, names are validated with an
//! allow-list. No `/`, no `\`, no `..`, no absolute paths, nothing exotic.

use crate::error::{ExchangeError, Result};

/// Validate an object name and return it unchanged if it is safe.
///
/// A name is valid when it:
/// * is non-empty and at most 128 characters,
/// * contains only ASCII letters, digits, `.`, `_`, or `-`,
/// * is not exactly `.` or `..`.
///
/// This deliberately rejects any path separator, so a validated name can
/// never reference a location outside the vault's `objects/` directory.
pub fn validate(name: &str) -> Result<&str> {
    if name.is_empty() || name.len() > 128 {
        return Err(ExchangeError::InvalidName(name.to_string()));
    }
    if name == "." || name == ".." {
        return Err(ExchangeError::InvalidName(name.to_string()));
    }
    let ok = name
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-'));
    if !ok {
        return Err(ExchangeError::InvalidName(name.to_string()));
    }
    Ok(name)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_simple_names() {
        for n in ["a", "gold", "iron_bar", "circle-01", "note.txt", "A1"] {
            assert!(validate(n).is_ok(), "expected '{n}' to be valid");
        }
    }

    #[test]
    fn rejects_path_traversal_and_separators() {
        for n in ["..", ".", "", "a/b", "a\\b", "../etc/passwd", "/abs", "sp ace", "na*me"] {
            assert!(validate(n).is_err(), "expected '{n}' to be rejected");
        }
    }
}
