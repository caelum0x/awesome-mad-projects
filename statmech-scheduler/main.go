// Command statmech-scheduler is a simulation-only demo of a
// statistical-mechanics CPU scheduler. Tasks are modelled as particles with
// an energy derived from priority; the system has a temperature derived from
// load; and the next task each tick is drawn from the Boltzmann distribution
//
//	p_i proportional to exp(-E_i / (k*T)).
//
// It runs three load regimes (low / medium / high temperature) and prints,
// for each, the empirical fraction of CPU each task received against the
// theoretical Boltzmann weight. As the number of ticks grows, the two agree.
//
// This program NEVER touches the real operating-system scheduler. It is a
// pure numerical simulation.
package main

import (
	"flag"
	"fmt"
	"os"

	"statmech-scheduler/scheduler"
)

func main() {
	seed := flag.Int64("seed", 42, "PRNG seed for reproducible runs")
	decisions := flag.Int("decisions", 200000, "number of scheduling decisions per regime")
	quantum := flag.Int("quantum", 1, "ticks accounted per selection (time-slice length)")
	minT := flag.Float64("minT", 0.25, "temperature at zero load (cold: strict priority)")
	maxT := flag.Float64("maxT", 4.0, "temperature at full load (hot: near-uniform)")
	flag.Parse()

	// A small mixed workload. Higher priority => lower energy => favoured.
	tasks := []scheduler.Task{
		{Name: "audio-daemon", Priority: 10},
		{Name: "ui-render", Priority: 7},
		{Name: "web-request", Priority: 5},
		{Name: "backup-job", Priority: 2},
		{Name: "log-rotate", Priority: 1},
	}

	regimes := []struct {
		label string
		load  float64
	}{
		{"LOW load  (cold)", 0.0},
		{"MED load  (warm)", 0.5},
		{"HIGH load (hot)", 1.0},
	}

	fmt.Println("Statistical-Mechanics Scheduler (simulation only)")
	fmt.Printf("seed=%d  decisions/regime=%d  quantum=%d ticks  minT=%.2f  maxT=%.2f\n",
		*seed, *decisions, *quantum, *minT, *maxT)
	fmt.Println("Higher priority => lower energy => selected more often when cold.")

	for _, r := range regimes {
		temp := scheduler.TemperatureFromLoad(r.load, *minT, *maxT)
		sched, err := scheduler.New(tasks, temp, *quantum, *seed)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error building scheduler: %v\n", err)
			os.Exit(1)
		}
		result, err := sched.Run(*decisions)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error running scheduler: %v\n", err)
			os.Exit(1)
		}
		printRegime(r.label, r.load, temp, result)
	}
}

// printRegime renders one regime's theory-vs-empirical comparison table.
func printRegime(label string, load, temp float64, r scheduler.Result) {
	fmt.Printf("\n=== %s | load=%.2f | T=%.3f | ticks=%d ===\n", label, load, temp, r.Ticks)
	fmt.Printf("%-14s %6s %8s %10s %10s %9s\n",
		"task", "prio", "energy", "theory", "empirical", "abs.err")
	fmt.Println("--------------------------------------------------------------")

	var maxErr float64
	for i, t := range r.Tasks {
		theory := r.Theoretical[i]
		emp := r.Empirical[i]
		err := abs(theory - emp)
		if err > maxErr {
			maxErr = err
		}
		fmt.Printf("%-14s %6d %8.1f %9.4f%% %9.4f%% %8.4f%%\n",
			t.Name, t.Priority, t.Energy(),
			theory*100, emp*100, err*100)
	}
	fmt.Printf("max abs error (theory vs empirical): %.4f%%\n", maxErr*100)
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
