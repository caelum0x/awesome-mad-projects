//! The event log: an immutable record of everything that happened.

use crate::signal::{Outcome, Plane};
use std::fmt;

/// What kind of thing an [`Event`] records.
#[derive(Debug, Clone)]
pub enum EventKind {
    /// A signal was delivered (or bounced) against a field.
    Delivery {
        source: String,
        impact: f64,
        outcome: Outcome,
        plane: Plane,
        payload: String,
    },
    /// A field regenerated during a quiet tick.
    Regeneration { recovered: f64 },
}

/// One immutable entry in the world's event log.
#[derive(Debug, Clone)]
pub struct Event {
    pub tick: u64,
    /// The entity this event happened *to* (the target / regenerating field).
    pub actor: String,
    pub field_before: f64,
    pub field_after: f64,
    pub streak_after: u32,
    pub kind: EventKind,
}

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match &self.kind {
            EventKind::Delivery {
                source,
                impact,
                outcome,
                plane,
                payload,
            } => write!(
                f,
                "t{:>2} [{}] {} --impact {:>5.1}--> {} (field {:>5.1} -> {:>5.1}, streak {}) {:<13} \"{}\"",
                self.tick,
                plane.label(),
                source,
                impact,
                self.actor,
                self.field_before,
                self.field_after,
                self.streak_after,
                outcome.label(),
                payload,
            ),
            EventKind::Regeneration { recovered } => write!(
                f,
                "t{:>2} [rest ] {} regenerates (+{:>4.1}) (field {:>5.1} -> {:>5.1})",
                self.tick, self.actor, recovered, self.field_before, self.field_after,
            ),
        }
    }
}
