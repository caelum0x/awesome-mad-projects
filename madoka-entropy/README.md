# madoka-entropy — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/madoka_entropy/`](../infinity-lab/packages/madoka_entropy/)
➡️ **Docs:** `infinity-lab/packages/madoka_entropy/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/madoka_entropy/README.md`](../infinity-lab/packages/madoka_entropy/README.md)

A closed system of magical girls, a global entropy budget, and the incubators
who harvest the difference, modeled as an entropy ledger (`dS_total = (k-1)*x > 0`
per wish). The monorepo version is the src-layout package sharing the internal
`commons` package, with the witch-threshold/soul-gem purity model, the
incubator harvest bookkeeping, and the machine-checked second-law-like
invariant across the whole simulation.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/madoka_entropy          # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/madoka_entropy/src \
  python3 -m madoka_entropy.demo                    # default: seed 42, 120 steps
```
