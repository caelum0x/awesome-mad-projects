//! Entities: in-memory actors, each guarded by an AT Field.

use crate::field::{AtField, FieldDynamics};
use crate::signal::Signal;

/// A simulated "process": a named ego with a field and inboxes.
///
/// This is entirely in-memory. It is not backed by any real OS process.
#[derive(Debug, Clone)]
pub struct Entity {
    pub name: String,
    pub field: AtField,
    /// Messages that penetrated on the [`crate::Plane::Normal`] plane.
    pub inbox: Vec<Signal>,
    /// Messages that arrived on the [`crate::Plane::DiracSea`] plane.
    pub dirac_inbox: Vec<Signal>,
    /// Capability flag: may this entity touch the Dirac Sea plane at all?
    pub dirac_capable: bool,
}

impl Entity {
    /// Create an entity with the given starting field strength and default
    /// field dynamics. Not Dirac-capable by default.
    pub fn new(name: impl Into<String>, strength: f64) -> Self {
        Self::with_dynamics(name, strength, FieldDynamics::default())
    }

    /// Create an entity with custom field dynamics.
    pub fn with_dynamics(
        name: impl Into<String>,
        strength: f64,
        dynamics: FieldDynamics,
    ) -> Self {
        Self {
            name: name.into(),
            field: AtField::new(strength, dynamics),
            inbox: Vec::new(),
            dirac_inbox: Vec::new(),
            dirac_capable: false,
        }
    }

    /// Grant this entity the Dirac Sea capability (builder-style, immutable).
    pub fn dirac_capable(mut self) -> Self {
        self.dirac_capable = true;
        self
    }

    /// Total number of messages this entity has actually received.
    pub fn received_count(&self) -> usize {
        self.inbox.len() + self.dirac_inbox.len()
    }
}
