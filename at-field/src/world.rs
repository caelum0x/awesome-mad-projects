//! The world: orchestrates entities, routes signals, and keeps the event log.

use std::collections::HashMap;

use crate::dirac_sea::{DiracAccess, DiracSea};
use crate::entity::Entity;
use crate::event::{Event, EventKind};
use crate::signal::{classify, Outcome, Plane, Signal};

/// Holds every entity and the immutable event log. Signals are routed here.
pub struct World {
    entities: Vec<Entity>,
    index: HashMap<String, usize>,
    log: Vec<Event>,
    tick: u64,
}

impl World {
    pub fn new() -> Self {
        Self {
            entities: Vec::new(),
            index: HashMap::new(),
            log: Vec::new(),
            tick: 0,
        }
    }

    /// Add an entity. Panics if the name is already taken (a programming error
    /// in the demo, not a runtime input path).
    pub fn spawn(&mut self, entity: Entity) {
        assert!(
            !self.index.contains_key(&entity.name),
            "duplicate entity name: {}",
            entity.name
        );
        self.index.insert(entity.name.clone(), self.entities.len());
        self.entities.push(entity);
    }

    /// Borrow an entity by name.
    pub fn get(&self, name: &str) -> Option<&Entity> {
        self.index.get(name).map(|&i| &self.entities[i])
    }

    /// The full event log so far.
    pub fn log(&self) -> &[Event] {
        &self.log
    }

    /// The current tick counter.
    pub fn tick(&self) -> u64 {
        self.tick
    }

    /// Route a signal, advancing the clock by one tick. Returns the resulting
    /// [`Outcome`]. Unknown targets are reported (and logged) as reflected
    /// with zero effect.
    pub fn send(&mut self, signal: Signal) -> Outcome {
        self.tick += 1;
        let tick = self.tick;

        let target_idx = match self.index.get(&signal.to) {
            Some(&i) => i,
            None => return Outcome::Reflected, // no such membrane to cross
        };

        match signal.plane {
            Plane::DiracSea => self.route_dirac(tick, target_idx, signal),
            Plane::Normal => self.route_normal(tick, target_idx, signal),
        }
    }

    fn route_normal(&mut self, tick: u64, target_idx: usize, signal: Signal) -> Outcome {
        let entity = &mut self.entities[target_idx];
        let field_before = entity.field.strength();
        let outcome = classify(signal.impact, field_before);

        // Every attack — landed or not — corrodes the membrane.
        entity.field.absorb_attack(signal.impact);
        let field_after = entity.field.strength();
        let streak_after = entity.field.assault_streak();

        if outcome.delivered() {
            entity.inbox.push(signal.clone());
        }

        self.log.push(Event {
            tick,
            actor: signal.to.clone(),
            field_before,
            field_after,
            streak_after,
            kind: EventKind::Delivery {
                source: signal.from,
                impact: signal.impact,
                outcome,
                plane: Plane::Normal,
                payload: signal.payload,
            },
        });
        outcome
    }

    fn route_dirac(&mut self, tick: u64, target_idx: usize, signal: Signal) -> Outcome {
        let sender_capable = self
            .get(&signal.from)
            .map(|e| e.dirac_capable)
            .unwrap_or(false);
        let target_capable = self.entities[target_idx].dirac_capable;

        let access = DiracSea::check(sender_capable, target_capable);
        let outcome = match access {
            DiracAccess::Granted => Outcome::Penetrated,
            _ => Outcome::DiracBlocked,
        };

        let entity = &mut self.entities[target_idx];
        let field = entity.field.strength();
        if access == DiracAccess::Granted {
            DiracSea::deliver(&mut entity.dirac_inbox, signal.clone());
        }

        self.log.push(Event {
            tick,
            actor: signal.to.clone(),
            field_before: field,
            field_after: field, // Dirac plane ignores AT Fields entirely
            streak_after: entity.field.assault_streak(),
            kind: EventKind::Delivery {
                source: signal.from,
                impact: signal.impact,
                outcome,
                plane: Plane::DiracSea,
                payload: signal.payload,
            },
        });
        outcome
    }

    /// A quiet tick for the whole world: every entity's field regenerates and
    /// its assault streak cools. Only fields that actually recover are logged.
    pub fn rest(&mut self) {
        self.tick += 1;
        let tick = self.tick;
        for entity in &mut self.entities {
            let before = entity.field.strength();
            let recovered = entity.field.regenerate();
            if recovered > 0.0 {
                self.log.push(Event {
                    tick,
                    actor: entity.name.clone(),
                    field_before: before,
                    field_after: entity.field.strength(),
                    streak_after: entity.field.assault_streak(),
                    kind: EventKind::Regeneration { recovered },
                });
            }
        }
    }
}

impl Default for World {
    fn default() -> Self {
        Self::new()
    }
}
