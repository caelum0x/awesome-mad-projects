//! JoJo Stand System — a safe, pure in-memory process simulation.
//!
//! SAFETY: Nothing in this crate touches the operating system. There are no
//! real threads, no OS processes, no PIDs, no signals sent to the kernel, and
//! no `unsafe` code. Every "process" is an in-memory [`SimProcess`] value living
//! inside a [`Scheduler`]'s own table. Stand abilities are ordinary Rust
//! functions that mutate this simulated table. The worst thing that can happen
//! is that a simulated struct gets dropped from a `HashMap`.
#![forbid(unsafe_code)]

pub mod command;
pub mod process;
pub mod scheduler;
pub mod stand;

pub use command::Command;
pub use process::{ProcState, SimProcess, Task};
pub use scheduler::Scheduler;
pub use stand::Stand;
