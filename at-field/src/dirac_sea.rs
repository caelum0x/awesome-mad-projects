//! The Dirac Sea: a hidden message plane behind the ordinary one.
//!
//! In physics the Dirac sea is the infinite reservoir of negative-energy states
//! underlying the vacuum. Here it is a parallel messaging plane that ordinary
//! entities cannot perceive: a signal only reaches it if **both** the sender
//! and the receiver hold the Dirac capability flag. It is a separate namespace
//! from the normal inbox, so ego boundaries (AT Fields) are irrelevant on it:
//! access is gated purely by capability, not by field strength.

use crate::signal::Signal;

/// Records whether a Dirac-plane transmission is permitted, and why not if it
/// is refused.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiracAccess {
    Granted,
    SenderLacksCapability,
    TargetLacksCapability,
}

/// A thin capability gate for the Dirac Sea plane.
pub struct DiracSea;

impl DiracSea {
    /// Decide whether `sender_capable -> target_capable` may transmit on the
    /// Dirac plane. Both ends must hold the capability flag.
    pub fn check(sender_capable: bool, target_capable: bool) -> DiracAccess {
        if !sender_capable {
            DiracAccess::SenderLacksCapability
        } else if !target_capable {
            DiracAccess::TargetLacksCapability
        } else {
            DiracAccess::Granted
        }
    }

    /// Deliver a signal onto a target's Dirac inbox. Access must already have
    /// been [`DiracSea::check`]ed as `Granted`.
    pub fn deliver(dirac_inbox: &mut Vec<Signal>, signal: Signal) {
        dirac_inbox.push(signal);
    }
}
