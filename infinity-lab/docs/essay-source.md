# Source Essay — Companion & Provenance

> **Original work:** *Mathematics Behind Jujutsu Kaisen: Gojo Satoru's Infinity*
> **Author:** Achmad Roykhan Sabiq
> **Venue:** Oxford University Mathematics Essay Competition 2026 · March 2026
> **PDF:** hosted on Tom Rocks Maths —
> <https://tomrocksmaths.com/wp-content/uploads/2026/06/achmad-roykhan-sabiq_essay_competition_2026-achmad-roykhan-sabiq.pdf>
> **Local copy:** `mad-man-projects/achmad-roykhan-sabiq_essay_competition_2026-achmad-roykhan-sabiq.pdf` (10 pages — the authoritative full text)

**What this file is.** A faithful section-by-section *companion* to the essay: a summary of each section's argument (in my own words), the **mathematical statements and formulas reproduced exactly**, the figures described, the reference list, and a mapping from each section to the code that implements it. It is **not** a verbatim reproduction of the essay's prose — the copyright in the written text belongs to the author, and the complete original lives in the PDF above. Read this to navigate the code; read the PDF for the author's full writing.

The essay's thesis: take Gojo's *Infinity* seriously as a mathematical object and interrogate it through **four lenses**, each reaching its own verdict. The verdicts disagree, and that disagreement is the point.

---

## §1 Introduction

Sets up Infinity as Gojo describes it: between any attacker and Gojo there is always a distance; that distance is halved, then halved again, forever, so no attack completes the infinite sequence of steps and Gojo is never reached. The essay immediately connects this to **Zeno of Elea** — the same 2,500-year-old argument — and previews that geometric series plus Lebesgue's theory of measurement will show Infinity is *stranger and more fragile* than it looks, and will explain how Ryomen Sukuna defeated it.

- **Figure 1** — anime still of Infinity stopping an attack (JJK Wiki, *Limitless*).
- **Figure 2** — side-by-side of Gojo's Infinity (distance halved each step, attacker never arrives) and Zeno's Achilles-and-tortoise, framed as the *same structure*: infinitely many steps between pursuer and target.

## §2 Zeno's Paradoxes

States the Achilles-and-tortoise paradox (c. 450 BCE): before Achilles catches the tortoise he must reach its current position, by which time it has moved on — infinitely many stages, so "how can anyone complete an infinite number of anything?" The argument is *logically watertight yet empirically wrong* — Achilles does catch up. Gojo's technique weaponizes exactly this paradox. To learn whether it can be defeated, the essay asks what is wrong (and right) about Zeno.

- **Figure 3** — the unit square tiled by ½, ¼, ⅛, 1/16, … regions, posing: does `1/2 + 1/4 + 1/8 + 1/16 + ... = 1` exactly?

## §3 Geometric Series → **verdict: FRAGILE**

The tiling answers Zeno: the pieces fill the square exactly, so the infinite sum is a finite whole. Partial sums:

$$S_n = \tfrac12 + \tfrac14 + \cdots + \tfrac{1}{2^n} = 1 - \tfrac{1}{2^n}.$$

As `n → ∞`, `1/2^n → 0`, so `S_n → 1`. General geometric series:

$$\sum_{n=1}^{\infty} a\,r^{\,n-1} = \frac{a}{1-r}, \qquad |r| < 1.$$

The Zeno series is the case `a = 1/2, r = 1/2`, giving `(1/2)/(1 − 1/2) = 1`. Crucially the essay notes the **travel times** also form a geometric series (each step taking half as long), so their sum is finite too — Achilles arrives in finite *time*, not just finite distance. Under this lens Infinity "offers no defence whatsoever… simply collapses." It closes by asking a sharper question: the subdivision points `1/2, 3/4, 7/8, …` form an infinite set — *how large*, precisely, is that set? That needs different mathematics.

- **Figure 4** — `S_n = 1 − (1/2)^n` as a bar chart (0.500, 0.750, 0.875, …) and as a curve approaching the dashed line `S = 1`.

→ **Code:** `gojo_infinity/core/zeno.py` — exact `Fraction` partial sums `S_1..S_8`, `a/(1−r) = 1` exactly, the strict-positivity certificate that `(1/2)^n > 0` for every finite `n` (exact, immune to IEEE underflow at `n = 1075`), the ε–N oracle, and the arrival-time series with speed `v` as an explicit parameter.

## §4 The Lebesgue Measure → **verdict: FRAGILE (negligible)**

The subdivision set is countably infinite. To measure it, the essay introduces the **Lebesgue outer measure** via coverings:

$$m^*(A) = \inf\left\{ \sum_{n=1}^{\infty} |I_n| \;:\; A \subseteq \bigcup_{n=1}^{\infty} I_n \right\},$$

the infimum of total lengths over all countable open-interval covers. Basic facts stated: `m([a,b]) = b − a`, `m(∅) = 0`, and countable additivity `m(⋃ E_n) = Σ m(E_n)` for disjoint measurable sets.

**Theorem (reproduced proof).** For `Z = { z_n = 1 − 1/2^n : n ≥ 1 } = {1/2, 3/4, 7/8, …}`, `m(Z) = 0`.
*Proof.* Fix `ε > 0`. Cover each `z_n` by

$$I_n = \left( z_n - \frac{\varepsilon}{2^{\,n+1}},\; z_n + \frac{\varepsilon}{2^{\,n+1}} \right), \qquad |I_n| = \frac{\varepsilon}{2^n}.$$

Then `{I_n}` covers `Z` and

$$\sum_{n=1}^{\infty} |I_n| = \sum_{n=1}^{\infty} \frac{\varepsilon}{2^n} = \varepsilon \sum_{n=1}^{\infty} \frac{1}{2^n} = \varepsilon \cdot 1 = \varepsilon.$$

Since `ε > 0` is arbitrary, the infimum of covering lengths is `0`, so `m(Z) = 0`. ∎

The essay stresses this holds for *any* countably infinite set: infinitely many points can occupy zero total length — the count and the length are independent. Implication: Infinity's barrier is a **null set**, occupying no space at all.

- **Figure 5** — the covering construction: each `z_n` boxed by `I_n` of length `ε/2^n`, totals `ε`.
- **Figure 6** — Infinity *looks* solid, but measure theory reveals countably many points with `m(Z) = 0`; so what actually stops the attack? "The answer lies in the geometry of space itself."

→ **Code:** `gojo_infinity/core/measure.py` — exact `Fraction` covering total `= ε`, the `m(Z) = 0` argument, and the documented Lebesgue facts.

## §5 Riemannian Geometry: Infinity as a Metric Transformation → **verdict: FORMIDABLE**

If the barrier has measure zero, why does every attack still stall? The essay cites the **2021 RIKEN × Gege Akutami collaboration (Jump GIGA)**: Infinity is not a subdivision of distance but a **transformation of the metric** by which distance is measured. Euclidean length `ds² = dx² + dy² + dz²` becomes, on a Riemannian manifold,

$$ds^2 = \sum_{ij} g_{ij}\, dx_i\, dx_j,$$

with metric tensor `g_ij`. The RIKEN team's proposed form uses a **Gaussian (RBF) kernel**:

$$K(x,y) = \exp\!\left(-\frac{|x-y|^2}{\sigma^2}\right), \qquad g_{ij} = \frac{K(x + dx_i,\, x + dx_j)}{dx_i \cdot dx_j}.$$

The kernel equals 1 when `x = y` and decays with distance; embedding it in `g_ij` makes the geometry highly non-linear. Far from Gojo `g_ij ≈ I` so `ds ≈ dx`; as the attacker's coordinates approach Gojo's (`x → y`) the tensor blows up. The essay's worked figures: a physical step `dx = 0.1` far from Gojo feels like `ds ≈ 0.1`, but near Gojo the same `dx = 0.1` is stretched to `ds = 10`, then `ds = 100`, scaling without bound — Euclidean position barely changes while felt distance diverges. It highlights the irony that this kernel comes from **machine learning** (image/music similarity), not physics. It then abstracts to a single **conformal factor** `Ω(x)` — the local ruler-stretch between attacker and Gojo — flat far away, rising steeply near, and (critically for §6) *smooth and unbroken across the whole space*.

- **Figure 7** — the RIKEN "Abyss of Math Course" handwritten board (Hino, RIKEN; Jump GIGA Summer 2021).
- **Figure 8** — the metric function `g(x)`: flat `g ≈ 1.0` far (Step A at `x = 0.1`, `dx = 0.1 → ds ≈ 0.10`), rising to `g ≈ 4.1` near (Step B at `x = 0.8`, `dx = 0.1 → ds ≈ 0.20`), and `g → ∞` at Gojo (`x = 1`).

→ **Code:** `gojo_infinity/core/riemannian.py` — the RBF kernel `K(x,y)`, the conformal factor `Ω(x) = 1 + λ·exp(−(x_g−x)²/σ²)/(x_g−x)` calibrated (σ ≈ 0.35, λ ≈ 0.284) so `g(0.1) ≈ 1.0 / ds ≈ 0.10` and `g(0.8) ≈ 4.1 / ds ≈ 0.20`, and the **improper geodesic** `L = ∫ Ω dx` that returns `math.inf` as the limit → Gojo. `gojo_infinity/accel/numpy_backend.py` vectorizes `Ω`, `g`, `ds`; `adapters/viz.py` renders `artifacts/gojo_metric_blowup.png`. **Enhancement:** `gojo_infinity/core/riemannian_manifold.py` extends this to a genuine 2-D conformally-flat Riemannian manifold (`g_ij = Ω² δ_ij`, Gojo at the origin) with a real RK4 geodesic solver — closed-form vs finite-difference Christoffel cross-check, affine-energy conservation, exact radial parity with the 1-D lens, felt-length divergence, and a light-bending deflection; `accel/manifold_backend.py` batch-integrates many geodesics and `adapters/viz.py` renders `artifacts/gojo_geodesic_bundle.png` and `artifacts/gojo_length_divergence.png`. **3-D (n-D) generalisation:** `gojo_infinity/core/riemannian_manifold_nd.py` (`ConformalMetricND`) lifts the solver to arbitrary dimension — the same conformal Christoffel / geodesic closed forms operate on `n`-vectors, so ONE code path serves 1-D, 2-D and 3-D (the geodesic RHS `conformal_acceleration` has a single implementation, which the 2-D solver now delegates to). In 3-D it verifies the Christoffel cross-check, affine-energy conservation, exact radial parity with the 1-D lens, the **planarity symmetry** (a geodesic stays in the 2-plane spanned by its initial position, initial velocity and Gojo), an inward light-bending deflection, and the felt-length divergence; `accel/manifold_backend.py` (`integrate_geodesics_batch_nd`) batch-integrates 3-D geodesics and `adapters/viz.py` renders `artifacts/gojo_geodesic_3d.png` (`mpl_toolkits.mplot3d`). **Animations:** `gojo_infinity/adapters/animate.py` (matplotlib `FuncAnimation` + `PillowWriter`, deferred behind matplotlib **and** Pillow) renders `artifacts/gojo_geodesic_approach.gif` (a geodesic bending around Gojo, slowing as its accumulated felt length climbs and never arriving) and `artifacts/gojo_never_arrives.gif` (the Zeno steps `x_n = 1 − (1/2)ⁿ` approaching Gojo forever, residual `(1/2)ⁿ > 0` while the felt length diverges). `gojo_infinity/adapters/animate_3d.py` adds `artifacts/gojo_geodesic_3d_rotating.gif` — a few geodesics bending around Gojo in `R³` (`ConformalMetricND`, `mpl_toolkits.mplot3d`) while the **camera orbits** the scene (the azimuth advances and the elevation sweeps each frame via `ax.view_init`). **MP4 export:** the same `FuncAnimation` setups are re-encoded through `matplotlib.animation.FFMpegWriter` (deferred behind an **ffmpeg** binary on `PATH`, probed at call time) as `save_geodesic_approach_mp4` → `artifacts/gojo_geodesic_approach.mp4` and `save_geodesic_3d_rotating_mp4` → `artifacts/gojo_geodesic_3d_rotating.mp4`. The CLI `animate OUTDIR` subcommand emits the two baseline GIFs by default; `--rotate` adds the rotating 3-D GIF and `--mp4` adds both MP4s.

## §6 Mahoraga's Adaptation and the World Cutting Slash → **verdict: FALLS (topology)**

Two facts are now in hand: the subdivision points are measure-zero, and the kernel metric makes the barrier feel impenetrable from *within* the distorted geometry. Sukuna's route goes deeper than either. Mahoraga adapts to any technique; against Infinity "the wheel turned five times" before it found an answer — it stopped targeting Gojo and started targeting the **space around him**, bypassing Infinity entirely. Sukuna copied this with a modified Dismantle aimed at *reality itself*: the World Cutting Slash. The precise mathematical content: Infinity depends on `Ω(x)` being **continuous** across space; every ordinary attack must cross the points of `Z` one by one under the amplified metric. The slash instead **severs the continuity of `Ω(x)` at a single point**, rendering the metric undefined across the cut. A cut that destroys continuity "does not need to cross any particular distance" — the barrier is not penetrated; the space carrying it is torn. Infinity has a blind spot: nothing in its construction defends against an operation that ignores its points and severs its space.

- **Figure 9** — Mahoraga adapting (JJK Wiki).
- **Figure 10** — the conformal factor `Ω(x)`: **left**, smooth/continuous (Infinity intact, steep near Gojo); **right**, `Ω(x)` with its continuity severed at a point (metric undefined across the cut — "continuity destroyed").
- **Figure 11** — Sukuna's World Cutting Slash defeating Infinity (JJK Wiki).

→ **Code:** `gojo_infinity/core/topology.py` — continuity classification of `Ω`, the severing operation, the three type-distinct return semantics (finite / `+inf` / `None`), and the proof that `[x₀, x₁] \ {c}` is disconnected into exactly two components.

## §7 Conclusion

Whether Infinity is "mathematically undefeatable" depends on the language you ask in. Under geometric series and Lebesgue measure it is **fragile** — a paradox of limits and a measure-zero set (`m(Z) = 0`) that can be surrounded and made negligible, mirroring Mahoraga's adaptation. Under Riemannian geometry it is **formidable** — an exponential distortion of the metric. Under topology it **falls** — sever the continuity of the supporting space and it collapses, as the World Cutting Slash did. The essay's honest caveat: applying pure mathematics to a fictional universe has limits — "Cursed Energy" and authorial intent do not obey the axioms of real analysis; the RIKEN model translates the manga's logic but cannot cage magic in an equation. Still, it took four of the deepest ideas in modern mathematics — **convergence, measure, metric geometry, topology** — to see why Infinity stood and why it could fall.

→ **Code:** `gojo_infinity/core/verdicts.py` and `demo.py` — the four-lens table **Fragile / Fragile / Formidable / Falls** plus the cursed-energy caveat.

---

## References (as listed in the essay)

1. R. G. Bartle, *The Elements of Integration and Lebesgue Measure*, John Wiley & Sons, 1996, p. 19.
2. R. G. Bartle and D. R. Sherbert, *Introduction to Real Analysis*, 4th ed., John Wiley & Sons, 2011, pp. 94–101.
3. J. M. Lee, *Introduction to Riemannian Manifolds*, 2nd ed., Springer, 2018.
4. J. R. Munkres, *Topology*, 2nd ed., Prentice Hall, 2000.
5. Jujutsu Kaisen Wiki, *Satoru Gojo*, <https://jujutsu-kaisen.fandom.com/wiki/Satoru_Gojo>, retrieved March 2026.
6. Jujutsu Kaisen Wiki, *Limitless*, <https://jujutsu-kaisen.fandom.com/wiki/Limitless>, retrieved March 2026.
7. Jujutsu Kaisen Wiki, *Eight-Handled Sword Divergent Sila Divine General Mahoraga*, <https://jujutsu-kaisen.fandom.com/wiki/Eight-Handled_Sword_Divergent_Sila_Divine_General_Mahoraga>, retrieved March 2026.
8. Jujutsu Kaisen Wiki, *Ryomen Sukuna*, <https://jujutsu-kaisen.fandom.com/wiki/Sukuna>, retrieved March 2026.
9. Tempenensis, *Jujutsu Kaisen: Abyss of Math Course, Part 2* (translation of Jump GIGA Summer 2021, Shueisha), <https://tempenensis.tumblr.com/post/658588987455422464>, retrieved March 2026.

---

*Attribution:* all mathematical framing above is due to Achmad Roykhan Sabiq's essay; Jujutsu Kaisen and its characters are © Gege Akutami / Shueisha. This companion exists to link the paper to the `gojo_infinity` implementation. For the author's complete text, see the PDF in the workspace root.
