package main

import (
	"fmt"
	"strings"
)

// watch is a stable handle to one logical guest: the arrival it came with and
// its member index. Its physical room is always recomputed lazily, proving the
// guest is relocated (never evicted) as later arrivals reshape the hotel.
type watch struct {
	name   string
	arr    *Arrival
	member uint64
}

func main() {
	fmt.Println("Hilbert's Infinite Hotel -- Cloud Scheduler")
	fmt.Println("A resource allocator that is NEVER full.")
	fmt.Println(strings.Repeat("=", 60))

	h := New()
	fmt.Println("\nOpening state: the hotel is already FULL.")
	fmt.Println("  founding residents occupy every room 0, 1, 2, 3, ...")

	var watched []watch

	section("1) AddGuest -- one VM shows up; shift n -> n+1 frees room 0")
	alice := h.AddGuest(Request{ID: "alice", Kind: "vm", VCPU: 4, MemMB: 8192})
	watched = append(watched, watch{"alice (vm)", alice, 0})
	report(h, watched)

	section("2) AddBus(3) -- a bus of 3 containers; shift n -> n+3 frees rooms 0..2")
	bus := h.AddBus("blue", 3)
	watched = append(watched, watch{"bus.blue seat0", bus, 0}, watch{"bus.blue seat2", bus, 2})
	report(h, watched)

	section("3) AddInfiniteBus -- residents n -> 2n; the infinite bus takes the odds")
	ghost := h.AddInfiniteBus("ghost")
	watched = append(watched, watch{"inf-bus.ghost seat0", ghost, 0}, watch{"inf-bus.ghost seat5", ghost, 5})
	report(h, watched)

	section("4) AddInfiniteBuses -- countably many infinite buses via Cantor pairing")
	fleet := h.AddInfiniteBuses("fleet")
	fmt.Println("  Cantor pairing (bus, seat) -> member -> odd room:")
	for _, bs := range [][2]uint64{{0, 0}, {0, 1}, {1, 0}, {2, 3}} {
		b, s := bs[0], bs[1]
		fmt.Printf("    bus %d seat %d -> member %d -> room %d\n",
			b, s, cantor(b, s), fleet.SeatRoom(b, s))
	}
	// The doubling relocated the previously-watched guests again; refresh trace.
	report(h, watched)

	section("Transform stack (composed, newest last)")
	for i, t := range h.Transforms() {
		if i == 0 {
			fmt.Printf("  [%d] %-22s  founding residents\n", i, t.Name())
			continue
		}
		fmt.Printf("  [%d] %-22s  admitted %s\n", i, t.Name(), h.Arrivals()[i].Label)
	}

	section("Proof: no eviction, no collision, still full")
	proveInjective(h, watched)
	proveFull(h)

	fmt.Println("\nEvery room is occupied, every guest has a unique room, and the")
	fmt.Println("hotel still accepted an infinite fleet of infinite buses. Never full.")
}

func section(title string) {
	fmt.Println("\n" + strings.Repeat("-", 60))
	fmt.Println(title)
	fmt.Println(strings.Repeat("-", 60))
}

// report prints where each watched guest currently lives and confirms the
// physical-room -> guest reverse lookup round-trips.
func report(h *Hotel, watched []watch) {
	for _, w := range watched {
		room := w.arr.RoomOf(w.member)
		occ := h.WhoIsInRoom(room)
		fmt.Printf("  %-22s -> room %-6d (WhoIsInRoom(%d) = %s#%d)\n",
			w.name, room, room, occ.Arrival, occ.Member)
	}
	occ := h.WhoIsInRoom(0)
	fmt.Printf("  physical room 0 currently holds: %s#%d\n", occ.Arrival, occ.Member)
	fmt.Printf("  IsOccupied(0)=%v  IsOccupied(1)=%v  IsOccupied(1000000)=%v\n",
		h.IsOccupied(0), h.IsOccupied(1), h.IsOccupied(1000000))
}

func proveInjective(h *Hotel, watched []watch) {
	seen := map[uint64]string{}
	clash := false
	for _, w := range watched {
		room := w.arr.RoomOf(w.member)
		if prev, ok := seen[room]; ok {
			fmt.Printf("  COLLISION: %s and %s both in room %d\n", prev, w.name, room)
			clash = true
		}
		seen[room] = w.name
	}
	if !clash {
		fmt.Printf("  %d tracked guests occupy %d distinct rooms -> injective, no collisions\n",
			len(watched), len(seen))
	}
}

func proveFull(h *Hotel) {
	rooms := []uint64{0, 1, 2, 3, 7, 42, 123, 10000, 999999}
	all := true
	for _, r := range rooms {
		if !h.IsOccupied(r) {
			all = false
		}
	}
	fmt.Printf("  sampled rooms %v -> all occupied: %v\n", rooms, all)
}
