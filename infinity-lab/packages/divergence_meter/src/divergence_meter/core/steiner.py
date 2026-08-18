"""Reading Steiner: persist and recall named worldline snapshots.

"Reading Steiner" is Okabe Rintaro's ability to retain memories across worldline
shifts. Here it is a tiny JSON-backed store: you :func:`save_line` the current
divergence reading under a name, and later :func:`get_line` back to it to see the
delta between where you are now and the line you recorded.

The store is a plain JSON object mapping ``name -> record``. All writes are done
by rewriting a *new* dict (never mutating the loaded one in place) and then
atomically replacing the file.

This module is part of the pure ``core`` layer (stdlib + ``commons.core`` only).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from divergence_meter.core.divergence import DivergenceReading

# Package root (the directory that contains ``src/``); the default store lives
# there so the tool is fully self-contained and never writes elsewhere.
_PACKAGE_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DEFAULT_STORE_PATH = os.path.join(_PACKAGE_ROOT, "worldlines_store.json")


class SteinerError(Exception):
    """Raised for any store read/write or lookup failure."""


@dataclass(frozen=True)
class WorldlineRecord:
    """A saved worldline entry."""

    name: str
    value: float
    display: str
    digest: str
    origin: str
    saved_at: str

    @classmethod
    def from_reading(cls, name: str, reading: DivergenceReading) -> "WorldlineRecord":
        return cls(
            name=name,
            value=reading.value,
            display=reading.display,
            digest=reading.digest,
            origin=reading.origin,
            saved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


def _load_raw(store_path: str) -> dict:
    """Load the raw store dict, returning ``{}`` when the file is absent."""
    if not os.path.exists(store_path):
        return {}
    try:
        with open(store_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SteinerError(f"Store at '{store_path}' is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise SteinerError(f"Store at '{store_path}' is corrupt (expected an object).")
    return data


def _atomic_write(store_path: str, data: dict) -> None:
    """Write ``data`` to ``store_path`` atomically via a temp file + rename."""
    directory = os.path.dirname(store_path) or "."
    try:
        os.makedirs(directory, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
        os.replace(tmp_path, store_path)
    except OSError as exc:
        raise SteinerError(f"Could not write store '{store_path}': {exc}") from exc


def save_line(
    name: str, reading: DivergenceReading, *, store_path: str = DEFAULT_STORE_PATH
) -> WorldlineRecord:
    """Save ``reading`` under ``name`` (overwriting any existing entry).

    Returns the stored record. Does not mutate the on-disk dict in place; a new
    dict is constructed and written atomically.
    """
    name = (name or "").strip()
    if not name:
        raise SteinerError("Worldline name must not be empty.")

    record = WorldlineRecord.from_reading(name, reading)
    current = _load_raw(store_path)
    # Build a new mapping rather than mutating the loaded one.
    updated = {**current, name: asdict(record)}
    _atomic_write(store_path, updated)
    return record


def get_line(name: str, *, store_path: str = DEFAULT_STORE_PATH) -> WorldlineRecord:
    """Recall a previously saved worldline by name.

    Raises:
        SteinerError: If no worldline with that name exists.
    """
    name = (name or "").strip()
    data = _load_raw(store_path)
    if name not in data:
        available = ", ".join(sorted(data)) or "(none)"
        raise SteinerError(f"No worldline named '{name}'. Saved lines: {available}.")
    entry = data[name]
    try:
        return WorldlineRecord(
            name=entry["name"],
            value=float(entry["value"]),
            display=entry["display"],
            digest=entry["digest"],
            origin=entry["origin"],
            saved_at=entry["saved_at"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SteinerError(f"Worldline '{name}' record is malformed: {exc}") from exc


def list_lines(*, store_path: str = DEFAULT_STORE_PATH) -> list[WorldlineRecord]:
    """Return all saved worldlines sorted by name."""
    data = _load_raw(store_path)
    records = []
    for name in sorted(data):
        try:
            records.append(get_line(name, store_path=store_path))
        except SteinerError:
            continue  # Skip malformed entries rather than failing the listing.
    return records


def divergence_delta(from_value: float, to_value: float) -> float:
    """Signed divergence delta when jumping from one line to another."""
    return round(to_value - from_value, 6)
