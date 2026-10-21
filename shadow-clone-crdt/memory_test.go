package main

import (
	"fmt"
	"math/rand"
	"reflect"
	"testing"
)

// randomMemory builds a Memory by replaying n random clone actions through a
// real CloneCtx -- i.e. through the same code path a goroutine in
// Army.Spawn would use, not a hand-built struct literal.
func randomMemory(rng *rand.Rand, replica string, n int) Memory {
	c := newCloneCtx(replica, NewMemory())
	jutsu := []string{"kawarimi", "rasengan-form", "leaf-whirlwind"}
	scrolls := []string{"fire-scroll", "wind-scroll"}
	status := []string{"sparring", "resting", "drilling"}
	for i := 0; i < n; i++ {
		switch rng.Intn(6) {
		case 0:
			c.Train(uint64(rng.Intn(30)))
		case 1:
			c.GainChakra(uint64(rng.Intn(20)))
		case 2:
			c.SpendChakra(uint64(rng.Intn(20)))
		case 3:
			c.LearnJutsu(jutsu[rng.Intn(len(jutsu))])
		case 4:
			c.PickUpScroll(scrolls[rng.Intn(len(scrolls))])
		case 5:
			c.DropScroll(scrolls[rng.Intn(len(scrolls))])
		}
		c.ReportStatus(status[rng.Intn(len(status))])
	}
	return c.Memory()
}

// TestMemoryIsAJoinSemilattice checks the three CvRDT laws on the *product*
// type, not just its five components in isolation. The product of
// join-semilattices, ordered and merged componentwise, is itself a
// join-semilattice -- this test is the empirical check of that algebraic
// fact for Memory specifically.
func TestMemoryIsAJoinSemilattice(t *testing.T) {
	rng := rand.New(rand.NewSource(99))
	for i := 0; i < 150; i++ {
		a := randomMemory(rng, fmt.Sprintf("a%d", i), 10)
		b := randomMemory(rng, fmt.Sprintf("b%d", i), 10)
		c := randomMemory(rng, fmt.Sprintf("c%d", i), 10)
		merge := func(x, y Memory) Memory { return x.Merge(y) }
		checkCommutative(t, "Memory", a, b, merge)
		checkAssociative(t, "Memory", a, b, c, merge)
		checkIdempotent(t, "Memory", a, merge)
	}
}

// TestMemoryMergeOrderIndependent is the direct simulation-level statement
// of "dispel order doesn't matter": build several independent clone
// memories, merge them into a base state in many random orders, and assert
// every order produces an identical result.
func TestMemoryMergeOrderIndependent(t *testing.T) {
	rng := rand.New(rand.NewSource(123))
	base := NewMemory()

	const numClones = 7
	results := make([]Memory, numClones)
	for i := range results {
		results[i] = randomMemory(rng, fmt.Sprintf("clone-%d", i), 15)
	}

	first := DispelInto(base, results...)

	for trial := 0; trial < 50; trial++ {
		shuffled := make([]Memory, numClones)
		copy(shuffled, results)
		rng.Shuffle(numClones, func(i, j int) { shuffled[i], shuffled[j] = shuffled[j], shuffled[i] })

		got := DispelInto(base, shuffled...)
		if !reflect.DeepEqual(first, got) {
			t.Fatalf("trial %d: merge order changed the result\n order=%v", trial, shuffled)
		}
	}
}

// TestMemoryDoubleDispelIsNoOp directly checks idempotency at the scenario
// level: merging the same clone's final memory into the original twice must
// be identical to merging it once.
func TestMemoryDoubleDispelIsNoOp(t *testing.T) {
	rng := rand.New(rand.NewSource(321))
	base := NewMemory()
	clone := randomMemory(rng, "clone-dup", 20)

	once := DispelInto(base, clone)
	twice := DispelInto(base, clone, clone)
	thrice := DispelInto(base, clone, clone, clone)

	if !reflect.DeepEqual(once, twice) {
		t.Fatalf("dispelling the same clone twice changed the result")
	}
	if !reflect.DeepEqual(once, thrice) {
		t.Fatalf("dispelling the same clone three times changed the result")
	}
}
