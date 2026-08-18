//! Reduced words in the free group F2 = <a, b>.
//!
//! An element of the free group on two generators is uniquely represented by a
//! *reduced word*: a finite sequence of letters drawn from {a, a^-1, b, b^-1}
//! that contains no adjacent inverse pair (no `x x^-1` and no `x^-1 x`).
//!
//! This module is the fully constructive, exact core. No floating point, no
//! choice, no magic: every operation here is a plain, deterministic algorithm.

/// One of the two generators of F2.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Hash)]
pub enum Gen {
    A,
    B,
}

/// A single letter: a generator, possibly inverted.
///
/// The four letters are `a` (A, false), `a^-1` (A, true), `b` (B, false) and
/// `b^-1` (B, true).
#[derive(Clone, Copy, PartialEq, Eq, Debug, Hash)]
pub struct Letter {
    pub gen: Gen,
    pub inverse: bool,
}

impl Letter {
    /// The four generators, as constants, for convenience.
    pub const A: Letter = Letter { gen: Gen::A, inverse: false };
    pub const A_INV: Letter = Letter { gen: Gen::A, inverse: true };
    pub const B: Letter = Letter { gen: Gen::B, inverse: false };
    pub const B_INV: Letter = Letter { gen: Gen::B, inverse: true };

    /// All four letters, in a fixed order.
    pub const ALL: [Letter; 4] = [Letter::A, Letter::A_INV, Letter::B, Letter::B_INV];

    /// The inverse of this single letter.
    pub fn inv(self) -> Letter {
        Letter { gen: self.gen, inverse: !self.inverse }
    }

    /// Two letters cancel iff one is the inverse of the other.
    pub fn cancels_with(self, other: Letter) -> bool {
        self.gen == other.gen && self.inverse != other.inverse
    }

    /// Human-readable symbol.
    pub fn symbol(self) -> &'static str {
        match (self.gen, self.inverse) {
            (Gen::A, false) => "a",
            (Gen::A, true) => "A", // A denotes a^-1 in compact notation
            (Gen::B, false) => "b",
            (Gen::B, true) => "B", // B denotes b^-1 in compact notation
        }
    }
}

/// A reduced word in F2. The invariant "reduced" (no adjacent inverse pair) is
/// maintained by every constructor and operation in this module.
#[derive(Clone, PartialEq, Eq, Debug, Hash, Default)]
pub struct Word {
    letters: Vec<Letter>,
}

impl Word {
    /// The identity element `e`, i.e. the empty word.
    pub fn identity() -> Word {
        Word { letters: Vec::new() }
    }

    /// Build a reduced word from a raw letter sequence, cancelling inverse
    /// pairs as they appear (free reduction). Returns a new value; the input is
    /// not mutated.
    pub fn reduced(raw: &[Letter]) -> Word {
        let mut stack: Vec<Letter> = Vec::with_capacity(raw.len());
        for &l in raw {
            match stack.last() {
                Some(&top) if top.cancels_with(l) => {
                    stack.pop();
                }
                _ => stack.push(l),
            }
        }
        Word { letters: stack }
    }

    /// Parse a compact word string such as "abAB" where lowercase letters are
    /// generators and uppercase letters are their inverses. Whitespace and `e`
    /// (identity) are ignored. Returns `None` on an unknown character.
    pub fn parse(s: &str) -> Option<Word> {
        let mut raw = Vec::new();
        for c in s.chars() {
            let letter = match c {
                'a' => Letter::A,
                'A' => Letter::A_INV,
                'b' => Letter::B,
                'B' => Letter::B_INV,
                'e' | ' ' | '\t' | '\n' => continue,
                _ => return None,
            };
            raw.push(letter);
        }
        Some(Word::reduced(&raw))
    }

    /// Length of the reduced word (its distance from the identity in the
    /// Cayley graph word metric).
    pub fn len(&self) -> usize {
        self.letters.len()
    }

    /// Is this the identity element?
    pub fn is_identity(&self) -> bool {
        self.letters.is_empty()
    }

    /// The first letter, or `None` for the identity.
    pub fn first(&self) -> Option<Letter> {
        self.letters.first().copied()
    }

    /// Read-only view of the underlying letters.
    pub fn letters(&self) -> &[Letter] {
        &self.letters
    }

    /// Left-multiply by a single generator letter, reducing the result.
    /// Returns a NEW word (immutable style); `self` is untouched.
    pub fn left_mul_letter(&self, g: Letter) -> Word {
        let mut raw = Vec::with_capacity(self.letters.len() + 1);
        raw.push(g);
        raw.extend_from_slice(&self.letters);
        Word::reduced(&raw)
    }

    /// Group multiplication `self * other`, reduced.
    pub fn mul(&self, other: &Word) -> Word {
        let mut raw = Vec::with_capacity(self.letters.len() + other.letters.len());
        raw.extend_from_slice(&self.letters);
        raw.extend_from_slice(&other.letters);
        Word::reduced(&raw)
    }

    /// Compact string form, e.g. "abAB". Identity renders as "e".
    pub fn to_compact(&self) -> String {
        if self.letters.is_empty() {
            return "e".to_string();
        }
        self.letters.iter().map(|l| l.symbol()).collect()
    }
}

impl std::fmt::Display for Word {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.to_compact())
    }
}
