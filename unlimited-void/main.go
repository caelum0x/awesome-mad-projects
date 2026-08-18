package main

import "fmt"

// Unlimited Void as a Container Runtime (simulation).
//
// A privileged "caster" process opens a Domain Expansion over a set of victim
// processes. Inside the domain, each victim is flooded with an overwhelming but
// entirely VIRTUAL stream of information (counters, not real memory). Because
// the flood dwarfs each victim's finite per-tick attention budget, useful-work
// throughput collapses to ~0 while the domain is open. The caster is immune and
// keeps working. On close, victims recover.
//
// SAFETY: This is a bounded simulation. No real memory is exhausted, no real
// CPU is flooded, no fork bombs. "Infinity" is represented as growing integer
// counters (VirtualQueue capped at QueueCap, with the remainder counted as
// Overflow). It is NOT a real denial-of-service tool.

const (
	warmupTicks   = 5
	domainTicks   = 8
	recoveryTicks = 6
)

func main() {
	fmt.Println("Unlimited Void :: Container Runtime Simulation")
	fmt.Println("(bounded, virtual attention model — NOT a real DoS)")

	sim := NewSimulation()

	// Phase 1: normal operation. Everyone does useful work.
	fmt.Println("\n--- Phase 1: normal operation ---")
	before1 := sim.snapshot()
	sim.Run(warmupTicks, "normal")
	phase1 := sim.measurePhase(before1, warmupTicks)

	// Phase 2: Domain Expansion. Victims are shown infinity.
	fmt.Println("--- Phase 2: Unlimited Void open ---")
	sim.Domain.Expand()
	before2 := sim.snapshot()
	sim.Run(domainTicks, "VOID")
	phase2 := sim.measurePhase(before2, domainTicks)
	sim.Domain.Close()

	// Phase 3: recovery after the domain closes.
	fmt.Println("--- Phase 3: recovery ---")
	before3 := sim.snapshot()
	sim.Run(recoveryTicks, "recover")
	phase3 := sim.measurePhase(before3, recoveryTicks)

	// Throughput tables: the collapse and recovery are visible per phase.
	printPhaseTable("Phase 1 (normal)", phase1)
	printPhaseTable("Phase 2 (Unlimited Void open)", phase2)
	printPhaseTable("Phase 3 (recovery)", phase3)

	printSummary(sim)
}

// printSummary reports lifetime virtual-flood accounting to underline that the
// "infinity" was tracked as bounded counters, never allocated.
func printSummary(sim *Simulation) {
	fmt.Println("\n=== Virtual flood accounting (nothing was actually allocated) ===")
	fmt.Printf("%-15s %-16s %-14s %-12s\n",
		"process", "virt-injected", "queue-capped", "overflow")
	fmt.Println("-------------------------------------------------------------------")
	for _, p := range sim.Processes {
		fmt.Printf("%-15s %-16d %-14d %-12d\n",
			p.Name, p.VirtualQueued, p.VirtualQueue, p.Overflow)
	}
	fmt.Printf("\nQueue cap per process: %d units. Everything above the cap is counted\n", QueueCap)
	fmt.Println("as overflow (a number), so the model never holds 'infinity' in memory.")
}
