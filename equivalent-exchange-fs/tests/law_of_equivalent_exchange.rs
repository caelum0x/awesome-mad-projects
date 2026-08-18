//! Integration tests proving the Law of Equivalent Exchange holds:
//! mass is conserved, free lunches are rejected, and the sandbox is respected.

use std::path::PathBuf;

use equivalent_exchange_fs::error::ExchangeError;
use equivalent_exchange_fs::ExchangeStore;

/// Create a unique temporary vault directory for an isolated test.
fn temp_vault(tag: &str) -> PathBuf {
    let mut p = std::env::temp_dir();
    let uniq = format!(
        "eqx-it-{}-{}-{}",
        tag,
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    );
    p.push(uniq);
    p
}

fn cleanup(p: &PathBuf) {
    std::fs::remove_dir_all(p).ok();
}

#[test]
fn grant_then_balanced_alchemy_conserves_mass() {
    let dir = temp_vault("balanced");
    let store = ExchangeStore::open(&dir).unwrap();

    // Truth's toll: seed 500 bytes.
    store.grant("ore", 500).unwrap();
    assert_eq!(store.status().unwrap().current_mass, 500);

    // 300 <= 500: allowed. Sacrifices "ore".
    store.alchemize("sword", 300, &["ore".into()]).unwrap();

    let s = store.status().unwrap();
    assert_eq!(s.current_mass, 300, "new object must be exactly 300 bytes");
    assert_eq!(s.total_granted, 500);
    assert!(s.all_balanced, "every op must be balanced");
    assert!(s.law_holds(), "current mass ({}) must not exceed granted (500)", s.current_mass);
    // Conservation: mass on disk never exceeds what was granted.
    assert!(s.current_mass <= s.total_granted);

    cleanup(&dir);
}

#[test]
fn unbalanced_alchemy_is_rejected_and_disk_unchanged() {
    let dir = temp_vault("unbalanced");
    let store = ExchangeStore::open(&dir).unwrap();

    store.grant("pebble", 50).unwrap();

    // Attempt a free lunch: create 1000 bytes by sacrificing only 50.
    let err = store
        .alchemize("gold_mountain", 1000, &["pebble".into()])
        .unwrap_err();
    match err {
        ExchangeError::UnbalancedExchange { created, sacrificed } => {
            assert_eq!(created, 1000);
            assert_eq!(sacrificed, 50);
        }
        other => panic!("expected UnbalancedExchange, got {other:?}"),
    }

    // Nothing changed: pebble still there, no new object, mass still 50.
    assert!(store.vault().exists("pebble").unwrap());
    assert!(!store.vault().exists("gold_mountain").unwrap());
    assert_eq!(store.status().unwrap().current_mass, 50);

    cleanup(&dir);
}

#[test]
fn creating_from_nothing_is_rejected() {
    let dir = temp_vault("nothing");
    let store = ExchangeStore::open(&dir).unwrap();

    // No sacrifice at all -> EmptySacrifice.
    let err = store.alchemize("free", 1, &[]).unwrap_err();
    assert!(matches!(err, ExchangeError::EmptySacrifice));
    assert_eq!(store.status().unwrap().current_mass, 0);

    cleanup(&dir);
}

#[test]
fn transmute_default_conserves_all_mass() {
    let dir = temp_vault("transmute");
    let store = ExchangeStore::open(&dir).unwrap();

    store.grant("a", 120).unwrap();
    store.grant("b", 80).unwrap();

    // Reshape a + b (200 bytes) into one object; default keeps all mass.
    store.transmute(&["a".into(), "b".into()], "alloy", None).unwrap();

    let s = store.status().unwrap();
    assert_eq!(s.current_mass, 200);
    assert_eq!(s.object_count, 1);
    assert_eq!(store.vault().size_of("alloy").unwrap(), 200);
    assert!(s.law_holds());
    // sources are consumed
    assert!(!store.vault().exists("a").unwrap());
    assert!(!store.vault().exists("b").unwrap());

    cleanup(&dir);
}

#[test]
fn transmute_may_lose_mass_but_never_gain() {
    let dir = temp_vault("lose");
    let store = ExchangeStore::open(&dir).unwrap();

    store.grant("scrap", 300).unwrap();

    // Ask for less than available: allowed (mass may be lost).
    store.transmute(&["scrap".into()], "ring", Some(100)).unwrap();
    assert_eq!(store.vault().size_of("ring").unwrap(), 100);
    assert!(store.status().unwrap().law_holds());

    // Now seed and try to gain mass: rejected.
    store.grant("dust", 10).unwrap();
    let err = store
        .transmute(&["dust".into()], "boulder", Some(9999))
        .unwrap_err();
    assert!(matches!(err, ExchangeError::UnbalancedExchange { .. }));
    assert!(store.vault().exists("dust").unwrap());

    cleanup(&dir);
}

#[test]
fn law_holds_across_a_long_random_session() {
    // Property-style check: after any sequence of grants + balanced exchanges,
    // current mass never exceeds total granted, and every op is balanced.
    let dir = temp_vault("session");
    let store = ExchangeStore::open(&dir).unwrap();

    store.grant("seed", 1000).unwrap();
    store.alchemize("x", 400, &["seed".into()]).unwrap(); // 400 <= 1000
    // remaining object: x(400). Grant more, then chain exchanges.
    store.grant("seed2", 600).unwrap(); // total granted 1600, mass now 1000
    store
        .alchemize("y", 900, &["x".into(), "seed2".into()])
        .unwrap(); // 900 <= 1000
    store.transmute(&["y".into()], "z", Some(500)).unwrap(); // lose 400

    let s = store.status().unwrap();
    assert!(s.all_balanced);
    assert!(s.current_mass <= s.total_granted);
    assert_eq!(s.total_granted, 1600);
    assert_eq!(s.current_mass, 500);
    assert!(s.law_holds());

    // Ledger replay must agree with on-disk mass invariant.
    let ledger = store.ledger().unwrap();
    assert!(ledger.all_balanced());
    assert!(ledger.total_created() >= s.current_mass);

    cleanup(&dir);
}

#[test]
fn sandbox_refuses_path_traversal_names() {
    let dir = temp_vault("sandbox");
    let store = ExchangeStore::open(&dir).unwrap();

    for bad in ["../escape", "..", "a/b", "/etc/passwd"] {
        assert!(
            store.grant(bad, 10).is_err(),
            "name '{bad}' must be rejected"
        );
    }
    // The vault stayed empty; nothing escaped.
    assert_eq!(store.status().unwrap().current_mass, 0);

    cleanup(&dir);
}
