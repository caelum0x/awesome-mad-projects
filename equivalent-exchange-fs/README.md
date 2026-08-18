# Equivalent-Exchange Filesystem (`eqx`)

> "Humankind cannot gain anything without first giving something in return.
> To obtain, something of equal value must be lost."
> — the Law of Equivalent Exchange, *Fullmetal Alchemist*

A small, **dependency-free Rust** prototype: a userspace object store that
enforces **conservation of mass**. The total number of bytes stored can never
increase unless an **equal-or-greater number of bytes is sacrificed**. The only
way new mass may enter the system is an explicit, logged `grant` — the
alchemist's *"Truth's toll"*.

This is a library + CLI over a single managed **vault** directory. It is **not**
a FUSE mount and needs **no root**.

---

## The concept, honestly

In *Fullmetal Alchemist*, alchemy can reshape matter but never create it from
nothing. This project turns that fictional law into a real runtime invariant
for a byte store:

| Alchemy in the show                        | This filesystem                                        |
| ------------------------------------------ | ------------------------------------------------------ |
| Matter is reshaped, not created            | Bytes are moved between objects, total mass is bounded |
| To make something you must give up as much | `created_mass <= sacrificed_mass` for every operation  |
| The Gate / Truth demands a toll            | `grant` is the only lawful, explicit source of mass    |
| A transmutation circle combines materials  | `transmute <src...> -> <dst>` fuses objects            |

The core invariant, enforced on **every** operation except `grant`:

```
created_mass <= sacrificed_mass
```

and at the whole-vault scale, the ledger guarantees:

```
current_mass_on_disk <= total_mass_ever_granted
```

If an operation would break the law, it is **rejected before any file is
created or deleted**, so the vault is never left half-transmuted.

## Honest description of the systems core

This is a real, runnable prototype — here is exactly what it does and does not do.

- **What it is:** an ordinary userspace program that stores each "object" as a
  real file of the requested byte length under `./vault/objects/`, and appends
  one line per operation to `./vault/ledger.log`. "Mass" is literally file
  length in bytes. Created objects are filled with deterministic printable
  content (not sparse holes), so `du` and `ls -l` agree with the ledger.
- **The law is enforced in code, not by the OS.** `ExchangeStore::alchemize`
  and `transmute` compute the sacrificed mass, compare it to the requested
  mass, and return `UnbalancedExchange` *before* mutating the filesystem.
- **It is a managed store, not a POSIX filesystem.** There is no FUSE, no mount,
  no `open()/read()/write()` interception. You interact through the `eqx` CLI or
  the library API. This deliberate choice avoids needing root and keeps the
  blast radius to one directory.
- **Not transactional across a crash.** Operations are ordered (delete
  sacrifices, then create) but there is no journaling/rollback if the process is
  killed mid-operation. Good enough for a prototype; not a production database.
- **Single process, no locking.** Concurrent `eqx` invocations on the same vault
  are not synchronized.

### Safety: the sandbox is the whole point

The store operates **only** on its own vault directory (default `./vault`
inside this project):

- Object names are validated with a strict allow-list (`[A-Za-z0-9._-]`, never
  `.`/`..`, never a path separator). See `src/name.rs`.
- The only filesystem API, `Vault` (`src/vault.rs`), joins validated names under
  `vault/objects/` and then **re-checks** that the resulting path's parent is
  exactly the objects directory (defence in depth against traversal).
- There is **no** API that accepts an arbitrary path. The program cannot read,
  write, or delete anything outside the vault it manages. It never runs
  destructive commands on your wider filesystem.

## Layout

```
equivalent-exchange-fs/
├── Cargo.toml
├── README.md
├── src/
│   ├── lib.rs      # crate root + docs + re-exports
│   ├── error.rs    # ExchangeError (incl. UnbalancedExchange = the law)
│   ├── name.rs     # SAFETY: strict object-name validation
│   ├── vault.rs    # SAFETY: sandbox directory, all file I/O
│   ├── ledger.rs   # append-only audit trail + conservation math
│   ├── store.rs    # ExchangeStore: enforces created <= sacrificed
│   └── main.rs     # `eqx` CLI (hand-rolled arg parsing, zero deps)
└── tests/
    └── law_of_equivalent_exchange.rs  # proves the invariant + rejections
```

## Build, run, test

```bash
cd equivalent-exchange-fs
cargo build
cargo test          # unit + integration tests, incl. the invariant proofs
cargo run -- help   # CLI usage
```

The vault defaults to `./vault` (override with `--vault <dir>` or `$EQX_VAULT`).

### Commands

```
eqx grant <name> <bytes>                       Seed new mass (Truth's toll; logged).
eqx alchemize <name> <bytes> --sacrifice a,b   Create <name> by deleting a,b.
                                               Rejected unless size(a)+size(b) >= bytes.
eqx transmute <src...> -> <dst> [--size N]     Reshape sources into one dst object.
                                               dst mass defaults to combined source mass.
eqx list                                       List objects and their masses.
eqx ledger                                     Print the full audit trail + status.
eqx status                                     Print the conservation summary.
```

> **Shell note:** quote the arrow — `transmute a b '->' dst` — because a bare
> `->` is parsed by the shell as the redirection operator `>`.

## Sample session

A successful transmutation **and** a rejected free-lunch attempt:

```text
$ eqx grant ore 500
Truth's toll paid. Granted 500 bytes as 'ore'.
  ledger <- [t=...] GRANT      +500 bytes -> 'ore'  (Truth's toll; no sacrifice) [OK]
  current mass: 500 bytes across 1 object(s)

$ eqx alchemize sword 300 --sacrifice ore
Transmutation complete: 'sword' (300 bytes) formed.
  ledger <- [t=...] ALCHEMIZE  created 300b 'sword'  <=  sacrificed 500b [OK] sacrificed: [ore(500b)]
  current mass: 300 bytes across 1 object(s)

# --- the forbidden free lunch: 1000 bytes out of a 300-byte sword ---
$ eqx alchemize gold_mountain 1000 --sacrifice sword
error: LAW OF EQUIVALENT EXCHANGE VIOLATED: cannot create 1000 bytes from a
       sacrifice of only 300 bytes. To obtain, something of equal value must be lost.
# (exit code 1; nothing on disk changed — sword is untouched)

$ eqx grant gems 250
Truth's toll paid. Granted 250 bytes as 'gems'.
  current mass: 550 bytes across 2 object(s)

# --- the classic transmutation circle: fuse sword + gems into one object ---
$ eqx transmute sword gems '->' alloy
The circle closes: sources reshaped into 'alloy'.
  ledger <- [t=...] TRANSMUTE  created 550b 'alloy'  <=  sacrificed 550b [OK] sacrificed: [sword(300b), gems(250b)]
  current mass: 550 bytes across 1 object(s)

$ eqx list
OBJECT                          BYTES
-------------------------------------
alloy                             550
-------------------------------------
TOTAL MASS                        550

$ eqx ledger
=== ALCHEMIST'S LEDGER ===
#1   [t=...] GRANT      +500 bytes -> 'ore'  (Truth's toll; no sacrifice) [OK]
#2   [t=...] ALCHEMIZE  created 300b 'sword'  <=  sacrificed 500b [OK] sacrificed: [ore(500b)]
#3   [t=...] GRANT      +250 bytes -> 'gems'  (Truth's toll; no sacrifice) [OK]
#4   [t=...] TRANSMUTE  created 550b 'alloy'  <=  sacrificed 550b [OK] sacrificed: [sword(300b), gems(250b)]

=== CONSERVATION STATUS ===
current mass on disk : 550 bytes
objects in vault     : 1
total ever granted   : 750 bytes  (lawful mass source)
total ever created   : 1600 bytes
total ever sacrificed: 1050 bytes
every op balanced    : yes
mass <= granted      : yes
>>> LAW OF EQUIVALENT EXCHANGE UPHELD
```

## Library API

```rust
use equivalent_exchange_fs::ExchangeStore;

let store = ExchangeStore::open("./vault")?;
store.grant("ore", 500)?;                          // seed mass (logged)
store.alchemize("sword", 300, &["ore".into()])?;   // 300 <= 500  -> ok
store.transmute(&["sword".into()], "ring", Some(100))?; // may lose mass, never gain

// This returns Err(ExchangeError::UnbalancedExchange { .. }):
// store.alchemize("free_gold", 9999, &["ring".into()]);
```

## Tests that prove the law

`tests/law_of_equivalent_exchange.rs` includes:

- balanced alchemy conserves mass and keeps `current_mass <= total_granted`;
- an unbalanced `alchemize` is **rejected** and leaves the disk unchanged;
- creating from an empty sacrifice is rejected;
- `transmute` with no `--size` conserves *all* mass; with `--size` it may lose
  mass but a request to *gain* mass is rejected;
- a long mixed session keeps every operation balanced and the law upheld;
- path-traversal object names are refused and nothing escapes the vault.

Run them with `cargo test`.

## License

MIT.
