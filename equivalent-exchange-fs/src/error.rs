//! Error types for the Equivalent-Exchange filesystem.
//!
//! Every fallible operation returns [`ExchangeError`]. The most important
//! variant is [`ExchangeError::UnbalancedExchange`]: it is the runtime
//! embodiment of the Law of Equivalent Exchange. If mass would be created
//! from nothing, the operation is rejected with this error.

use std::fmt;

/// The set of things that can go wrong inside the vault.
#[derive(Debug)]
pub enum ExchangeError {
    /// A referenced object does not exist in the vault.
    ObjectNotFound(String),
    /// An object with the target name already exists.
    ObjectExists(String),
    /// An object name is unsafe or malformed (path traversal, separators, ..).
    InvalidName(String),
    /// The requested creation would violate conservation of mass:
    /// `created` bytes were requested but only `sacrificed` bytes were offered.
    UnbalancedExchange { created: u64, sacrificed: u64 },
    /// A transmutation / alchemy was attempted with no sacrifice at all.
    EmptySacrifice,
    /// The same object was listed twice as a sacrifice.
    DuplicateSacrifice(String),
    /// The destination of a transmutation was also listed as a source.
    SelfSacrifice(String),
    /// Underlying filesystem failure.
    Io(String),
    /// The ledger on disk is corrupt and could not be parsed.
    CorruptLedger(String),
}

impl fmt::Display for ExchangeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ExchangeError::ObjectNotFound(n) => {
                write!(f, "no such object in the vault: '{n}'")
            }
            ExchangeError::ObjectExists(n) => {
                write!(f, "object already exists: '{n}'")
            }
            ExchangeError::InvalidName(n) => write!(
                f,
                "invalid object name '{n}': names may only contain \
                 [A-Za-z0-9._-], must be non-empty, and may not be '.' or '..'"
            ),
            ExchangeError::UnbalancedExchange {
                created,
                sacrificed,
            } => write!(
                f,
                "LAW OF EQUIVALENT EXCHANGE VIOLATED: cannot create {created} bytes \
                 from a sacrifice of only {sacrificed} bytes. \
                 To obtain, something of equal value must be lost.",
            ),
            ExchangeError::EmptySacrifice => write!(
                f,
                "nothing was offered: creation requires a sacrifice of equal or greater mass"
            ),
            ExchangeError::DuplicateSacrifice(n) => {
                write!(f, "object '{n}' was offered as a sacrifice more than once")
            }
            ExchangeError::SelfSacrifice(n) => {
                write!(f, "destination '{n}' cannot also be a source of the transmutation")
            }
            ExchangeError::Io(msg) => write!(f, "filesystem error: {msg}"),
            ExchangeError::CorruptLedger(msg) => write!(f, "corrupt ledger: {msg}"),
        }
    }
}

impl std::error::Error for ExchangeError {}

impl From<std::io::Error> for ExchangeError {
    fn from(e: std::io::Error) -> Self {
        ExchangeError::Io(e.to_string())
    }
}

/// Convenience alias used throughout the crate.
pub type Result<T> = std::result::Result<T, ExchangeError>;
