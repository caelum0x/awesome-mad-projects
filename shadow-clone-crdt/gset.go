package main

import "sort"

// GSet is a grow-only set CRDT: jutsu techniques a clone has drilled enough
// to have "muscle memory" of. Once learned, a jutsu is never forgotten, so
// union is a safe, lossless merge.
type GSet struct {
	elems map[string]struct{}
}

// NewGSet returns the identity element: the empty set.
func NewGSet() GSet {
	return GSet{elems: map[string]struct{}{}}
}

// Clone returns an independent deep copy.
func (s GSet) Clone() GSet {
	cp := make(map[string]struct{}, len(s.elems))
	for k := range s.elems {
		cp[k] = struct{}{}
	}
	return GSet{elems: cp}
}

// Add returns a new GSet with elem learned. Adding an already-known jutsu is
// a no-op value-wise, which is exactly why union is idempotent.
func (s GSet) Add(elem string) GSet {
	cp := s.Clone()
	cp.elems[elem] = struct{}{}
	return cp
}

// Merge is set union: the join in the subset lattice ordered by ⊆.
func (s GSet) Merge(other GSet) GSet {
	cp := s.Clone()
	for k := range other.elems {
		cp.elems[k] = struct{}{}
	}
	return cp
}

// Contains reports whether elem has been learned.
func (s GSet) Contains(elem string) bool {
	_, ok := s.elems[elem]
	return ok
}

// Len is the number of distinct jutsu learned.
func (s GSet) Len() int { return len(s.elems) }

// Elements returns a sorted snapshot, for deterministic display/testing.
func (s GSet) Elements() []string {
	out := make([]string, 0, len(s.elems))
	for k := range s.elems {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
