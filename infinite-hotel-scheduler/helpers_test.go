package main

import (
	"strings"
	"testing"
)

func TestFoundingResidentRoomOf(t *testing.T) {
	h := New()
	orig := h.Arrivals()[0]
	// Before any arrival, founding resident g lives in room g.
	if room := orig.RoomOf(9); room != 9 {
		t.Fatalf("founding#9 want room 9, got %d", room)
	}
	// After a shift and a doubling, resident g is at 2*(g+1).
	h.AddGuest(Request{ID: "a", Kind: "vm"})
	h.AddInfiniteBus("ghost")
	room := orig.RoomOf(3)
	if room != 2*(3+1) {
		t.Fatalf("founding#3 want room %d, got %d", 2*(3+1), room)
	}
	if occ := h.WhoIsInRoom(room); occ.Arrival != "founding-residents" || occ.Member != 3 {
		t.Fatalf("want founding-residents#3, got %s#%d", occ.Arrival, occ.Member)
	}
}

func TestAccessorsAndNames(t *testing.T) {
	h := New()
	h.AddGuest(Request{ID: "a", Kind: "vm"})
	h.AddBus("blue", 2)
	h.AddInfiniteBus("ghost")

	if got := len(h.Arrivals()); got != 4 {
		t.Fatalf("want 4 arrivals, got %d", got)
	}
	if got := len(h.Transforms()); got != 4 {
		t.Fatalf("want 4 transforms, got %d", got)
	}
	for _, tr := range h.Transforms() {
		if strings.TrimSpace(tr.Name()) == "" {
			t.Fatal("transform name should not be empty")
		}
	}
}

func TestPlacerDescriptions(t *testing.T) {
	placers := []Placer{originalPlacer{}, contiguousPlacer{3}, oddPlacer{}}
	for _, p := range placers {
		if strings.TrimSpace(p.Describe()) == "" {
			t.Fatal("placer description should not be empty")
		}
		// Room/Member must be mutual inverses on the placer's domain.
		for m := uint64(0); m < 3; m++ {
			if p.Member(p.Room(m)) != m {
				t.Fatalf("%T not invertible at %d", p, m)
			}
		}
	}
}

func TestRequestString(t *testing.T) {
	r := Request{ID: "alice", Kind: "vm", VCPU: 4, MemMB: 8192}
	got := r.String()
	for _, want := range []string{"vm", "alice", "4", "8192"} {
		if !strings.Contains(got, want) {
			t.Fatalf("Request.String()=%q missing %q", got, want)
		}
	}
}

func TestIdentityTransform(t *testing.T) {
	id := identity{}
	if id.Apply(7) != 7 {
		t.Fatal("identity.Apply should be a no-op")
	}
	if v, ok := id.Invert(7); !ok || v != 7 {
		t.Fatal("identity.Invert should be a no-op")
	}
	if strings.TrimSpace(id.Name()) == "" {
		t.Fatal("identity.Name should not be empty")
	}
}
