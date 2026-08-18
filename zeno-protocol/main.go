// Command zeno-protocol demonstrates a toy "Zeno's paradox" transport.
//
// A message is delivered by moving it half of the remaining distance to the
// destination on every tick. Cumulative progress after k ticks is 1 - (1/2)^k,
// which converges to 1 but never reaches it in exact arithmetic. An epsilon
// "close enough" threshold lets real payloads actually complete.
package main

import (
	"fmt"
	"strings"

	"zeno-protocol/zeno"
)

func main() {
	const message = "Hello, Elea!" // Zeno of Elea, ~490 BC

	fmt.Println("=== Zeno's Paradox Transport Protocol ===")
	fmt.Printf("Each tick moves the message HALF of the remaining distance.\n")
	fmt.Printf("Cumulative progress after k ticks = 1 - (1/2)^k.\n\n")

	demoConvergence(message)
	fmt.Println()
	demoPureParadox(message)
}

// demoConvergence runs the transport with a real epsilon so the payload lands.
func demoConvergence(message string) {
	const eps = 1e-6

	k, residualAtK := zeno.KForEpsilonExplained(eps)
	fmt.Printf("--- Delivery mode (epsilon = %g) ---\n", eps)
	fmt.Printf("Closed form: k = ceil(log2(1/eps)) = ceil(log2(%g)) = %d\n", 1/eps, k)
	fmt.Printf("Residual gap at k=%d is (1/2)^%d = %g (<= eps, so we deliver)\n\n", k, k, residualAtK)

	tp := zeno.New(zeno.Config{Epsilon: eps, MaxTicks: 64})

	fmt.Printf("%-5s %-14s %-14s %-14s\n", "tick", "step", "progress", "residual")
	fmt.Println(strings.Repeat("-", 52))

	res := tp.Send(message, func(p zeno.Packet) {
		marker := ""
		if p.Delivered {
			marker = "  <- close enough: DELIVERED"
		}
		// Trim the trace: show the first few ticks and the final few before k.
		if p.Tick <= 6 || p.Delivered || p.Tick >= k-2 {
			fmt.Printf("%-5d %-14.10f %-14.10f %-14.3e%s\n",
				p.Tick, p.StepFraction, p.Progress, p.Residual, marker)
		} else if p.Tick == 7 {
			fmt.Println("  ...")
		}
	})

	fmt.Printf("\nConverged within epsilon in %d ticks.\n", res.Ticks)
	fmt.Printf("Final progress = %.12f (residual gap = %.3e)\n", res.Progress, res.Residual)
	fmt.Printf("Receiver holds: %q (delivered=%t)\n", res.Received, res.Delivered)
}

// demoPureParadox runs with epsilon = 0: delivery never completes, and the run
// is capped at MaxTicks. We report the residual gap that Zeno can never close.
func demoPureParadox(message string) {
	const maxTicks = 20

	fmt.Printf("--- Pure paradox mode (epsilon = 0, capped at %d ticks) ---\n", maxTicks)
	tp := zeno.New(zeno.Config{Epsilon: 0, MaxTicks: maxTicks})

	fmt.Printf("%-5s %-16s %-16s\n", "tick", "progress", "residual")
	fmt.Println(strings.Repeat("-", 40))

	r := tp.Send(message, func(p zeno.Packet) {
		if p.Tick <= 5 || p.Tick > maxTicks-3 {
			fmt.Printf("%-5d %-16.12f %-16.3e\n", p.Tick, p.Progress, p.Residual)
		} else if p.Tick == 6 {
			fmt.Println("  ...")
		}
	})

	fmt.Printf("\nStopped after the %d-tick cap. Delivered = %t.\n", r.Ticks, r.Delivered)
	fmt.Printf("Progress = %.12f, but a residual gap of %.3e always remains.\n", r.Progress, r.Residual)
	fmt.Printf("In exact arithmetic the message %q never fully arrives.\n", message)
}
