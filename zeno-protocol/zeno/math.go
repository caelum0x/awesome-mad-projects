// Package zeno models Zeno's dichotomy paradox as a toy transport protocol.
//
// The dichotomy paradox: to reach a destination you must first travel half the
// distance, then half of the remaining distance, then half of that, and so on.
// Each step covers half of what is left, so after k steps the fraction of the
// journey completed is:
//
//	progress(k) = 1/2 + 1/4 + 1/8 + ... + 1/2^k = 1 - (1/2)^k
//
// This is a geometric series that converges to 1, but in exact arithmetic it
// never actually equals 1 for any finite k: there is always a residual gap of
// (1/2)^k remaining. The traveler gets arbitrarily close but "never arrives".
package zeno

import "math"

// Progress returns the cumulative fraction of the journey completed after k
// half-steps, i.e. 1 - (1/2)^k. It is strictly less than 1 for every finite k.
func Progress(k int) float64 {
	if k <= 0 {
		return 0
	}
	return 1 - math.Ldexp(1, -k) // 1 - 2^-k, computed without loss of precision
}

// Residual returns the remaining gap to the destination after k half-steps,
// which is exactly (1/2)^k. This is the amount Zeno can never close in a finite
// number of ticks.
func Residual(k int) float64 {
	if k <= 0 {
		return 1
	}
	return math.Ldexp(1, -k) // 2^-k
}

// StepFraction returns the fraction of the WHOLE journey covered by the single
// k-th half-step (k >= 1). Each tick covers half of the previously remaining
// gap, so the k-th step contributes (1/2)^k of the total distance.
func StepFraction(k int) float64 {
	if k <= 0 {
		return 0
	}
	return math.Ldexp(1, -k) // 2^-k
}

// TicksForEpsilon returns the smallest number of half-steps k such that the
// residual gap (1/2)^k is <= eps, i.e. the traveler is "close enough" to be
// considered delivered.
//
// Because Residual(k) = 2^-k, we need 2^-k <= eps, i.e. k >= log2(1/eps).
// The smallest such integer is k = ceil(log2(1/eps)).
//
// eps must be in (0, 1]. For eps <= 0 the paradox never resolves, so this
// returns math.MaxInt to signal "infinite" (pure-paradox mode should cap ticks).
func TicksForEpsilon(eps float64) int {
	if eps <= 0 {
		return math.MaxInt
	}
	if eps >= 1 {
		return 1
	}
	return int(math.Ceil(math.Log2(1 / eps)))
}
