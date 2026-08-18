# Vanguard-style Integrity Monitor (Rust, safe userspace)

An **educational, defensive** prototype that implements the *honest subset* of
what a game anti-cheat (in the spirit of Riot Vanguard) does — but entirely in
**safe userspace**, over a **sandbox that this tool creates and owns**.

It demonstrates four defensive building blocks:

1. **Integrity manifest** — fingerprint the tool's own game-asset files with
   **SHA-256** at a "trusted" moment, sign the manifest with **HMAC-SHA256**,
   then re-scan later and detect tampering (modified / added / removed files).
2. **Process attestation** — the tool launches its **own** "game" child process
   and periodically verifies it is still the exact process the tool spawned and
   that its on-disk binary still matches the trusted hash. It only ever inspects
   a child it started via a retained handle — **never arbitrary PIDs**.
3. **Heartbeat challenge/response** — a client and server exchange messages with
   a **rolling HMAC** and a monotonic counter, so a **replayed** or **forged**
   (wrong-key) heartbeat is rejected.
4. **Tamper log + report** — a clear, ordered report of exactly what changed.

The whole thing is **zero-dependency**: SHA-256 (FIPS 180-4) and HMAC-SHA256
(RFC 2104) are implemented in pure, safe Rust so it builds and runs fully
offline. `#![forbid(unsafe_code)]` is enforced at the crate root.

---

## ⚠️ SAFETY & ETHICS — READ THIS FIRST

This is a **DEFENSIVE, USERSPACE, OPT-IN integrity monitor** and an **educational
attestation/integrity checker**. It is **NOT** a real kernel anti-cheat. It
deliberately and explicitly **does NOT**:

- ❌ install a **kernel driver** or run at **ring-0**;
- ❌ **scan, read, or write another process's memory**;
- ❌ **attach to, debug, or anti-debug arbitrary processes** or foreign PIDs;
- ❌ perform any **evasion, stealth, rootkit, or surveillance** behavior;
- ❌ inspect, modify, or monitor **anyone else's files, system, or software**.

Everything it does is confined to:

- ✅ a **sandbox directory the tool itself creates** (seeded by copying this
  repo's `assets/`), and
- ✅ a **child process the tool itself spawns** (a subcommand of this very
  binary), tracked through a process handle the tool owns.

Real kernel-level anti-cheats raise serious **privacy, security, and trust**
concerns (ring-0 access, always-on drivers, telemetry). This prototype exists to
teach the *legitimate, transparent, consent-based* techniques — content
attestation, signed manifests, and anti-replay — **without** any of the invasive
mechanisms. Do not use this code as a base for surveilling users or processes you
do not own. The demo signing keys in `src/main.rs` are clearly labeled as
throwaway demo values and must never be treated as real secrets.

---

## Requirements

- Rust + Cargo (tested with Cargo 1.94). No network access required.

## Run instructions

```bash
cd vanguard-anticheat

# Build
cargo build

# Run the full end-to-end demo
cargo run

# Run the test suite (SHA-256/HMAC test vectors, tamper detection,
# replay/forgery rejection, own-child attestation)
cargo test
```

Internal subcommand (used by the attestation demo; you normally won't call it
directly): `cargo run -- game-loop <milliseconds>` — the tool's own idle "game"
child process.

## What the demo does

1. Copies `assets/` into a fresh temp **sandbox** (keeps the repo pristine).
2. Builds a **signed SHA-256 manifest** over the sandbox.
3. Re-scans an untouched sandbox → reports **clean**.
4. **Tampers**: modifies `config.cfg`, adds `cheat.dll`, removes `textures.pak`
   → re-scan detects all three.
5. Verifies the **manifest's own HMAC signature** (correct key ✓, wrong key ✗,
   silently edited manifest ✗).
6. Launches the tool's **own child** and **attests** it (alive + binary hash
   matches), then confirms it reports *exited* after termination.
7. Runs the **heartbeat**: three honest rounds accepted, a **replayed** round-1
   heartbeat rejected (`RejectedStaleCounter`), and a **forged** wrong-key
   heartbeat rejected (`RejectedBadMac`).

## Sample output

```
Vanguard-style Integrity Monitor — DEFENSIVE / USERSPACE / EDUCATIONAL
This tool only inspects a sandbox it creates and a child it spawns.
No kernel driver. No foreign-process memory scanning. No anti-debugging.

Sandbox (tool-owned): /var/folders/.../T/vanguard_sandbox_1787058084631392000/assets

=== 1. Build signed integrity manifest (trusted snapshot) ===
Hashed 3 asset file(s) with SHA-256:
  config.cfg           113 bytes  483df8b375882db4…
  scripts/init.lua     152 bytes  092f3ace300cd97b…
  textures.pak         305 bytes  c1658edce81ac4b1…
Manifest signed (HMAC-SHA256): 1f23c3917c3db6a8…
Manifest written to: /var/folders/.../T/vanguard_sandbox_.../vanguard.manifest

=== 2. Re-scan an untampered sandbox ===
Integrity scan: 3 file(s) checked, 0 change(s) detected
  OK: all assets match the trusted manifest.

=== 3. Tamper with the sandbox, then re-scan ===
Applied tampering: modified config.cfg, added cheat.dll, removed textures.pak
Integrity scan: 2 file(s) checked, 3 change(s) detected
  [ADDED] cheat.dll — unexpected file not in trusted manifest
  [MODIFIED] config.cfg — hash 483df8b37588… -> fba34f03df81…
  [REMOVED] textures.pak — file present in manifest is missing on disk

=== 4. Verify the manifest's own signature (defends the manifest) ===
Loaded manifest signature valid with correct key : true
Loaded manifest signature valid with wrong key   : false
Tampered manifest (edited hash) signature valid  : false  <- rejected

=== 5. Process attestation (own child only, never arbitrary PIDs) ===
Launched tool-owned child pid=50935 backed by .../target/debug/vanguard
Trusted binary hash: 3f0637bd2a5c0032…
  attest #1: OK — pid 50935 alive, binary hash matches
  attest #2: OK — pid 50935 alive, binary hash matches
  attest after terminate: process exited (expected)

=== 6. Heartbeat challenge/response (rolling HMAC anti-replay) ===
  round 1: counter=1 -> Accepted
  round 2: counter=2 -> Accepted
  round 3: counter=3 -> Accepted
  replay of round 1 heartbeat -> RejectedStaleCounter  <- rejected
  forged heartbeat (wrong key) -> RejectedBadMac  <- rejected

=== Summary ===
Integrity: 3 tamper finding(s) detected against the signed manifest.
Manifest signature protects the manifest from silent edits.
Process attestation verified only the child this tool spawned.
Heartbeat rejected both a replayed and a forged message.

Reminder: this is a defensive, educational userspace prototype only.
```

## Project layout

```
vanguard-anticheat/
├── Cargo.toml
├── README.md
├── assets/                 # sample "game" assets (the tool's own sandbox seed)
│   ├── config.cfg
│   ├── textures.pak
│   └── scripts/init.lua
└── src/
    ├── lib.rs              # crate root, #![forbid(unsafe_code)]
    ├── main.rs             # demo driver + the tool's own "game-loop" child
    ├── sha256.rs           # pure-Rust SHA-256 (+ test vectors)
    ├── hmac.rs             # HMAC-SHA256 + constant-time compare (+ RFC 4231 vectors)
    ├── manifest.rs         # signed integrity manifest, build/scan/verify
    ├── process.rs          # attestation of the tool's OWN spawned child
    ├── heartbeat.rs        # rolling-HMAC challenge/response, anti-replay
    └── report.rs           # change kinds + tamper report rendering
```

## Design notes

- **Immutability / no shared mutation** for reporting: scans return a fresh
  `ScanReport`; rendering builds a new `String`.
- **Deterministic canonical form**: manifest entries are sorted and serialized
  with a fixed field order so the HMAC is reproducible.
- **Streaming hashing**: files are hashed in 8 KiB chunks (large files are never
  loaded fully into memory).
- **Constant-time MAC comparison** to avoid trivial timing side channels.

## License

MIT (educational sample).
