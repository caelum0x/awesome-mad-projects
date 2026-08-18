# Reading Steiner Git

A tiny, self-contained **worldline version-control toy** written in TypeScript,
inspired by *Steins;Gate*. It snapshots a sandbox directory, addresses content
by hash, and reports a six-decimal **Divergence Meter** reading for every
commit. Jumping between commits is a "world line jump" — you keep the *memory*
of the divergence delta and of exactly what changed on disk (that is the
"Reading Steiner" ability).

> El Psy Kongroo.

---

## Concept (Steins;Gate)

In *Steins;Gate*, every altered timeline is a **world line** identified by a
**divergence number** on a nixie-tube *Divergence Meter* (the famous reading is
`1.048596`). World lines cluster into **attractor fields**:

- **Alpha (α)** — divergence `< 1.0`
- **Beta (β)** — divergence `>= 1.0`

The protagonist Okabe has **Reading Steiner**: when the world line shifts, he
alone retains his memories of the previous line. This project maps those ideas
onto a version-control system:

| Steins;Gate            | Reading Steiner Git                                  |
| ---------------------- | ---------------------------------------------------- |
| World line             | a commit (a snapshot of the sandbox)                 |
| Divergence number      | deterministic hash of the tree state, mapped to `[0, 2)` |
| Attractor field α / β  | divergence `< 1.0` / `>= 1.0`                         |
| Branch of world lines  | a branch (`main`, `beta`, `steinsgate`, …)           |
| Time-leap / world jump | `steiner jump <ref>` — restores that snapshot        |
| Reading Steiner        | after a jump you get the divergence **delta** + a change log |
| History destabilizing  | a warning when the divergence delta grows large      |

---

## Honest core (what is real vs. flavor)

**Real:**

- **Content-addressable store.** Every file is stored as a blob named by the
  SHA-1 of its bytes under `.steiner/objects/`. A *tree* manifest maps paths to
  blob hashes; commits reference a tree and a parent. This is the same core
  idea as real content-addressable VCSs.
- **Deterministic snapshots & restores.** `commit` hashes the working tree;
  `jump` rewrites the sandbox to exactly match a stored snapshot (adding,
  modifying, and removing files, then pruning empty dirs).
- **Branches & HEAD.** `refs/heads/<branch>` hold commit ids; `HEAD` is either
  `ref: <branch>` or a detached commit id — mirroring git's model.
- **Divergence is a pure function of tree content.** The same files always
  produce the same reading, regardless of commit order or timestamps.

**Flavor (honest about it):**

- The **divergence number** is an *honest hash projection*, not a physically
  meaningful value: take the first 13 hex digits of the tree hash, divide by
  `16^13`, multiply by 2, round to six decimals → a value in `[0, 2)`.
- "History is destabilizing" is a threshold on the divergence **delta**
  (`>= 0.4` warns, `>= 1.0` is "critical"), plus a note when a jump crosses the
  α ⇄ β attractor-field boundary. It is narrative, not a data-integrity signal.
- In the demo, the Beta-field `steinsgate` world line uses a **pre-computed
  nonce** (`nonce=188`) in one file so its reading (`1.153035`) reproducibly
  lands in the Beta field. That is the only "engineered" number; everything
  else falls out of the file contents.

**Safety:** this is a *toy* VCS. It **never** invokes real `git` and refuses to
operate on any path outside this project folder. All state lives in a sandbox
directory inside the project (default `./workspace`, demo uses
`./workspace-demo`), each containing its own `.steiner/` store.

---

## Store layout

```
<workspace>/                 # the sandbox working tree (your tracked files)
  <your files...>
  .steiner/
    objects/<sha1>           # content-addressed blobs (raw file bytes)
    commits/<id>.json        # one world-line node each (tree, parent, divergence…)
    refs/heads/<branch>      # text file holding a commit id
    HEAD                     # "ref: <branch>" or a detached commit id
```

---

## Install & build

Requires Node.js (tested on Node 24) and npm.

```bash
cd reading-steiner-git
npm install      # installs typescript + @types/node (dev only; zero runtime deps)
npm run build    # compiles src/*.ts -> dist/*.js via tsc
```

## Run the CLI

```bash
node dist/cli.js <command> [options]

# commands
init    [--dir <ws>] [--branch <name>]   create a repo in a sandbox dir
commit  -m "<msg>"  [--dir <ws>]         snapshot the sandbox as a world line
log     [--dir <ws>]                     show the world-line tree + divergence
status  [--dir <ws>]                     show HEAD + working-tree divergence
branch  <name>      [--dir <ws>]         fork a new world line and switch to it
jump    <ref>       [--dir <ws>]         restore a world line (Reading Steiner)
```

`<ref>` is a branch name or a commit id / prefix. `--dir` defaults to
`./workspace`. Set `NO_COLOR=1` to disable ANSI colors.

### Quick tour

```bash
node dist/cli.js init --dir workspace
echo "hello" > workspace/a.txt
node dist/cli.js commit -m "first world line" --dir workspace
node dist/cli.js log --dir workspace
node dist/cli.js branch beta --dir workspace
echo "changed" > workspace/a.txt
node dist/cli.js commit -m "diverge" --dir workspace
node dist/cli.js jump main --dir workspace   # Reading Steiner: restore + delta
```

## Run the demo

```bash
npm run demo        # builds a fresh ./workspace-demo, commits on 3 world lines, jumps around
```

The demo is deterministic in its **divergence readings** (they depend only on
file content). Only the short commit **ids** vary between runs, because a commit
id includes its wall-clock timestamp.

---

## Sample demo output

```
════════════════════════════════════════════════════════════════
  commit #2 on main
════════════════════════════════════════════════════════════════
Committed cef7dd4a on main
  message   : Kurisu survives; add a plan
  divergence: 0.123902 [α Alpha]
  Δ from parent: -0.349547
  ~ lab-mail.txt
  + notes/plan.txt

════════════════════════════════════════════════════════════════
  commit #4 on steinsgate  (crosses into the Beta field)
════════════════════════════════════════════════════════════════
Committed c42ac849 on steinsgate
  message   : Reach the Beta attractor field
  divergence: 1.153035 [β Beta]
  Δ from parent: +0.532882
  - lab-mail.txt
  - notes/plan.txt
  + worldline.txt

════════════════════════════════════════════════════════════════
  log — the world line tree
════════════════════════════════════════════════════════════════
World Line Tree  (Divergence Meter readings)
branches: beta, main, steinsgate

● c42ac849  1.153035 [β Beta] (steinsgate) ← HEAD
    Reach the Beta attractor field
    steinsgate parent 174210ea
○ 174210ea  0.620153 [α Alpha] (beta)
    Diverge: Mayuri route; drop divergence note
    beta parent cef7dd4a
○ cef7dd4a  0.123902 [α Alpha] (main)
    Kurisu survives; add a plan
    main parent 220bd93e
○ 220bd93e  0.473449 [α Alpha]
    First lab mail; establish the α world line
    main root

════════════════════════════════════════════════════════════════
  jump → steinsgate  (Alpha ⇒ Beta: history destabilizes)
════════════════════════════════════════════════════════════════
READING STEINER — worldline jump
  from cef7dd4a  0.123902 [α Alpha]
  to   c42ac849  1.153035 [β Beta]
  divergence Δ: 1.029133
  ⚠ attractor-field boundary crossed (Alpha ⇄ Beta).
  ‼ WORLD LINE SHIFT CRITICAL — history is destabilizing violently.
  HEAD now on worldline steinsgate.
  restored files:
    - lab-mail.txt
    - notes/divergence.txt
    - notes/plan.txt
    + worldline.txt
  (You alone retain the memory of the previous world line.)

════════════════════════════════════════════════════════════════
  jump → beta
════════════════════════════════════════════════════════════════
READING STEINER — worldline jump
  from 220bd93e  0.473449 [α Alpha]
  to   174210ea  0.620153 [α Alpha]
  divergence Δ: 0.146704
  worldline stable.
  HEAD now on worldline beta.
  restored files:
    ~ lab-mail.txt
    - notes/divergence.txt
    + notes/plan.txt
  (You alone retain the memory of the previous world line.)
```

(Full run also shows `init`, commits #1 and #3, a critical jump back to `main`,
a detached jump to the root world line, and a final `status`.)

---

## Source layout

```
src/
  hash.ts        SHA-1 + tree hashing + the divergence projection & attractor field
  paths.ts       sandbox path resolution and the "stay inside the project" guard
  store.ts       .steiner persistence: blobs, commits, refs, HEAD
  workspace.ts   read/snapshot and restore the sandbox working tree
  diff.ts        manifest-level tree diffing (added / removed / modified)
  repo.ts        high-level ops: init, commit, branch, log, jump, status
  format.ts      Divergence-Meter-flavored console rendering
  cli.ts         the `steiner` command-line entry point
  demo.ts        the runnable multi-world-line demo
```

## Notes & limitations

- Toy scope: no merges, no packing, no compression, snapshots are stored inline
  in each commit JSON (fine for small sandboxes). SHA-1 is used for its brevity,
  not its cryptographic strength.
- Committing requires an attached HEAD. After a `jump` to a bare commit, HEAD is
  detached; run `steiner branch <name>` to anchor a new world line before
  committing again.

## License

MIT
