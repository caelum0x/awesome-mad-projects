package scheduler

import (
	"statmech-scheduler/boltzmann"
)

// Result records the outcome of a simulation run: how many quanta each task
// received and the temperature the run was performed at.
type Result struct {
	Tasks        []Task
	Temperature  float64
	Ticks        int
	Quanta       []int     // CPU quanta granted to each task, index-aligned with Tasks
	Theoretical  []float64 // Boltzmann probability for each task
	Empirical    []float64 // observed fraction of CPU for each task
	QuantumTicks int       // how many ticks make up one quantum
}

// Scheduler runs the Boltzmann selection loop. It is a pure simulation: it
// never touches the real operating-system scheduler. Each tick it samples a
// task, "runs" it for a quantum, and records the CPU time granted.
type Scheduler struct {
	tasks        []Task
	sampler      *boltzmann.Sampler
	temperature  float64
	quantumTicks int
}

// New constructs a Scheduler for the given tasks at the given temperature,
// with a deterministic seed. quantumTicks is the number of ticks accounted to
// a task each time it is selected (a time-slice length); it must be >= 1.
func New(tasks []Task, temperature float64, quantumTicks int, seed int64) (*Scheduler, error) {
	if quantumTicks < 1 {
		quantumTicks = 1
	}
	sampler, err := boltzmann.NewSampler(Energies(tasks), temperature, seed)
	if err != nil {
		return nil, err
	}
	// Defensive copy so external mutation of the caller's slice cannot change
	// the scheduler's view of the task set.
	tasksCopy := make([]Task, len(tasks))
	copy(tasksCopy, tasks)
	return &Scheduler{
		tasks:        tasksCopy,
		sampler:      sampler,
		temperature:  temperature,
		quantumTicks: quantumTicks,
	}, nil
}

// Run simulates the scheduler for the given number of scheduling decisions
// and returns a Result comparing empirical CPU distribution against the
// theoretical Boltzmann weights. It does not mutate the Scheduler's task set.
func (s *Scheduler) Run(decisions int) (Result, error) {
	quanta := make([]int, len(s.tasks))
	for d := 0; d < decisions; d++ {
		idx := s.sampler.Next()
		quanta[idx] += s.quantumTicks
	}

	theoretical, err := boltzmann.Probabilities(Energies(s.tasks), s.temperature)
	if err != nil {
		return Result{}, err
	}

	totalTicks := decisions * s.quantumTicks
	empirical := make([]float64, len(s.tasks))
	if totalTicks > 0 {
		for i, q := range quanta {
			empirical[i] = float64(q) / float64(totalTicks)
		}
	}

	tasksCopy := make([]Task, len(s.tasks))
	copy(tasksCopy, s.tasks)

	return Result{
		Tasks:        tasksCopy,
		Temperature:  s.temperature,
		Ticks:        totalTicks,
		Quanta:       quanta,
		Theoretical:  theoretical,
		Empirical:    empirical,
		QuantumTicks: s.quantumTicks,
	}, nil
}
