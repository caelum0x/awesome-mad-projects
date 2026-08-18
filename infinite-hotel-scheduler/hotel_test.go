package main

import "testing"

// roundTrip asserts that a member of an arrival lands in a room whose reverse
// lookup names that same arrival and member -- the core no-eviction invariant.
func roundTrip(t *testing.T, h *Hotel, a *Arrival, member uint64) uint64 {
	t.Helper()
	room := a.RoomOf(member)
	occ := h.WhoIsInRoom(room)
	if occ.Arrival != a.Label || occ.Member != member {
		t.Fatalf("room %d: want %s#%d, got %s#%d", room, a.Label, member, occ.Arrival, occ.Member)
	}
	return room
}

func TestAddGuestFreesRoomZero(t *testing.T) {
	h := New()
	g := h.AddGuest(Request{ID: "a", Kind: "vm"})
	if room := g.RoomOf(0); room != 0 {
		t.Fatalf("new guest want room 0, got %d", room)
	}
	// The founding resident formerly in room 0 moved to room 1.
	occ := h.WhoIsInRoom(1)
	if occ.Arrival != "founding-residents" || occ.Member != 0 {
		t.Fatalf("room 1 want founding-residents#0, got %s#%d", occ.Arrival, occ.Member)
	}
	roundTrip(t, h, g, 0)
}

func TestAddBusFreesKRooms(t *testing.T) {
	h := New()
	b := h.AddBus("blue", 3)
	for m := uint64(0); m < 3; m++ {
		if room := roundTrip(t, h, b, m); room != m {
			t.Fatalf("bus member %d want room %d, got %d", m, m, room)
		}
	}
	// Founding resident 0 pushed to room 3.
	if occ := h.WhoIsInRoom(3); occ.Arrival != "founding-residents" || occ.Member != 0 {
		t.Fatalf("room 3 want founding-residents#0, got %s#%d", occ.Arrival, occ.Member)
	}
}

func TestAddInfiniteBusTakesOdds(t *testing.T) {
	h := New()
	bus := h.AddInfiniteBus("ghost")
	for j := uint64(0); j < 100; j++ {
		room := roundTrip(t, h, bus, j)
		if room != 2*j+1 {
			t.Fatalf("seat %d want room %d, got %d", j, 2*j+1, room)
		}
	}
	// Founding residents now live in even rooms.
	if occ := h.WhoIsInRoom(10); occ.Arrival != "founding-residents" || occ.Member != 5 {
		t.Fatalf("room 10 want founding-residents#5, got %s#%d", occ.Arrival, occ.Member)
	}
}

func TestAddInfiniteBusesPairing(t *testing.T) {
	h := New()
	fleet := h.AddInfiniteBuses("fleet")
	seen := map[uint64]bool{}
	for bus := uint64(0); bus < 30; bus++ {
		for seat := uint64(0); seat < 30; seat++ {
			room := fleet.SeatRoom(bus, seat)
			if room%2 == 0 {
				t.Fatalf("bus %d seat %d got even room %d", bus, seat, room)
			}
			if seen[room] {
				t.Fatalf("room %d assigned twice", room)
			}
			seen[room] = true
			// Reverse lookup must find the fleet and decode back to (bus, seat).
			occ := h.WhoIsInRoom(room)
			if occ.Arrival != "inf-buses:fleet" {
				t.Fatalf("room %d want inf-buses:fleet, got %s", room, occ.Arrival)
			}
			gotBus, gotSeat := uncantor(occ.Member)
			if gotBus != bus || gotSeat != seat {
				t.Fatalf("decode want (%d,%d), got (%d,%d)", bus, seat, gotBus, gotSeat)
			}
		}
	}
}

// TestNoEvictionAcrossSequence runs the full demo sequence and checks that
// every previously admitted guest still has a unique, valid room afterwards.
func TestNoEvictionAcrossSequence(t *testing.T) {
	h := New()
	type ref struct {
		a *Arrival
		m uint64
	}
	var refs []ref

	alice := h.AddGuest(Request{ID: "alice", Kind: "vm"})
	refs = append(refs, ref{alice, 0})

	bus := h.AddBus("blue", 3)
	refs = append(refs, ref{bus, 0}, ref{bus, 1}, ref{bus, 2})

	inf := h.AddInfiniteBus("ghost")
	refs = append(refs, ref{inf, 0}, ref{inf, 7}, ref{inf, 99})

	fleet := h.AddInfiniteBuses("fleet")
	_ = fleet

	rooms := map[uint64]bool{}
	for _, r := range refs {
		room := roundTrip(t, h, r.a, r.m)
		if rooms[room] {
			t.Fatalf("collision at room %d", room)
		}
		rooms[room] = true
	}
}

func TestIsOccupiedAlwaysTrue(t *testing.T) {
	h := New()
	h.AddGuest(Request{ID: "a", Kind: "vm"})
	h.AddInfiniteBus("ghost")
	for _, r := range []uint64{0, 1, 2, 5, 1000, 1 << 40} {
		if !h.IsOccupied(r) {
			t.Fatalf("room %d should be occupied", r)
		}
	}
}
