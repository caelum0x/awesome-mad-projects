package main

import "testing"

func TestCantorBijection(t *testing.T) {
	seen := map[uint64]bool{}
	for a := uint64(0); a < 60; a++ {
		for b := uint64(0); b < 60; b++ {
			z := cantor(a, b)
			if seen[z] {
				t.Fatalf("cantor collision at (%d,%d) -> %d", a, b, z)
			}
			seen[z] = true
			ga, gb := uncantor(z)
			if ga != a || gb != b {
				t.Fatalf("uncantor(%d) want (%d,%d), got (%d,%d)", z, a, b, ga, gb)
			}
		}
	}
}

func TestUncantorCoversLowIntegers(t *testing.T) {
	// Every natural number is some Cantor pair; check the inverse is exact.
	for z := uint64(0); z < 5000; z++ {
		a, b := uncantor(z)
		if cantor(a, b) != z {
			t.Fatalf("uncantor(%d)=(%d,%d) does not round-trip", z, a, b)
		}
	}
}

func TestTransformInverses(t *testing.T) {
	sh := shift{5}
	for n := uint64(0); n < 50; n++ {
		if got, ok := sh.Invert(sh.Apply(n)); !ok || got != n {
			t.Fatalf("shift invert failed at %d", n)
		}
	}
	for r := uint64(0); r < 5; r++ {
		if _, ok := sh.Invert(r); ok {
			t.Fatalf("room %d should be freed by shift{5}", r)
		}
	}
	d := doubling{}
	for n := uint64(0); n < 50; n++ {
		if got, ok := d.Invert(d.Apply(n)); !ok || got != n {
			t.Fatalf("doubling invert failed at %d", n)
		}
		if _, ok := d.Invert(2*n + 1); ok {
			t.Fatalf("odd room %d should be freed by doubling", 2*n+1)
		}
	}
}
