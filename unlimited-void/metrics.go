package main

import "fmt"

// metrics.go builds the per-phase throughput table that makes the effect
// obvious: victims flatline while the domain is open; the caster is unaffected.

// phaseSnapshot captures useful-work counters at a phase boundary so we can
// measure work done *within* a phase.
type phaseSnapshot map[int]int // processID -> UsefulWork

// snapshot records current useful work for every process.
func (s *Simulation) snapshot() phaseSnapshot {
	snap := make(phaseSnapshot, len(s.Processes))
	for _, p := range s.Processes {
		snap[p.ID] = p.UsefulWork
	}
	return snap
}

// PhaseResult is the measured throughput of one process during one phase.
type PhaseResult struct {
	Name          string
	Role          string  // "caster" or "victim"
	WorkInPhase   int     // useful work completed during the phase
	Ticks         int     // ticks the phase ran
	WorkPerTick   float64 // WorkInPhase / Ticks
	BudgetPerTick int     // attention budget, for context
}

// measurePhase computes per-process throughput between two snapshots.
func (s *Simulation) measurePhase(before phaseSnapshot, ticks int) []PhaseResult {
	results := make([]PhaseResult, 0, len(s.Processes))
	for _, p := range s.Processes {
		work := p.UsefulWork - before[p.ID]
		role := "victim"
		if p.IsCaster {
			role = "caster"
		}
		perTick := 0.0
		if ticks > 0 {
			perTick = float64(work) / float64(ticks)
		}
		results = append(results, PhaseResult{
			Name:          p.Name,
			Role:          role,
			WorkInPhase:   work,
			Ticks:         ticks,
			WorkPerTick:   perTick,
			BudgetPerTick: p.AttentionBudget,
		})
	}
	return results
}

// printPhaseTable renders a throughput table for a single phase.
func printPhaseTable(title string, results []PhaseResult) {
	fmt.Printf("\n=== Throughput: %s ===\n", title)
	fmt.Printf("%-15s %-8s %-12s %-14s %-12s\n",
		"process", "role", "work/tick", "work(total)", "budget/tick")
	fmt.Println("-------------------------------------------------------------------")
	for _, r := range results {
		fmt.Printf("%-15s %-8s %-12.1f %-14d %-12d\n",
			r.Name, r.Role, r.WorkPerTick, r.WorkInPhase, r.BudgetPerTick)
	}
}
