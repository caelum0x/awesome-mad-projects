//! Dyadic rationals: numbers of the form `n / 2^k`.
//!
//! Every surreal number that is "born on a finite day" is a dyadic rational,
//! so dyadics are the natural coefficient ring for the finite part of a
//! priority. We keep the value in a normalized form `num / 2^den_pow` where,
//! whenever `num != 0`, `num` is odd (all common factors of two are removed).
//!
//! The type is immutable: every operation returns a fresh `Dyadic`.

use std::cmp::Ordering;
use std::fmt;
use std::ops::{Add, Neg, Sub};

/// A dyadic rational `num / 2^den_pow`.
///
/// Invariant (maintained by `normalize`): if `num == 0` then `den_pow == 0`;
/// otherwise `num` is odd.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Dyadic {
    num: i128,
    den_pow: u32,
}

impl Dyadic {
    /// The additive identity, `0`.
    pub const ZERO: Dyadic = Dyadic { num: 0, den_pow: 0 };
    /// The multiplicative unit, `1`.
    pub const ONE: Dyadic = Dyadic { num: 1, den_pow: 0 };

    /// Build a dyadic from an integer.
    pub const fn integer(n: i128) -> Dyadic {
        Dyadic { num: n, den_pow: 0 }
    }

    /// Build the dyadic `num / 2^den_pow`, then normalize.
    pub fn new(num: i128, den_pow: u32) -> Dyadic {
        Dyadic { num, den_pow }.normalize()
    }

    /// Return `1 / 2^k` (a positive dyadic smaller than any coarser step).
    pub fn inv_pow2(k: u32) -> Dyadic {
        Dyadic::new(1, k)
    }

    /// Remove shared powers of two so the representation is canonical.
    fn normalize(self) -> Dyadic {
        if self.num == 0 {
            return Dyadic::ZERO;
        }
        let mut num = self.num;
        let mut den_pow = self.den_pow;
        while den_pow > 0 && num % 2 == 0 {
            num /= 2;
            den_pow -= 1;
        }
        Dyadic { num, den_pow }
    }

    /// Multiply by an integer scalar (enough for `2 * omega`-style combos).
    pub fn scale_int(self, k: i128) -> Dyadic {
        Dyadic::new(self.num * k, self.den_pow)
    }

    /// True when the value is exactly zero.
    pub fn is_zero(self) -> bool {
        self.num == 0
    }

    /// Compare two dyadics by cross-multiplying over a common denominator.
    pub fn compare(self, other: Dyadic) -> Ordering {
        let shift = self.den_pow.max(other.den_pow);
        let a = self.num << (shift - self.den_pow);
        let b = other.num << (shift - other.den_pow);
        a.cmp(&b)
    }

    /// Approximate floating-point value (for display only, never for ordering).
    pub fn to_f64(self) -> f64 {
        self.num as f64 / 2f64.powi(self.den_pow as i32)
    }
}

impl PartialOrd for Dyadic {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Dyadic {
    fn cmp(&self, other: &Self) -> Ordering {
        Dyadic::compare(*self, *other)
    }
}

impl Add for Dyadic {
    type Output = Dyadic;

    /// Add over a common denominator `2^max(k1, k2)`.
    fn add(self, other: Dyadic) -> Dyadic {
        let shift = self.den_pow.max(other.den_pow);
        let a = self.num << (shift - self.den_pow);
        let b = other.num << (shift - other.den_pow);
        Dyadic::new(a + b, shift)
    }
}

impl Neg for Dyadic {
    type Output = Dyadic;

    fn neg(self) -> Dyadic {
        Dyadic {
            num: -self.num,
            den_pow: self.den_pow,
        }
    }
}

impl Sub for Dyadic {
    type Output = Dyadic;

    fn sub(self, other: Dyadic) -> Dyadic {
        self + (-other)
    }
}

impl fmt::Display for Dyadic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.den_pow == 0 {
            write!(f, "{}", self.num)
        } else {
            write!(f, "{}/{}", self.num, 1i128 << self.den_pow)
        }
    }
}

impl fmt::Debug for Dyadic {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalization_removes_factors_of_two() {
        // 2/4 == 1/2
        assert_eq!(Dyadic::new(2, 2), Dyadic::new(1, 1));
        // 4/4 == 1
        assert_eq!(Dyadic::new(4, 2), Dyadic::ONE);
        // 0/8 == 0
        assert_eq!(Dyadic::new(0, 3), Dyadic::ZERO);
    }

    #[test]
    fn addition_and_subtraction() {
        // 1/2 + 1/4 == 3/4
        assert_eq!(Dyadic::new(1, 1) + Dyadic::new(1, 2), Dyadic::new(3, 2));
        // 3/4 - 1/4 == 1/2
        assert_eq!(Dyadic::new(3, 2) - Dyadic::new(1, 2), Dyadic::new(1, 1));
        // a + (-a) == 0
        let a = Dyadic::new(5, 3);
        assert!((a + (-a)).is_zero());
    }

    #[test]
    fn ordering() {
        assert!(Dyadic::new(1, 2) < Dyadic::new(1, 1)); // 1/4 < 1/2
        assert!(Dyadic::integer(3) > Dyadic::new(3, 1)); // 3 > 3/2
        assert!(Dyadic::integer(-1) < Dyadic::ZERO);
    }
}
