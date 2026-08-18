# central-finite-curve — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/central_finite_curve/`](../infinity-lab/packages/central_finite_curve/)
➡️ **Package README:** [`infinity-lab/packages/central_finite_curve/README.md`](../infinity-lab/packages/central_finite_curve/README.md)
➡️ **Landing page & gallery:** [`infinity-lab/index.html`](../infinity-lab/index.html) · [`infinity-lab/gallery/index.html`](../infinity-lab/gallery/index.html)

The monorepo version is the src-layout package sharing the internal `commons`
package (seeded RNG, numerics, ASCII/PNG rendering). It models a simulated
multiverse, scores each universe's **Rickness**, and extracts the **Central
Finite Curve** as the near-maximal epsilon band — a *third* reading of the
Central Finite Curve idea, complementing `mobius_rickness`'s two readings
(the zero-set `R⁻¹(0)` and the SCMS ridge). It adds an optional numpy fast-path,
a matplotlib projection PNG, and a portal-gun walk GIF/MP4.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/central_finite_curve          # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/central_finite_curve/src \
  python3 -m central_finite_curve.demo                   # demo
# optional numpy/matplotlib features (PNG, walk GIF/MP4):
./.venv/bin/python -m pytest packages/central_finite_curve
```
