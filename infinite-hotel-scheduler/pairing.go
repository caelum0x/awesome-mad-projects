package main

import "math"

// cantor is the Cantor pairing function, a bijection N x N -> N:
//
//	cantor(a, b) = (a+b)(a+b+1)/2 + b
//
// It lets "infinitely many infinite buses" (indexed by bus a and seat b) be
// collapsed into a single stream of member indices, which then fit into the
// countably-infinite set of odd rooms via oddPlacer.
func cantor(a, b uint64) uint64 {
	s := a + b
	return s*(s+1)/2 + b
}

// uncantor inverts cantor: given z it recovers the (a, b) pair.
func uncantor(z uint64) (a, b uint64) {
	// w is the triangular-root: the largest w with w(w+1)/2 <= z.
	w := uint64((math.Sqrt(8*float64(z)+1) - 1) / 2)
	// Correct any floating-point drift.
	for (w+1)*(w+2)/2 <= z {
		w++
	}
	for w > 0 && w*(w+1)/2 > z {
		w--
	}
	t := w * (w + 1) / 2
	b = z - t
	a = w - b
	return a, b
}
