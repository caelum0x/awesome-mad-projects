# calabi-yau-latent — moved

This standalone prototype has been superseded by the maintained version in the
**infinity-lab monorepo**.

➡️ **Code:** [`infinity-lab/packages/calabi_yau_latent/`](../infinity-lab/packages/calabi_yau_latent/)
➡️ **Docs:** `infinity-lab/packages/calabi_yau_latent/docs/` — `ARCHITECTURE.md`, `PLAN.md`, `RESEARCH.md`
➡️ **Package README:** [`infinity-lab/packages/calabi_yau_latent/README.md`](../infinity-lab/packages/calabi_yau_latent/README.md)

A toy compactified `R^k x T^m` latent space — large "extended" dimensions plus
small periodic ("compactified") angle dimensions — whose wrap-aware toroidal
metric recovers cluster structure a naive Euclidean view misses across the
`0 / 2π` seam. The monorepo version is the src-layout package sharing the
internal `commons` package.

## Run it

```bash
cd ../infinity-lab
python3 -m pytest packages/calabi_yau_latent        # core, offline, zero-install
PYTHONPATH=packages/commons/src:packages/calabi_yau_latent/src \
  python3 -m calabi_yau_latent.demo                  # narrated demo, seed 7
```
