package main

// GCounter is a grow-only counter CRDT: it tracks training reps performed by
// every clone (and the original) and only ever goes up.
//
// State is one non-negative count per replica ("clone-0", "clone-3",
// "original", ...). Each replica may only increment its *own* slot, which is
// what makes the per-slot maximum a safe merge: no replica can ever shrink
// another replica's contribution, so taking the pointwise max can never lose
// an increment that either side has already recorded.
type GCounter struct {
	counts map[string]uint64
}

// NewGCounter returns the identity element: every replica at zero.
func NewGCounter() GCounter {
	return GCounter{counts: map[string]uint64{}}
}

// Clone returns an independent deep copy.
func (g GCounter) Clone() GCounter {
	cp := make(map[string]uint64, len(g.counts))
	for k, v := range g.counts {
		cp[k] = v
	}
	return GCounter{counts: cp}
}

// Increment returns a new GCounter with replica's own slot increased by n.
// It never mutates g.
//
// n == 0 is a true no-op: it returns an unchanged clone rather than writing
// a zero-valued map entry for replica. That guard matters for more than
// style -- Go's `map[k] += 0` on an absent key *does* insert k with value 0,
// which would make two semantically-identical counters (same Value(), same
// per-replica contributions) compare unequal under reflect.DeepEqual purely
// because one has an explicit zero entry and the other doesn't. The
// commutativity/associativity/idempotency property tests in crdt_test.go
// compare states with DeepEqual, so a stray zero entry is a real
// correctness bug, not a cosmetic one, and was caught by exactly that test.
func (g GCounter) Increment(replica string, n uint64) GCounter {
	if n == 0 {
		return g.Clone()
	}
	cp := g.Clone()
	cp.counts[replica] += n
	return cp
}

// Merge returns the pointwise maximum of every replica slot: the join of the
// two counters in the natural-numbers-per-replica lattice.
func (g GCounter) Merge(other GCounter) GCounter {
	cp := g.Clone()
	for k, v := range other.counts {
		if v > cp.counts[k] {
			cp.counts[k] = v
		}
	}
	return cp
}

// Value is the total reps across every replica: sum of the per-replica maxes.
func (g GCounter) Value() uint64 {
	var total uint64
	for _, v := range g.counts {
		total += v
	}
	return total
}

// Replicas returns a snapshot of the per-replica counts, for display/testing.
func (g GCounter) Replicas() map[string]uint64 {
	return g.Clone().counts
}
