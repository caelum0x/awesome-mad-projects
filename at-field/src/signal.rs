//! Signals: the particles thrown at AT Fields, and the outcomes of doing so.

/// Which message plane a signal travels on.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Plane {
    /// The ordinary plane every entity can send and receive on.
    Normal,
    /// The Dirac Sea: a hidden plane reachable only by entities holding the
    /// Dirac capability flag. See [`crate::dirac_sea`].
    DiracSea,
}

impl Plane {
    pub fn label(self) -> &'static str {
        match self {
            Plane::Normal => "Normal",
            Plane::DiracSea => "DiracSea",
        }
    }
}

/// A message hurled from one entity at another.
#[derive(Debug, Clone)]
pub struct Signal {
    pub from: String,
    pub to: String,
    /// How hard the signal strikes; compared against the target field height.
    pub impact: f64,
    pub payload: String,
    pub plane: Plane,
}

impl Signal {
    pub fn new(
        from: impl Into<String>,
        to: impl Into<String>,
        impact: f64,
        payload: impl Into<String>,
        plane: Plane,
    ) -> Self {
        Self {
            from: from.into(),
            to: to.into(),
            impact: impact.max(0.0),
            payload: payload.into(),
            plane,
        }
    }
}

/// What happened when a signal met a field.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Outcome {
    /// `impact >= field.strength`: the signal crossed the membrane and landed
    /// in the target's inbox.
    Penetrated,
    /// The signal was strong enough to rattle the membrane but not cross it;
    /// it bounced off.
    Reflected,
    /// The signal was too weak to matter and soaked harmlessly into the
    /// membrane.
    Absorbed,
    /// The signal targeted the Dirac Sea but sender or target lacked the
    /// capability flag, so it never reached the plane.
    DiracBlocked,
}

impl Outcome {
    pub fn label(self) -> &'static str {
        match self {
            Outcome::Penetrated => "PENETRATED",
            Outcome::Reflected => "reflected",
            Outcome::Absorbed => "absorbed",
            Outcome::DiracBlocked => "DIRAC-BLOCKED",
        }
    }

    /// True only when the signal actually reached an inbox.
    pub fn delivered(self) -> bool {
        matches!(self, Outcome::Penetrated)
    }
}

/// Classify a non-Dirac signal against a field height.
///
/// * `impact >= strength`            -> Penetrated
/// * `strength/2 <= impact < strength` -> Reflected
/// * `impact < strength/2`           -> Absorbed
pub fn classify(impact: f64, strength: f64) -> Outcome {
    if impact >= strength {
        Outcome::Penetrated
    } else if impact >= strength * 0.5 {
        Outcome::Reflected
    } else {
        Outcome::Absorbed
    }
}
