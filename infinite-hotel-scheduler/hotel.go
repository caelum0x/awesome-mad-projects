package main

// Hotel is a resource allocator that is never full.
//
// It does NOT store an entry per room -- that would require materializing
// infinity. Instead it stores only the finite list of arrivals and the finite
// stack of Transformers that were applied. The physical room of any logical
// guest, and the occupant of any physical room, are computed on demand by
// evaluating the composed transform. That is the whole trick: infinity is kept
// lazy behind a handful of injective functions.
type Hotel struct {
	arrivals   []*Arrival
	transforms []Transformer // transforms[i] was applied when arrivals[i] checked in
}

// Arrival is one check-in event: a group of guests (finite or countably
// infinite) placed into the rooms freed by its Transformer.
type Arrival struct {
	Label  string
	Size   int64 // -1 means countably infinite
	idx    int
	hotel  *Hotel
	placer Placer
}

// RoomOf returns the physical room that member m of this arrival currently
// occupies, by pushing its freed-room forward through every later transform.
func (a *Arrival) RoomOf(member uint64) uint64 {
	r := a.placer.Room(member)
	for j := a.idx + 1; j < len(a.hotel.transforms); j++ {
		r = a.hotel.transforms[j].Apply(r)
	}
	return r
}

// New creates a hotel that starts completely FULL: the founding residents
// already occupy every room 0, 1, 2, .... The demonstrations then show that a
// full infinite hotel can still absorb new guests without evicting anyone.
func New() *Hotel {
	h := &Hotel{}
	h.arrivals = []*Arrival{{
		Label:  "founding-residents",
		Size:   -1,
		idx:    0,
		hotel:  h,
		placer: originalPlacer{},
	}}
	h.transforms = []Transformer{identity{}}
	return h
}

// admit relocates every current resident via t (freeing rooms) and records the
// new arrival that fills them. This is the single mutation point; note it
// appends rather than editing prior entries, so past arrivals keep their
// meaning.
func (h *Hotel) admit(label string, size int64, t Transformer, p Placer) *Arrival {
	a := &Arrival{Label: label, Size: size, idx: len(h.arrivals), hotel: h, placer: p}
	h.transforms = append(h.transforms, t)
	h.arrivals = append(h.arrivals, a)
	return a
}

// AddGuest shifts everyone n -> n+1 to free room 0 for a single new guest.
func (h *Hotel) AddGuest(req Request) *Arrival {
	return h.admit("guest:"+req.ID, 1, shift{1}, contiguousPlacer{1})
}

// AddBus shifts everyone n -> n+k to free rooms 0..k-1 for k new guests.
func (h *Hotel) AddBus(label string, k uint64) *Arrival {
	return h.admit("bus:"+label, int64(k), shift{k}, contiguousPlacer{k})
}

// AddInfiniteBus maps existing residents n -> 2n (into the even rooms) so the
// countably-infinite odd rooms 1, 3, 5, ... admit a whole infinite bus.
// Seat j of the bus rides to room 2j+1.
func (h *Hotel) AddInfiniteBus(label string) *Arrival {
	return h.admit("inf-bus:"+label, -1, doubling{}, oddPlacer{})
}

// InfiniteBuses is the view returned by AddInfiniteBuses: countably many buses,
// each countably infinite. It reuses the very same doubling move -- a single
// freeing of the odd rooms -- and threads (bus, seat) pairs through the Cantor
// pairing function so that N x N seats fit into the N odd rooms.
type InfiniteBuses struct{ arr *Arrival }

// SeatRoom returns the physical room for a given (bus, seat).
func (b InfiniteBuses) SeatRoom(bus, seat uint64) uint64 {
	return b.arr.RoomOf(cantor(bus, seat))
}

// AddInfiniteBuses admits countably-many countably-infinite buses at once.
func (h *Hotel) AddInfiniteBuses(label string) InfiniteBuses {
	return InfiniteBuses{arr: h.admit("inf-buses:"+label, -1, doubling{}, oddPlacer{})}
}

// Occupant identifies who lives in a physical room.
type Occupant struct {
	Arrival string // label of the arrival they came with
	Member  uint64 // index within that arrival
}

// WhoIsInRoom returns the current occupant of a physical room by inverting the
// transform stack from newest to oldest. The first transform whose inverse
// rejects the room is exactly the one that freed it -- so the room belongs to
// that transform's arrival. If every inverse succeeds, the room traces all the
// way back to a founding resident. Because the hotel started full and never
// evicts, this function is TOTAL: every room always has an occupant.
func (h *Hotel) WhoIsInRoom(room uint64) Occupant {
	r := room
	for i := len(h.transforms) - 1; i >= 1; i-- {
		pre, ok := h.transforms[i].Invert(r)
		if !ok {
			return Occupant{Arrival: h.arrivals[i].Label, Member: h.arrivals[i].placer.Member(r)}
		}
		r = pre
	}
	return Occupant{Arrival: h.arrivals[0].Label, Member: r}
}

// IsOccupied reports whether a physical room has an occupant. In this hotel the
// answer is always true after opening -- that is the point of the exercise: a
// full infinite hotel stays full even as it keeps saying yes to new guests.
func (h *Hotel) IsOccupied(room uint64) bool {
	_ = h.WhoIsInRoom(room) // total by construction
	return true
}

// Arrivals returns the recorded check-ins (founding residents first).
func (h *Hotel) Arrivals() []*Arrival { return h.arrivals }

// Transforms returns the composed transform stack, oldest first.
func (h *Hotel) Transforms() []Transformer { return h.transforms }
