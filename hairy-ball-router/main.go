// Command hairy-ball-router is a simulation of packet routing over a network
// whose nodes live on the sphere S^2 and whose forwarding rule is a continuous
// tangent vector field.
//
// The Hairy Ball Theorem guarantees that such a field must vanish somewhere,
// producing at least one forced "black hole" node where routing stalls. This
// program builds the sphere network, locates the mandatory singularities,
// routes several packets, and reports which ones get trapped.
package main

import (
	"fmt"
	"math"
)

const (
	numNodes    = 300 // nodes placed on the sphere via Fibonacci lattice
	numNeighbor = 6   // topology: k nearest neighbors per node
)

func main() {
	// 1. Build the sphere network.
	nodes := FibonacciSphere(numNodes)
	adj := Neighbors(nodes, numNeighbor)

	// 2. Comb the sphere with a global direction. The field is the projection
	//    of this direction onto each node's tangent plane.
	field := NewField(Vec3{X: 0, Y: 1, Z: 0})

	// 3. Pick a fallback node far from the singularities (near the equator).
	fallback := nearestNode(nodes, Vec3{X: 1, Y: 0, Z: 0})
	r := NewRouter(nodes, adj, field, fallback)

	printHeader(nodes, field, r, fallback)

	// 4. Prove the theorem empirically and report the singular nodes.
	printSingularities(nodes, field, r)

	// 5. Route several packets and report outcomes.
	printRouting(nodes, r)
}

// nearestNode returns the ID of the node closest to target on the sphere.
func nearestNode(nodes []Node, target Vec3) int {
	t := target.Normalize()
	best, bestDist := -1, math.MaxFloat64
	for _, n := range nodes {
		if d := AngularDist(n.Pos, t); d < bestDist {
			bestDist, best = d, n.ID
		}
	}
	return best
}

func printHeader(nodes []Node, field Field, r Router, fallback int) {
	fmt.Println("=== Hairy Ball Theorem Router (S^2 routing simulation) ===")
	fmt.Printf("nodes=%d  neighbors/node=%d  combing-direction=%s\n",
		len(nodes), numNeighbor, fmtVec(field.G))
	fmt.Printf("Hairy Ball Theorem: any continuous tangent vector field on S^2\n")
	fmt.Printf("has at least one zero -> at least one forced singularity.\n")
	fmt.Printf("fallback node = %d @ %s\n\n", fallback, fmtVec(nodes[fallback].Pos))
}

func printSingularities(nodes []Node, field Field, r Router) {
	fmt.Println("--- Mandatory singularities (field zeros) ---")
	zeros := field.Zeros()
	fmt.Printf("Analytic field zeros (poles of the combing): %s and %s\n",
		fmtVec(zeros[0]), fmtVec(zeros[1]))

	// Empirical check: find the minimum field magnitude over all nodes and
	// list every node the router flagged as singular.
	minMag, minID := math.MaxFloat64, -1
	for _, n := range nodes {
		if m := field.TangentAt(n.Pos).Len(); m < minMag {
			minMag, minID = m, n.ID
		}
	}
	fmt.Printf("min field magnitude over nodes = %.6f at node %d %s\n",
		minMag, minID, fmtVec(nodes[minID].Pos))

	sing := r.SingularNodes()
	if len(sing) == 0 {
		// Should never happen: the theorem forbids a non-vanishing field.
		fmt.Printf("WARNING: no node fell within eps=%.3f of a zero, but one\n",
			singularityEps)
		fmt.Printf("MUST exist -> nearest node %d is the effective black hole.\n\n", minID)
		return
	}
	fmt.Printf("Nodes on singularities (|field| <= %.3f): %v\n", singularityEps, sing)
	for _, id := range sing {
		fmt.Printf("    node %d @ %s  |field|=%.6f  <- BLACK HOLE\n",
			id, fmtVec(nodes[id].Pos), field.TangentAt(nodes[id].Pos).Len())
	}
	fmt.Printf("=> theorem confirmed empirically: %d forced singularity(ies).\n\n", len(sing))
}

func printRouting(nodes []Node, r Router) {
	fmt.Println("--- Routing packets (greedy field-following) ---")

	// Choose sources/destinations spread around the sphere, including cases
	// that flow into the sink singularity and get trapped.
	south := nearestNode(nodes, Vec3{X: 0, Y: -1, Z: 0})
	north := nearestNode(nodes, Vec3{X: 0, Y: 1, Z: 0})
	eqA := nearestNode(nodes, Vec3{X: 1, Y: 0, Z: 0})
	eqB := nearestNode(nodes, Vec3{X: -1, Y: 0, Z: 0})
	eqC := nearestNode(nodes, Vec3{X: 0, Y: 0, Z: 1})

	pairs := [][2]int{
		{south, north}, // flows with the comb toward the north sink
		{eqA, north},    // equator up to the sink pole
		{eqA, eqB},      // across the sphere: likely swept into the sink
		{south, eqC},    // destination off the flow line
		{eqC, south},    // against the comb toward the source pole
	}

	var delivered, dropped, fell int
	for _, p := range pairs {
		res := r.Route(p[0], p[1])
		fmt.Println(res.TraceString())
		switch res.Status {
		case Delivered:
			delivered++
		case Dropped:
			dropped++
		case Fallback:
			fell++
		}
	}
	fmt.Printf("\nsummary: delivered=%d dropped=%d fallback=%d\n",
		delivered, dropped, fell)

	// Same trapped packet, but with no fallback configured: it is force-dropped.
	noFallback := NewRouter(r.Nodes, r.Adj, r.Field, -1)
	res := noFallback.Route(eqA, eqB)
	fmt.Println("\nwith fallback disabled (fallback=-1):")
	fmt.Println(res.TraceString())

	fmt.Println("\nPackets trapped at a black-hole node are exactly the routing")
	fmt.Println("failures forced by the Hairy Ball Theorem.")
}

func fmtVec(v Vec3) string {
	return fmt.Sprintf("(% .3f,% .3f,% .3f)", v.X, v.Y, v.Z)
}
