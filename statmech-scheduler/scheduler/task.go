package scheduler

// Task is a "particle" in the statistical-mechanics analogy. Its priority is
// mapped to an energy: high priority means low energy, so it sits near the
// bottom of the energy well and is selected most often at low temperature.
type Task struct {
	Name     string
	Priority int // higher number = more important
}

// Energy converts a task's priority into an energy level. We use
//
//	E = -priority
//
// so that a higher priority yields a lower (more negative) energy. Any
// monotonically decreasing function of priority would work; a linear map
// keeps the relationship between priority gaps and probability ratios easy
// to reason about. The absolute offset is irrelevant because it cancels in
// the Boltzmann normalisation.
func (t Task) Energy() float64 {
	return -float64(t.Priority)
}

// Energies returns the energy of every task, in order. The input slice is
// not mutated.
func Energies(tasks []Task) []float64 {
	energies := make([]float64, len(tasks))
	for i, t := range tasks {
		energies[i] = t.Energy()
	}
	return energies
}
