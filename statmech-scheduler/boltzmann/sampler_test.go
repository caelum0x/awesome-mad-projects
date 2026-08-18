package boltzmann

import (
	"math"
	"testing"
)

// TestSamplerReproducible verifies that identical seeds yield identical draw
// sequences and that different seeds generally diverge.
func TestSamplerReproducible(t *testing.T) {
	energies := []float64{-10, -7, -5, -2, -1}

	a, _ := NewSampler(energies, 1.0, 123)
	b, _ := NewSampler(energies, 1.0, 123)
	for i := 0; i < 1000; i++ {
		if a.Next() != b.Next() {
			t.Fatalf("same seed diverged at draw %d", i)
		}
	}

	c, _ := NewSampler(energies, 1.0, 999)
	d, _ := NewSampler(energies, 1.0, 123)
	var diffs int
	for i := 0; i < 1000; i++ {
		if c.Next() != d.Next() {
			diffs++
		}
	}
	if diffs == 0 {
		t.Error("different seeds produced identical sequences")
	}
}

// TestSamplerConvergesToBoltzmann verifies that empirical frequencies from
// many draws converge to the theoretical Boltzmann probabilities.
func TestSamplerConvergesToBoltzmann(t *testing.T) {
	energies := []float64{-10, -7, -5, -2, -1}
	temp := 2.0
	want, _ := Probabilities(energies, temp)

	s, _ := NewSampler(energies, temp, 42)
	counts := make([]int, len(energies))
	const n = 400000
	for i := 0; i < n; i++ {
		counts[s.Next()]++
	}
	for i := range counts {
		got := float64(counts[i]) / float64(n)
		if math.Abs(got-want[i]) > 5e-3 {
			t.Errorf("index %d: empirical %.4f vs theory %.4f", i, got, want[i])
		}
	}
}
