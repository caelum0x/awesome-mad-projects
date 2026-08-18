package main

// Field defines a continuous tangent vector field on S^2.
//
// We build it by "combing" the sphere with a single global direction G
// (think: a constant breeze blowing through space). At a point p on the
// sphere the ambient direction G is projected onto the local tangent
// plane:
//
//	t(p) = G - (G . p) p
//
// t(p) is, by construction, orthogonal to p, so it always lies in the
// tangent plane of S^2 at p -- it is a genuine tangent vector field.
//
// The Hairy Ball Theorem states that no continuous tangent vector field
// on S^2 can be non-vanishing everywhere: it must have at least one zero.
// For this projected-constant field the zeros occur exactly where G is
// parallel to p, i.e. at the two antipodal points p = +/- G/|G|. Those
// are the mandatory routing singularities -- the "black hole" nodes.
type Field struct {
	G Vec3 // global combing direction (need not be a unit vector)
}

// NewField returns a combed tangent field along the given global direction.
func NewField(g Vec3) Field {
	return Field{G: g.Normalize()}
}

// TangentAt returns the tangent vector of the field at unit point p.
// The result is guaranteed to satisfy result . p == 0 (up to rounding).
func (f Field) TangentAt(p Vec3) Vec3 {
	// Remove the component of G along the surface normal p.
	return f.G.Sub(p.Scale(f.G.Dot(p)))
}

// singularityEps is the magnitude below which a tangent vector is treated
// as vanishing. Nodes at or below this threshold are forced singularities.
const singularityEps = 0.05

// IsSingular reports whether the field effectively vanishes at p.
func (f Field) IsSingular(p Vec3) bool {
	return f.TangentAt(p).Len() <= singularityEps
}

// Zeros returns the two exact analytic zeros of the field (the poles of
// the combing), independent of node placement. These are the locations the
// theorem forces to exist; real nodes near them are flagged as singular.
func (f Field) Zeros() []Vec3 {
	g := f.G.Normalize()
	return []Vec3{g, g.Scale(-1)}
}
