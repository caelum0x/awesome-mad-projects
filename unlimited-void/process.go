package main

// process.go models a single simulated "process" as an actor with a bounded,
// virtual attention budget. Everything here is a counter. No real memory is
// allocated to represent flooded work, and no real CPU is burned to simulate
// the flood: overflow is arithmetic, not allocation.

// Process is a simulated actor with a finite per-tick attention budget.
//
// The mental model (JJK "Unlimited Void"): a mind can only attend to a bounded
// amount of information per unit of time. Normally a process spends that
// attention on useful tasks. Under Domain Expansion it is shown "infinity":
// the incoming virtual information vastly exceeds what it can attend to, so all
// of its attention is consumed just perceiving the flood and none is left for
// useful work.
type Process struct {
	ID   int
	Name string

	// AttentionBudget is the number of virtual information units the process
	// can attend to per tick. This is its "processing budget".
	AttentionBudget int

	// UsefulInflow is how many genuinely useful task-units arrive per tick
	// under normal operation. Kept below AttentionBudget so a healthy process
	// keeps up and does useful work every tick.
	UsefulInflow int

	// IsCaster marks the privileged process that opens the domain. The caster
	// is immune to its own Unlimited Void.
	IsCaster bool

	// --- runtime counters (all virtual) ---

	Ticks         int // ticks this process has been alive for
	UsefulWork    int // cumulative useful work units completed
	VirtualQueue  int // current backlog of virtual info units (capped)
	VirtualQueued int // cumulative virtual info units ever injected
	Overflow      int // cumulative units dropped because the queue was capped
}

// QueueCap bounds the modeled backlog. When the flood would push the queue past
// this cap, the excess is counted as Overflow instead of being stored. This is
// the safety valve that keeps the simulation from pretending to hold "infinity"
// in memory: infinity is represented as a growing Overflow number.
const QueueCap = 10_000

// NewProcess builds a healthy process actor.
func NewProcess(id int, name string, budget, usefulInflow int, isCaster bool) *Process {
	return &Process{
		ID:              id,
		Name:            name,
		AttentionBudget: budget,
		UsefulInflow:    usefulInflow,
		IsCaster:        isCaster,
	}
}

// injectFlood adds `units` virtual information units to the queue, capping the
// stored backlog at QueueCap and accumulating the rest as Overflow. It never
// allocates memory proportional to `units`; it only updates integer counters.
func (p *Process) injectFlood(units int) {
	if units <= 0 {
		return
	}
	p.VirtualQueued += units

	room := QueueCap - p.VirtualQueue
	if units <= room {
		p.VirtualQueue += units
		return
	}
	// Queue is (or becomes) full: store what fits, count the rest as overflow.
	if room > 0 {
		p.VirtualQueue = QueueCap
		units -= room
	}
	p.Overflow += units
}

// tickNormal advances the process one tick under normal conditions: useful work
// arrives and is completed up to the attention budget.
func (p *Process) tickNormal() {
	p.Ticks++

	// Under normal load, attention first drains any lingering virtual backlog
	// (e.g. recovering right after a domain closes), then does useful work with
	// whatever attention remains.
	attention := p.AttentionBudget
	drained := min(attention, p.VirtualQueue)
	p.VirtualQueue -= drained
	attention -= drained

	// Useful tasks arrive; complete as many as remaining attention allows.
	work := min(attention, p.UsefulInflow)
	p.UsefulWork += work
}

// tickFlooded advances the process one tick while trapped inside a domain.
// `floodPerTick` virtual info units are injected; because floodPerTick greatly
// exceeds the attention budget, all attention is spent perceiving the flood and
// useful throughput collapses to ~0.
func (p *Process) tickFlooded(floodPerTick int) {
	p.Ticks++

	p.injectFlood(floodPerTick)

	// Attention is spent attending to the overwhelming virtual queue first.
	attention := p.AttentionBudget
	perceived := min(attention, p.VirtualQueue)
	p.VirtualQueue -= perceived
	attention -= perceived

	// Whatever attention is left (normally zero, since flood >> budget) could do
	// useful work. With an overwhelming flood this is 0: "shown infinity, cannot
	// act." No new useful tasks are even reached.
	_ = attention // documents that leftover attention would do useful work
}

// Throughput returns useful work per tick as a ratio in [0, 1] relative to the
// process's own attention budget. A healthy process sits near UsefulInflow/Budget.
func (p *Process) Throughput() float64 {
	if p.Ticks == 0 {
		return 0
	}
	return float64(p.UsefulWork) / float64(p.Ticks*p.AttentionBudget)
}
