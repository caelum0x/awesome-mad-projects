# mobius-rickness — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/mobius_rickness/`](../infinity-lab/packages/mobius_rickness/)
➡️ **Docs:** `infinity-lab/packages/mobius_rickness/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/mobius_rickness/README.md`](../infinity-lab/packages/mobius_rickness/README.md)

The monorepo version is the src-layout package that shares the internal `commons`
package and includes everything added after the prototype: the three
cross-validating curvature paths, the real Central Finite Curve zero-set tracer,
the torus surface, the numpy fast-path (with parity tests), the SCMS/Eberly ridge
(the second Central Finite Curve formalization), and matplotlib PNG export.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/mobius_rickness        # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  python3 -m mobius_rickness.demo                  # demo
# optional numpy/matplotlib features (ridge, PNGs):
./.venv/bin/python -m pytest packages/mobius_rickness
```
