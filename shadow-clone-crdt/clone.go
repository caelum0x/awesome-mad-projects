package main

import "fmt"

// CloneCtx is the private workspace a single spawned clone works in. It
// starts as a deep copy of the original's memory at spawn time and is
// mutated ONLY by the goroutine that owns it -- no other goroutine, clone or
// original, ever touches it. That is the concurrency-safety argument for
// this whole project: clones don't share memory while they work, they only
// exchange *values* (Memory snapshots) at spawn and at dispel. `go test
// -race` has nothing to catch because there is nothing to race on -- see
// Army.Spawn.
type CloneCtx struct {
	ID  string
	mem Memory

	tagSeq   uint64 // local-only counter, mints globally-unique ORSet tags
	clockSeq uint64 // local-only counter, this clone's logical clock
}

func newCloneCtx(id string, snapshot Memory) *CloneCtx {
	return &CloneCtx{ID: id, mem: snapshot.Clone()}
}

// nextTag mints a tag that is unique across the whole army:
// "<cloneID>#<n>", where n is this clone's own private, monotonically
// increasing counter. Because no two clones share an ID and each clone only
// ever increments its own counter, no coordination (locks, a shared atomic,
// a UUID library) is needed for global uniqueness.
func (c *CloneCtx) nextTag() string {
	c.tagSeq++
	return fmt.Sprintf("%s#%d", c.ID, c.tagSeq)
}

func (c *CloneCtx) nextClock() uint64 {
	c.clockSeq++
	return c.clockSeq
}

// Train adds reps training reps to this clone's own GCounter slot.
func (c *CloneCtx) Train(reps uint64) {
	c.mem.Reps = c.mem.Reps.Increment(c.ID, reps)
}

// GainChakra records n chakra found or regenerated.
func (c *CloneCtx) GainChakra(n uint64) {
	c.mem.Chakra = c.mem.Chakra.Gain(c.ID, n)
}

// SpendChakra records n chakra spent casting a technique.
func (c *CloneCtx) SpendChakra(n uint64) {
	c.mem.Chakra = c.mem.Chakra.Spend(c.ID, n)
}

// LearnJutsu drills a jutsu name into muscle memory (idempotent: drilling
// the same jutsu twice changes nothing about the resulting set).
func (c *CloneCtx) LearnJutsu(name string) {
	c.mem.Jutsu = c.mem.Jutsu.Add(name)
}

// PickUpScroll adds name to the scrolls this clone is carrying, tagged with
// a fresh, globally-unique id so a concurrent drop elsewhere can never
// phantom-remove this specific pickup (see ORSet's add-wins semantics).
func (c *CloneCtx) PickUpScroll(name string) {
	c.mem.Scrolls = c.mem.Scrolls.Add(name, c.nextTag())
}

// DropScroll removes every currently-visible copy of name this clone has
// observed so far.
func (c *CloneCtx) DropScroll(name string) {
	c.mem.Scrolls = c.mem.Scrolls.Remove(name)
}

// ReportStatus stamps a new status with this clone's own logical clock tick
// and ID, so LWWRegister merges resolve deterministically.
func (c *CloneCtx) ReportStatus(status string) {
	c.mem.Status = c.mem.Status.Set(status, c.nextClock(), c.ID)
}

// Memory returns an independent deep copy of the clone's current working
// state. Callers may Clone/Merge the returned value freely without any
// effect on c.
func (c *CloneCtx) Memory() Memory {
	return c.mem.Clone()
}
