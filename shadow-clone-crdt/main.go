package main

import (
	"fmt"
	"math/rand"
	"reflect"
	"strings"
)

var jutsuPool = []string{"kawarimi", "rasengan-form", "leaf-whirlwind", "shuriken-combo", "tree-walking"}
var scrollPool = []string{"fire-scroll", "summoning-scroll", "wind-scroll"}
var statusPool = []string{"drilling basics", "sparring", "refining form", "exhausted, resting"}

// train is one clone's independent training session: it only touches its
// own CloneCtx and its own *rand.Rand (a fresh instance per goroutine,
// provided by Army.Spawn -- never a *rand.Rand shared across goroutines,
// which would be a real data race).
func train(c *CloneCtx, rng *rand.Rand) {
	c.Train(uint64(20 + rng.Intn(60)))
	c.GainChakra(uint64(10 + rng.Intn(40)))
	c.SpendChakra(uint64(5 + rng.Intn(25)))
	c.LearnJutsu(jutsuPool[rng.Intn(len(jutsuPool))])

	if rng.Intn(2) == 0 {
		c.PickUpScroll(scrollPool[rng.Intn(len(scrollPool))])
	}
	if rng.Intn(3) == 0 {
		c.DropScroll(scrollPool[rng.Intn(len(scrollPool))])
	}
	c.ReportStatus(statusPool[rng.Intn(len(statusPool))])
}

func printMemory(label string, m Memory) {
	fmt.Printf("%s\n", label)
	fmt.Printf("  reps total:     %d\n", m.Reps.Value())
	fmt.Printf("  net chakra:     %d\n", m.Chakra.Value())
	fmt.Printf("  jutsu learned:  %s\n", strings.Join(withFallback(m.Jutsu.Elements()), ", "))
	fmt.Printf("  scrolls held:   %s\n", strings.Join(withFallback(m.Scrolls.Elements()), ", "))
	fmt.Printf("  status:         %q (clock %d, set by %s)\n", m.Status.Value, m.Status.Counter, m.Status.ReplicaID)
}

func withFallback(ss []string) []string {
	if len(ss) == 0 {
		return []string{"(none)"}
	}
	return ss
}

func shuffledCopy(rng *rand.Rand, in []Memory) []Memory {
	out := make([]Memory, len(in))
	copy(out, in)
	rng.Shuffle(len(out), func(i, j int) { out[i], out[j] = out[j], out[i] })
	return out
}

func main() {
	fmt.Println("Shadow Clone CRDT -- Kage Bunshin no Jutsu as a state-based CRDT")
	fmt.Println("Every clone trains independently. Dispel order never matters.")
	fmt.Println(strings.Repeat("=", 68))

	const startingChakra = 600
	army := NewArmy(startingChakra)
	fmt.Printf("\nOriginal spawned with %d chakra.\n", army.ChakraBudget())

	// ------------------------------------------------------------------
	// Wave 1: five clones train concurrently, in real goroutines, each on
	// its own private Memory snapshot and its own private RNG.
	// ------------------------------------------------------------------
	fmt.Println(strings.Repeat("-", 68))
	fmt.Println("1) Spawn 5 clones (100 chakra each = 500) -- concurrent training")
	fmt.Println(strings.Repeat("-", 68))

	const n1, cost1 = 5, 100
	seedRNG := rand.New(rand.NewSource(42))
	seeds1 := make([]int64, n1)
	for i := range seeds1 {
		seeds1[i] = seedRNG.Int63()
	}
	wave1, err := army.Spawn(n1, cost1, seeds1, train)
	if err != nil {
		fmt.Println("  spawn failed:", err)
		return
	}
	fmt.Printf("  chakra left after wave 1: %d\n", army.ChakraLeft())
	for i, id := range wave1.CloneIDs {
		m := wave1.Results[i]
		fmt.Printf("  %-14s reps=%-4d chakra=%-4d jutsu=%-16s scrolls=%-24s status=%q\n",
			id, m.Reps.Value(), m.Chakra.Value(),
			strings.Join(m.Jutsu.Elements(), "+"),
			strings.Join(withFallback(m.Scrolls.Elements()), "+"),
			m.Status.Value)
	}

	// ------------------------------------------------------------------
	// Prove dispel order doesn't matter: merge the same wave's results into
	// fresh snapshots in three independently shuffled orders and compare.
	// ------------------------------------------------------------------
	fmt.Println(strings.Repeat("-", 68))
	fmt.Println("2) Dispel the wave in three different random orders")
	fmt.Println(strings.Repeat("-", 68))

	base := army.Snapshot()
	orderRNG := rand.New(rand.NewSource(7))
	var merged []Memory
	for trial := 1; trial <= 3; trial++ {
		order := shuffledCopy(orderRNG, wave1.Results)
		result := DispelInto(base, order...)
		merged = append(merged, result)
		fmt.Printf("  trial %d: shuffled dispel order -> reps total %d, jutsu learned %d\n",
			trial, result.Reps.Value(), result.Jutsu.Len())
	}
	allEqual := true
	for i := 1; i < len(merged); i++ {
		if !reflect.DeepEqual(merged[0], merged[i]) {
			allEqual = false
		}
	}
	fmt.Printf("  all 3 shuffled-order merges produced an identical Memory value: %v\n", allEqual)

	// Actually dispel into the real army, in spawn order.
	army.Dispel(wave1.Results...)
	fmt.Println("  dispelled wave 1 into the original (in spawn order).")

	// ------------------------------------------------------------------
	// Prove double-dispel is a no-op: dispel the exact same wave again.
	// ------------------------------------------------------------------
	fmt.Println(strings.Repeat("-", 68))
	fmt.Println("3) Accidentally dispel the same wave a second time")
	fmt.Println(strings.Repeat("-", 68))

	before := army.Snapshot()
	army.Dispel(wave1.Results...)
	after := army.Snapshot()
	fmt.Printf("  state unchanged by the duplicate dispel: %v\n", reflect.DeepEqual(before, after))

	// ------------------------------------------------------------------
	// Chakra is a real, finite budget: try to over-spend it.
	// ------------------------------------------------------------------
	fmt.Println(strings.Repeat("-", 68))
	fmt.Println("4) Try to spawn more clones than remaining chakra allows")
	fmt.Println(strings.Repeat("-", 68))

	fmt.Printf("  chakra left: %d\n", army.ChakraLeft())
	tooMany := int(army.ChakraLeft()/cost1) + 3
	_, err = army.Spawn(tooMany, cost1, nil, train)
	fmt.Printf("  Spawn(%d, %d, ...): %v\n", tooMany, cost1, err)

	if affordable := int(army.ChakraLeft() / cost1); affordable > 0 {
		wave2, err := army.Spawn(affordable, cost1, nil, train)
		if err == nil {
			army.Dispel(wave2.Results...)
			fmt.Printf("  spawned+dispelled %d more clones with the remaining chakra; chakra left: %d\n",
				affordable, army.ChakraLeft())
		}
	}

	// ------------------------------------------------------------------
	// Final state of the original.
	// ------------------------------------------------------------------
	fmt.Println(strings.Repeat("-", 68))
	fmt.Println("Final memory of the original, after every clone dispelled")
	fmt.Println(strings.Repeat("-", 68))
	printMemory("original", army.Snapshot())

	fmt.Println()
	fmt.Println("No clone ever wrote to another clone's memory, and the original")
	fmt.Println("never had to merge results in spawn order on purpose -- yet the")
	fmt.Println("final state is the same regardless of merge order, because")
	fmt.Println("Memory.Merge is commutative, associative, and idempotent. That")
	fmt.Println("is the whole trick, and it is real math, not a narrative device.")
}
