//! # AT Field
//!
//! A pure-userspace *simulation* of process isolation reimagined as the
//! Evangelion "Absolute Terror Field" (AT Field): the ego boundary that keeps
//! one mind (process) distinct from another.
//!
//! ## Safety
//!
//! Nothing here touches the real operating system. "Entities" are plain
//! in-memory actors, "signals" are plain structs pushed into `Vec` inboxes,
//! and "fields" are `f64` values. No real processes, memory pages, threads,
//! or OS signals are created, inspected, or manipulated. `#![forbid(unsafe_code)]`
//! is enforced crate-wide.
//!
//! ## The model
//!
//! * Each [`Entity`] owns an [`AtField`] (its boundary membrane) and inboxes.
//! * A [`Signal`] from one entity to another must *penetrate* the target's
//!   field: it succeeds only if the sender's `impact >= target.field.strength`.
//! * Otherwise the signal is [`Outcome::Reflected`] (bounced) or
//!   [`Outcome::Absorbed`] (too weak, soaked into the membrane).
//! * Sustained assault *corrodes* a field via a monotone attenuation function;
//!   an unattacked field slowly *regenerates*.
//! * A separate [`Plane::DiracSea`] message plane is reachable only by entities
//!   holding the Dirac capability flag.

#![forbid(unsafe_code)]

pub mod dirac_sea;
pub mod entity;
pub mod event;
pub mod field;
pub mod signal;
pub mod world;

pub use dirac_sea::DiracSea;
pub use entity::Entity;
pub use event::{Event, EventKind};
pub use field::{AtField, FieldDynamics};
pub use signal::{Outcome, Plane, Signal};
pub use world::World;
