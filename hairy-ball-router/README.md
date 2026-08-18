# Hairy Ball Theorem Router

A small, self-contained Go simulation that models a network as points on the
unit sphere **S²** and routes packets by following a **continuous tangent
vector field**. The [Hairy Ball Theorem](https://en.wikipedia.org/wiki/Hairy_ball_theorem)
guarantees that such a field must vanish somewhere, which forces at least one
node where routing physically cannot proceed — a "black hole" node where
packets stall and must be dropped or handed to a fallback.

This is a **simulation only**. No packets, sockets, or destructive operations
are involved.

## Concept

- **Nodes on a sphere.** Network nodes are placed on S² using a *Fibonacci
  lattice* (golden-angle spiral), which spreads points far more evenly than a
  naive latitude/longitude grid.
- **Routing = a tangent vector field.** Every node forwards a packet in the
  direction the field points at its location. Forwarding is greedy: a node
  hands the packet to the neighbor whose direction (projected onto the local
  tangent plane) best aligns with the field.
- **Forced singularities.** Where the field magnitude is ~0, a node has *no
  forwarding direction*. It cannot route. Packets that reach it stall.

## The math (honest version)

The **Hairy Ball Theorem** states:

> There is no non-vanishing continuous tangent vector field on the 2-sphere S².

Equivalently: *you cannot comb a hairy ball flat without creating at least one
cowlick.* Any continuous tangent field on S² has **≥ 1 zero**. (More precisely,
the sum of the indices of its zeros equals the Euler characteristic of S²,
which is **2** — so a "generic" field has two simple zeros, e.g. a source and a
sink.)

### The field we use

We "comb" the sphere with a single global ambient direction **G** (here
`G = (0, 1, 0)`, i.e. "north"). At a surface point **p** (a unit vector) we
project **G** onto the tangent plane by removing its normal component:

```
t(p) = G − (G · p) p
```

Because `t(p) · p = 0` by construction, `t(p)` always lies in the tangent
plane of S² at `p` — it is a genuine, continuous tangent vector field.

Its magnitude is `|t(p)| = |G| · sin(θ)`, where `θ` is the angle between `G`
and `p`. This is **zero exactly when `p` is parallel to `G`**, i.e. at the two
antipodal poles:

```
p = +G/|G|   (the sink  — flow lines converge here)
p = −G/|G|   (the source — flow lines diverge here)
```

These two points are the **mandatory singularities**. The theorem does not
merely *permit* them — it *forbids* their absence. The simulation confirms this
empirically by scanning every node and reporting the minimum field magnitude
(which lands on the pole nodes at ~0).

## Files

| File         | Responsibility                                             |
|--------------|------------------------------------------------------------|
| `vec.go`     | Immutable 3D vector math (add, dot, cross, normalize).     |
| `sphere.go`  | Fibonacci-sphere node placement and k-nearest topology.    |
| `field.go`   | The tangent vector field, zeros, and singularity test.     |
| `router.go`  | Greedy field-following router with drop/fallback handling. |
| `main.go`    | Builds the network, locates singularities, routes packets. |

## Run

Requires Go (developed against Go 1.24).

```bash
cd hairy-ball-router
go build ./...      # compile everything
go vet ./...        # static checks
go run .            # run the simulation
```

## Sample output

```
=== Hairy Ball Theorem Router (S^2 routing simulation) ===
nodes=300  neighbors/node=6  combing-direction=( 0.000, 1.000, 0.000)
Hairy Ball Theorem: any continuous tangent vector field on S^2
has at least one zero -> at least one forced singularity.
fallback node = 144 @ ( 0.999, 0.037, 0.019)

--- Mandatory singularities (field zeros) ---
Analytic field zeros (poles of the combing): ( 0.000, 1.000, 0.000) and (-0.000,-1.000,-0.000)
min field magnitude over nodes = 0.000000 at node 0 ( 0.000, 1.000, 0.000)
Nodes on singularities (|field| <= 0.050): [0 299]
    node 0 @ ( 0.000, 1.000, 0.000)  |field|=0.000000  <- BLACK HOLE
    node 299 @ ( 0.000,-1.000, 0.000)  |field|=0.000000  <- BLACK HOLE
=> theorem confirmed empirically: 2 forced singularity(ies).

--- Routing packets (greedy field-following) ---
packet 299 -> 0 : FALLBACK (handed to designated node)
    trace: [299 144] (trapped-at=299)
packet 144 -> 0 : DELIVERED
    trace: [144 110 76 42 21 8 3 0] (trapped-at=-1)
packet 144 -> 161 : FALLBACK (handed to designated node)
    trace: [144 110 76 42 21 8 3 0 144] (trapped-at=0)
packet 299 -> 142 : FALLBACK (handed to designated node)
    trace: [299 144] (trapped-at=299)
packet 142 -> 299 : FALLBACK (handed to designated node)
    trace: [142 108 74 40 19 6 1 0 144] (trapped-at=0)

summary: delivered=1 dropped=0 fallback=4

with fallback disabled (fallback=-1):
packet 144 -> 161 : DROPPED (forced singularity)
    trace: [144 110 76 42 21 8 3 0] (trapped-at=0)

Packets trapped at a black-hole node are exactly the routing
failures forced by the Hairy Ball Theorem.
```

### Reading the results

- **Singularity locations.** With 300 nodes, node **0** lands on the north
  pole `(0, 1, 0)` and node **299** on the south pole `(0, −1, 0)`. Both report
  `|field| = 0` — the two forced zeros the theorem promises.
- **A delivered packet.** `144 -> 0`:
  `[144 110 76 42 21 8 3 0]`. Node 144 sits near the equator; following the
  field "uphill" along a meridian sweeps the packet straight into the north-pole
  sink, which *is* the destination. Delivered.
- **A trapped packet.** `144 -> 161`:
  `[144 110 76 42 21 8 3 0 144]`. The field carries the packet to node 0 (the
  black hole). Node 0 has no forwarding direction, so the packet is handed to
  the fallback node 144. Its true destination (161) is off the flow line and is
  never reached by pure field-following.
- **Source-pole stall.** `299 -> 0`: node 299 sits on the *source* pole; the
  field vanishes there too, so the packet stalls immediately and goes to
  fallback.
- **Forced drop.** With `fallback = -1`, the same `144 -> 161` packet has
  nowhere to go and is **DROPPED (forced singularity)** at node 0.

Every routing failure in this run is caused by a packet flowing into one of the
two zeros that the Hairy Ball Theorem *forces* to exist. Change the combing
direction `G` in `main.go` and the poles (and therefore the black-hole nodes)
move — but they never disappear. That is the whole point of the theorem.
