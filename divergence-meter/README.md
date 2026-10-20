# divergence-meter — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/divergence_meter/`](../infinity-lab/packages/divergence_meter/)
➡️ **Docs:** `infinity-lab/packages/divergence_meter/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/divergence_meter/README.md`](../infinity-lab/packages/divergence_meter/README.md)

A Steins;Gate worldline-divergence number derived from `SHA-256(payload)`,
classified into Alpha/Beta attractor fields and rendered on a nixie-tube
display. The monorepo version is the src-layout package sharing the internal
`commons` package, with exact `Fraction`-valued readings, a "Reading Steiner"
store for named worldlines, and the attractor-field CLI.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/divergence_meter        # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/divergence_meter/src \
  python3 -m divergence_meter.adapters.cli measure "El Psy Kongroo"
```
