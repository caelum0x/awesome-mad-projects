//! Integration tests for the JoJo Stand simulation engine.
//! All state is in-memory; no OS resources are touched.

use jojo_stands::process::Task;
use jojo_stands::{Command, Scheduler, Stand};

fn seed(sched: &mut Scheduler, name: &str, lane: &str, n: usize) -> u64 {
    let tasks: Vec<Task> = (0..n).map(|i| Task::new(format!("{name}-{i}"))).collect();
    sched.spawn(name, lane, tasks)
}

#[test]
fn normal_tick_advances_all_processes() {
    let mut sched = Scheduler::new(4);
    let a = seed(&mut sched, "a", "main", 3);
    let b = seed(&mut sched, "b", "main", 3);
    sched.tick();
    assert_eq!(sched.get(a).unwrap().work_done, 1);
    assert_eq!(sched.get(b).unwrap().work_done, 1);
    assert_eq!(sched.tick, 1);
}

#[test]
fn the_world_freezes_others_but_not_caster() {
    let mut sched = Scheduler::new(4);
    let caster = seed(&mut sched, "dio", "main", 5);
    let victim = seed(&mut sched, "victim", "main", 5);
    sched.assign_stand(caster, Stand::TheWorld).unwrap();

    sched.the_world(caster, 2).unwrap();
    sched.tick();
    sched.tick();

    // Caster advanced twice, victim advanced zero times (frozen for both ticks).
    assert_eq!(sched.get(caster).unwrap().work_done, 2);
    assert_eq!(sched.get(victim).unwrap().work_done, 0);

    // Freeze expired; a third tick advances the victim.
    sched.tick();
    assert_eq!(sched.get(victim).unwrap().work_done, 1);
}

#[test]
fn killer_queen_detonates_on_signal() {
    let mut sched = Scheduler::new(4);
    let kira = seed(&mut sched, "kira", "main", 2);
    let target = seed(&mut sched, "target", "main", 2);
    sched.assign_stand(kira, Stand::KillerQueen).unwrap();

    sched.killer_queen_mark(kira, target).unwrap();
    assert!(sched.get(target).is_some());
    sched.send_signal(target, "SIGUSR1").unwrap();
    // Detonated => removed from the sim table.
    assert!(sched.get(target).is_none());
}

#[test]
fn unprimed_signal_is_harmless() {
    let mut sched = Scheduler::new(4);
    let p = seed(&mut sched, "p", "main", 2);
    sched.send_signal(p, "SIGTERM").unwrap();
    assert!(sched.get(p).is_some());
}

#[test]
fn king_crimson_rolls_back_state() {
    let mut sched = Scheduler::new(8);
    let giorno = seed(&mut sched, "giorno", "main", 10);
    sched.assign_stand(giorno, Stand::KingCrimson).unwrap();

    sched.tick(); // t1 work_done=1
    sched.tick(); // t2 work_done=2
    let checkpoint = sched.get(giorno).unwrap().work_done; // 2
    sched.tick(); // t3 work_done=3
    sched.tick(); // t4 work_done=4
    assert_eq!(sched.get(giorno).unwrap().work_done, 4);

    sched.king_crimson_erase(giorno, 2).unwrap(); // back to t2
    assert_eq!(sched.tick, 2);
    assert_eq!(sched.get(giorno).unwrap().work_done, checkpoint);
}

#[test]
fn king_crimson_outside_window_errors() {
    let mut sched = Scheduler::new(2);
    let p = seed(&mut sched, "p", "main", 10);
    sched.assign_stand(p, Stand::KingCrimson).unwrap();
    sched.tick();
    sched.tick();
    sched.tick();
    // History only keeps 2 ticks; asking for 3 back is out of range.
    assert!(sched.king_crimson_erase(p, 3).is_err());
}

#[test]
fn sticky_fingers_moves_process_and_queue() {
    let mut sched = Scheduler::new(4);
    let bruno = seed(&mut sched, "bruno", "main", 1);
    let target = seed(&mut sched, "target", "main", 3);
    sched.assign_stand(bruno, Stand::StickyFingers).unwrap();

    let qlen_before = sched.get(target).unwrap().queue.len();
    sched.sticky_fingers_zip(bruno, target, "isolated").unwrap();

    let moved = sched.get(target).unwrap();
    assert_eq!(moved.lane, "isolated");
    // Its queue travels with it.
    assert_eq!(moved.queue.len(), qlen_before);
}

#[test]
fn wrong_stand_is_rejected() {
    let mut sched = Scheduler::new(4);
    let p = seed(&mut sched, "p", "main", 2);
    sched.assign_stand(p, Stand::KillerQueen).unwrap();
    // p does not wield The World.
    assert!(sched.the_world(p, 1).is_err());
}

#[test]
fn command_interface_drives_engine() {
    let mut sched = Scheduler::new(4);
    let pid = Command::Spawn { name: "cmd".into(), lane: "main".into(), tasks: vec!["x".into(), "y".into()] }
        .apply(&mut sched)
        .unwrap();
    Command::AssignStand { pid, stand: Stand::TheWorld }.apply(&mut sched);
    Command::Tick { n: 1 }.apply(&mut sched);
    assert_eq!(sched.get(pid).unwrap().work_done, 1);
    assert_eq!(sched.get(pid).unwrap().stand, Some(Stand::TheWorld));
}
