package main

import "fmt"

// Status is the outcome of routing a single packet.
type Status int

const (
	// Delivered means the packet reached its destination node.
	Delivered Status = iota
	// Dropped means the packet reached a forced singularity (a "black hole"
	// node) or entered a loop and no fallback was available.
	Dropped
	// Fallback means the packet stalled at a singularity but was handed to
	// the designated fallback node for special handling.
	Fallback
)

func (s Status) String() string {
	switch s {
	case Delivered:
		return "DELIVERED"
	case Dropped:
		return "DROPPED (forced singularity)"
	case Fallback:
		return "FALLBACK (handed to designated node)"
	default:
		return "UNKNOWN"
	}
}

// RouteResult records what happened to one packet.
type RouteResult struct {
	Src, Dst  int
	Path      []int
	Status    Status
	TrappedAt int // node ID of the singularity that trapped the packet, or -1
}

// maxHops bounds the walk so a packet caught in a cycle terminates.
const maxHops = 512

// Router greedily forwards packets along the tangent field over the sphere
// network. At each node it steps to the neighbor whose direction on the
// tangent plane best aligns with the field's local forwarding direction.
type Router struct {
	Nodes    []Node
	Adj      [][]int
	Field    Field
	Singular map[int]bool // node IDs whose field magnitude ~ 0
	Fallback int          // designated node to receive trapped packets, or -1
}

// NewRouter builds a router and pre-computes which nodes sit on singularities.
func NewRouter(nodes []Node, adj [][]int, field Field, fallback int) Router {
	sing := make(map[int]bool)
	for _, n := range nodes {
		if field.IsSingular(n.Pos) {
			sing[n.ID] = true
		}
	}
	return Router{
		Nodes:    nodes,
		Adj:      adj,
		Field:    field,
		Singular: sing,
		Fallback: fallback,
	}
}

// SingularNodes returns the sorted-by-appearance list of singular node IDs.
func (r Router) SingularNodes() []int {
	ids := make([]int, 0, len(r.Singular))
	for _, n := range r.Nodes {
		if r.Singular[n.ID] {
			ids = append(ids, n.ID)
		}
	}
	return ids
}

// bestNeighbor returns the neighbor whose tangent-plane step direction best
// aligns with the field at cur. It also reports the alignment score.
func (r Router) bestNeighbor(cur int) (int, float64) {
	pos := r.Nodes[cur].Pos
	t := r.Field.TangentAt(pos).Normalize()
	best, bestScore := -1, -2.0
	for _, nb := range r.Adj[cur] {
		step := r.Nodes[nb].Pos.Sub(pos)
		// Project the hop onto the tangent plane at cur.
		stepT := step.Sub(pos.Scale(step.Dot(pos))).Normalize()
		score := stepT.Dot(t)
		if score > bestScore {
			bestScore, best = score, nb
		}
	}
	return best, bestScore
}

// Route walks a packet from src toward dst by following the field. Delivery
// happens if dst is reached (either landed on or offered as a neighbor).
// Reaching a singular node, or revisiting a node (a loop), ends the walk;
// the packet is then dropped or handed to the fallback node.
func (r Router) Route(src, dst int) RouteResult {
	path := []int{src}
	visited := map[int]bool{src: true}
	cur := src

	for hop := 0; hop < maxHops; hop++ {
		if cur == dst {
			return RouteResult{src, dst, path, Delivered, -1}
		}
		// A node sitting on a field zero cannot forward: it is a black hole.
		if r.Singular[cur] {
			return r.trap(src, dst, path, cur)
		}
		next, _ := r.bestNeighbor(cur)
		if next == dst {
			path = append(path, next)
			return RouteResult{src, dst, path, Delivered, -1}
		}
		if next < 0 || visited[next] {
			// Dead end or loop: the flow has stalled near a singularity.
			return r.trap(src, dst, path, cur)
		}
		visited[next] = true
		path = append(path, next)
		cur = next
	}
	return r.trap(src, dst, path, cur)
}

// trap resolves a stalled packet: hand it to the fallback if one exists and
// it is not itself the trap, otherwise drop it.
func (r Router) trap(src, dst int, path []int, at int) RouteResult {
	if r.Fallback >= 0 && r.Fallback != at {
		return RouteResult{src, dst, append(path, r.Fallback), Fallback, at}
	}
	return RouteResult{src, dst, path, Dropped, at}
}

// TraceString renders a routing result as a compact human-readable line.
func (rr RouteResult) TraceString() string {
	return fmt.Sprintf("packet %d -> %d : %s\n    trace: %v (trapped-at=%d)",
		rr.Src, rr.Dst, rr.Status, rr.Path, rr.TrappedAt)
}
