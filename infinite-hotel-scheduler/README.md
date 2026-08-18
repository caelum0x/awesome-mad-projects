# Hilbert's Infinite Hotel — Cloud Scheduler

A resource allocator that is **never full**. Rooms are indexed by the natural
numbers `0, 1, 2, 3, ...` and every "guest" is a VM or container request. No
matter how many guests are already checked in — even infinitely many — the
allocator can always admit more without evicting anyone.

This is a **simulation**, not a real cluster. It exists to make the classic
thought experiment concrete and runnable, and to be honest about the math that
makes it work.

## The concept

David Hilbert's paradox of the Grand Hotel: a hotel with a countably infinite
number of rooms, all occupied, can still accommodate new guests by relocating
existing ones. This project implements the four classic moves as real allocator
methods:

| Method                | Move                     | Frees                         |
|-----------------------|--------------------------|-------------------------------|
| `AddGuest()`          | shift `n -> n+1`         | room `0` (one guest)          |
| `AddBus(k)`           | shift `n -> n+k`         | rooms `0..k-1` (k guests)     |
| `AddInfiniteBus()`    | double `n -> 2n`         | all odd rooms (∞ guests)      |
| `AddInfiniteBuses()`  | double + Cantor pairing  | all odd rooms (∞ buses × ∞)   |

## The lazy representation (no materialized infinity)

Storing one record per room is impossible — there are infinitely many. Instead
the hotel keeps only:

- a finite **list of arrivals** (each finite or countably infinite), and
- a finite **stack of injective transforms** applied over time.

The physical room of any logical guest, and the occupant of any physical room,
are **computed on demand** by evaluating the composed transform. Infinity stays
lazy behind a handful of functions (`hotel.go`, `transform.go`, `placer.go`).

Each transform `t` is an injective function `N -> N`:

- `Apply(room)` pushes an existing resident **forward** (relocation).
- `Invert(room)` pushes **backward**; it returns `ok == false` exactly when the
  room is *not* in the image of `Apply` — i.e. the room this transform **freed**,
  now home to the arrival admitted alongside it.

## Honest math

### `AddGuest` — shift `n -> n+1`
Every resident in room `n` moves to `n+1`. The map is a bijection from `N` onto
`{1, 2, 3, ...}`, so room `0` is freed. One new guest checks into room `0`.
Nobody is evicted; everybody has a (new) unique room.

### `AddBus(k)` — shift `n -> n+k`
Resident `n` moves to `n+k`. Image is `{k, k+1, ...}`, freeing rooms `0..k-1`
for the bus's `k` passengers. Passenger `m` takes room `m`.

### `AddInfiniteBus` — double `n -> 2n`
Resident `n` moves to the even room `2n`. The evens are a proper subset of `N`
with the same cardinality (`n <-> 2n` is a bijection `N -> evens`), so **all the
odd rooms** `1, 3, 5, ...` are freed at once. Seat `j` of the infinite bus takes
room `2j + 1`. A countably-infinite arrival absorbed by one move.

### `AddInfiniteBuses` — double + Cantor pairing
Countably many buses (`bus = 0, 1, 2, ...`), each with countably many seats
(`seat = 0, 1, 2, ...`). The key fact is `N × N` is countable, witnessed by the
**Cantor pairing function**, a bijection `N × N -> N`:

```
cantor(a, b) = (a + b)(a + b + 1)/2 + b
```

So the whole fleet collapses into a single stream of member indices `j`, which
then lands in the countably-infinite set of odd rooms via the same doubling move:

```
(bus b, seat s)  --cantor-->  member j  -->  room 2j + 1
```

That is why `AddInfiniteBus` and `AddInfiniteBuses` reuse the *same* `n -> 2n`
transform: freeing the odds once is enough, because `N` odd rooms can hold
`N × N` passengers.

### Why no eviction is possible
Every transform is injective, so no two residents ever collide. The hotel starts
**full** and only ever relocates residents forward, so `WhoIsInRoom(R)` is a
**total** function: every room always has exactly one occupant. `IsOccupied(R)`
is therefore always `true` after opening — that is the whole point. A full
infinite hotel stays full while still saying yes to new guests.

## Reverse lookup: who is in room `R`?

To find the occupant of a physical room, invert the transform stack from newest
to oldest. The first transform whose inverse **rejects** `R` is exactly the one
that freed it, so `R` belongs to that transform's arrival. If every inverse
succeeds, `R` traces all the way back to a founding resident. This is
`Hotel.WhoIsInRoom`.

## Run it

Requires Go 1.24+.

```bash
cd infinite-hotel-scheduler
go run .          # run the demo trace
go test ./...     # run the test suite
go test -race -cover ./...
go build ./...
```

## Files

- `transform.go` — injective room transforms (`shift`, `doubling`, `identity`).
- `placer.go` — how each arrival lays members into the rooms it freed.
- `pairing.go` — Cantor pairing `N × N -> N` and its inverse.
- `hotel.go` — the lazy allocator: arrivals, transform stack, `RoomOf`,
  `WhoIsInRoom`, `IsOccupied`.
- `request.go` — VM/container request model.
- `main.go` — the demo trace below.
- `*_test.go` — round-trip, injectivity, and pairing-bijection tests.

## Sample output

```
Hilbert's Infinite Hotel -- Cloud Scheduler
A resource allocator that is NEVER full.
============================================================

Opening state: the hotel is already FULL.
  founding residents occupy every room 0, 1, 2, 3, ...

------------------------------------------------------------
1) AddGuest -- one VM shows up; shift n -> n+1 frees room 0
------------------------------------------------------------
  alice (vm)             -> room 0      (WhoIsInRoom(0) = guest:alice#0)
  physical room 0 currently holds: guest:alice#0
  IsOccupied(0)=true  IsOccupied(1)=true  IsOccupied(1000000)=true

------------------------------------------------------------
2) AddBus(3) -- a bus of 3 containers; shift n -> n+3 frees rooms 0..2
------------------------------------------------------------
  alice (vm)             -> room 3      (WhoIsInRoom(3) = guest:alice#0)
  bus.blue seat0         -> room 0      (WhoIsInRoom(0) = bus:blue#0)
  bus.blue seat2         -> room 2      (WhoIsInRoom(2) = bus:blue#2)
  physical room 0 currently holds: bus:blue#0
  IsOccupied(0)=true  IsOccupied(1)=true  IsOccupied(1000000)=true

------------------------------------------------------------
3) AddInfiniteBus -- residents n -> 2n; the infinite bus takes the odds
------------------------------------------------------------
  alice (vm)             -> room 6      (WhoIsInRoom(6) = guest:alice#0)
  bus.blue seat0         -> room 0      (WhoIsInRoom(0) = bus:blue#0)
  bus.blue seat2         -> room 4      (WhoIsInRoom(4) = bus:blue#2)
  inf-bus.ghost seat0    -> room 1      (WhoIsInRoom(1) = inf-bus:ghost#0)
  inf-bus.ghost seat5    -> room 11     (WhoIsInRoom(11) = inf-bus:ghost#5)
  physical room 0 currently holds: bus:blue#0
  IsOccupied(0)=true  IsOccupied(1)=true  IsOccupied(1000000)=true

------------------------------------------------------------
4) AddInfiniteBuses -- countably many infinite buses via Cantor pairing
------------------------------------------------------------
  Cantor pairing (bus, seat) -> member -> odd room:
    bus 0 seat 0 -> member 0 -> room 1
    bus 0 seat 1 -> member 2 -> room 5
    bus 1 seat 0 -> member 1 -> room 3
    bus 2 seat 3 -> member 18 -> room 37
  alice (vm)             -> room 12     (WhoIsInRoom(12) = guest:alice#0)
  bus.blue seat0         -> room 0      (WhoIsInRoom(0) = bus:blue#0)
  bus.blue seat2         -> room 8      (WhoIsInRoom(8) = bus:blue#2)
  inf-bus.ghost seat0    -> room 2      (WhoIsInRoom(2) = inf-bus:ghost#0)
  inf-bus.ghost seat5    -> room 22     (WhoIsInRoom(22) = inf-bus:ghost#5)
  physical room 0 currently holds: bus:blue#0
  IsOccupied(0)=true  IsOccupied(1)=true  IsOccupied(1000000)=true

------------------------------------------------------------
Transform stack (composed, newest last)
------------------------------------------------------------
  [0] identity  (n -> n)      founding residents
  [1] shift     (n -> n+1)    admitted guest:alice
  [2] shift     (n -> n+3)    admitted bus:blue
  [3] doubling  (n -> 2n)     admitted inf-bus:ghost
  [4] doubling  (n -> 2n)     admitted inf-buses:fleet

------------------------------------------------------------
Proof: no eviction, no collision, still full
------------------------------------------------------------
  5 tracked guests occupy 5 distinct rooms -> injective, no collisions
  sampled rooms [0 1 2 3 7 42 123 10000 999999] -> all occupied: true

Every room is occupied, every guest has a unique room, and the
hotel still accepted an infinite fleet of infinite buses. Never full.
```

### Reading the trace

Watch `alice`: she enters room `0`, gets pushed to `3` by the bus, then `n -> 2n`
sends her to `6`, then the second doubling to `12`. She is relocated four times
and **never evicted** — her room is always recomputed from the composed
transform, never stored. Meanwhile every sampled physical room, up to `999999`,
still resolves to a unique occupant: the hotel is provably still full.

## Limitations (honest notes)

- Room indices are `uint64`. The demo values stay tiny, but a long chain of
  doublings or large Cantor pairs will eventually overflow `uint64`. A
  production version would use `math/big`. This is a teaching simulation, so it
  keeps the arithmetic native and fast.
- "Countably infinite" arrivals are represented lazily; only the seats you query
  are ever computed. Nothing iterates to infinity.
```
