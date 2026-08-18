//! AT Field demo: entities exchange signals across their ego boundaries.
//!
//! Pure in-memory simulation — see the crate docs and README for the safety
//! statement. Run with `cargo run`.

#![forbid(unsafe_code)]

use at_field::{Entity, Plane, Signal, World};

/// Print every log entry the world has accumulated since `from`, returning the
/// new log length.
fn drain_log(world: &World, from: usize) -> usize {
    let log = world.log();
    for event in &log[from..] {
        println!("  {event}");
    }
    log.len()
}

fn scene(title: &str) {
    println!("\n=== {title} ===");
}

fn main() {
    let mut world = World::new();

    // --- Cast of in-memory entities (NOT real OS processes) ---
    world.spawn(Entity::new("Unit-01", 60.0));
    world.spawn(Entity::new("Unit-00", 45.0));
    world.spawn(Entity::new("Sachiel", 90.0)); // an Angel: heavy hitter
    world.spawn(Entity::new("Kaworu", 70.0).dirac_capable());
    world.spawn(Entity::new("Lilith", 30.0).dirac_capable());

    println!("AT Field :: process isolation as an ego boundary (simulation)");
    println!("Entities: Unit-01(60) Unit-00(45) Sachiel(90) Kaworu(70,dirac) Lilith(30,dirac)");

    let mut cursor = 0;

    // --- Scene 1: ordinary exchange — penetrate / reflect / absorb ---
    scene("Scene 1: ordinary signals meet ordinary fields");
    // Strong enough to cross Unit-00's field (45): penetrates.
    world.send(Signal::new("Unit-01", "Unit-00", 50.0, "sync clock", Plane::Normal));
    // Rattles Unit-01's field (60) but does not cross: reflected.
    world.send(Signal::new("Unit-00", "Unit-01", 40.0, "ping", Plane::Normal));
    // Far too weak for Sachiel's field (90): absorbed.
    world.send(Signal::new("Unit-00", "Sachiel", 15.0, "who are you?", Plane::Normal));
    cursor = drain_log(&world, cursor);

    // --- Scene 2: a sustained barrage corrodes and finally breaks a field ---
    scene("Scene 2: Sachiel barrages Unit-00 — field corrosion and a break");
    let mut hit = 0;
    loop {
        hit += 1;
        // Each blow is below Unit-00's *initial* field, but corrosion compounds.
        let outcome = world.send(Signal::new(
            "Sachiel",
            "Unit-00",
            30.0,
            format!("barrage #{hit}"),
            Plane::Normal,
        ));
        if outcome == at_field::Outcome::Penetrated {
            println!("  >> Unit-00's AT Field has been breached after {hit} blows!");
            break;
        }
        if hit >= 20 {
            println!("  >> barrage exhausted without a clean break");
            break;
        }
    }
    cursor = drain_log(&world, cursor);

    // --- Scene 3: rest lets a corroded field regenerate ---
    scene("Scene 3: quiet ticks — Unit-00's field regenerates");
    for _ in 0..4 {
        world.rest();
    }
    cursor = drain_log(&world, cursor);

    // --- Scene 4: the Dirac Sea, gated purely by capability ---
    scene("Scene 4: the Dirac Sea plane (capability-gated, ignores fields)");
    // Both Kaworu and Lilith hold the flag: granted, regardless of field height.
    world.send(Signal::new("Kaworu", "Lilith", 1.0, "the sea remembers", Plane::DiracSea));
    // Unit-01 lacks the capability: blocked even though it is powerful.
    world.send(Signal::new("Unit-01", "Kaworu", 999.0, "let me in", Plane::DiracSea));
    // Kaworu (capable) -> Unit-01 (not capable): blocked at the far end.
    world.send(Signal::new("Kaworu", "Unit-01", 5.0, "come below", Plane::DiracSea));
    drain_log(&world, cursor);

    // --- Final summary ---
    scene("Final state");
    for name in ["Unit-01", "Unit-00", "Sachiel", "Kaworu", "Lilith"] {
        if let Some(e) = world.get(name) {
            println!(
                "  {:<8} field {:>5.1}  normal-inbox {}  dirac-inbox {}",
                e.name,
                e.field.strength(),
                e.inbox.len(),
                e.dirac_inbox.len(),
            );
        }
    }
    println!("\nTotal events logged: {}", world.log().len());
}
