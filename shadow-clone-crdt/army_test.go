package main

import (
	"math/rand"
	"reflect"
	"strings"
	"sync"
	"testing"
)

// countingWork is deterministic clone work (no randomness) so tests can
// assert exact numeric outcomes: it trains a fixed number of reps and learns
// one jutsu named after its own clone ID, so every clone's contribution is
// distinguishable in the merged result.
func countingWork(reps uint64) func(c *CloneCtx, rng *rand.Rand) {
	return func(c *CloneCtx, rng *rand.Rand) {
		c.Train(reps)
		c.LearnJutsu("jutsu-of-" + c.ID)
		c.GainChakra(reps)
	}
}

func TestSpawnRunsNRealGoroutinesConcurrently(t *testing.T) {
	army := NewArmy(1000)
	const n = 16

	var concurrent int32
	var maxConcurrent int32
	var mu sync.Mutex
	// Instrumented work: record how many clones are running at once, purely
	// for the test's own observation -- this does NOT touch army or any
	// other clone's state, only test-local counters guarded by mu.
	wave, err := army.Spawn(n, 10, nil, func(c *CloneCtx, rng *rand.Rand) {
		mu.Lock()
		concurrent++
		if concurrent > maxConcurrent {
			maxConcurrent = concurrent
		}
		mu.Unlock()

		c.Train(1)

		mu.Lock()
		concurrent--
		mu.Unlock()
	})
	if err != nil {
		t.Fatalf("Spawn: %v", err)
	}
	if len(wave.CloneIDs) != n || len(wave.Results) != n {
		t.Fatalf("got %d ids / %d results, want %d", len(wave.CloneIDs), len(wave.Results), n)
	}
	// This is a liveness/sanity signal, not the correctness guarantee (the
	// scheduler is free to run goroutines near-sequentially); the real
	// concurrency-safety claim is checked by `go test -race`, which inspects
	// every memory access, not just this counter.
	t.Logf("max observed concurrent clones: %d (of %d spawned)", maxConcurrent, n)
}

func TestSpawnEachCloneWritesOnlyItsOwnSlot(t *testing.T) {
	army := NewArmy(1000)
	wave, err := army.Spawn(5, 10, nil, countingWork(7))
	if err != nil {
		t.Fatalf("Spawn: %v", err)
	}
	for i, id := range wave.CloneIDs {
		m := wave.Results[i]
		if !strings.HasPrefix(id, "clone-w1-") {
			t.Fatalf("unexpected clone id format: %q", id)
		}
		if got := m.Reps.Value(); got != 7 {
			t.Fatalf("clone %s: reps = %d, want 7", id, got)
		}
		if !m.Jutsu.Contains("jutsu-of-" + id) {
			t.Fatalf("clone %s: expected to have learned jutsu-of-%s", id, id)
		}
		// Must NOT have learned any other clone's jutsu -- proof that
		// clones never see each other's writes before Dispel.
		for j, otherID := range wave.CloneIDs {
			if j == i {
				continue
			}
			if m.Jutsu.Contains("jutsu-of-" + otherID) {
				t.Fatalf("clone %s unexpectedly contains jutsu-of-%s before any dispel", id, otherID)
			}
		}
	}
}

func TestChakraBudgetEnforced(t *testing.T) {
	army := NewArmy(100)

	// Affordable: exactly the whole budget.
	wave, err := army.Spawn(5, 20, nil, countingWork(1))
	if err != nil {
		t.Fatalf("Spawn(5, 20): unexpected error: %v", err)
	}
	if len(wave.Results) != 5 {
		t.Fatalf("expected 5 results, got %d", len(wave.Results))
	}
	if got := army.ChakraLeft(); got != 0 {
		t.Fatalf("chakra left = %d, want 0", got)
	}

	// Now broke: even a single clone must fail.
	_, err = army.Spawn(1, 1, nil, countingWork(1))
	if err == nil {
		t.Fatalf("expected an error spawning with zero chakra left, got nil")
	}
	if got := army.ChakraLeft(); got != 0 {
		t.Fatalf("a failed Spawn must not change the chakra budget; got %d, want 0", got)
	}
}

func TestChakraNotDeductedOnFailedSpawn(t *testing.T) {
	army := NewArmy(50)
	before := army.ChakraLeft()

	_, err := army.Spawn(10, 10, nil, countingWork(1)) // needs 100, have 50
	if err == nil {
		t.Fatalf("expected an error for an unaffordable spawn")
	}
	if got := army.ChakraLeft(); got != before {
		t.Fatalf("chakra left changed after a failed spawn: %d -> %d", before, got)
	}
}

func TestSpawnRejectsNonPositiveN(t *testing.T) {
	army := NewArmy(100)
	if _, err := army.Spawn(0, 10, nil, countingWork(1)); err == nil {
		t.Fatalf("expected an error for n=0")
	}
	if _, err := army.Spawn(-1, 10, nil, countingWork(1)); err == nil {
		t.Fatalf("expected an error for n=-1")
	}
}

func TestSpawnRejectsMismatchedSeeds(t *testing.T) {
	army := NewArmy(100)
	_, err := army.Spawn(3, 10, []int64{1, 2}, countingWork(1))
	if err == nil {
		t.Fatalf("expected an error when len(seeds) != n")
	}
}

// TestDispelOrderIndependentAcrossRealWaves is the end-to-end version of the
// algebraic laws: spawn real concurrent clones against a live Army, merge
// their results into fresh copies of the army's snapshot in many random
// orders, and assert every order converges to the same Memory.
func TestDispelOrderIndependentAcrossRealWaves(t *testing.T) {
	army := NewArmy(2000)
	wave, err := army.Spawn(10, 50, nil, func(c *CloneCtx, rng *rand.Rand) {
		c.Train(uint64(1 + rng.Intn(20)))
		c.GainChakra(uint64(rng.Intn(10)))
		c.SpendChakra(uint64(rng.Intn(10)))
		c.LearnJutsu([]string{"a", "b", "c"}[rng.Intn(3)])
		c.PickUpScroll("fire-scroll")
		c.ReportStatus("training")
	})
	if err != nil {
		t.Fatalf("Spawn: %v", err)
	}

	base := army.Snapshot()
	first := DispelInto(base, wave.Results...)

	rng := rand.New(rand.NewSource(555))
	for trial := 0; trial < 100; trial++ {
		shuffled := make([]Memory, len(wave.Results))
		copy(shuffled, wave.Results)
		rng.Shuffle(len(shuffled), func(i, j int) { shuffled[i], shuffled[j] = shuffled[j], shuffled[i] })

		got := DispelInto(base, shuffled...)
		if !reflect.DeepEqual(first, got) {
			t.Fatalf("trial %d: dispel order changed the final state", trial)
		}
	}
}

func TestDispelMutatesArmyOriginal(t *testing.T) {
	army := NewArmy(500)
	wave, err := army.Spawn(3, 50, nil, countingWork(5))
	if err != nil {
		t.Fatalf("Spawn: %v", err)
	}
	before := army.Snapshot()
	army.Dispel(wave.Results...)
	after := army.Snapshot()

	if reflect.DeepEqual(before, after) {
		t.Fatalf("Dispel did not change the army's original memory")
	}
	if got, want := after.Reps.Value(), uint64(15); got != want { // 3 clones * 5 reps
		t.Fatalf("after dispel reps = %d, want %d", got, want)
	}
}

func TestDoubleDispelOnRealArmyIsNoOp(t *testing.T) {
	army := NewArmy(500)
	wave, err := army.Spawn(4, 50, nil, countingWork(3))
	if err != nil {
		t.Fatalf("Spawn: %v", err)
	}
	army.Dispel(wave.Results...)
	before := army.Snapshot()
	army.Dispel(wave.Results...) // accidental re-dispel of the same wave
	after := army.Snapshot()

	if !reflect.DeepEqual(before, after) {
		t.Fatalf("re-dispelling an already-dispelled wave changed the army's state")
	}
}
