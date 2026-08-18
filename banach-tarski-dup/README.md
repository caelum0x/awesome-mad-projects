# Banach-Tarski "Duplicator" (Rust)

A small, real, runnable prototype that demonstrates the **combinatorial heart of
the Banach-Tarski paradox** on the free group `F2 = <a, b>` — constructively,
exactly, and honestly.

> **TL;DR honesty caveat.** No disk bytes, atoms, or energy are duplicated for
> free anywhere in this project. The "duplication" that is *genuinely real and
> constructive* happens on the **free-group combinatorics** (`src/word.rs`,
> `src/decomp.rs`), which need no Axiom of Choice. The optional "file mode" is
> **clearly-labelled theatre**: it makes a hard link (a second name for the same
> bytes) and says so loudly. See [Honesty](#honesty-what-is-and-isnt-real).

---

## The concept

The **Banach-Tarski paradox** (1924) says a solid ball in 3D can be cut into
finitely many pieces and reassembled, using only rotations and translations,
into **two** solid balls each the same size as the original. It sounds like it
violates conservation of volume — and it would, if the pieces were measurable.
They are not: the pieces are non-measurable sets, and constructing them requires
the **Axiom of Choice**, which is exactly why the 3D theorem is
**non-constructive** (you can prove the pieces exist but cannot exhibit them).

### The honest, constructive skeleton

The paradox's engine is *pure group theory* and is completely constructive. The
free group on two generators,

```text
F2 = <a, b>   (all reduced words in a, a^-1, b, b^-1, no adjacent inverse pair)
```

admits a **paradoxical decomposition**. Partition every element of F2 by the
letter it starts with:

```text
F2 = {e}  u  W(a)  u  W(a^-1)  u  W(b)  u  W(b^-1)
```

where `W(x)` = reduced words whose first letter is `x`. These five sets are
pairwise disjoint and cover the whole group (a genuine partition).

Now translate two of the pieces by a single generator each. The key identities
are:

```text
a . W(a^-1)   u   W(a)   =   F2
b . W(b^-1)   u   W(b)   =   F2
```

**Why they hold.** Take any reduced word `w`.
- If `w` starts with `a`, then `w ∈ W(a)`.
- If `w` does *not* start with `a`, then `a^-1 . w` is already reduced and
  starts with `a^-1`, so `w = a . (a^-1 w) ∈ a . W(a^-1)`.

Either way `w` is covered — using only **two** of the five pieces, each rigidly
shifted by one generator. The identical argument with `b` covers *all of F2 a
second time* using the other two pieces. So a single copy of F2, cut into
finitely many pieces and translated, yields **two full copies of F2**. That is
the paradox, and it is 100% constructive.

### Where the Axiom of Choice sneaks in (the 3D version)

To get from this group paradox to the ball, one makes `F2` act on the sphere by
rotations, then uses the **Axiom of Choice** to pick one representative point
from each orbit of that action. Transporting the F2 decomposition along the
orbits turns the group paradox into a paradoxical decomposition of the sphere
(and then the ball). That orbit-representative choice is the **only**
non-constructive step — and this prototype deliberately does **not** perform it,
because it cannot be done constructively. We stop at the honest part.

---

## What this prototype actually does

Everything below is exact integer/word computation. No floating point, no
`unsafe`, no Axiom of Choice.

- **`src/word.rs`** — reduced words in F2: letters `{a, a^-1, b, b^-1}`, free
  reduction (cancel adjacent inverse pairs), parsing (`"abAB"`), group
  multiplication, and left-multiplication by a generator.
- **`src/decomp.rs`** — the five-piece classification, the shift/translate
  operation, membership tests for the translated pieces `g . W(g^-1)`,
  breadth-first enumeration of the ball of radius `L` in the Cayley graph, and a
  constructive reconstruction that literally rebuilds two copies of the ball
  from a partition of one.
- **`src/theatrical.rs`** — the clearly-labelled, not-real file "duplication".
- **`src/main.rs`** — the CLI.
- **`tests/paradox.rs`** — 11 tests verifying reduction, the partition property,
  the paradoxical identities, and the set-for-set reconstruction on finite balls.

Uppercase letters are compact notation for inverses: `A = a^-1`, `B = b^-1`.

---

## Build & run

Requires a Rust toolchain (`cargo`).

```bash
cd banach-tarski-dup

cargo build            # compile
cargo test             # run the 11 verification tests
cargo run -- help      # CLI help
```

### CLI commands

```bash
# Verify the paradox on the ball of radius L (default 6)
cargo run -- verify 6

# Enumerate + classify reduced words up to length L (default 4)
cargo run -- words 2

# Actually rebuild two copies from a partition of one, on ball radius L (default 5)
cargo run -- reconstruct 5

# THEATRICAL, NOT REAL: "duplicate" a file via hard link (shared bytes)
cargo run -- theatrical path/to/original.txt path/to/copy.txt
```

---

## Sample output

`cargo test`:

```text
running 11 tests
test left_multiplication_reduces ... ok
test parse_and_display_roundtrip ... ok
test ball_has_expected_cardinality ... ok
test reduction_cancels_inverse_pairs ... ok
test no_duplicate_words_in_ball ... ok
test translated_piece_predicate_matches_definition ... ok
test a_reconstruction_covers_whole_group ... ok
test five_pieces_partition_the_ball ... ok
test b_reconstruction_covers_whole_group ... ok
test verify_report_all_ok ... ok
test constructive_reconstruction_equals_full_ball ... ok

test result: ok. 11 passed; 0 failed; 0 ignored; ...
```

`cargo run -- verify 6`:

```text
== Banach-Tarski paradox on F2, ball radius 6 ==

Reduced words in ball: 1457

Partition into 5 pieces (counts within the ball):
  {e}                   1
  W(a)                364
  W(A)                364
  W(b)                364
  W(B)                364

Partition is disjoint : YES
Partition covers ball : YES

Paradoxical reconstructions:
  a . W(a^-1)  U  W(a)  ==  F2  : YES
  b . W(b^-1)  U  W(b)  ==  F2  : YES

Two full copies of F2 rebuilt from a partition of one : YES
```

`cargo run -- reconstruct 5`:

```text
== Two-copies reconstruction on ball radius 5 ==

Target ball (one copy of F2, truncated): 485 words
Copy A = (W(a) U a.W(a^-1)) rebuilt         : 485 words  -> equals target? YES
Copy B = (W(b) U b.W(b^-1)) rebuilt         : 485 words  -> equals target? YES

Both copies each equal the whole ball, from a partition of ONE : YES
```

`cargo run -- theatrical original.txt copy.txt` (then `ls -li`):

```text
!! THEATRICAL MODE --- this does NOT duplicate real bytes. !!

original : original.txt
'copy'   : copy.txt
method   : hard link (same inode, same bytes)
shares bytes with original : true

THEATRE ONLY: no bytes were duplicated. The 'copy' is a hard link sharing
the SAME inode / the SAME bytes as the original ...

# ls -li confirms both names share one inode and link-count 2:
220640399 -rw-r--r-- 2 user wheel 13 ... copy.txt
220640399 -rw-r--r-- 2 user wheel 13 ... original.txt
```

Note in `verify`: the four non-identity pieces have **equal** counts (364 each
at radius 6) because F2 is symmetric under permuting/inverting generators. Any
two of them, translated, already reproduce the whole thing — twice.

---

## Honesty: what is and isn't real

**Real and constructive (the point of this project):**
- The free-group `F2` decomposition and the identities
  `a.W(a^-1) u W(a) = F2` and `b.W(b^-1) u W(b) = F2`.
- These are verified by direct computation on every reduced word up to a chosen
  length — not sampled, not approximated. The tests build the two copies
  set-for-set and check equality with the original ball.

**Real math, but NOT performed here (because it can't be, constructively):**
- The jump from the group paradox to the 3D ball. That step needs the **Axiom
  of Choice** to select one point per sphere-rotation orbit. The pieces it
  produces are non-measurable and cannot be exhibited. This prototype stops
  before that step on purpose.

**Not real at all (stagecraft, clearly labelled):**
- The `theatrical` file mode does **not** duplicate matter or bytes. It creates
  a **hard link** — a second directory entry pointing at the *same* inode / the
  *same* bytes (verifiable with `ls -li`: identical inode, link count 2). If
  hard-linking is unsupported it instead writes a tiny text pointer file. Both
  behaviours are openly explained in the program's own output. This mirrors how
  the two translated pieces of F2 "share" one underlying group — but on a real
  filesystem you never get free storage, and Banach-Tarski never gives you free
  matter.

## License

MIT.
