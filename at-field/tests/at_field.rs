//! Integration tests for the AT Field simulation.

use at_field::{
    field::{AtField, FieldDynamics},
    signal::classify,
    Entity, Outcome, Plane, Signal, World,
};

fn world_with_cast() -> World {
    let mut w = World::new();
    w.spawn(Entity::new("A", 60.0));
    w.spawn(Entity::new("B", 45.0));
    w.spawn(Entity::new("K", 70.0).dirac_capable());
    w.spawn(Entity::new("L", 30.0).dirac_capable());
    w
}

#[test]
fn strong_signal_penetrates_and_lands_in_inbox() {
    let mut w = world_with_cast();
    let outcome = w.send(Signal::new("A", "B", 50.0, "hi", Plane::Normal));
    assert_eq!(outcome, Outcome::Penetrated);
    assert_eq!(w.get("B").unwrap().inbox.len(), 1);
}

#[test]
fn medium_signal_reflects_and_delivers_nothing() {
    let mut w = world_with_cast();
    // Against A's field of 60, an impact of 40 is >= 30 but < 60: reflected.
    let outcome = w.send(Signal::new("B", "A", 40.0, "ping", Plane::Normal));
    assert_eq!(outcome, Outcome::Reflected);
    assert_eq!(w.get("A").unwrap().inbox.len(), 0);
}

#[test]
fn weak_signal_is_absorbed() {
    let mut w = world_with_cast();
    // Against A's field of 60, impact 10 < 30: absorbed.
    let outcome = w.send(Signal::new("B", "A", 10.0, "psst", Plane::Normal));
    assert_eq!(outcome, Outcome::Absorbed);
    assert_eq!(w.get("A").unwrap().inbox.len(), 0);
}

#[test]
fn classify_boundaries() {
    assert_eq!(classify(60.0, 60.0), Outcome::Penetrated);
    assert_eq!(classify(59.9, 60.0), Outcome::Reflected);
    assert_eq!(classify(30.0, 60.0), Outcome::Reflected);
    assert_eq!(classify(29.9, 60.0), Outcome::Absorbed);
}

#[test]
fn sustained_barrage_corrodes_and_eventually_breaks_a_field() {
    let mut w = world_with_cast();
    let mut broke = false;
    for i in 0..20 {
        let outcome = w.send(Signal::new("K", "B", 30.0, format!("hit {i}"), Plane::Normal));
        if outcome == Outcome::Penetrated {
            broke = true;
            break;
        }
    }
    assert!(broke, "a sustained sub-threshold barrage should eventually break the field");
    // The break means at least one message got through.
    assert!(w.get("B").unwrap().inbox.len() >= 1);
}

#[test]
fn attenuation_is_monotone_in_streak_and_impact() {
    let dyn_ = FieldDynamics::default();
    let mut f = AtField::new(100.0, dyn_);

    // Monotone in impact at a fixed streak.
    assert!(f.attenuation(60.0) > f.attenuation(30.0));
    assert_eq!(f.attenuation(0.0), 0.0);

    // Monotone (non-decreasing) in streak: each absorbed attack raises the
    // per-blow attenuation for the same impact.
    let a0 = f.attenuation(30.0);
    f.absorb_attack(30.0);
    let a1 = f.attenuation(30.0);
    f.absorb_attack(30.0);
    let a2 = f.attenuation(30.0);
    assert!(a1 > a0);
    assert!(a2 > a1);
}

#[test]
fn field_regenerates_but_never_exceeds_max() {
    let dyn_ = FieldDynamics::default();
    let mut f = AtField::new(10.0, dyn_);
    f.absorb_attack(50.0); // corrode a bit
    let low = f.strength();
    f.regenerate();
    assert!(f.strength() > low);
    // Streak resets on rest.
    assert_eq!(f.assault_streak(), 0);
    for _ in 0..1000 {
        f.regenerate();
    }
    assert!(f.strength() <= dyn_.max_strength);
}

#[test]
fn dirac_plane_requires_capability_on_both_ends() {
    let mut w = world_with_cast();

    // K and L are both capable: granted.
    let ok = w.send(Signal::new("K", "L", 1.0, "below", Plane::DiracSea));
    assert_eq!(ok, Outcome::Penetrated);
    assert_eq!(w.get("L").unwrap().dirac_inbox.len(), 1);

    // A is not capable as a sender: blocked.
    let blocked_sender = w.send(Signal::new("A", "K", 999.0, "in", Plane::DiracSea));
    assert_eq!(blocked_sender, Outcome::DiracBlocked);

    // K capable, but A not capable as a receiver: blocked at far end.
    let blocked_target = w.send(Signal::new("K", "A", 5.0, "come", Plane::DiracSea));
    assert_eq!(blocked_target, Outcome::DiracBlocked);
    assert_eq!(w.get("A").unwrap().dirac_inbox.len(), 0);
}

#[test]
fn dirac_plane_ignores_field_strength() {
    let mut w = world_with_cast();
    let before = w.get("L").unwrap().field.strength();
    // Tiny impact still reaches the Dirac inbox; field is untouched.
    w.send(Signal::new("K", "L", 0.5, "x", Plane::DiracSea));
    let after = w.get("L").unwrap().field.strength();
    assert_eq!(before, after);
    assert_eq!(w.get("L").unwrap().dirac_inbox.len(), 1);
    // Nothing landed on the normal inbox.
    assert_eq!(w.get("L").unwrap().inbox.len(), 0);
}
