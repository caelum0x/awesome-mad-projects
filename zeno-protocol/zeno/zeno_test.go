package zeno

import (
	"math"
	"testing"
)

func TestProgressNeverReachesOne(t *testing.T) {
	for _, k := range []int{1, 2, 5, 10, 30, 52} {
		p := Progress(k)
		if p >= 1.0 {
			t.Fatalf("Progress(%d) = %v, must be strictly < 1", k, p)
		}
		if got, want := 1-p, Residual(k); math.Abs(got-want) > 1e-15 {
			t.Fatalf("k=%d: 1-progress=%v, residual=%v", k, got, want)
		}
	}
}

func TestProgressGeometricSeries(t *testing.T) {
	// Progress(k) must equal the partial sum 1/2 + 1/4 + ... + 1/2^k.
	sum := 0.0
	for k := 1; k <= 20; k++ {
		sum += StepFraction(k)
		if got := Progress(k); math.Abs(got-sum) > 1e-15 {
			t.Fatalf("k=%d: partial sum=%v, Progress=%v", k, sum, got)
		}
	}
}

func TestTicksForEpsilon(t *testing.T) {
	cases := []struct {
		eps  float64
		want int
	}{
		{0.5, 1},   // 2^-1 = 0.5
		{0.25, 2},  // 2^-2 = 0.25
		{0.1, 4},   // ceil(log2(10)) = 4  -> 2^-4 = 0.0625 <= 0.1
		{1e-3, 10}, // ceil(log2(1000)) = 10
		{1e-6, 20}, // ceil(log2(1e6)) = 20
	}
	for _, c := range cases {
		if got := TicksForEpsilon(c.eps); got != c.want {
			t.Errorf("TicksForEpsilon(%g) = %d, want %d", c.eps, got, c.want)
		}
		// The residual at k must actually be within epsilon.
		if r := Residual(c.want); r > c.eps {
			t.Errorf("Residual(%d)=%g exceeds eps=%g", c.want, r, c.eps)
		}
	}
}

func TestSendDelivers(t *testing.T) {
	tp := New(Config{Epsilon: 1e-6, MaxTicks: 64})
	msg := "ping"
	res := tp.Send(msg, nil)
	if !res.Delivered {
		t.Fatal("expected delivery within epsilon")
	}
	if res.Received != msg {
		t.Fatalf("received %q, want %q", res.Received, msg)
	}
	if want := TicksForEpsilon(1e-6); res.Ticks != want {
		t.Fatalf("delivered in %d ticks, want %d", res.Ticks, want)
	}
}

func TestSendPureParadoxNeverDelivers(t *testing.T) {
	const maxTicks = 20
	tp := New(Config{Epsilon: 0, MaxTicks: maxTicks})
	res := tp.Send("ping", nil)
	if res.Delivered {
		t.Fatal("pure paradox mode must never deliver")
	}
	if res.Ticks != maxTicks {
		t.Fatalf("expected to run full %d ticks, got %d", maxTicks, res.Ticks)
	}
	if res.Residual != Residual(maxTicks) {
		t.Fatalf("residual = %v, want %v", res.Residual, Residual(maxTicks))
	}
}
