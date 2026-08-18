package main

// Transformer is an injective function on room indices (the natural numbers).
//
// Every arrival in the hotel is admitted by first applying a Transformer to the
// rooms of every current resident. Because the function is injective it never
// makes two residents collide, and because its image is a proper subset of the
// naturals it frees up rooms for the newcomers. No resident is ever evicted:
// they are only relocated.
//
// Apply moves a room forward (relocate an existing resident).
// Invert moves a room backward. It returns ok == false exactly when the room is
// NOT in the image of Apply, i.e. when the room was *freed* by this transform
// and is therefore now home to the arrival admitted alongside it.
type Transformer interface {
	Apply(room uint64) uint64
	Invert(room uint64) (uint64, bool)
	Name() string
}

// identity is the transform for the hotel's original residents. It relocates
// nobody and frees nobody; it exists only so slot 0 has a parallel entry.
type identity struct{}

func (identity) Apply(room uint64) uint64          { return room }
func (identity) Invert(room uint64) (uint64, bool) { return room, true }
func (identity) Name() string                      { return "identity  (n -> n)" }

// shift maps n -> n+k. Its image is {k, k+1, ...}, so it frees rooms 0..k-1.
// AddGuest uses shift{1}; AddBus(k) uses shift{k}.
type shift struct{ k uint64 }

func (s shift) Apply(room uint64) uint64 { return room + s.k }

func (s shift) Invert(room uint64) (uint64, bool) {
	if room < s.k {
		return 0, false // room was freed by the shift
	}
	return room - s.k, true
}

func (s shift) Name() string { return "shift     (n -> n+" + u64(s.k) + ")" }

// doubling maps n -> 2n. Its image is the even rooms, so it frees every odd
// room. AddInfiniteBus and AddInfiniteBuses both use it: a single doubling frees
// a countably-infinite set of rooms (the odds) in one move.
type doubling struct{}

func (doubling) Apply(room uint64) uint64 { return 2 * room }

func (doubling) Invert(room uint64) (uint64, bool) {
	if room%2 == 0 {
		return room / 2, true
	}
	return 0, false // odd room was freed by the doubling
}

func (doubling) Name() string { return "doubling  (n -> 2n)" }
