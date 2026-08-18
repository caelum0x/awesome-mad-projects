package main

import "fmt"

// domain.go models the "Domain Expansion: Unlimited Void". A privileged caster
// opens the domain over a set of victim processes. While open, every victim is
// flooded each tick with FloodPerTick virtual information units. The caster is
// immune.

// Domain represents an Unlimited Void cast by one process over others.
type Domain struct {
	Caster       *Process
	Victims      []*Process
	FloodPerTick int // virtual info units injected into each victim per tick
	Open         bool
}

// FloodMultiplier sets how overwhelming the flood is relative to a victim's
// attention budget. "Unlimited Void" shows infinity, so the flood dwarfs any
// finite budget. This is a fixed factor, not real infinity — the model stays
// bounded and safe.
const FloodMultiplier = 1_000

// NewDomain builds a (closed) domain for the given caster and victims. The
// flood rate is derived from the strongest victim's budget so it overwhelms
// everyone.
func NewDomain(caster *Process, victims []*Process) *Domain {
	maxBudget := 1
	for _, v := range victims {
		if v.AttentionBudget > maxBudget {
			maxBudget = v.AttentionBudget
		}
	}
	return &Domain{
		Caster:       caster,
		Victims:      victims,
		FloodPerTick: maxBudget * FloodMultiplier,
	}
}

// Expand opens the Unlimited Void.
func (d *Domain) Expand() {
	d.Open = true
	fmt.Printf("\n>>> DOMAIN EXPANSION: UNLIMITED VOID  (caster: %s)\n", d.Caster.Name)
	fmt.Printf("    Victims are shown infinity: %d virtual info units / tick vs. budgets ~%d/tick.\n\n",
		d.FloodPerTick, d.strongestVictimBudget())
}

// Close collapses the domain. The virtual flood was an illusion, so when the
// domain closes it vanishes: each victim's virtual backlog is dispelled to 0 and
// attention is freed for useful work again. Overflow counters are kept as a
// historical record of how much "infinity" was shown. Victims recover fully on
// the very next tick.
func (d *Domain) Close() {
	d.Open = false
	for _, v := range d.Victims {
		v.VirtualQueue = 0 // the illusion disappears; nothing real to drain
	}
	fmt.Printf("\n<<< DOMAIN CLOSED  (caster: %s). The flood vanishes; victims recover throughput.\n\n", d.Caster.Name)
}

func (d *Domain) strongestVictimBudget() int {
	if d.FloodPerTick == 0 {
		return 0
	}
	return d.FloodPerTick / FloodMultiplier
}

// isVictim reports whether p is caught in this domain.
func (d *Domain) isVictim(p *Process) bool {
	for _, v := range d.Victims {
		if v.ID == p.ID {
			return true
		}
	}
	return false
}
