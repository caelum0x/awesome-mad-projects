//! `eqx` — command-line front end for the Equivalent-Exchange filesystem.
//!
//! Usage (vault defaults to `./vault`, override with `--vault <dir>` or the
//! `EQX_VAULT` environment variable):
//!
//!   eqx grant <name> <bytes>                     Seed mass (Truth's toll).
//!   eqx alchemize <name> <bytes> --sacrifice a,b Create by sacrificing a,b.
//!   eqx transmute <src...> -> <dst> [--size N]   Reshape sources into dst.
//!   eqx list                                     List objects and masses.
//!   eqx ledger                                   Print audit trail + status.
//!   eqx status                                   Print conservation summary.
//!
//! The parser is hand-rolled to keep the crate dependency-free.

use std::process::ExitCode;

use equivalent_exchange_fs::store::ConservationStatus;
use equivalent_exchange_fs::ledger::{Ledger, Transaction, TxKind};
use equivalent_exchange_fs::{ExchangeStore, Result};

const DEFAULT_VAULT: &str = "./vault";

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match run(&args) {
        Ok(()) => ExitCode::SUCCESS,
        Err(msg) => {
            eprintln!("error: {msg}");
            ExitCode::FAILURE
        }
    }
}

/// Top-level dispatch. Returns a human-readable error string on failure.
fn run(args: &[String]) -> std::result::Result<(), String> {
    // Extract an optional leading/trailing `--vault <dir>` flag anywhere.
    let (vault_dir, rest) = extract_vault_flag(args);

    let cmd = match rest.first() {
        Some(c) => c.as_str(),
        None => {
            print_help();
            return Ok(());
        }
    };
    let params = &rest[1..];

    let store = ExchangeStore::open(&vault_dir).map_err(|e| e.to_string())?;

    match cmd {
        "grant" => cmd_grant(&store, params),
        "alchemize" => cmd_alchemize(&store, params),
        "transmute" => cmd_transmute(&store, params),
        "list" => cmd_list(&store),
        "ledger" => cmd_ledger(&store),
        "status" => cmd_status(&store),
        "help" | "-h" | "--help" => {
            print_help();
            Ok(())
        }
        other => Err(format!("unknown command '{other}' (try `eqx help`)")),
    }
}

/// Pull `--vault <dir>` out of the argument list, returning the chosen vault
/// directory and the remaining args. Falls back to `$EQX_VAULT` then default.
fn extract_vault_flag(args: &[String]) -> (String, Vec<String>) {
    let mut vault = std::env::var("EQX_VAULT").unwrap_or_else(|_| DEFAULT_VAULT.to_string());
    let mut rest = Vec::new();
    let mut i = 0;
    while i < args.len() {
        if args[i] == "--vault" {
            if let Some(dir) = args.get(i + 1) {
                vault = dir.clone();
                i += 2;
                continue;
            }
        }
        rest.push(args[i].clone());
        i += 1;
    }
    (vault, rest)
}

fn cmd_grant(store: &ExchangeStore, params: &[String]) -> std::result::Result<(), String> {
    if params.len() != 2 {
        return Err("usage: eqx grant <name> <bytes>".into());
    }
    let name = &params[0];
    let bytes = parse_bytes(&params[1])?;
    let tx = store.grant(name, bytes).map_err(|e| e.to_string())?;
    println!("Truth's toll paid. Granted {bytes} bytes as '{name}'.");
    print_tx_summary(&tx);
    print_status_line(store).map_err(|e| e.to_string())?;
    Ok(())
}

fn cmd_alchemize(store: &ExchangeStore, params: &[String]) -> std::result::Result<(), String> {
    // eqx alchemize <name> <bytes> --sacrifice a,b,c
    if params.len() < 2 {
        return Err("usage: eqx alchemize <name> <bytes> --sacrifice a,b,c".into());
    }
    let name = &params[0];
    let bytes = parse_bytes(&params[1])?;
    let sacrifices = parse_sacrifice_flag(&params[2..])?;
    if sacrifices.is_empty() {
        return Err("alchemize requires --sacrifice <a,b,...>".into());
    }
    let tx = store
        .alchemize(name, bytes, &sacrifices)
        .map_err(|e| e.to_string())?;
    println!("Transmutation complete: '{name}' ({bytes} bytes) formed.");
    print_tx_summary(&tx);
    print_status_line(store).map_err(|e| e.to_string())?;
    Ok(())
}

fn cmd_transmute(store: &ExchangeStore, params: &[String]) -> std::result::Result<(), String> {
    // eqx transmute <src...> -> <dst> [--size N]
    // Split params on the literal "->" arrow.
    let arrow = params.iter().position(|p| p == "->");
    let arrow = arrow.ok_or("usage: eqx transmute <src...> -> <dst> [--size N]")?;

    let sources: Vec<String> = params[..arrow].to_vec();
    let tail = &params[arrow + 1..];
    if sources.is_empty() {
        return Err("transmute needs at least one source before '->'".into());
    }
    let dst = tail.first().ok_or("transmute needs a destination after '->'")?;

    // Optional --size N after the destination.
    let mut dst_bytes: Option<u64> = None;
    let mut j = 1;
    while j < tail.len() {
        if tail[j] == "--size" {
            let v = tail.get(j + 1).ok_or("--size requires a value")?;
            dst_bytes = Some(parse_bytes(v)?);
            j += 2;
        } else {
            return Err(format!("unexpected argument '{}'", tail[j]));
        }
    }

    let tx = store
        .transmute(&sources, dst, dst_bytes)
        .map_err(|e| e.to_string())?;
    println!("The circle closes: sources reshaped into '{dst}'.");
    print_tx_summary(&tx);
    print_status_line(store).map_err(|e| e.to_string())?;
    Ok(())
}

fn cmd_list(store: &ExchangeStore) -> std::result::Result<(), String> {
    let objects = store.list().map_err(|e| e.to_string())?;
    if objects.is_empty() {
        println!("(vault is empty)");
        return Ok(());
    }
    println!("{:<24} {:>12}", "OBJECT", "BYTES");
    println!("{}", "-".repeat(37));
    for (name, bytes) in &objects {
        println!("{name:<24} {bytes:>12}");
    }
    let total: u64 = objects.iter().map(|(_, b)| *b).sum();
    println!("{}", "-".repeat(37));
    println!("{:<24} {:>12}", "TOTAL MASS", total);
    Ok(())
}

fn cmd_ledger(store: &ExchangeStore) -> std::result::Result<(), String> {
    let ledger = store.ledger().map_err(|e| e.to_string())?;
    print_ledger(&ledger);
    println!();
    print_status_block(&store.status().map_err(|e| e.to_string())?);
    Ok(())
}

fn cmd_status(store: &ExchangeStore) -> std::result::Result<(), String> {
    print_status_block(&store.status().map_err(|e| e.to_string())?);
    Ok(())
}

// ---------------------------------------------------------------------------
// Rendering helpers
// ---------------------------------------------------------------------------

fn print_ledger(ledger: &Ledger) {
    println!("=== ALCHEMIST'S LEDGER ===");
    if ledger.transactions.is_empty() {
        println!("(no transactions yet)");
        return;
    }
    for (i, tx) in ledger.transactions.iter().enumerate() {
        println!("#{:<3} {}", i + 1, describe_tx(tx));
    }
}

fn describe_tx(tx: &Transaction) -> String {
    let balance = if tx.kind.is_balanced() { "OK" } else { "VIOLATION" };
    match &tx.kind {
        TxKind::Grant { created } => format!(
            "[t={}] GRANT      +{} bytes -> '{}'  (Truth's toll; no sacrifice) [{}]",
            tx.timestamp, created.bytes, created.name, balance
        ),
        TxKind::Alchemize { created, sacrificed } => format!(
            "[t={}] ALCHEMIZE  created {}b '{}'  <=  sacrificed {}b [{}] {}",
            tx.timestamp,
            created.bytes,
            created.name,
            tx.kind.sacrificed_mass(),
            balance,
            render_sacrifices(sacrificed),
        ),
        TxKind::Transmute { created, sacrificed } => format!(
            "[t={}] TRANSMUTE  created {}b '{}'  <=  sacrificed {}b [{}] {}",
            tx.timestamp,
            created.bytes,
            created.name,
            tx.kind.sacrificed_mass(),
            balance,
            render_sacrifices(sacrificed),
        ),
    }
}

fn render_sacrifices(sacrificed: &[equivalent_exchange_fs::MassRef]) -> String {
    let items: Vec<String> = sacrificed
        .iter()
        .map(|m| format!("{}({}b)", m.name, m.bytes))
        .collect();
    format!("sacrificed: [{}]", items.join(", "))
}

fn print_tx_summary(tx: &Transaction) {
    println!("  ledger <- {}", describe_tx(tx));
}

fn print_status_line(store: &ExchangeStore) -> Result<()> {
    let s = store.status()?;
    println!(
        "  current mass: {} bytes across {} object(s)",
        s.current_mass, s.object_count
    );
    Ok(())
}

fn print_status_block(s: &ConservationStatus) {
    println!("=== CONSERVATION STATUS ===");
    println!("current mass on disk : {} bytes", s.current_mass);
    println!("objects in vault     : {}", s.object_count);
    println!("total ever granted   : {} bytes  (lawful mass source)", s.total_granted);
    println!("total ever created   : {} bytes", s.total_created);
    println!("total ever sacrificed: {} bytes", s.total_sacrificed);
    println!("every op balanced    : {}", yes_no(s.all_balanced));
    println!("mass <= granted      : {}", yes_no(s.current_mass <= s.total_granted));
    let verdict = if s.law_holds() {
        "LAW OF EQUIVALENT EXCHANGE UPHELD"
    } else {
        "LAW VIOLATED — investigate the ledger!"
    };
    println!(">>> {verdict}");
}

fn yes_no(b: bool) -> &'static str {
    if b {
        "yes"
    } else {
        "NO"
    }
}

// ---------------------------------------------------------------------------
// Parsing helpers
// ---------------------------------------------------------------------------

fn parse_bytes(s: &str) -> std::result::Result<u64, String> {
    s.parse::<u64>()
        .map_err(|_| format!("'{s}' is not a valid non-negative byte count"))
}

/// Parse `--sacrifice a,b,c` (comma-separated) from the trailing args.
fn parse_sacrifice_flag(params: &[String]) -> std::result::Result<Vec<String>, String> {
    if params.is_empty() {
        return Ok(Vec::new());
    }
    if params[0] != "--sacrifice" {
        return Err(format!("expected '--sacrifice', found '{}'", params[0]));
    }
    let list = params
        .get(1)
        .ok_or("--sacrifice requires a comma-separated list")?;
    let names: Vec<String> = list
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();
    Ok(names)
}

fn print_help() {
    println!(
        r#"eqx — the Equivalent-Exchange filesystem

"To obtain, something of equal value must be lost."

USAGE:
  eqx [--vault <dir>] <command> [args]

COMMANDS:
  grant <name> <bytes>                       Seed new mass (Truth's toll; logged).
  alchemize <name> <bytes> --sacrifice a,b   Create <name> of <bytes> by deleting a,b.
                                             Rejected unless size(a)+size(b) >= bytes.
  transmute <src...> -> <dst> [--size N]     Reshape sources into one dst object.
                                             dst mass defaults to combined source mass.
  list                                       List objects and their masses.
  ledger                                     Print the full audit trail + status.
  status                                     Print the conservation summary.
  help                                       Show this message.

The vault defaults to ./vault (override with --vault or $EQX_VAULT).
Nothing outside the vault directory is ever read, written, or deleted."#
    );
}
