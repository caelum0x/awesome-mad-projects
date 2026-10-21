package main

import (
	"fmt"
	"math/rand"
	"sync"
)

// Army is "the original": the single ninja who owns the canonical Memory and
// a finite chakra budget. Only the goroutine that calls Army's own methods
// ever touches original/chakraLeft -- clones never read or write them
// directly, they only receive an immutable snapshot at spawn time and hand
// back a finished Memory value at dispel time. That ownership discipline
// (actor-style message passing, not shared mutable memory) is what makes the
// concurrency in this project real without needing a mutex around original
// itself: there is nothing two goroutines ever write to at once.
type Army struct {
	original     Memory
	chakraBudget uint64
	chakraLeft   uint64
	waveSeq      uint64
}

// NewArmy starts a fresh original with an empty Memory and a finite chakra
// budget. Chakra is not decorative: it is the one real resource constraint
// that keeps "shadow clones" from being an unbounded goroutine fork-bomb --
// you can only ever spawn as many clones as the budget allows, which mirrors
// the manga's own rule that overusing the jutsu exhausts the caster.
func NewArmy(chakraBudget uint64) *Army {
	return &Army{original: NewMemory(), chakraBudget: chakraBudget, chakraLeft: chakraBudget}
}

// Snapshot returns the original's current memory, deep-copied.
func (a *Army) Snapshot() Memory { return a.original.Clone() }

// ChakraBudget reports the starting chakra budget.
func (a *Army) ChakraBudget() uint64 { return a.chakraBudget }

// ChakraLeft reports the remaining chakra budget.
func (a *Army) ChakraLeft() uint64 { return a.chakraLeft }

// Wave is the result of one Spawn call: the clone IDs that ran and the
// Memory value each one finished with, ready to be fed to Dispel in any
// order, any number of times.
type Wave struct {
	CloneIDs []string
	Results  []Memory
}

// Spawn creates n shadow clones as n real goroutines. Each clone starts from
// an independent deep copy of the original's memory at the moment of the
// call (a.original.Clone()), runs work against its own private CloneCtx and
// its own private *rand.Rand, and nothing it does is visible to any other
// clone or to the original until its result is handed to Dispel. Spawn
// blocks until every clone finishes.
//
// seeds, if non-nil, must have length n: seeds[i] seeds clone i's *rand.Rand.
// If seeds is nil, deterministic seeds are derived from the wave number and
// clone index, so a given sequence of Spawn calls on a fresh Army is
// reproducible from run to run without the caller having to manage seeds
// itself. Every clone gets its own *rand.Rand instance -- never a shared one
// -- because a shared *rand.Rand mutated from multiple goroutines is a real
// Go data race, not a hypothetical one, and this project avoids it by
// construction rather than by luck.
//
// Returns an error without spawning anything, and without touching the
// chakra budget, if n*chakraPerClone exceeds what remains -- a wave either
// happens in full or not at all.
func (a *Army) Spawn(n int, chakraPerClone uint64, seeds []int64, work func(c *CloneCtx, rng *rand.Rand)) (Wave, error) {
	if n <= 0 {
		return Wave{}, fmt.Errorf("spawn: n must be positive, got %d", n)
	}
	if seeds != nil && len(seeds) != n {
		return Wave{}, fmt.Errorf("spawn: seeds has length %d, want %d", len(seeds), n)
	}
	cost := uint64(n) * chakraPerClone
	if cost > a.chakraLeft {
		return Wave{}, fmt.Errorf("spawn: not enough chakra for %d clones at %d each: need %d, have %d",
			n, chakraPerClone, cost, a.chakraLeft)
	}
	a.chakraLeft -= cost
	a.waveSeq++
	wave := a.waveSeq

	snapshot := a.original.Clone()
	ids := make([]string, n)
	results := make([]Memory, n)
	var wg sync.WaitGroup
	for i := 0; i < n; i++ {
		id := fmt.Sprintf("clone-w%d-%d", wave, i)
		ids[i] = id
		seed := int64(wave)*1_000_003 + int64(i) // deterministic fallback
		if seeds != nil {
			seed = seeds[i]
		}
		wg.Add(1)
		go func(i int, id string, seed int64) {
			defer wg.Done()
			ctx := newCloneCtx(id, snapshot)
			rng := rand.New(rand.NewSource(seed)) // one private RNG per goroutine
			work(ctx, rng)
			results[i] = ctx.Memory() // each goroutine writes only its own slot
		}(i, id, seed)
	}
	wg.Wait()

	return Wave{CloneIDs: ids, Results: results}, nil
}

// Dispel merges each given Memory into the original, one at a time, in
// whatever order they are given. Because Memory.Merge is commutative,
// associative and idempotent (proven in crdt_test.go and memory_test.go),
// the final original is the same value regardless of:
//   - what order the results are passed in (clones can "pop" in any order),
//   - whether a result is passed more than once (an accidental double
//     dispel, or a duplicate delivery, changes nothing once it has already
//     been applied).
func (a *Army) Dispel(results ...Memory) {
	for _, r := range results {
		a.original = a.original.Merge(r)
	}
}

// DispelInto is Dispel's pure counterpart: it returns start.Merge'd with
// every result, in order, without mutating any Army. It exists so tests
// (and the demo) can merge the same Wave into independent starting states,
// in independently shuffled orders, and compare the results -- without the
// comparisons interfering with each other via a shared *Army.
func DispelInto(start Memory, results ...Memory) Memory {
	out := start
	for _, r := range results {
		out = out.Merge(r)
	}
	return out
}
