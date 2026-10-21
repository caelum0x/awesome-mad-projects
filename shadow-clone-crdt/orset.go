package main

import "sort"

// orTag uniquely identifies one *add event* of an element, not the element
// itself. Two clones can each add "exploding-tag-scroll" and get two
// different tags for the same element name -- that is what lets the
// add-wins rule below work.
type orTag struct {
	elem string
	id   string // caller-supplied, must be unique per add (see Clone.nextTag)
}

// ORSet is an add-wins Observed-Remove Set CRDT (Shapiro et al. 2011, section
// 3.3.2): the scrolls a clone is currently carrying. Unlike GSet, elements
// *can* be removed (a scroll gets used or dropped) -- but naive
// "remove = delete from a shared set" is not commutative under concurrency:
// if clone A drops a scroll while clone B concurrently picks up a fresh copy
// of the same scroll, a delete-wins merge would lose B's scroll. ORSet avoids
// that by tagging every add with a fresh id and only removing the tags a
// replica has actually observed.
//
// This project implements the add-wins variant: Remove(elem) only tombstones
// the tags for elem that are visible to the caller *at the time of the
// call*. A concurrent Add(elem) that the caller hasn't observed yet survives
// the merge, so concurrent add-vs-remove resolves in favor of the add --
// a scroll a clone just picked up is never phantom-dropped by another
// clone's stale Remove.
type ORSet struct {
	adds    map[orTag]struct{}
	removes map[orTag]struct{}
}

// NewORSet returns the identity element: nothing carried, nothing dropped.
func NewORSet() ORSet {
	return ORSet{adds: map[orTag]struct{}{}, removes: map[orTag]struct{}{}}
}

// Clone returns an independent deep copy.
func (s ORSet) Clone() ORSet {
	adds := make(map[orTag]struct{}, len(s.adds))
	for k := range s.adds {
		adds[k] = struct{}{}
	}
	removes := make(map[orTag]struct{}, len(s.removes))
	for k := range s.removes {
		removes[k] = struct{}{}
	}
	return ORSet{adds: adds, removes: removes}
}

// Add tags elem with id (caller must guarantee id is globally unique, e.g. a
// per-replica monotonic counter -- see Clone.nextTag) and returns a new
// ORSet with that tag present.
func (s ORSet) Add(elem, id string) ORSet {
	cp := s.Clone()
	cp.adds[orTag{elem: elem, id: id}] = struct{}{}
	return cp
}

// Remove tombstones every tag for elem that is *currently visible* in s
// (i.e. added but not already removed). Tags for elem added by a replica
// that hasn't been merged in yet are untouched -- that replica's add will
// win when the two states are later merged.
func (s ORSet) Remove(elem string) ORSet {
	cp := s.Clone()
	for tag := range cp.adds {
		if tag.elem != elem {
			continue
		}
		if _, tombstoned := cp.removes[tag]; tombstoned {
			continue
		}
		cp.removes[tag] = struct{}{}
	}
	return cp
}

// Merge is the union of the add-tag set and the union of the remove-tag set,
// independently. Union is commutative/associative/idempotent, so the pair is
// too; visibility (Contains/Elements) is then a pure function of the merged
// pair, which is what makes add-wins fall out automatically rather than
// needing special-case merge logic.
func (s ORSet) Merge(other ORSet) ORSet {
	adds := make(map[orTag]struct{}, len(s.adds)+len(other.adds))
	for k := range s.adds {
		adds[k] = struct{}{}
	}
	for k := range other.adds {
		adds[k] = struct{}{}
	}
	removes := make(map[orTag]struct{}, len(s.removes)+len(other.removes))
	for k := range s.removes {
		removes[k] = struct{}{}
	}
	for k := range other.removes {
		removes[k] = struct{}{}
	}
	return ORSet{adds: adds, removes: removes}
}

// Contains reports whether elem has at least one add tag that is not
// tombstoned.
func (s ORSet) Contains(elem string) bool {
	for tag := range s.adds {
		if tag.elem != elem {
			continue
		}
		if _, tombstoned := s.removes[tag]; !tombstoned {
			return true
		}
	}
	return false
}

// Elements returns the sorted, deduplicated set of currently-visible
// elements.
func (s ORSet) Elements() []string {
	seen := map[string]struct{}{}
	for tag := range s.adds {
		if _, tombstoned := s.removes[tag]; tombstoned {
			continue
		}
		seen[tag.elem] = struct{}{}
	}
	out := make([]string, 0, len(seen))
	for e := range seen {
		out = append(out, e)
	}
	sort.Strings(out)
	return out
}
