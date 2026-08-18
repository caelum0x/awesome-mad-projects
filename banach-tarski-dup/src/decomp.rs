//! The paradoxical decomposition of F2, done constructively.
//!
//! Classic five-piece decomposition of the free group F2 = <a, b>:
//!
//! ```text
//! F2 = {e} u W(a) u W(a^-1) u W(b) u W(b^-1)
//! ```
//!
//! where W(x) is the set of reduced words whose FIRST letter is x. These five
//! sets are pairwise disjoint and cover the whole group.
//!
//! The paradox is the pair of identities
//!
//! ```text
//! a . W(a^-1)  u  W(a)  =  F2
//! b . W(b^-1)  u  W(b)  =  F2
//! ```
//!
//! Reason: if w does not start with `a`, then `a^-1 · w` is already reduced and
//! starts with `a^-1`, so `w ∈ a·W(a^-1)`. If w does start with `a`, then
//! `w ∈ W(a)`. Either way w is covered — using only TWO of the five pieces
//! (each translated by one generator). The very same trick with `b` covers all
//! of F2 a SECOND time using the other two pieces. So a single copy of F2,
//! cut into finitely many pieces and rigidly translated, yields TWO copies of
//! F2. That is the group-theoretic heart of Banach-Tarski.

use crate::word::{Letter, Word};
use std::collections::HashSet;

/// The five pieces of the classic decomposition of F2.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Piece {
    /// The identity element {e}.
    Identity,
    /// W(x): reduced words whose first letter is `x`.
    StartsWith(Letter),
}

impl Piece {
    /// The five pieces, in canonical order.
    pub fn all() -> [Piece; 5] {
        [
            Piece::Identity,
            Piece::StartsWith(Letter::A),
            Piece::StartsWith(Letter::A_INV),
            Piece::StartsWith(Letter::B),
            Piece::StartsWith(Letter::B_INV),
        ]
    }

    /// Short label such as "{e}", "W(a)", "W(A=a^-1)".
    pub fn label(self) -> String {
        match self {
            Piece::Identity => "{e}".to_string(),
            Piece::StartsWith(l) => format!("W({})", l.symbol()),
        }
    }
}

/// Classify a reduced word into exactly one of the five pieces.
///
/// This is a total function: every element of F2 lands in precisely one piece,
/// which is what makes {e}, W(a), W(a^-1), W(b), W(b^-1) a genuine PARTITION.
pub fn classify(w: &Word) -> Piece {
    match w.first() {
        None => Piece::Identity,
        Some(l) => Piece::StartsWith(l),
    }
}

/// True iff `w` belongs to `piece`.
pub fn in_piece(w: &Word, piece: Piece) -> bool {
    classify(w) == piece
}

/// Convenience: the label of the piece a word falls into (for CLI display).
pub fn classify_label(w: &Word) -> String {
    classify(w).label()
}

/// Membership test for the translated piece `g · W(g^-1)`.
///
/// `w ∈ g·W(g^-1)` iff `g^-1 · w ∈ W(g^-1)`, i.e. the reduced form of
/// `g^-1 · w` starts with `g^-1`. Equivalently (and this is the punch line):
/// `w` does NOT start with `g`.
pub fn in_translated_piece(w: &Word, g: Letter) -> bool {
    let shifted = w.left_mul_letter(g.inv());
    shifted.first() == Some(g.inv())
}

/// Enumerate every reduced word of length `<= max_len` (the closed ball of
/// radius `max_len` around the identity in the Cayley graph). Deterministic,
/// exact, and free of the Axiom of Choice.
pub fn enumerate_ball(max_len: usize) -> Vec<Word> {
    // Breadth-first growth: level n holds all reduced words of length exactly n.
    let mut all: Vec<Word> = vec![Word::identity()];
    let mut frontier: Vec<Word> = vec![Word::identity()];

    for _ in 0..max_len {
        let mut next = Vec::new();
        for w in &frontier {
            for &g in &Letter::ALL {
                // Appending g keeps the word reduced iff g does not cancel the
                // last letter. For the identity, any g is fine.
                let keeps_reduced = match w.letters().last() {
                    Some(&last) => !last.cancels_with(g),
                    None => true,
                };
                if keeps_reduced {
                    let mut raw = w.letters().to_vec();
                    raw.push(g);
                    next.push(Word::reduced(&raw));
                }
            }
        }
        all.extend(next.iter().cloned());
        frontier = next;
    }
    all
}

/// Result of empirically verifying the paradox on a finite ball.
#[derive(Clone, Debug)]
pub struct VerificationReport {
    pub radius: usize,
    /// Number of reduced words in the target ball of `radius`.
    pub target_ball_size: usize,
    /// Piece -> count within the target ball (proves it is a partition).
    pub piece_counts: Vec<(String, usize)>,
    /// Did `a·W(a^-1) ∪ W(a)` cover the whole target ball?
    pub copy_a_covers: bool,
    /// Did `b·W(b^-1) ∪ W(b)` cover the whole target ball?
    pub copy_b_covers: bool,
    /// Are the five pieces genuinely disjoint on the target ball?
    pub partition_is_disjoint: bool,
    /// Do the piece counts sum to the whole ball (partition covers everything)?
    pub partition_covers: bool,
}

impl VerificationReport {
    /// Everything checks out?
    pub fn all_ok(&self) -> bool {
        self.copy_a_covers
            && self.copy_b_covers
            && self.partition_is_disjoint
            && self.partition_covers
    }
}

/// Empirically confirm the paradoxical identities on the closed ball of the
/// given `radius`.
///
/// For each reduced word `w` in the ball we check membership in the two
/// translated reconstructions using the exact predicates above, and we verify
/// that the five pieces form a partition. Everything is checked by direct
/// computation on concrete words — no probabilistic sampling.
pub fn verify(radius: usize) -> VerificationReport {
    let ball = enumerate_ball(radius);
    let ball_set: HashSet<&Word> = ball.iter().collect();

    // Piece counts + disjointness + coverage, all in one pass.
    let mut piece_counts: Vec<(String, usize)> =
        Piece::all().iter().map(|p| (p.label(), 0usize)).collect();
    let mut assigned_total = 0usize;
    let mut disjoint = true;

    for w in &ball {
        // Exactly one piece must claim w.
        let mut hits = 0;
        for (idx, p) in Piece::all().iter().enumerate() {
            if in_piece(w, *p) {
                piece_counts[idx].1 += 1;
                hits += 1;
            }
        }
        if hits != 1 {
            disjoint = false;
        }
        assigned_total += hits.min(1);
    }

    let partition_covers = assigned_total == ball.len();

    // Reconstruction coverage: does a·W(a^-1) ∪ W(a) hit every word of the ball?
    let copy_a_covers = ball.iter().all(|w| {
        in_piece(w, Piece::StartsWith(Letter::A)) || in_translated_piece(w, Letter::A)
    });
    let copy_b_covers = ball.iter().all(|w| {
        in_piece(w, Piece::StartsWith(Letter::B)) || in_translated_piece(w, Letter::B)
    });

    // Sanity: ball_set has the same cardinality as the ball vector (no dupes).
    debug_assert_eq!(ball_set.len(), ball.len());

    VerificationReport {
        radius,
        target_ball_size: ball.len(),
        piece_counts,
        copy_a_covers,
        copy_b_covers,
        partition_is_disjoint: disjoint,
        partition_covers,
    }
}

/// Constructively rebuild F2 (restricted to the ball) from two of its pieces,
/// translated. Returns the set actually produced by
/// `(W(g) ∩ ball) ∪ (g · (W(g^-1) ∩ ball_source))`.
///
/// Because left-multiplying `W(g^-1)` by `g` shortens words by one letter, we
/// draw the source pieces from a slightly larger ball (`radius + 1`) so that
/// the reconstruction fully covers the target ball of `radius`. The returned
/// set, intersected with the target ball, should equal the entire target ball.
pub fn reconstruct_copy(radius: usize, g: Letter) -> HashSet<Word> {
    let source = enumerate_ball(radius + 1);
    let target: HashSet<Word> = enumerate_ball(radius).into_iter().collect();

    let mut produced: HashSet<Word> = HashSet::new();

    for w in &source {
        // Piece W(g): kept as-is.
        if in_piece(w, Piece::StartsWith(g)) && target.contains(w) {
            produced.insert(w.clone());
        }
        // Piece W(g^-1): translated by g (left-multiply, then reduce).
        if in_piece(w, Piece::StartsWith(g.inv())) {
            let moved = w.left_mul_letter(g);
            if target.contains(&moved) {
                produced.insert(moved);
            }
        }
    }
    produced
}
