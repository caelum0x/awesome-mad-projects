package main

import (
	"fmt"
	"sync"
)

// sim.go orchestrates the simulated processes. Each process is driven as a
// goroutine-actor: a tick signal is fanned out, every actor advances one step
// concurrently, and the orchestrator waits for all of them before printing the
// tick. Concurrency here models independent "processes"; it is bounded (one
// goroutine per actor, one step per tick) and never spawns unbounded work.

// Simulation holds all actors and the (optional) active domain.
type Simulation struct {
	Processes []*Process
	Domain    *Domain
}

// NewSimulation wires up a caster plus victims.
func NewSimulation() *Simulation {
	caster := NewProcess(0, "gojo (caster)", 100, 80, true)
	victims := []*Process{
		NewProcess(1, "worker-a", 100, 80, false),
		NewProcess(2, "worker-b", 120, 90, false),
		NewProcess(3, "worker-c", 80, 60, false),
	}
	all := append([]*Process{caster}, victims...)
	return &Simulation{
		Processes: all,
		Domain:    NewDomain(caster, victims),
	}
}

// step advances every actor by exactly one tick, concurrently. A process that
// is a victim of an open domain is flooded; everyone else runs normally.
func (s *Simulation) step() {
	var wg sync.WaitGroup
	for _, p := range s.Processes {
		wg.Add(1)
		go func(p *Process) {
			defer wg.Done()
			if s.Domain.Open && s.Domain.isVictim(p) {
				p.tickFlooded(s.Domain.FloodPerTick)
				return
			}
			p.tickNormal()
		}(p)
	}
	wg.Wait()
}

// Run advances the simulation `ticks` times, printing a per-tick snapshot.
func (s *Simulation) Run(ticks int, phase string) {
	for i := 0; i < ticks; i++ {
		s.step()
		s.printTick(phase)
	}
}

// printTick prints a compact per-process line for the latest tick.
func (s *Simulation) printTick(phase string) {
	last := s.Processes[0].Ticks // all actors share the same tick count
	fmt.Printf("[t=%02d %-10s] ", last, phase)
	for _, p := range s.Processes {
		tag := "  "
		if p.IsCaster {
			tag = "* " // caster
		} else if s.Domain.Open && s.Domain.isVictim(p) {
			tag = "! " // flooded victim
		}
		fmt.Printf("%s%-13s work=%-5d q=%-6d ovf=%-9d | ",
			tag, p.Name, p.UsefulWork, p.VirtualQueue, p.Overflow)
	}
	fmt.Println()
}
