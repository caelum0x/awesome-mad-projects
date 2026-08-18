# gojo-infinity — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/gojo_infinity/`](../infinity-lab/packages/gojo_infinity/)
➡️ **Docs:** `infinity-lab/packages/gojo_infinity/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Essay companion:** [`infinity-lab/docs/essay-source.md`](../infinity-lab/docs/essay-source.md)
➡️ **Package README:** [`infinity-lab/packages/gojo_infinity/README.md`](../infinity-lab/packages/gojo_infinity/README.md)

Faithful code implementation of *Mathematics Behind Jujutsu Kaisen: Gojo Satoru's
Infinity* by Achmad Roykhan Sabiq (Oxford Maths Essay Competition 2026). The
monorepo version is the src-layout package sharing the internal `commons`
package, and includes everything added after the prototype: the four lenses with
exact-arithmetic tests, the numpy fast-path (parity-tested), matplotlib PNG
export, and — beyond the essay — a real 1/2/3-D Riemannian-manifold geodesic
solver plus animated approach GIFs.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/gojo_infinity          # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  python3 -m gojo_infinity.demo                    # four-verdict demo
# optional numpy/matplotlib features (fast-path, PNGs, GIFs):
./.venv/bin/python -m pytest packages/gojo_infinity
```

See [`infinity-lab/artifacts/`](../infinity-lab/artifacts/) for rendered figures
and animations (metric blow-up, geodesic bundles in 2-D/3-D, approach GIFs).
