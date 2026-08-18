//! The append-only ledger: the alchemist's audit trail.
//!
//! Every state-changing operation writes exactly one [`Transaction`] line to
//! `vault/ledger.log`. The format is a simple, dependency-free pipe-delimited
//! record so the log stays human-readable and the crate needs no serde.
//!
//! Ledger records are immutable once written. In memory we always build a
//! fresh `Vec` rather than mutating existing records, honouring the project's
//! immutability guideline.

use std::time::{SystemTime, UNIX_EPOCH};

use crate::error::{ExchangeError, Result};

/// A single object referenced by a transaction, with the mass it carried.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MassRef {
    pub name: String,
    pub bytes: u64,
}

impl MassRef {
    pub fn new(name: impl Into<String>, bytes: u64) -> Self {
        MassRef {
            name: name.into(),
            bytes,
        }
    }
}

/// The kind of operation a [`Transaction`] records.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TxKind {
    /// "Truth's toll": mass granted into the system without a sacrifice.
    /// This is the ONLY way mass may enter, and it is always logged explicitly.
    Grant { created: MassRef },
    /// `alchemize`: a new object is formed by sacrificing designated objects.
    Alchemize {
        created: MassRef,
        sacrificed: Vec<MassRef>,
    },
    /// `transmute`: sources are reshaped into a single destination object.
    Transmute {
        created: MassRef,
        sacrificed: Vec<MassRef>,
    },
}

impl TxKind {
    /// Bytes brought into existence by this transaction.
    pub fn created_mass(&self) -> u64 {
        match self {
            TxKind::Grant { created } => created.bytes,
            TxKind::Alchemize { created, .. } => created.bytes,
            TxKind::Transmute { created, .. } => created.bytes,
        }
    }

    /// Bytes destroyed (offered) by this transaction.
    pub fn sacrificed_mass(&self) -> u64 {
        match self {
            TxKind::Grant { .. } => 0,
            TxKind::Alchemize { sacrificed, .. } | TxKind::Transmute { sacrificed, .. } => {
                sacrificed.iter().map(|m| m.bytes).sum()
            }
        }
    }

    /// Whether this transaction respects conservation of mass.
    ///
    /// Grants are exempt (they are the explicit, logged entry point of mass).
    /// Every other transaction must create no more than it sacrifices.
    pub fn is_balanced(&self) -> bool {
        match self {
            TxKind::Grant { .. } => true,
            _ => self.created_mass() <= self.sacrificed_mass(),
        }
    }

    fn tag(&self) -> &'static str {
        match self {
            TxKind::Grant { .. } => "GRANT",
            TxKind::Alchemize { .. } => "ALCHEMIZE",
            TxKind::Transmute { .. } => "TRANSMUTE",
        }
    }
}

/// One immutable, timestamped record in the ledger.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Transaction {
    /// Unix seconds when the transaction was committed.
    pub timestamp: u64,
    pub kind: TxKind,
}

impl Transaction {
    /// Build a transaction stamped with the current wall-clock time.
    pub fn now(kind: TxKind) -> Self {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        Transaction { timestamp, kind }
    }

    /// Serialize to a single ledger line (no trailing newline).
    ///
    /// Grammar:
    /// `TAG|<ts>|<name>:<bytes>|<src_name>:<src_bytes>,<...>`
    /// The sacrifice field is empty for grants.
    pub fn to_line(&self) -> String {
        let created = match &self.kind {
            TxKind::Grant { created } => created,
            TxKind::Alchemize { created, .. } => created,
            TxKind::Transmute { created, .. } => created,
        };
        let sacrifices = match &self.kind {
            TxKind::Grant { .. } => String::new(),
            TxKind::Alchemize { sacrificed, .. } | TxKind::Transmute { sacrificed, .. } => {
                sacrificed
                    .iter()
                    .map(|m| format!("{}:{}", m.name, m.bytes))
                    .collect::<Vec<_>>()
                    .join(",")
            }
        };
        format!(
            "{}|{}|{}:{}|{}",
            self.kind.tag(),
            self.timestamp,
            created.name,
            created.bytes,
            sacrifices
        )
    }

    /// Parse a single ledger line back into a transaction.
    pub fn from_line(line: &str) -> Result<Transaction> {
        let corrupt = |why: &str| ExchangeError::CorruptLedger(format!("{why}: '{line}'"));

        let parts: Vec<&str> = line.split('|').collect();
        if parts.len() != 4 {
            return Err(corrupt("expected 4 fields"));
        }
        let tag = parts[0];
        let timestamp: u64 = parts[1].parse().map_err(|_| corrupt("bad timestamp"))?;
        let created = parse_mass_ref(parts[2]).ok_or_else(|| corrupt("bad created object"))?;
        let sacrificed = parse_sacrifices(parts[3]).ok_or_else(|| corrupt("bad sacrifice list"))?;

        let kind = match tag {
            "GRANT" => {
                if !sacrificed.is_empty() {
                    return Err(corrupt("grant must have no sacrifice"));
                }
                TxKind::Grant { created }
            }
            "ALCHEMIZE" => TxKind::Alchemize {
                created,
                sacrificed,
            },
            "TRANSMUTE" => TxKind::Transmute {
                created,
                sacrificed,
            },
            other => return Err(corrupt(&format!("unknown tag '{other}'"))),
        };
        Ok(Transaction { timestamp, kind })
    }
}

fn parse_mass_ref(field: &str) -> Option<MassRef> {
    let (name, bytes) = field.rsplit_once(':')?;
    if name.is_empty() {
        return None;
    }
    let bytes: u64 = bytes.parse().ok()?;
    Some(MassRef::new(name, bytes))
}

fn parse_sacrifices(field: &str) -> Option<Vec<MassRef>> {
    if field.is_empty() {
        return Some(Vec::new());
    }
    field.split(',').map(parse_mass_ref).collect()
}

/// A parsed ledger: an ordered, immutable list of transactions plus helpers
/// for computing conservation statistics.
#[derive(Debug, Clone, Default)]
pub struct Ledger {
    pub transactions: Vec<Transaction>,
}

impl Ledger {
    /// Parse a whole ledger file body (may be empty).
    pub fn parse(body: &str) -> Result<Ledger> {
        let mut transactions = Vec::new();
        for line in body.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            transactions.push(Transaction::from_line(trimmed)?);
        }
        Ok(Ledger { transactions })
    }

    /// Total bytes ever granted (the only lawful source of new mass).
    pub fn total_granted(&self) -> u64 {
        self.transactions
            .iter()
            .filter_map(|t| match &t.kind {
                TxKind::Grant { created } => Some(created.bytes),
                _ => None,
            })
            .sum()
    }

    /// Sum of all bytes ever sacrificed across every transaction.
    pub fn total_sacrificed(&self) -> u64 {
        self.transactions.iter().map(|t| t.kind.sacrificed_mass()).sum()
    }

    /// Sum of all bytes ever created (grants + alchemy + transmutation).
    pub fn total_created(&self) -> u64 {
        self.transactions.iter().map(|t| t.kind.created_mass()).sum()
    }

    /// True when every non-grant transaction respected the law.
    pub fn all_balanced(&self) -> bool {
        self.transactions.iter().all(|t| t.kind.is_balanced())
    }
}
