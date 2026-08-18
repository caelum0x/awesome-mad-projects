package main

// A Placer describes how the members of a single arrival are laid out into the
// rooms that were just freed by that arrival's Transformer. It is a bijection
// between member indices and the freed room set, expressed in the coordinate
// system that exists immediately after the transform is applied. Later
// transforms then relocate those rooms forward (see Arrival.RoomOf).
type Placer interface {
	// Room returns the freed room that member m checks into.
	Room(member uint64) uint64
	// Member returns which member currently lives in a freed room.
	Member(room uint64) uint64
	// Describe explains the layout for humans.
	Describe() string
}

// originalPlacer lays the founding residents into every room: member m -> room m.
type originalPlacer struct{}

func (originalPlacer) Room(member uint64) uint64 { return member }
func (originalPlacer) Member(room uint64) uint64 { return room }
func (originalPlacer) Describe() string          { return "member m -> room m (fills every room)" }

// contiguousPlacer fills the first k rooms freed by shift{k}: member m -> room m.
type contiguousPlacer struct{ k uint64 }

func (contiguousPlacer) Room(member uint64) uint64 { return member }
func (contiguousPlacer) Member(room uint64) uint64 { return room }
func (p contiguousPlacer) Describe() string {
	return "member m -> room m for m in [0.." + u64(p.k-1) + "]"
}

// oddPlacer fills the odd rooms freed by doubling: member j -> room 2j+1.
// A single infinite bus enumerates seats directly (seat j -> member j).
// Infinitely many infinite buses enumerate (bus, seat) pairs through the Cantor
// pairing function first (see pairing.go), collapsing N x N into the single
// member index j -- which then lands in the countably-infinite set of odd rooms.
type oddPlacer struct{}

func (oddPlacer) Room(member uint64) uint64 { return 2*member + 1 }
func (oddPlacer) Member(room uint64) uint64 { return (room - 1) / 2 }
func (oddPlacer) Describe() string          { return "member j -> room 2j+1 (the odd rooms)" }
