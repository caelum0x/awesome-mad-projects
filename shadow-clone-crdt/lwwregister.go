package main

// LWWRegister is a Last-Writer-Wins Register CRDT: the clone's latest
// reported training status ("drilling kunai form", "sparring", "exhausted",
// ...). Exactly one value is visible at a time, chosen by comparing
// timestamps.
//
// Real LWW-Registers need a *total order* on timestamps to be deterministic,
// and wall-clock time is not actually total (two writes on two goroutines can
// get the identical wall-clock tick, and clocks can skew). This project does
// not hand-wave that problem away with time.Now(): it uses a Lamport-style
// logical clock, (Counter, ReplicaID), ordered lexicographically. Counter
// ties are broken by ReplicaID, which is unique per clone, so the order is
// always total and the merge is always deterministic -- including in tests,
// which would otherwise be flaky against real wall-clock resolution.
type LWWRegister struct {
	Value     string
	Counter   uint64
	ReplicaID string
}

// NewLWWRegister returns the identity element: an empty, zero-clock status
// that any real write will immediately outrank.
func NewLWWRegister() LWWRegister {
	return LWWRegister{}
}

// Clone returns an independent copy (the struct has no reference fields, so
// this is a plain value copy, but it keeps the CRDT[T] contract uniform).
func (r LWWRegister) Clone() LWWRegister { return r }

// Set returns a new register reporting value, stamped with counter (the
// writer's own monotonically increasing logical clock) and replica (the
// writer's id, used only to break Counter ties deterministically).
func (r LWWRegister) Set(value string, counter uint64, replica string) LWWRegister {
	return LWWRegister{Value: value, Counter: counter, ReplicaID: replica}
}

// Merge keeps whichever register has the higher (Counter, ReplicaID) pair.
// Lexicographic comparison on that pair is a total order, so exactly one
// side wins (or they are equal, in the idempotent a.Merge(a) == a case).
func (r LWWRegister) Merge(other LWWRegister) LWWRegister {
	if other.Counter > r.Counter {
		return other
	}
	if other.Counter < r.Counter {
		return r
	}
	// Counter tie: break deterministically on ReplicaID.
	if other.ReplicaID > r.ReplicaID {
		return other
	}
	return r
}
