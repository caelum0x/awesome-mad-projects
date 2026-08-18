//! Stand abilities that can be bound to a simulated process.
//!
//! Each variant maps to a real operation on the SIMULATED process table,
//! implemented in [`crate::scheduler`]. No Stand touches the host OS.

use std::fmt;

/// A Stand ability bound to a [`crate::process::SimProcess`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Stand {
    /// Star Platinum / The World — "time stop".
    /// Freezes every other simulated process for a number of ticks while the
    /// caster keeps advancing.
    TheWorld,
    /// Killer Queen — "touch to detonate".
    /// Marks a target; the next signal it receives removes it from the sim table.
    KillerQueen,
    /// King Crimson — "erase time".
    /// Rolls the whole simulated table back to a snapshot from X ticks ago.
    KingCrimson,
    /// Sticky Fingers — "zip".
    /// Moves a process (and its queue) from one scheduler lane to another.
    StickyFingers,
}

impl Stand {
    /// The canonical user (for flavour in logs).
    pub fn user(self) -> &'static str {
        match self {
            Stand::TheWorld => "DIO / Jotaro",
            Stand::KillerQueen => "Kira Yoshikage",
            Stand::KingCrimson => "Diavolo",
            Stand::StickyFingers => "Bruno Bucciarati",
        }
    }

    /// Short ability tagline.
    pub fn ability(self) -> &'static str {
        match self {
            Stand::TheWorld => "time stop",
            Stand::KillerQueen => "touch to detonate",
            Stand::KingCrimson => "erase time",
            Stand::StickyFingers => "zip",
        }
    }
}

impl fmt::Display for Stand {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = match self {
            Stand::TheWorld => "The World",
            Stand::KillerQueen => "Killer Queen",
            Stand::KingCrimson => "King Crimson",
            Stand::StickyFingers => "Sticky Fingers",
        };
        write!(f, "{name}")
    }
}
