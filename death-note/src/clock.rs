//! Tiny time helper.

use std::time::{SystemTime, UNIX_EPOCH};

/// Current time as whole epoch seconds.
pub fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}
