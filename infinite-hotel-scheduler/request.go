package main

import "strconv"

// Request models the workload a "guest" really represents in this cloud
// scheduler: a VM or container asking for a room (a scheduling slot). The room
// index is the physical slot the allocator hands out; the hotel guarantees a
// free room always exists, so a Request is never rejected for lack of capacity.
type Request struct {
	ID    string
	Kind  string // "vm" or "container"
	VCPU  int
	MemMB int
}

func (r Request) String() string {
	return r.Kind + ":" + r.ID + " (" + strconv.Itoa(r.VCPU) + " vCPU, " + strconv.Itoa(r.MemMB) + " MB)"
}

// u64 is a tiny helper for building human-readable transform/placer names
// without pulling fmt into those hot, allocation-light files.
func u64(v uint64) string { return strconv.FormatUint(v, 10) }
