package main

import "math"

// Vec3 is a point or vector in 3D space. Values are immutable: every
// operation returns a new Vec3 rather than mutating the receiver.
type Vec3 struct {
	X, Y, Z float64
}

// Add returns a + b.
func (a Vec3) Add(b Vec3) Vec3 {
	return Vec3{a.X + b.X, a.Y + b.Y, a.Z + b.Z}
}

// Sub returns a - b.
func (a Vec3) Sub(b Vec3) Vec3 {
	return Vec3{a.X - b.X, a.Y - b.Y, a.Z - b.Z}
}

// Scale returns a * s.
func (a Vec3) Scale(s float64) Vec3 {
	return Vec3{a.X * s, a.Y * s, a.Z * s}
}

// Dot returns the dot product a . b.
func (a Vec3) Dot(b Vec3) float64 {
	return a.X*b.X + a.Y*b.Y + a.Z*b.Z
}

// Cross returns the cross product a x b.
func (a Vec3) Cross(b Vec3) Vec3 {
	return Vec3{
		a.Y*b.Z - a.Z*b.Y,
		a.Z*b.X - a.X*b.Z,
		a.X*b.Y - a.Y*b.X,
	}
}

// Len returns the Euclidean length of the vector.
func (a Vec3) Len() float64 {
	return math.Sqrt(a.Dot(a))
}

// Normalize returns a unit vector in the same direction. A zero vector
// is returned unchanged to avoid division by zero.
func (a Vec3) Normalize() Vec3 {
	l := a.Len()
	if l == 0 {
		return a
	}
	return a.Scale(1 / l)
}
