// Package boltzmann implements the statistical-mechanics core of the
// scheduler: it maps a set of task "energies" and a system "temperature"
// onto Boltzmann selection probabilities.
//
// The Boltzmann (Gibbs) distribution assigns to a state i with energy E_i
// the probability
//
//	p_i = exp(-E_i / (k*T)) / Z,  where  Z = sum_j exp(-E_j / (k*T))
//
// Z is the partition function. Low-energy states (high-priority tasks) are
// favoured; raising the temperature T flattens the distribution toward
// uniform, while lowering it concentrates all probability on the
// minimum-energy state(s).
package boltzmann

import (
	"errors"
	"math"
)

// Boltzmann's constant is set to 1 here: in a scheduler there is no physical
// unit for energy, so we fold k into the temperature scale and work in
// natural units. This is an honest simplification, not real thermodynamics.
const BoltzmannConstant = 1.0

// ErrEmpty is returned when a distribution is requested for zero energies.
var ErrEmpty = errors.New("boltzmann: need at least one energy")

// ErrNonPositiveTemperature is returned when T <= 0, which would divide by
// zero. The zero-temperature limit is handled separately by ProbabilitiesAtZeroT.
var ErrNonPositiveTemperature = errors.New("boltzmann: temperature must be > 0")

// Weight returns the unnormalised Boltzmann factor exp(-E / (k*T)) for a
// single energy. Callers normally use Probabilities instead.
func Weight(energy, temperature float64) float64 {
	return math.Exp(-energy / (BoltzmannConstant * temperature))
}

// PartitionFunction computes Z = sum_i exp(-E_i / (k*T)).
//
// To avoid floating-point overflow/underflow when energies are large
// relative to k*T, the sum is shifted by the minimum energy (the classic
// log-sum-exp trick). This does not change the resulting probabilities
// because the shared factor cancels in normalisation.
func PartitionFunction(energies []float64, temperature float64) (float64, error) {
	if len(energies) == 0 {
		return 0, ErrEmpty
	}
	if temperature <= 0 {
		return 0, ErrNonPositiveTemperature
	}
	minE := energies[0]
	for _, e := range energies[1:] {
		if e < minE {
			minE = e
		}
	}
	var z float64
	beta := 1.0 / (BoltzmannConstant * temperature)
	for _, e := range energies {
		z += math.Exp(-(e - minE) * beta)
	}
	return z, nil
}

// Probabilities returns the normalised Boltzmann selection probability for
// each energy at the given temperature. The returned slice is a fresh copy;
// the input is never mutated. The probabilities sum to 1 (up to floating
// point rounding).
func Probabilities(energies []float64, temperature float64) ([]float64, error) {
	if len(energies) == 0 {
		return nil, ErrEmpty
	}
	if temperature <= 0 {
		return nil, ErrNonPositiveTemperature
	}
	minE := energies[0]
	for _, e := range energies[1:] {
		if e < minE {
			minE = e
		}
	}
	beta := 1.0 / (BoltzmannConstant * temperature)
	weights := make([]float64, len(energies))
	var z float64
	for i, e := range energies {
		w := math.Exp(-(e - minE) * beta)
		weights[i] = w
		z += w
	}
	probs := make([]float64, len(energies))
	for i, w := range weights {
		probs[i] = w / z
	}
	return probs, nil
}

// ProbabilitiesAtZeroT returns the T -> 0 limiting distribution: all
// probability is shared equally among the state(s) of minimum energy and
// zero everywhere else. This is the deterministic "always run the highest
// priority" regime that a strict priority scheduler implements.
func ProbabilitiesAtZeroT(energies []float64) ([]float64, error) {
	if len(energies) == 0 {
		return nil, ErrEmpty
	}
	minE := energies[0]
	for _, e := range energies[1:] {
		if e < minE {
			minE = e
		}
	}
	var count int
	for _, e := range energies {
		if e == minE {
			count++
		}
	}
	probs := make([]float64, len(energies))
	share := 1.0 / float64(count)
	for i, e := range energies {
		if e == minE {
			probs[i] = share
		}
	}
	return probs, nil
}
