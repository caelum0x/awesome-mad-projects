package main

// Memory is the full replicated state a single clone (or the original)
// carries: one shard per kind of "shinobi experience", built as a *product*
// of five independent CRDTs.
//
//   - Reps    GCounter    training reps drilled (never un-drilled)
//   - Chakra  PNCounter   net chakra: pills found minus techniques cast
//   - Jutsu   GSet        jutsu names drilled to muscle memory
//   - Scrolls ORSet       scrolls currently carried (can be picked up/used)
//   - Status  LWWRegister latest self-reported training status
//
// Merge is defined componentwise. This is the standard CRDT composition
// result: the Cartesian product of join-semilattices, ordered componentwise,
// is itself a join-semilattice, with join computed componentwise. Each
// component already satisfies commutativity/associativity/idempotency on its
// own (proven in crdt_test.go); componentwise combination preserves all
// three laws for the product, because each law is checked independently,
// coordinate by coordinate. memory_test.go verifies this empirically on the
// composite type as well, not just the parts.
type Memory struct {
	Reps    GCounter
	Chakra  PNCounter
	Jutsu   GSet
	Scrolls ORSet
	Status  LWWRegister
}

// NewMemory returns the identity element of the product lattice: the
// identity element of every component.
func NewMemory() Memory {
	return Memory{
		Reps:    NewGCounter(),
		Chakra:  NewPNCounter(),
		Jutsu:   NewGSet(),
		Scrolls: NewORSet(),
		Status:  NewLWWRegister(),
	}
}

// Clone returns an independent deep copy: every component cloned.
func (m Memory) Clone() Memory {
	return Memory{
		Reps:    m.Reps.Clone(),
		Chakra:  m.Chakra.Clone(),
		Jutsu:   m.Jutsu.Clone(),
		Scrolls: m.Scrolls.Clone(),
		Status:  m.Status.Clone(),
	}
}

// Merge merges every component independently and recombines them.
func (m Memory) Merge(other Memory) Memory {
	return Memory{
		Reps:    m.Reps.Merge(other.Reps),
		Chakra:  m.Chakra.Merge(other.Chakra),
		Jutsu:   m.Jutsu.Merge(other.Jutsu),
		Scrolls: m.Scrolls.Merge(other.Scrolls),
		Status:  m.Status.Merge(other.Status),
	}
}
