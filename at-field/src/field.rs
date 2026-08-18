//! The AT Field itself: a boundary membrane with corrosion and regeneration.
//!
//! ## Topological framing
//!
//! Think of the field strength `s` as the "height" of a membrane enclosing an
//! entity's ego. A signal is a particle thrown at the membrane. Crossing the
//! membrane (penetration) requires the particle's `impact` to clear the height
//! `s`. Two entities attacking each other are two membranes pressed together;
//! whichever wall is lower gives way first.
//!
//! ## Phase-space attenuation (documented, monotone)
//!
//! We track an `assault_streak` counter: the number of consecutive attacks a
//! field has absorbed without a chance to rest. The strength lost to a single
//! attack of magnitude `impact` is:
//!
//! ```text
//! attenuation(impact, streak) = corrosion_base
//!                             * (impact / max_strength)
//!                             * (1 + streak * streak_escalation)
//! ```
//!
//! This function is **monotonically non-decreasing** in both `impact` and
//! `streak`: a harder blow corrodes more, and each successive blow in an
//! unbroken barrage corrodes more than the last (fatigue). It is zero only when
//! `impact == 0`. A quiet tick resets `streak` to 0, so the membrane "cools"
//! and can regenerate. This is the simple monotone phase-space law the README
//! refers to.

/// Tunable constants that govern how a field corrodes and heals.
#[derive(Debug, Clone, Copy)]
pub struct FieldDynamics {
    /// Upper bound a field can regenerate back to.
    pub max_strength: f64,
    /// Strength recovered on each quiet (unattacked) tick.
    pub regen_per_tick: f64,
    /// Base corrosion applied to a full-impact blow at streak 0.
    pub corrosion_base: f64,
    /// How much each consecutive blow escalates corrosion (fatigue slope).
    pub streak_escalation: f64,
}

impl Default for FieldDynamics {
    fn default() -> Self {
        Self {
            max_strength: 100.0,
            regen_per_tick: 4.0,
            corrosion_base: 6.0,
            streak_escalation: 0.35,
        }
    }
}

/// An entity's Absolute Terror Field: its ego boundary.
#[derive(Debug, Clone)]
pub struct AtField {
    strength: f64,
    assault_streak: u32,
    dynamics: FieldDynamics,
}

impl AtField {
    /// Create a field at `strength`, clamped to `[0, max_strength]`.
    pub fn new(strength: f64, dynamics: FieldDynamics) -> Self {
        let strength = strength.clamp(0.0, dynamics.max_strength);
        Self {
            strength,
            assault_streak: 0,
            dynamics,
        }
    }

    /// Current membrane height.
    pub fn strength(&self) -> f64 {
        self.strength
    }

    /// Number of consecutive attacks absorbed without rest.
    pub fn assault_streak(&self) -> u32 {
        self.assault_streak
    }

    /// A field is "broken" once its strength collapses to zero: any signal will
    /// now penetrate.
    pub fn is_broken(&self) -> bool {
        self.strength <= 0.0
    }

    /// The monotone phase-space attenuation for a blow of `impact` at the
    /// current assault streak. See the module docs for the law.
    pub fn attenuation(&self, impact: f64) -> f64 {
        if impact <= 0.0 {
            return 0.0;
        }
        let impact_ratio = impact / self.dynamics.max_strength;
        self.dynamics.corrosion_base
            * impact_ratio
            * (1.0 + self.assault_streak as f64 * self.dynamics.streak_escalation)
    }

    /// Absorb one attack (whether or not it penetrated). Corrodes the field by
    /// [`AtField::attenuation`] and advances the assault streak. Returns the
    /// amount of strength lost.
    pub fn absorb_attack(&mut self, impact: f64) -> f64 {
        let loss = self.attenuation(impact);
        self.strength = (self.strength - loss).max(0.0);
        self.assault_streak = self.assault_streak.saturating_add(1);
        loss
    }

    /// A quiet tick: no attack landed. The streak cools to zero and the field
    /// regenerates toward its maximum. Returns the amount recovered.
    pub fn regenerate(&mut self) -> f64 {
        self.assault_streak = 0;
        let before = self.strength;
        self.strength = (self.strength + self.dynamics.regen_per_tick).min(self.dynamics.max_strength);
        self.strength - before
    }
}
