# domain-expansion — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/domain_expansion/`](../infinity-lab/packages/domain_expansion/)
➡️ **Docs:** `infinity-lab/packages/domain_expansion/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/domain_expansion/README.md`](../infinity-lab/packages/domain_expansion/README.md)

A Domain Expansion as a coupled boundary-value constraint solver: each domain
is a discretized Laplace equation on a 7x7 grid, solved two independent ways
(Gauss-Seidel relaxation and direct Gaussian elimination) that must agree; in
a clash the domain with the higher rigidity/refinement score overwrites the
other. The monorepo version is the src-layout package sharing the internal
`commons` package.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/domain_expansion         # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/domain_expansion/src \
  python3 -m domain_expansion.demo                   # end-to-end demo
```
