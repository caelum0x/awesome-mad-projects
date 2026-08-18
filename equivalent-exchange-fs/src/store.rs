//! The Equivalent-Exchange store: the law-enforcing layer.
//!
//! This ties a [`Vault`] (storage) to a [`Ledger`] (audit trail) and exposes
//! the three alchemical operations plus reporting. The single rule enforced
//! everywhere but [`ExchangeStore::grant`] is:
//!
//! > created_mass <= sacrificed_mass
//!
//! If that inequality would break, the operation is rejected BEFORE any file
//! is created or deleted, so the vault is never left in a half-transmuted
//! state on a rejected exchange.

use crate::error::{ExchangeError, Result};
use crate::ledger::{Ledger, MassRef, Transaction, TxKind};
use crate::name;
use crate::vault::Vault;

/// The alchemist's workbench.
pub struct ExchangeStore {
    vault: Vault,
}

/// A snapshot of the vault's conservation status, for reporting.
#[derive(Debug, Clone)]
pub struct ConservationStatus {
    pub current_mass: u64,
    pub total_granted: u64,
    pub total_sacrificed: u64,
    pub total_created: u64,
    pub object_count: usize,
    pub all_balanced: bool,
}

impl ConservationStatus {
    /// The law at the whole-vault scale: nothing may exist that was not,
    /// ultimately, paid for by a grant. Current mass can never exceed the
    /// total mass ever granted into the system.
    pub fn law_holds(&self) -> bool {
        self.all_balanced && self.current_mass <= self.total_granted
    }
}

impl ExchangeStore {
    /// Open a store over the vault rooted at `root`.
    pub fn open(root: impl AsRef<std::path::Path>) -> Result<ExchangeStore> {
        Ok(ExchangeStore {
            vault: Vault::open(root)?,
        })
    }

    /// Borrow the underlying vault (read-only helpers).
    pub fn vault(&self) -> &Vault {
        &self.vault
    }

    /// Load and parse the ledger.
    pub fn ledger(&self) -> Result<Ledger> {
        Ledger::parse(&self.vault.read_ledger()?)
    }

    /// List objects as `(name, bytes)`.
    pub fn list(&self) -> Result<Vec<(String, u64)>> {
        self.vault.list()
    }

    /// GRANT ("Truth's toll"): inject `bytes` of new mass without a sacrifice.
    ///
    /// This is the ONLY way mass may enter the vault, and it is always logged
    /// explicitly as a `GRANT`. Use it to seed the system.
    pub fn grant(&self, name_str: &str, bytes: u64) -> Result<Transaction> {
        name::validate(name_str)?;
        if self.vault.exists(name_str)? {
            return Err(ExchangeError::ObjectExists(name_str.to_string()));
        }
        self.vault.create(name_str, bytes)?;
        let tx = Transaction::now(TxKind::Grant {
            created: MassRef::new(name_str, bytes),
        });
        self.vault.append_ledger_line(&tx.to_line())?;
        Ok(tx)
    }

    /// ALCHEMIZE: create a brand-new object of `bytes`, paid for by deleting
    /// the designated `sacrifices` whose combined mass must be `>= bytes`.
    ///
    /// Rejected (with nothing changed on disk) if the exchange is unbalanced,
    /// the target already exists, a sacrifice is missing, or the sacrifice
    /// list is empty / contains duplicates.
    pub fn alchemize(&self, name_str: &str, bytes: u64, sacrifices: &[String]) -> Result<Transaction> {
        name::validate(name_str)?;
        if self.vault.exists(name_str)? {
            return Err(ExchangeError::ObjectExists(name_str.to_string()));
        }
        let offered = self.resolve_sacrifices(sacrifices, Some(name_str))?;
        let sacrificed_mass: u64 = offered.iter().map(|m| m.bytes).sum();

        // THE LAW. Check before mutating anything.
        if bytes > sacrificed_mass {
            return Err(ExchangeError::UnbalancedExchange {
                created: bytes,
                sacrificed: sacrificed_mass,
            });
        }

        // Consume the offered mass, then form the new object.
        for m in &offered {
            self.vault.remove(&m.name)?;
        }
        self.vault.create(name_str, bytes)?;

        let tx = Transaction::now(TxKind::Alchemize {
            created: MassRef::new(name_str, bytes),
            sacrificed: offered,
        });
        self.vault.append_ledger_line(&tx.to_line())?;
        Ok(tx)
    }

    /// TRANSMUTE: reshape one or more `sources` into a single destination
    /// object `dst`. The destination mass defaults to the full combined mass
    /// of the sources (a perfectly conserving circle); an optional `dst_bytes`
    /// may request less (mass may be lost, never gained).
    pub fn transmute(&self, sources: &[String], dst: &str, dst_bytes: Option<u64>) -> Result<Transaction> {
        name::validate(dst)?;
        if self.vault.exists(dst)? {
            return Err(ExchangeError::ObjectExists(dst.to_string()));
        }
        let offered = self.resolve_sacrifices(sources, Some(dst))?;
        let sacrificed_mass: u64 = offered.iter().map(|m| m.bytes).sum();
        let created = dst_bytes.unwrap_or(sacrificed_mass);

        // THE LAW.
        if created > sacrificed_mass {
            return Err(ExchangeError::UnbalancedExchange {
                created,
                sacrificed: sacrificed_mass,
            });
        }

        for m in &offered {
            self.vault.remove(&m.name)?;
        }
        self.vault.create(dst, created)?;

        let tx = Transaction::now(TxKind::Transmute {
            created: MassRef::new(dst, created),
            sacrificed: offered,
        });
        self.vault.append_ledger_line(&tx.to_line())?;
        Ok(tx)
    }

    /// Compute the current conservation status from vault + ledger.
    pub fn status(&self) -> Result<ConservationStatus> {
        let ledger = self.ledger()?;
        let objects = self.vault.list()?;
        Ok(ConservationStatus {
            current_mass: objects.iter().map(|(_, b)| *b).sum(),
            total_granted: ledger.total_granted(),
            total_sacrificed: ledger.total_sacrificed(),
            total_created: ledger.total_created(),
            object_count: objects.len(),
            all_balanced: ledger.all_balanced(),
        })
    }

    /// Validate a sacrifice list: non-empty, no duplicates, none equal to the
    /// destination, all existing. Returns their current masses.
    fn resolve_sacrifices(&self, names: &[String], dst: Option<&str>) -> Result<Vec<MassRef>> {
        if names.is_empty() {
            return Err(ExchangeError::EmptySacrifice);
        }
        let mut seen: Vec<&str> = Vec::new();
        let mut refs = Vec::with_capacity(names.len());
        for raw in names {
            name::validate(raw)?;
            if let Some(d) = dst {
                if raw == d {
                    return Err(ExchangeError::SelfSacrifice(raw.clone()));
                }
            }
            if seen.contains(&raw.as_str()) {
                return Err(ExchangeError::DuplicateSacrifice(raw.clone()));
            }
            seen.push(raw.as_str());
            if !self.vault.exists(raw)? {
                return Err(ExchangeError::ObjectNotFound(raw.clone()));
            }
            let bytes = self.vault.size_of(raw)?;
            refs.push(MassRef::new(raw.clone(), bytes));
        }
        Ok(refs)
    }
}
