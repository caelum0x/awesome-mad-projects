# Contributing to awesome-mad-projects

Thanks for wanting to add to the collection. This is a curated list of projects that turn
fictional or folk-mathematical ideas into **real, runnable, honest code** — and contributions
that fit that spirit are very welcome.

## The bar

A project belongs here if it meets all of these:

1. **An honest core.** There is a genuine mathematical or systems idea underneath, and the
   code actually implements it. No mock code, no stubs, no "pretend" functions.
2. **Honesty about the costume.** Where the real thing is impossible or unsafe (kernel-level
   process control, Banach–Tarski, "true" infinity), you implement a clearly-labeled **safe
   simulation** and say so in the README. If the math collapses when written down honestly,
   the project *says that* — that's a feature, not a failure.
3. **It runs.** A reader can clone it and run it with the project's native toolchain.
4. **Tests.** Meaningful tests that pin the behavior/numbers you claim.
5. **Safety.** Nothing that targets other people's machines, processes, memory, or data.
   System-flavored projects must operate only on an opt-in sandbox they create themselves.
6. **No copyright violations.** Original code and original renders only. Cite any published
   mathematics you build on; do not commit copyrighted anime/manga/game images, screenshots,
   or third-party art. Reference official sources by link instead.

## How to add a project

1. **Fork** the repo and create a branch.
2. **Add a folder** `your-project/` (or, for a Python project that can share the internal
   `commons` package, a package under `infinity-lab/packages/`). Include:
   - source + tests that pass,
   - a `README.md` (concept → the honest math/systems core with formulas → how it works →
     run instructions → sample output → limitations → references),
   - a `banner.png` in the ink-on-cream style is nice but optional.
3. **Register it for the site:** add an entry to [`site/projects.json`](./site/projects.json)
   with `name`, `slug`, `tagline`, `language`, `cluster`
   (`infinity-lab` | `math-in-code` | `systems-anime`), and `github_url`.
4. **Add a row** to the catalog in the root [`README.md`](./README.md).
5. **Open a PR** describing the idea, what's real vs. simulated, and how you tested it.

## Style

- Match the surrounding language's idioms and the existing project structure.
- Small, focused files. Clear names. Explicit error handling. No dead code.
- For the `infinity-lab` monorepo: keep the pure core stdlib-only; put numpy/matplotlib behind
  the optional-dependency guard; keep tests offline. Run `cd infinity-lab && make verify`.

## Reporting ideas / issues

Have an idea but not the time to build it? [Open an issue](https://github.com/caelum0x/awesome-mad-projects/issues)
describing the fictional concept and the mathematics you think is underneath.

By contributing you agree your work is released under the repository's [MIT License](./LICENSE).
