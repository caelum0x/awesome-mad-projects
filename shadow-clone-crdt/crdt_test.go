package main

import (
	"fmt"
	"math/rand"
	"reflect"
	"testing"
)

// randomGCounter builds a GCounter by applying n random increments across a
// small pool of replica names.
func randomGCounter(rng *rand.Rand, n int) GCounter {
	g := NewGCounter()
	replicas := []string{"r0", "r1", "r2", "r3"}
	for i := 0; i < n; i++ {
		g = g.Increment(replicas[rng.Intn(len(replicas))], uint64(rng.Intn(50)))
	}
	return g
}

func randomPNCounter(rng *rand.Rand, n int) PNCounter {
	c := NewPNCounter()
	replicas := []string{"r0", "r1", "r2", "r3"}
	for i := 0; i < n; i++ {
		rep := replicas[rng.Intn(len(replicas))]
		if rng.Intn(2) == 0 {
			c = c.Gain(rep, uint64(rng.Intn(50)))
		} else {
			c = c.Spend(rep, uint64(rng.Intn(50)))
		}
	}
	return c
}

func randomGSet(rng *rand.Rand, n int) GSet {
	s := NewGSet()
	pool := []string{"a", "b", "c", "d", "e"}
	for i := 0; i < n; i++ {
		s = s.Add(pool[rng.Intn(len(pool))])
	}
	return s
}

func randomORSet(rng *rand.Rand, n int) ORSet {
	s := NewORSet()
	pool := []string{"scroll-a", "scroll-b", "scroll-c"}
	tagSeq := 0
	for i := 0; i < n; i++ {
		elem := pool[rng.Intn(len(pool))]
		if rng.Intn(2) == 0 {
			tagSeq++
			s = s.Add(elem, fmt.Sprintf("t%d", tagSeq))
		} else {
			s = s.Remove(elem)
		}
	}
	return s
}

// randomLWW builds a register by replaying n random Set calls. The value is
// derived deterministically from (counter, replica) rather than drawn
// independently at random: an LWWRegister's merge correctness assumes a
// (Counter, ReplicaID) pair identifies exactly one write (that is the whole
// point of ReplicaID being unique per writer -- see lwwregister.go). Two
// independently-random values sharing a (counter, replica) stamp by chance
// would violate that precondition and make Merge's tie-break genuinely
// ambiguous, which is a test-generator bug, not a Merge bug: it would be
// asking "which of two different facts about the same write is true" of an
// object that only ever stores one fact per write.
func randomLWW(rng *rand.Rand, n int) LWWRegister {
	r := NewLWWRegister()
	replicas := []string{"r0", "r1", "r2"}
	for i := 0; i < n; i++ {
		counter := uint64(rng.Intn(20))
		replica := replicas[rng.Intn(len(replicas))]
		value := fmt.Sprintf("v-%s-%d", replica, counter)
		r = r.Set(value, counter, replica)
	}
	return r
}

// The three join-semilattice laws, checked generically over any CRDT[T].
func checkCommutative[T any](t *testing.T, name string, a, b T, merge func(x, y T) T) {
	t.Helper()
	ab := merge(a, b)
	ba := merge(b, a)
	if !reflect.DeepEqual(ab, ba) {
		t.Errorf("%s: Merge not commutative\n a.Merge(b) = %#v\n b.Merge(a) = %#v", name, ab, ba)
	}
}

func checkAssociative[T any](t *testing.T, name string, a, b, c T, merge func(x, y T) T) {
	t.Helper()
	left := merge(merge(a, b), c)
	right := merge(a, merge(b, c))
	if !reflect.DeepEqual(left, right) {
		t.Errorf("%s: Merge not associative\n (a.Merge(b)).Merge(c) = %#v\n a.Merge(b.Merge(c)) = %#v", name, left, right)
	}
}

func checkIdempotent[T any](t *testing.T, name string, a T, merge func(x, y T) T) {
	t.Helper()
	aa := merge(a, a)
	if !reflect.DeepEqual(a, aa) {
		t.Errorf("%s: Merge not idempotent\n a          = %#v\n a.Merge(a) = %#v", name, a, aa)
	}
}

// TestJoinSemilatticeLaws is a table-driven, randomized property test: for
// every CRDT type in this project, over many random triples of states, Merge
// must be commutative, associative, and idempotent. These three laws are
// exactly what the Shapiro et al. (2011) CvRDT definition requires, and
// exactly what guarantees a Shadow Clone's memory converges no matter what
// order (or how many times) it is dispelled.
func TestJoinSemilatticeLaws(t *testing.T) {
	const trials = 200
	const opsPerState = 12

	t.Run("GCounter", func(t *testing.T) {
		rng := rand.New(rand.NewSource(1))
		for i := 0; i < trials; i++ {
			a := randomGCounter(rng, opsPerState)
			b := randomGCounter(rng, opsPerState)
			c := randomGCounter(rng, opsPerState)
			merge := func(x, y GCounter) GCounter { return x.Merge(y) }
			checkCommutative(t, "GCounter", a, b, merge)
			checkAssociative(t, "GCounter", a, b, c, merge)
			checkIdempotent(t, "GCounter", a, merge)
		}
	})

	t.Run("PNCounter", func(t *testing.T) {
		rng := rand.New(rand.NewSource(2))
		for i := 0; i < trials; i++ {
			a := randomPNCounter(rng, opsPerState)
			b := randomPNCounter(rng, opsPerState)
			c := randomPNCounter(rng, opsPerState)
			merge := func(x, y PNCounter) PNCounter { return x.Merge(y) }
			checkCommutative(t, "PNCounter", a, b, merge)
			checkAssociative(t, "PNCounter", a, b, c, merge)
			checkIdempotent(t, "PNCounter", a, merge)
		}
	})

	t.Run("GSet", func(t *testing.T) {
		rng := rand.New(rand.NewSource(3))
		for i := 0; i < trials; i++ {
			a := randomGSet(rng, opsPerState)
			b := randomGSet(rng, opsPerState)
			c := randomGSet(rng, opsPerState)
			merge := func(x, y GSet) GSet { return x.Merge(y) }
			checkCommutative(t, "GSet", a, b, merge)
			checkAssociative(t, "GSet", a, b, c, merge)
			checkIdempotent(t, "GSet", a, merge)
		}
	})

	t.Run("ORSet", func(t *testing.T) {
		rng := rand.New(rand.NewSource(4))
		for i := 0; i < trials; i++ {
			a := randomORSet(rng, opsPerState)
			b := randomORSet(rng, opsPerState)
			c := randomORSet(rng, opsPerState)
			merge := func(x, y ORSet) ORSet { return x.Merge(y) }
			checkCommutative(t, "ORSet", a, b, merge)
			checkAssociative(t, "ORSet", a, b, c, merge)
			checkIdempotent(t, "ORSet", a, merge)
		}
	})

	t.Run("LWWRegister", func(t *testing.T) {
		rng := rand.New(rand.NewSource(5))
		for i := 0; i < trials; i++ {
			a := randomLWW(rng, opsPerState)
			b := randomLWW(rng, opsPerState)
			c := randomLWW(rng, opsPerState)
			merge := func(x, y LWWRegister) LWWRegister { return x.Merge(y) }
			checkCommutative(t, "LWWRegister", a, b, merge)
			checkAssociative(t, "LWWRegister", a, b, c, merge)
			checkIdempotent(t, "LWWRegister", a, merge)
		}
	})
}

func TestGCounterValueIsSumOfReplicaMaxes(t *testing.T) {
	a := NewGCounter().Increment("clone-a", 10).Increment("clone-b", 5)
	b := NewGCounter().Increment("clone-a", 7).Increment("clone-b", 20).Increment("clone-c", 3)
	merged := a.Merge(b)
	// Pointwise max: clone-a -> 10, clone-b -> 20, clone-c -> 3.
	if got, want := merged.Value(), uint64(33); got != want {
		t.Fatalf("merged value = %d, want %d", got, want)
	}
	if got := merged.Replicas()["clone-a"]; got != 10 {
		t.Fatalf("clone-a slot = %d, want 10 (max(10,7))", got)
	}
}

func TestPNCounterCanGoNegative(t *testing.T) {
	c := NewPNCounter().Gain("clone-a", 5).Spend("clone-a", 12)
	if got, want := c.Value(), int64(-7); got != want {
		t.Fatalf("value = %d, want %d", got, want)
	}
}

func TestGSetElementsIsSortedAndDeduplicated(t *testing.T) {
	s := NewGSet().Add("tree-walking").Add("kawarimi").Add("tree-walking")
	got := s.Elements()
	want := []string{"kawarimi", "tree-walking"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("Elements() = %v, want %v", got, want)
	}
}

func TestORSetElementsIsSortedAndDeduplicated(t *testing.T) {
	s := NewORSet().Add("wind-scroll", "t1").Add("fire-scroll", "t2").Add("wind-scroll", "t3")
	got := s.Elements()
	want := []string{"fire-scroll", "wind-scroll"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("Elements() = %v, want %v", got, want)
	}
	s = s.Remove("fire-scroll")
	got = s.Elements()
	want = []string{"wind-scroll"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("after Remove: Elements() = %v, want %v", got, want)
	}
	if s.Contains("fire-scroll") {
		t.Fatalf("Contains(fire-scroll) should be false after Remove")
	}
}

func TestGSetAddIsIdempotentOnValue(t *testing.T) {
	s := NewGSet().Add("rasengan-form")
	s2 := s.Add("rasengan-form")
	if !reflect.DeepEqual(s, s2) {
		t.Fatalf("adding an already-present element changed the set")
	}
	if s.Len() != 1 {
		t.Fatalf("Len() = %d, want 1", s.Len())
	}
}

// TestORSetAddWinsConcurrentRemove is the specific scenario add-wins OR-Sets
// exist to solve: clone A drops a scroll it has observed; concurrently,
// clone B (who has NOT observed A's drop) picks up a fresh copy of the same
// scroll. After merging both replicas, the scroll must still be present --
// B's add was concurrent with, and not observed by, A's remove, so it wins.
func TestORSetAddWinsConcurrentRemove(t *testing.T) {
	shared := NewORSet().Add("fire-scroll", "origin#1")

	// Clone A observes the shared state and drops the scroll it sees.
	a := shared.Remove("fire-scroll")
	if a.Contains("fire-scroll") {
		t.Fatalf("clone A should no longer see fire-scroll after dropping it")
	}

	// Clone B, concurrently, independently picks up its OWN fresh copy,
	// without having observed A's remove.
	b := shared.Add("fire-scroll", "cloneB#1")

	merged := a.Merge(b)
	if !merged.Contains("fire-scroll") {
		t.Fatalf("add-wins OR-Set should keep the concurrently-added scroll, but it was lost")
	}

	// But a sequential remove of a tag that HAS been observed must stick:
	// clone A removes clone B's pickup once it has actually been merged in.
	aSeesB := a.Merge(b)
	afterSequentialRemove := aSeesB.Remove("fire-scroll")
	if afterSequentialRemove.Contains("fire-scroll") {
		t.Fatalf("removing an observed tag should remove it")
	}
}

func TestLWWRegisterHigherCounterWins(t *testing.T) {
	r1 := NewLWWRegister().Set("sparring", 3, "clone-a")
	r2 := NewLWWRegister().Set("resting", 5, "clone-b")
	merged := r1.Merge(r2)
	if merged.Value != "resting" {
		t.Fatalf("merged.Value = %q, want %q (higher counter)", merged.Value, "resting")
	}
}

func TestLWWRegisterTiesBreakOnReplicaID(t *testing.T) {
	r1 := NewLWWRegister().Set("from-a", 9, "clone-a")
	r2 := NewLWWRegister().Set("from-z", 9, "clone-z")
	merged := r1.Merge(r2)
	if merged.Value != "from-z" {
		t.Fatalf("tie-break: merged.Value = %q, want %q (higher ReplicaID)", merged.Value, "from-z")
	}
	// Merging the other direction must agree -- commutativity, concretely.
	merged2 := r2.Merge(r1)
	if !reflect.DeepEqual(merged, merged2) {
		t.Fatalf("tie-break result depends on merge order: %#v vs %#v", merged, merged2)
	}
}
