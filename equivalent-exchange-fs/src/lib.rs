//! # Equivalent-Exchange Filesystem
//!
//! A userspace, sandbox-only object store that enforces **conservation of
//! mass**, inspired by the Law of Equivalent Exchange from *Fullmetal
//! Alchemist*:
//!
//! > "To obtain, something of equal value must be lost."
//!
//! The total number of bytes stored can never increase unless an equal or
//! greater number of bytes is sacrificed. The single exception is an explicit,
//! logged `grant` — the "Truth's toll" that seeds the system.
//!
//! Everything lives under one managed directory (the *vault*). The library
//! never touches, reads, or deletes anything outside that directory: object
//! names are strictly validated and all paths are confined to `vault/objects/`.
//!
//! ## Quick start
//! ```no_run
//! use equivalent_exchange_fs::ExchangeStore;
//!
//! let store = ExchangeStore::open("./vault").unwrap();
//! store.grant("ore", 500).unwrap();                       // seed 500 bytes
//! store.alchemize("sword", 300, &["ore".into()]).unwrap(); // 300 <= 500, ok
//! // store.alchemize("free", 10, &[]).unwrap();            // would be rejected
//! ```

pub mod error;
pub mod ledger;
pub mod name;
pub mod store;
pub mod vault;

pub use error::{ExchangeError, Result};
pub use ledger::{Ledger, MassRef, Transaction, TxKind};
pub use store::{ConservationStatus, ExchangeStore};
pub use vault::Vault;
