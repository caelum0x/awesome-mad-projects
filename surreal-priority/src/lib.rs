//! Surreal numbers as process priorities.
//!
//! * [`dyadic`] — dyadic rationals `n / 2^k`, the finite coefficient ring.
//! * [`surreal`] — the `omega*a + b + (1/omega)*c` priority subgroup with
//!   surreal ordering, addition, and negation.
//! * [`scheduler`] — a deterministic, OS-free scheduler simulation driven by
//!   surreal priorities.
//!
//! See `README.md` for the concept, the honest math boundary, and run
//! instructions with sample output.

#![forbid(unsafe_code)]

pub mod dyadic;
pub mod scheduler;
pub mod surreal;
