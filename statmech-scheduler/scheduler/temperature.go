package scheduler

// TemperatureFromLoad maps a normalised system load in [0, 1] onto a
// scheduler temperature.
//
// Physical intuition: a lightly loaded system can afford to be "cold" and
// strictly serve the highest-priority work; a heavily loaded system heats up,
// flattening the selection distribution so that lower-priority tasks also get
// occasional CPU time (this models fairness / anti-starvation pressure that
// appears when the run queue is saturated).
//
// The map is linear between a floor and a ceiling temperature:
//
//	T(load) = minT + load * (maxT - minT)
//
// load is clamped to [0, 1]. minT is kept strictly positive so the Boltzmann
// math never divides by zero; the true zero-temperature limit is available
// separately via boltzmann.ProbabilitiesAtZeroT.
func TemperatureFromLoad(load, minT, maxT float64) float64 {
	if load < 0 {
		load = 0
	}
	if load > 1 {
		load = 1
	}
	return minT + load*(maxT-minT)
}
