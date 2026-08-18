//! A usable subset of Conway's surreal numbers, specialized for priorities.
//!
//! # What we model
//!
//! Full surreal numbers form a proper class and are defined recursively as
//! `{ L | R }`. Implementing the entire construction is neither necessary nor
//! practical for a scheduler. Instead we model the subgroup that scheduling
//! actually needs:
//!
//! ```text
//!     p = a * omega  +  b  +  c * (1/omega)
//! ```
//!
//! where `a`, `b`, `c` are dyadic rationals (numbers born on a finite day),
//! `omega` is the first infinite ordinal, and `1/omega` is its infinitesimal
//! reciprocal. This is a genuine, honest slice of the surreal number line:
//!
//! * `b` alone ranges over every finite dyadic priority (integers included).
//! * `a * omega` gives priorities that dominate *every* finite priority.
//! * `c * (1/omega)` gives priorities that are positive yet smaller than
//!   *every* positive finite priority.
//!
//! Ordered by "most significant infinite order first", this subgroup inherits
//! exactly the surreal ordering, so `1/omega < 1 < omega` and `omega < 2*omega`
//! come out for free. Formally this is the lexicographically ordered group of
//! Hahn series supported on the powers `{omega^1, omega^0, omega^-1}` — a
//! faithful sub-ordering of the surreals.
//!
//! # What we deliberately leave out
//!
//! Surreal *multiplication*, higher powers of omega (`omega^2`, `sqrt(omega)`),
//! and the birthday/`{L|R}` machinery are out of scope. We implement only the
//! operations a scheduler needs: construction, comparison, addition, and
//! negation. See `README.md` for the honest math boundary.

use crate::dyadic::Dyadic;
use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Neg, Sub};

/// A single additive term used when building a priority by hand.
///
/// A `Priority` is a linear combination of these; see [`Priority::from_terms`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Term {
    /// A finite dyadic value `b` (contributes to `omega^0`).
    Finite(Dyadic),
    /// `scale * omega` — an infinite term dominating all finite priorities.
    Omega { scale: Dyadic },
    /// `scale * (1/omega)` — an infinitesimal term below all positive finites.
    InvOmega { scale: Dyadic },
}

/// A priority expressed as `omega*a + b + (1/omega)*c`.
///
/// The three coefficients are dyadic rationals. The type is immutable: every
/// arithmetic operation returns a new `Priority`.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Priority {
    /// Coefficient `a` of `omega` (the infinite part).
    omega: Dyadic,
    /// Coefficient `b` of `1` (the finite part).
    finite: Dyadic,
    /// Coefficient `c` of `1/omega` (the infinitesimal part).
    inv_omega: Dyadic,
}

impl Priority {
    /// The zero priority.
    pub const ZERO: Priority = Priority {
        omega: Dyadic::ZERO,
        finite: Dyadic::ZERO,
        inv_omega: Dyadic::ZERO,
    };

    /// A purely finite priority equal to the integer `n`.
    pub fn integer(n: i128) -> Priority {
        Priority {
            finite: Dyadic::integer(n),
            ..Priority::ZERO
        }
    }

    /// A purely finite priority equal to the dyadic `b`.
    pub fn finite(b: Dyadic) -> Priority {
        Priority {
            finite: b,
            ..Priority::ZERO
        }
    }

    /// The priority `scale * omega`.
    pub fn omega(scale: Dyadic) -> Priority {
        Priority {
            omega: scale,
            ..Priority::ZERO
        }
    }

    /// The priority `scale * (1/omega)`.
    pub fn inv_omega(scale: Dyadic) -> Priority {
        Priority {
            inv_omega: scale,
            ..Priority::ZERO
        }
    }

    /// Sum an arbitrary list of [`Term`]s into a single priority, e.g.
    /// `2*omega + 3 + 1/omega`.
    pub fn from_terms(terms: &[Term]) -> Priority {
        terms.iter().fold(Priority::ZERO, |acc, term| {
            let piece = match *term {
                Term::Finite(b) => Priority::finite(b),
                Term::Omega { scale } => Priority::omega(scale),
                Term::InvOmega { scale } => Priority::inv_omega(scale),
            };
            acc + piece
        })
    }

    /// Surreal comparison, realized as lexicographic order on
    /// `(omega, finite, inv_omega)`: the most significant order wins first.
    pub fn compare(self, other: Priority) -> Ordering {
        self.omega
            .compare(other.omega)
            .then_with(|| self.finite.compare(other.finite))
            .then_with(|| self.inv_omega.compare(other.inv_omega))
    }

    /// True when the two priorities are the exact same surreal value.
    pub fn eq_val(self, other: Priority) -> bool {
        self.compare(other) == Ordering::Equal
    }
}

impl PartialOrd for Priority {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Priority {
    fn cmp(&self, other: &Self) -> Ordering {
        Priority::compare(*self, *other)
    }
}

impl Add for Priority {
    type Output = Priority;

    /// Component-wise addition. The subgroup is closed under it.
    fn add(self, other: Priority) -> Priority {
        Priority {
            omega: self.omega + other.omega,
            finite: self.finite + other.finite,
            inv_omega: self.inv_omega + other.inv_omega,
        }
    }
}

impl Neg for Priority {
    type Output = Priority;

    /// Additive inverse (negate every coefficient).
    fn neg(self) -> Priority {
        Priority {
            omega: -self.omega,
            finite: -self.finite,
            inv_omega: -self.inv_omega,
        }
    }
}

impl Sub for Priority {
    type Output = Priority;

    fn sub(self, other: Priority) -> Priority {
        self + (-other)
    }
}

impl fmt::Display for Priority {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let mut parts: Vec<String> = Vec::new();
        if !self.omega.is_zero() {
            parts.push(format!("{}w", self.omega));
        }
        if !self.finite.is_zero() {
            parts.push(format!("{}", self.finite));
        }
        if !self.inv_omega.is_zero() {
            parts.push(format!("{}/w", self.inv_omega));
        }
        if parts.is_empty() {
            write!(f, "0")
        } else {
            write!(f, "{}", parts.join(" + "))
        }
    }
}

impl fmt::Debug for Priority {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(n: i128) -> Dyadic {
        Dyadic::integer(n)
    }

    #[test]
    fn canonical_ordering_of_omega_one_and_inv_omega() {
        let inv = Priority::inv_omega(Dyadic::ONE); // 1/omega
        let one = Priority::integer(1); // 1
        let om = Priority::omega(Dyadic::ONE); // omega

        // 1/omega < 1 < omega
        assert!(inv < one);
        assert!(one < om);
        assert!(inv < om);
    }

    #[test]
    fn infinite_dominates_all_finites() {
        let om = Priority::omega(Dyadic::ONE);
        let big_finite = Priority::integer(1_000_000);
        assert!(om > big_finite);
    }

    #[test]
    fn two_omega_beats_omega() {
        let om = Priority::omega(Dyadic::ONE);
        let two_om = Priority::omega(d(2));
        assert!(two_om > om);
    }

    #[test]
    fn infinitesimal_below_every_positive_finite() {
        let inv = Priority::inv_omega(Dyadic::ONE); // 1/omega
        let tiny_finite = Priority::finite(Dyadic::inv_pow2(20)); // 1/1048576
        assert!(inv < tiny_finite);
        assert!(inv > Priority::ZERO); // still strictly positive
    }

    #[test]
    fn linear_combinations_order_lexicographically() {
        // omega + 1 vs omega + 2  -> the finite part breaks the tie
        let a = Priority::from_terms(&[Term::Omega { scale: Dyadic::ONE }, Term::Finite(d(1))]);
        let b = Priority::from_terms(&[Term::Omega { scale: Dyadic::ONE }, Term::Finite(d(2))]);
        assert!(a < b);

        // omega + 1000 still loses to 2*omega
        let big = Priority::from_terms(&[Term::Omega { scale: Dyadic::ONE }, Term::Finite(d(1000))]);
        let two_om = Priority::omega(d(2));
        assert!(two_om > big);
    }

    #[test]
    fn addition_is_componentwise_and_commutative() {
        let p = Priority::from_terms(&[
            Term::Omega { scale: Dyadic::ONE },
            Term::Finite(d(3)),
            Term::InvOmega { scale: Dyadic::ONE },
        ]);
        let q = Priority::from_terms(&[
            Term::Omega { scale: d(2) },
            Term::Finite(d(-1)),
            Term::InvOmega { scale: d(4) },
        ]);
        let expected = Priority::from_terms(&[
            Term::Omega { scale: d(3) },
            Term::Finite(d(2)),
            Term::InvOmega { scale: d(5) },
        ]);
        assert!((p + q).eq_val(expected));
        assert!((p + q).eq_val(q + p));
    }

    #[test]
    fn negation_cancels() {
        let p = Priority::from_terms(&[
            Term::Omega { scale: d(2) },
            Term::Finite(Dyadic::new(3, 2)),
            Term::InvOmega { scale: d(7) },
        ]);
        assert!((p + (-p)).eq_val(Priority::ZERO));
    }

    #[test]
    fn equality_ignores_construction_order() {
        let a = Priority::from_terms(&[Term::Finite(d(1)), Term::Omega { scale: Dyadic::ONE }]);
        let b = Priority::from_terms(&[Term::Omega { scale: Dyadic::ONE }, Term::Finite(d(1))]);
        assert!(a.eq_val(b));
    }

    #[test]
    fn total_order_is_antisymmetric() {
        // Strictly ascending: 0 < 1/w < 1 < 3/2 < w < 2w. Note that the
        // positive infinitesimal 1/w sits *above* 0 but below every positive
        // finite value.
        let items = [
            Priority::integer(0),
            Priority::inv_omega(Dyadic::ONE),
            Priority::integer(1),
            Priority::finite(Dyadic::new(3, 1)),
            Priority::omega(Dyadic::ONE),
            Priority::omega(d(2)),
        ];
        for (i, a) in items.iter().enumerate() {
            for (j, b) in items.iter().enumerate() {
                match a.compare(*b) {
                    Ordering::Less => assert!(i < j),
                    Ordering::Greater => assert!(i > j),
                    Ordering::Equal => assert_eq!(i, j),
                }
            }
        }
    }
}
