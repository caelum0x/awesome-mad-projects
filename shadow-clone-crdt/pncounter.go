package main

// PNCounter is an increment/decrement counter CRDT: it tracks net chakra
// flow (chakra pills found minus chakra spent casting techniques) for every
// replica. It is built from two GCounters -- P for increments, N for
// decrements -- because a grow-only counter cannot merge decrements safely,
// but "decrements, tracked as their own grow-only ledger" can.
type PNCounter struct {
	P GCounter // chakra gained, per replica
	N GCounter // chakra spent, per replica
}

// NewPNCounter returns the identity element: zero net chakra everywhere.
func NewPNCounter() PNCounter {
	return PNCounter{P: NewGCounter(), N: NewGCounter()}
}

// Clone returns an independent deep copy.
func (c PNCounter) Clone() PNCounter {
	return PNCounter{P: c.P.Clone(), N: c.N.Clone()}
}

// Gain returns a new PNCounter with replica's gained-chakra ledger up by n.
func (c PNCounter) Gain(replica string, n uint64) PNCounter {
	return PNCounter{P: c.P.Increment(replica, n), N: c.N.Clone()}
}

// Spend returns a new PNCounter with replica's spent-chakra ledger up by n.
func (c PNCounter) Spend(replica string, n uint64) PNCounter {
	return PNCounter{P: c.P.Clone(), N: c.N.Increment(replica, n)}
}

// Merge merges the gain ledger and the spend ledger independently. Each is a
// GCounter, so each merge is itself commutative/associative/idempotent, and
// the pair of them (a product of two join-semilattices) is one too.
func (c PNCounter) Merge(other PNCounter) PNCounter {
	return PNCounter{P: c.P.Merge(other.P), N: c.N.Merge(other.N)}
}

// Value is net chakra: total gained minus total spent. It can go negative
// (a clone in chakra debt), unlike the underlying GCounters, which never do.
func (c PNCounter) Value() int64 {
	return int64(c.P.Value()) - int64(c.N.Value())
}
