package main

import "math"

// Node is a network node placed on the unit sphere S^2.
type Node struct {
	ID  int
	Pos Vec3 // unit vector: a point on S^2
}

// FibonacciSphere returns n nodes spread as evenly as possible over the
// unit sphere using the Fibonacci lattice. This avoids the clustering
// that naive lat/long grids produce near the poles.
func FibonacciSphere(n int) []Node {
	nodes := make([]Node, 0, n)
	// Golden angle in radians.
	phi := math.Pi * (3.0 - math.Sqrt(5.0))
	for i := 0; i < n; i++ {
		// y goes from ~1 down to ~-1.
		y := 1.0 - (float64(i)/float64(n-1))*2.0
		radius := math.Sqrt(math.Max(0, 1.0-y*y))
		theta := phi * float64(i)
		x := math.Cos(theta) * radius
		z := math.Sin(theta) * radius
		nodes = append(nodes, Node{
			ID:  i,
			Pos: Vec3{x, y, z}.Normalize(),
		})
	}
	return nodes
}

// Neighbors returns, for each node, the IDs of its k nearest neighbors by
// great-circle (angular) distance on the sphere. This defines the network
// topology over which packets hop.
func Neighbors(nodes []Node, k int) [][]int {
	adj := make([][]int, len(nodes))
	for i := range nodes {
		type cand struct {
			id   int
			dist float64
		}
		cands := make([]cand, 0, len(nodes)-1)
		for j := range nodes {
			if i == j {
				continue
			}
			cands = append(cands, cand{j, AngularDist(nodes[i].Pos, nodes[j].Pos)})
		}
		// Simple selection of k smallest distances.
		for a := 0; a < k && a < len(cands); a++ {
			min := a
			for b := a + 1; b < len(cands); b++ {
				if cands[b].dist < cands[min].dist {
					min = b
				}
			}
			cands[a], cands[min] = cands[min], cands[a]
		}
		lim := k
		if lim > len(cands) {
			lim = len(cands)
		}
		ids := make([]int, 0, lim)
		for a := 0; a < lim; a++ {
			ids = append(ids, cands[a].id)
		}
		adj[i] = ids
	}
	return adj
}

// AngularDist returns the great-circle angle (radians) between two unit
// vectors on the sphere.
func AngularDist(a, b Vec3) float64 {
	d := a.Dot(b)
	if d > 1 {
		d = 1
	} else if d < -1 {
		d = -1
	}
	return math.Acos(d)
}
