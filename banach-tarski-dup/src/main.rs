//! CLI for the Banach-Tarski "Duplicator".
//!
//! Subcommands:
//!   verify [L]                 Verify the paradox on the ball of radius L (default 6).
//!   words  [L]                 Enumerate and classify reduced words up to length L.
//!   reconstruct [L]            Show the two-copies reconstruction on the ball of radius L.
//!   theatrical <src> <dst>     CLEARLY-LABELLED fake "file duplication" (hard link).
//!   help                       Show this help.

use std::env;
use std::path::Path;
use std::process::ExitCode;

use banach_tarski_dup::decomp::{
    classify_label, enumerate_ball, reconstruct_copy, verify, Piece,
};
use banach_tarski_dup::theatrical::theatrical_duplicate;
use banach_tarski_dup::word::Letter;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let cmd = args.get(1).map(String::as_str).unwrap_or("verify");

    match cmd {
        "verify" => cmd_verify(parse_len(args.get(2), 6)),
        "words" => cmd_words(parse_len(args.get(2), 4)),
        "reconstruct" => cmd_reconstruct(parse_len(args.get(2), 5)),
        "theatrical" => cmd_theatrical(args.get(2), args.get(3)),
        "help" | "-h" | "--help" => {
            print_help();
            ExitCode::SUCCESS
        }
        other => {
            eprintln!("unknown command: {other}\n");
            print_help();
            ExitCode::from(2)
        }
    }
}

fn parse_len(arg: Option<&String>, default: usize) -> usize {
    arg.and_then(|s| s.parse::<usize>().ok()).unwrap_or(default)
}

fn print_help() {
    println!(
        "Banach-Tarski Duplicator (free-group F2 paradox)\n\
         \n\
         USAGE: bt-dup <command> [args]\n\
         \n\
         COMMANDS:\n  \
           verify [L]              Verify the paradox on the ball of radius L (default 6)\n  \
           words  [L]              Enumerate + classify reduced words up to length L (default 4)\n  \
           reconstruct [L]         Show the two-copies reconstruction on ball radius L (default 5)\n  \
           theatrical <src> <dst>  CLEARLY-LABELLED fake file 'duplication' (hard link, no real copy)\n  \
           help                    Show this help\n\
         \n\
         The math (verify/words/reconstruct) is real and constructive.\n\
         The 'theatrical' file mode is stagecraft and duplicates NO real bytes."
    );
}

fn cmd_verify(radius: usize) -> ExitCode {
    let report = verify(radius);
    println!("== Banach-Tarski paradox on F2, ball radius {radius} ==\n");
    println!("Reduced words in ball: {}", report.target_ball_size);
    println!("\nPartition into 5 pieces (counts within the ball):");
    for (label, count) in &report.piece_counts {
        println!("  {label:<12} {count:>10}");
    }
    println!(
        "\nPartition is disjoint : {}",
        yes_no(report.partition_is_disjoint)
    );
    println!(
        "Partition covers ball : {}",
        yes_no(report.partition_covers)
    );
    println!("\nParadoxical reconstructions:");
    println!(
        "  a . W(a^-1)  U  W(a)  ==  F2  : {}",
        yes_no(report.copy_a_covers)
    );
    println!(
        "  b . W(b^-1)  U  W(b)  ==  F2  : {}",
        yes_no(report.copy_b_covers)
    );
    println!(
        "\nTwo full copies of F2 rebuilt from a partition of one : {}",
        yes_no(report.all_ok())
    );

    if report.all_ok() {
        ExitCode::SUCCESS
    } else {
        eprintln!("\nVERIFICATION FAILED");
        ExitCode::FAILURE
    }
}

fn cmd_words(max_len: usize) -> ExitCode {
    let ball = enumerate_ball(max_len);
    println!("Reduced words up to length {max_len} ({} total):\n", ball.len());
    for w in &ball {
        println!("  {:<14} len={}  piece={}", w.to_compact(), w.len(), classify_label(w));
    }
    ExitCode::SUCCESS
}

fn cmd_reconstruct(radius: usize) -> ExitCode {
    let target: std::collections::HashSet<_> = enumerate_ball(radius).into_iter().collect();
    let copy_a = reconstruct_copy(radius, Letter::A);
    let copy_b = reconstruct_copy(radius, Letter::B);

    println!("== Two-copies reconstruction on ball radius {radius} ==\n");
    println!("Target ball (one copy of F2, truncated): {} words", target.len());
    println!(
        "Copy A = (W(a) U a.W(a^-1)) rebuilt         : {} words  -> equals target? {}",
        copy_a.len(),
        yes_no(copy_a == target)
    );
    println!(
        "Copy B = (W(b) U b.W(b^-1)) rebuilt         : {} words  -> equals target? {}",
        copy_b.len(),
        yes_no(copy_b == target)
    );

    let ok = copy_a == target && copy_b == target;
    println!(
        "\nBoth copies each equal the whole ball, from a partition of ONE : {}",
        yes_no(ok)
    );
    println!("\n(Note: {} + {} + ... pieces of a single F2 produced TWO full copies.)",
        Piece::StartsWith(Letter::A).label(),
        Piece::StartsWith(Letter::A_INV).label());

    if ok { ExitCode::SUCCESS } else { ExitCode::FAILURE }
}

fn cmd_theatrical(src: Option<&String>, dst: Option<&String>) -> ExitCode {
    let (src, dst) = match (src, dst) {
        (Some(s), Some(d)) => (s, d),
        _ => {
            eprintln!("usage: bt-dup theatrical <src> <dst>");
            return ExitCode::from(2);
        }
    };
    println!("!! THEATRICAL MODE --- this does NOT duplicate real bytes. !!\n");
    match theatrical_duplicate(Path::new(src), Path::new(dst)) {
        Ok(result) => {
            println!("original : {}", result.original.display());
            println!("'copy'   : {}", result.copy.display());
            println!("method   : {}", result.method);
            println!("shares bytes with original : {}", result.shares_bytes_with_original);
            println!("\n{}", result.disclaimer);
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("theatrical duplication failed: {e}");
            ExitCode::FAILURE
        }
    }
}

fn yes_no(b: bool) -> &'static str {
    if b { "YES" } else { "NO" }
}
