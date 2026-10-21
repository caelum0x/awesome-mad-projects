// Package main implements Shadow Clone CRDT: Naruto's Shadow Clone Jutsu
// (Kage Bunshin no Jutsu) modeled as a real, state-based CRDT replication
// system.
//
// The anime claim: a ninja spawns many autonomous clones, each clone trains
// or fights independently, and when a clone "dispels" its memories and
// experience flow back into the original instantly -- in whatever order the
// clones happen to dispel, even if several vanish at once.
//
// The honest systems core: that is exactly the convergence guarantee of a
// state-based Conflict-free Replicated Data Type (CvRDT), as formalized by
// Shapiro, Preguica, Baquero and Zawirski, "Conflict-free Replicated Data
// Types" (2011, https://inria.hal.science/inria-00609399/document). A CvRDT's
// merge operation forms a join-semilattice: it is commutative, associative,
// and idempotent. Those three laws, and nothing else, are what guarantee
// Strong Eventual Consistency (SEC) -- any set of replicas that have seen the
// same updates converge to the same state, no matter the order updates
// arrive in, and merging the same update twice changes nothing.
//
// That is implemented here, for real, with real goroutines playing the part
// of shadow clones and real property-based tests pinning the three laws.
package main

// CRDT is the contract every replicated "memory shard" in this project
// satisfies: a value type whose Merge computes the least upper bound (join)
// of two replica states, and whose Clone produces an independent deep copy so
// one goroutine can mutate its own replica without any shared memory with
// another.
//
// Implementations never mutate a receiver in place (see each type's Merge):
// every operation returns a new value. That is not just an immutability
// style preference -- it is required for the join-semilattice laws to even
// be a meaningful, testable statement about values rather than about
// mutation order.
//
// For T to be a valid CvRDT payload, Merge must satisfy, for all a, b, c of
// type T:
//
//	commutative:  a.Merge(b)            == b.Merge(a)
//	associative:  a.Merge(b).Merge(c)   == a.Merge(b.Merge(c))
//	idempotent:   a.Merge(a)            == a
//
// Every concrete type below (GCounter, PNCounter, GSet, ORSet, LWWRegister)
// and their product (Memory) is checked against these three laws by
// randomized property tests in crdt_test.go and memory_test.go.
type CRDT[T any] interface {
	Merge(other T) T
	Clone() T
}

// compile-time proof that each concrete type below actually implements the
// CRDT[T] contract with the right self-referencing type parameter.
var (
	_ CRDT[GCounter]    = GCounter{}
	_ CRDT[PNCounter]   = PNCounter{}
	_ CRDT[GSet]        = GSet{}
	_ CRDT[ORSet]       = ORSet{}
	_ CRDT[LWWRegister] = LWWRegister{}
	_ CRDT[Memory]      = Memory{}
)
