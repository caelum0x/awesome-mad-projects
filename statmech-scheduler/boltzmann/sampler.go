package boltzmann

import (
	"math/rand"
)

// Sampler draws indices according to a Boltzmann distribution over a fixed
// set of energies at a fixed temperature. It owns a seeded PRNG so that a
// given seed always produces the same sequence of draws, making simulation
// runs fully reproducible.
type Sampler struct {
	energies    []float64
	temperature float64
	// cumulative holds the running cumulative distribution function so that
	// each draw is a single O(log n) / O(n) inverse-CDF lookup.
	cumulative []float64
	rng        *rand.Rand
}

// NewSampler builds a Sampler for the given energies and temperature, seeded
// deterministically. It precomputes the cumulative distribution once so that
// repeated sampling is cheap. It returns an error for empty input or a
// non-positive temperature.
func NewSampler(energies []float64, temperature float64, seed int64) (*Sampler, error) {
	probs, err := Probabilities(energies, temperature)
	if err != nil {
		return nil, err
	}
	// Copy energies so the Sampler is immune to later caller mutation.
	energiesCopy := make([]float64, len(energies))
	copy(energiesCopy, energies)

	cumulative := make([]float64, len(probs))
	var running float64
	for i, p := range probs {
		running += p
		cumulative[i] = running
	}
	// Guard against floating-point drift: pin the last bucket to 1.0 so a
	// draw of nearly-1.0 always lands on a valid index.
	cumulative[len(cumulative)-1] = 1.0

	return &Sampler{
		energies:    energiesCopy,
		temperature: temperature,
		cumulative:  cumulative,
		rng:         rand.New(rand.NewSource(seed)),
	}, nil
}

// Next returns the index of the next selected task, drawn according to the
// Boltzmann distribution via inverse-CDF sampling.
func (s *Sampler) Next() int {
	u := s.rng.Float64()
	for i, c := range s.cumulative {
		if u < c {
			return i
		}
	}
	// Unreachable in practice because the last cumulative entry is 1.0 and
	// Float64() < 1.0, but return the last index defensively.
	return len(s.cumulative) - 1
}

// Temperature reports the temperature the Sampler was built with.
func (s *Sampler) Temperature() float64 {
	return s.temperature
}
