# awesome-mad-projects

Absurd-but-real prototypes at the intersection of **anime / pop-culture / games** and
**mathematics**. Each project takes a fictional or folk-mathematical claim and turns it into
actual, runnable, tested code.

> **Rule of the repo:** every project must have an *honest* mathematical or systems core.
> Where the real thing is impossible or unsafe (kernel-level process killing, Banach–Tarski,
> "true" infinity), we implement a clearly-labeled **safe simulation** and say so plainly.

🌐 **Showcase site:** [mad-projects.com](https://mad-projects.com) · 📬 **Contact:** caelum0x42@gmail.com

---

## 🧪 infinity-lab — the Python monorepo

The most-developed work lives in [`infinity-lab/`](./infinity-lab): a stdlib-first Python
monorepo where nine packages share an internal `commons` package. **576 tests pass offline
(zero-install), 600+ with the optional numpy/matplotlib extras** — both interpreters green.

| Package | Concept |
|---|---|
| [`gojo_infinity`](./infinity-lab/packages/gojo_infinity) | Gojo's Infinity through four mathematical lenses + real 1/2/3-D Riemannian geodesics |
| [`mobius_rickness`](./infinity-lab/packages/mobius_rickness) | Central Finite Curve as the zero-set R⁻¹(0) **and** the SCMS ridge |
| [`central_finite_curve`](./infinity-lab/packages/central_finite_curve) | Central Finite Curve as the near-maximal Rickness band over a simulated multiverse |
| [`calabi_yau_latent`](./infinity-lab/packages/calabi_yau_latent) | Toy compactified R^k × T^m latent space |
| [`domain_expansion`](./infinity-lab/packages/domain_expansion) | Domain Expansion as a coupled constraint solver |
| [`divergence_meter`](./infinity-lab/packages/divergence_meter) | Steins;Gate worldline divergence + attractor fields |
| [`padic_embeddings`](./infinity-lab/packages/padic_embeddings) | p-adic metric embedding space |
| [`madoka_entropy`](./infinity-lab/packages/madoka_entropy) | Wishes as local entropy decrease + global karmic cost |
| `commons` | Shared core: seeded RNG, numerics, exact arithmetic, ASCII/PNG rendering |

It ships a gallery of 35 rendered figures/animations, a landing page, and `make` glue.

```bash
cd infinity-lab
make test        # offline core (stdlib only)
make verify      # both interpreters
make artifacts   # regenerate all figures + animations + gallery
open index.html  # landing page
```

Full architecture, plan, and resolved-math docs live under each package's `docs/`.

---

## 🧩 Standalone prototypes (Rust / Go / TypeScript)

Self-contained, each with its own README, concept, math, and run instructions.

| Project | Concept | Language |
|---|---|---|
| [`surreal-priority`](./surreal-priority) | Conway surreal numbers as process priority (ω, 1/ω) | Rust |
| [`statmech-scheduler`](./statmech-scheduler) | Boltzmann/temperature process scheduler | Go |
| [`reading-steiner-git`](./reading-steiner-git) | Worldline-divergence version control | TypeScript |
| [`infinite-hotel-scheduler`](./infinite-hotel-scheduler) | Hilbert's Hotel resource allocator | Go |
| [`category-api`](./category-api) | Endpoints as morphisms, middleware as functors | TypeScript |
| [`zeno-protocol`](./zeno-protocol) | Packets that travel half the remaining distance, forever | Go |
| [`equivalent-exchange-fs`](./equivalent-exchange-fs) | FMA: create a file only by sacrificing equal mass | Rust |
| [`at-field`](./at-field) | Evangelion AT Field as process/message isolation | Rust |
| [`unlimited-void`](./unlimited-void) | JJK Unlimited Void: bounded information-flood "freeze" | Go |
| [`hairy-ball-router`](./hairy-ball-router) | Forced routing singularity via the hairy-ball theorem | Go |
| [`banach-tarski-dup`](./banach-tarski-dup) | Paradoxical "duplication" via free-group decomposition | Rust |
| [`death-note`](./death-note) | Rule-accurate process reaper (SAFE, opt-in sandbox) | Rust |
| [`jojo-stands`](./jojo-stands) | Stands as process abilities (SAFE userspace sim) | Rust |
| [`vanguard-anticheat`](./vanguard-anticheat) | Integrity/attestation monitor (SAFE userspace) | Rust |

> `gojo-infinity/`, `mobius-rickness/`, and `central-finite-curve/` at the repo root are
> pointer READMEs — those projects now live as packages inside `infinity-lab/`.

## 🛡️ Safety note

`death-note`, `jojo-stands`, and `vanguard-anticheat` are inspired by kernel-level ideas but
are implemented entirely in **userspace against an opt-in sandbox of processes the tool spawns
itself**. They never load kernel modules and never target arbitrary system PIDs.

## 📎 Attribution

The `gojo_infinity` package is a faithful code implementation of the mathematics in
*Mathematics Behind Jujutsu Kaisen: Gojo Satoru's Infinity* by **Achmad Roykhan Sabiq**
(Oxford University Mathematics Essay Competition 2026) —
[essay PDF](https://tomrocksmaths.com/wp-content/uploads/2026/06/achmad-roykhan-sabiq_essay_competition_2026-achmad-roykhan-sabiq.pdf).
We implement and cite the mathematics; the essay text itself is not redistributed here.
Anime, manga, and game references are © their respective creators; this repository contains
only original code and original renders.

## 📄 License

Original code is released under the MIT License (see `LICENSE`).
