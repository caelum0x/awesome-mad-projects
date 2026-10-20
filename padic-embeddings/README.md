# padic-embeddings — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/padic_embeddings/`](../infinity-lab/packages/padic_embeddings/)
➡️ **Docs:** `infinity-lab/packages/padic_embeddings/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/padic_embeddings/README.md`](../infinity-lab/packages/padic_embeddings/README.md)

An embedding space whose geometry is governed by the p-adic metric instead of
the usual Euclidean one — closeness is divisibility by a fixed prime `p`. The
monorepo version is the src-layout package sharing the internal `commons`
package, with the ultrametric inequality verified exhaustively over exact
`Fraction` distances and residue-class clustering.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/padic_embeddings         # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/padic_embeddings/src \
  python3 -m padic_embeddings.demo                   # narrated demo
```
