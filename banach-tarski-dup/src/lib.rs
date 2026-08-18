//! banach_tarski_dup --- a constructive, honest demonstration of the
//! Banach-Tarski paradox on the free group F2 = <a, b>.
//!
//! The group-theoretic paradox (see [`decomp`]) is 100% real and constructive:
//! no Axiom of Choice, no floating point, no hand-waving. The famous 3D
//! ball-doubling adds the Axiom of Choice on top of this skeleton to move from
//! F2 to points of the sphere, which is where non-constructiveness enters.
//!
//! The [`theatrical`] module is explicitly labelled stagecraft: it never
//! duplicates real bytes.

pub mod decomp;
pub mod theatrical;
pub mod word;

pub use decomp::{
    classify, enumerate_ball, in_piece, in_translated_piece, reconstruct_copy, verify, Piece,
    VerificationReport,
};
pub use word::{Gen, Letter, Word};
