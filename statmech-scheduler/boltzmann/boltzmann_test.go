package boltzmann

import (
	"math"
	"testing"
)

func TestProbabilitiesSumToOne(t *testing.T) {
	energies := []float64{-10, -7, -5, -2, -1}
	for _, temp := range []float64{0.25, 1.0, 4.0, 100.0} {
		probs, err := Probabilities(energies, temp)
		if err != nil {
			t.Fatalf("temp=%v: unexpected error: %v", temp, err)
		}
		var sum float64
		for _, p := range probs {
			sum += p
		}
		if math.Abs(sum-1.0) > 1e-12 {
			t.Errorf("temp=%v: probabilities sum to %v, want 1", temp, sum)
		}
	}
}

func TestLowerEnergyHasHigherProbability(t *testing.T) {
	// Energies strictly increasing => probabilities strictly decreasing.
	energies := []float64{-10, -7, -5, -2, -1}
	probs, err := Probabilities(energies, 1.0)
	if err != nil {
		t.Fatal(err)
	}
	for i := 1; i < len(probs); i++ {
		if probs[i] >= probs[i-1] {
			t.Errorf("prob[%d]=%v not < prob[%d]=%v", i, probs[i], i-1, probs[i-1])
		}
	}
}

func TestHighTemperatureFlattens(t *testing.T) {
	energies := []float64{-10, -7, -5, -2, -1}
	uniform := 1.0 / float64(len(energies))

	cold, _ := Probabilities(energies, 0.25)
	hot, _ := Probabilities(energies, 1000.0)

	// The top task dominates when cold, and approaches uniform when hot.
	if cold[0] < 0.9 {
		t.Errorf("expected cold top prob near 1, got %v", cold[0])
	}
	if math.Abs(hot[0]-uniform) > 1e-2 {
		t.Errorf("expected hot top prob near uniform %v, got %v", uniform, hot[0])
	}
}

func TestPartitionFunctionMatchesWeights(t *testing.T) {
	// With the log-sum-exp shift, Z equals sum of exp(-(E-minE)/T).
	energies := []float64{-10, -7, -5}
	temp := 2.0
	z, err := PartitionFunction(energies, temp)
	if err != nil {
		t.Fatal(err)
	}
	minE := -10.0
	var want float64
	for _, e := range energies {
		want += math.Exp(-(e - minE) / temp)
	}
	if math.Abs(z-want) > 1e-12 {
		t.Errorf("Z=%v, want %v", z, want)
	}
}

func TestZeroTemperatureLimit(t *testing.T) {
	energies := []float64{-10, -10, -5, -2}
	probs, err := ProbabilitiesAtZeroT(energies)
	if err != nil {
		t.Fatal(err)
	}
	// Two tied minima share the probability equally; others get zero.
	want := []float64{0.5, 0.5, 0, 0}
	for i := range want {
		if math.Abs(probs[i]-want[i]) > 1e-12 {
			t.Errorf("prob[%d]=%v, want %v", i, probs[i], want[i])
		}
	}
}

func TestErrors(t *testing.T) {
	if _, err := Probabilities(nil, 1.0); err != ErrEmpty {
		t.Errorf("empty: got %v, want ErrEmpty", err)
	}
	if _, err := Probabilities([]float64{1}, 0); err != ErrNonPositiveTemperature {
		t.Errorf("zero temp: got %v, want ErrNonPositiveTemperature", err)
	}
}
