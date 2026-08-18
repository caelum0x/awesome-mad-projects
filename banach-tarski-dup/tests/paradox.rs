//! Integration tests: the paradoxical identities and their supporting lemmas,
//! verified constructively on finite balls of the Cayley graph of F2.

use std::collections::HashSet;

use banach_tarski_dup::decomp::{
    classify, enumerate_ball, in_piece, in_translated_piece, reconstruct_copy, verify, Piece,
};
use banach_tarski_dup::word::{Letter, Word};

// ---------- word reduction ----------

#[test]
fn reduction_cancels_inverse_pairs() {
    // a a^-1 -> e
    let w = Word::reduced(&[Letter::A, Letter::A_INV]);
    assert!(w.is_identity(), "a a^-1 must reduce to identity");

    // a b b^-1 a^-1 -> e
    let w = Word::reduced(&[Letter::A, Letter::B, Letter::B_INV, Letter::A_INV]);
    assert!(w.is_identity(), "a b b^-1 a^-1 must reduce to identity");

    // a b a^-1 stays as-is (no adjacent inverse pair)
    let w = Word::reduced(&[Letter::A, Letter::B, Letter::A_INV]);
    assert_eq!(w.len(), 3);
    assert_eq!(w.to_compact(), "abA");
}

#[test]
fn parse_and_display_roundtrip() {
    let w = Word::parse("abAB").unwrap();
    assert_eq!(w.to_compact(), "abAB");
    assert_eq!(Word::parse("aA").unwrap().to_compact(), "e");
    assert_eq!(Word::parse("e").unwrap().to_compact(), "e");
    assert!(Word::parse("xyz").is_none());
}

#[test]
fn left_multiplication_reduces() {
    // a . (a^-1 b) = b
    let w = Word::parse("Ab").unwrap();
    let shifted = w.left_mul_letter(Letter::A);
    assert_eq!(shifted.to_compact(), "b");
}

// ---------- classification is a genuine partition ----------

#[test]
fn five_pieces_partition_the_ball() {
    let ball = enumerate_ball(7);
    for w in &ball {
        // Each word lies in exactly one piece.
        let hits = Piece::all().iter().filter(|p| in_piece(w, **p)).count();
        assert_eq!(hits, 1, "word {w} must belong to exactly one piece");
    }
    // Identity is the only element of the {e} piece.
    let identity_count = ball.iter().filter(|w| classify(w) == Piece::Identity).count();
    assert_eq!(identity_count, 1);
}

#[test]
fn ball_has_expected_cardinality() {
    // |ball(0)| = 1 (just the identity). Level 1 has 4 letters, and every later
    // level has 3x the previous (3 non-cancelling continuations per word):
    // |ball(L)| = 1 + sum_{n=1..L} 4 * 3^(n-1).
    for l in 0..=6usize {
        let got = enumerate_ball(l).len();
        let mut want = 1usize;
        let mut lvl = 4usize;
        for _ in 0..l {
            want += lvl;
            lvl *= 3;
        }
        assert_eq!(got, want, "ball radius {l}");
    }
}

#[test]
fn no_duplicate_words_in_ball() {
    let ball = enumerate_ball(6);
    let unique: HashSet<&Word> = ball.iter().collect();
    assert_eq!(unique.len(), ball.len(), "enumeration must be duplicate-free");
}

// ---------- the paradox itself ----------

#[test]
fn translated_piece_predicate_matches_definition() {
    // w in a.W(a^-1)  iff  a^-1.w starts with a^-1  iff  w does NOT start with a.
    for w in enumerate_ball(6) {
        let starts_with_a = classify(&w) == Piece::StartsWith(Letter::A);
        assert_eq!(
            in_translated_piece(&w, Letter::A),
            !starts_with_a,
            "membership of {w} in a.W(a^-1) contradicts the definition"
        );
    }
}

#[test]
fn a_reconstruction_covers_whole_group() {
    // a.W(a^-1) U W(a) == F2  (checked on a finite ball)
    for w in enumerate_ball(7) {
        let covered =
            in_piece(&w, Piece::StartsWith(Letter::A)) || in_translated_piece(&w, Letter::A);
        assert!(covered, "{w} not covered by a.W(a^-1) U W(a)");
    }
}

#[test]
fn b_reconstruction_covers_whole_group() {
    // b.W(b^-1) U W(b) == F2  (checked on a finite ball)
    for w in enumerate_ball(7) {
        let covered =
            in_piece(&w, Piece::StartsWith(Letter::B)) || in_translated_piece(&w, Letter::B);
        assert!(covered, "{w} not covered by b.W(b^-1) U W(b)");
    }
}

#[test]
fn constructive_reconstruction_equals_full_ball() {
    // Actually BUILD the two copies from the pieces and compare, set-for-set.
    for radius in 0..=5 {
        let target: HashSet<Word> = enumerate_ball(radius).into_iter().collect();
        let copy_a = reconstruct_copy(radius, Letter::A);
        let copy_b = reconstruct_copy(radius, Letter::B);
        assert_eq!(copy_a, target, "copy A must equal the full ball (radius {radius})");
        assert_eq!(copy_b, target, "copy B must equal the full ball (radius {radius})");
    }
}

#[test]
fn verify_report_all_ok() {
    for radius in 0..=6 {
        let report = verify(radius);
        assert!(report.all_ok(), "verification failed at radius {radius}: {report:?}");
        assert!(report.partition_is_disjoint);
        assert!(report.partition_covers);
    }
}
