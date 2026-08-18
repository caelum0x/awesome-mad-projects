package zeno

import "math"

// Packet is a single unit emitted by the sender on each tick. It carries the
// Zeno bookkeeping for that half-step. The actual payload is only attached on
// the packet that finally crosses the "close enough" threshold.
type Packet struct {
	Tick         int     // 1-based tick index
	StepFraction float64 // fraction of the whole journey covered THIS tick, (1/2)^Tick
	Progress     float64 // cumulative progress after this tick, 1 - (1/2)^Tick
	Residual     float64 // remaining gap after this tick, (1/2)^Tick
	Delivered    bool    // true on the packet that completes delivery
	Payload      string  // full message, set only when Delivered is true
}

// Config controls how the Zeno transport behaves.
type Config struct {
	// Epsilon is the "close enough to deliver" threshold. When the residual gap
	// drops to <= Epsilon, the receiver accepts the payload as delivered.
	// Epsilon must be in (0, 1] for delivery to ever complete.
	//
	// Set Epsilon to 0 for "pure paradox" mode: delivery never completes and the
	// run is capped at MaxTicks, reporting the residual gap that always remains.
	Epsilon float64

	// MaxTicks caps the number of half-steps. It is the safety bound for pure
	// paradox mode and a guard against pathological epsilons.
	MaxTicks int
}

// Result summarises a completed (or capped) transmission.
type Result struct {
	Message   string  // the message that was transmitted
	Delivered bool    // whether it crossed the epsilon threshold
	Ticks     int     // number of half-steps actually taken
	Progress  float64 // final cumulative progress
	Residual  float64 // final remaining gap
	Epsilon   float64 // threshold used
	Received  string  // what the receiver ended up holding ("" until delivered)
}

// TheoreticalTicks returns the tick count Zeno needs to get within the
// configured epsilon, purely from the closed form k = ceil(log2(1/eps)),
// clamped to MaxTicks. It does not run the transport.
func (c Config) TheoreticalTicks() int {
	k := TicksForEpsilon(c.Epsilon)
	if k > c.MaxTicks {
		return c.MaxTicks
	}
	return k
}

// Transport is a toy in-process transport. The sender and receiver communicate
// over a Go channel (loopback with no network involved), moving the message
// half of the remaining distance to the destination on every tick.
type Transport struct {
	cfg Config
}

// New returns a Transport with the given configuration.
func New(cfg Config) *Transport {
	if cfg.MaxTicks <= 0 {
		cfg.MaxTicks = 64
	}
	return &Transport{cfg: cfg}
}

// Send transmits msg over the Zeno transport. It spawns a sender goroutine that
// emits one Packet per tick onto a channel; the calling goroutine acts as the
// receiver, accumulating progress. The optional onTick callback is invoked for
// every received packet, which lets callers print a live convergence trace.
//
// Delivery completes on the first tick where the residual gap is <= Epsilon, at
// which point the sender flushes the full payload. In pure paradox mode
// (Epsilon <= 0) the loop runs until MaxTicks and never delivers.
func (t *Transport) Send(msg string, onTick func(Packet)) Result {
	packets := make(chan Packet)

	// Sender goroutine: walks the half-steps and closes the channel when done.
	go func() {
		defer close(packets)
		for k := 1; k <= t.cfg.MaxTicks; k++ {
			residual := Residual(k)
			p := Packet{
				Tick:         k,
				StepFraction: StepFraction(k),
				Progress:     Progress(k),
				Residual:     residual,
			}
			// "Close enough" only when a positive epsilon is configured.
			if t.cfg.Epsilon > 0 && residual <= t.cfg.Epsilon {
				p.Delivered = true
				p.Payload = msg
			}
			packets <- p
			if p.Delivered {
				return
			}
		}
	}()

	// Receiver: accumulate progress from each packet.
	res := Result{Message: msg, Epsilon: t.cfg.Epsilon}
	for p := range packets {
		if onTick != nil {
			onTick(p)
		}
		res.Ticks = p.Tick
		res.Progress = p.Progress
		res.Residual = p.Residual
		if p.Delivered {
			res.Delivered = true
			res.Received = p.Payload
		}
	}
	return res
}

// KForEpsilonExplained returns both the closed-form tick count and the residual
// gap at that tick, useful for documenting the k = log2(1/eps) relationship.
func KForEpsilonExplained(eps float64) (k int, residualAtK float64) {
	k = TicksForEpsilon(eps)
	if k == math.MaxInt {
		return k, 1
	}
	return k, Residual(k)
}
