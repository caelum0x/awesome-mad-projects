"""Gather a deterministic snapshot of "world state" (stdlib only).

The snapshot is the raw material from which a worldline divergence number is
derived. A snapshot is intentionally simple and reproducible: given the same
input, you always get the same bytes, and therefore the same divergence value.

Supported sources:
    - A directory  -> a sorted listing of (relative path, size) tuples.
    - A file       -> the file's raw contents.
    - "-"          -> data read from standard input.
    - JSON text    -> normalised (sorted keys) canonical JSON.
    - Plain text   -> the text itself.

Design notes:
    * :class:`Snapshot` is a frozen dataclass -> immutable, no shared-state
      mutation.
    * We never trust external data blindly; every branch validates its input and
      raises a clear :class:`WorldStateError` on failure.

This module is part of the pure ``core`` layer: it imports only the standard
library (no adapters, no numpy/matplotlib).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, Optional

# Cap how much we read so a huge file/stream cannot exhaust memory.
MAX_READ_BYTES = 8 * 1024 * 1024  # 8 MiB


class WorldStateError(Exception):
    """Raised when a snapshot cannot be built from the requested source."""


@dataclass(frozen=True)
class Snapshot:
    """An immutable snapshot of world state.

    Attributes:
        origin: Human-readable description of where the data came from.
        payload: The canonical bytes that represent this world state.
    """

    origin: str
    payload: bytes

    def summary(self) -> str:
        """Short, printable description of the snapshot size and origin."""
        return f"{self.origin} ({len(self.payload)} bytes)"


def _read_stream(stream) -> bytes:
    """Read a binary stream up to MAX_READ_BYTES, guarding against overflow."""
    data = stream.read(MAX_READ_BYTES + 1)
    if isinstance(data, str):
        data = data.encode("utf-8")
    if len(data) > MAX_READ_BYTES:
        raise WorldStateError(
            f"Input exceeds maximum of {MAX_READ_BYTES} bytes; refusing to read."
        )
    return data


def _directory_payload(path: str) -> bytes:
    """Build a canonical listing of a directory tree.

    The listing is a sorted sequence of ``relative/path\\tsize`` lines. Sorting
    makes the result independent of filesystem iteration order, so the same tree
    always yields the same bytes.
    """
    entries: list[str] = []
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            try:
                size = os.path.getsize(full)
            except OSError:
                # A file may vanish between walk and stat; record it as -1
                # rather than aborting the whole snapshot.
                size = -1
            rel = os.path.relpath(full, path)
            entries.append(f"{rel}\t{size}")
    body = "\n".join(sorted(entries))
    return body.encode("utf-8")


def _looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and stripped[0] in "{["


def _canonical_json(text: str) -> Optional[bytes]:
    """Return canonical JSON bytes if text is valid JSON, else ``None``."""
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":"))
    return canonical.encode("utf-8")


def snapshot_from_source(source: str, *, stdin=None) -> Snapshot:
    """Build a :class:`Snapshot` from a CLI source argument.

    Args:
        source: A path, ``"-"``, or literal text/JSON.
        stdin: Optional binary stream used when ``source == "-"`` (for tests).

    Raises:
        WorldStateError: If the source is empty or cannot be read.
    """
    if source is None:
        raise WorldStateError("No source provided.")

    if source == "-":
        stream = stdin if stdin is not None else _default_stdin()
        payload = _read_stream(stream)
        if not payload:
            raise WorldStateError("Standard input was empty.")
        return Snapshot(origin="stdin", payload=payload)

    # Filesystem paths take priority when they exist.
    if os.path.isdir(source):
        return Snapshot(origin=f"dir:{source}", payload=_directory_payload(source))

    if os.path.isfile(source):
        try:
            with open(source, "rb") as handle:
                payload = _read_stream(handle)
        except OSError as exc:
            raise WorldStateError(f"Could not read file '{source}': {exc}") from exc
        return Snapshot(origin=f"file:{source}", payload=payload)

    # Not a path: treat the argument as literal data.
    text = source.strip()
    if not text:
        raise WorldStateError("Literal source text was empty.")

    if _looks_like_json(text):
        canonical = _canonical_json(text)
        if canonical is not None:
            return Snapshot(origin="json:literal", payload=canonical)

    return Snapshot(origin="text:literal", payload=text.encode("utf-8"))


def snapshot_from_numbers(numbers: Iterable[float]) -> Snapshot:
    """Build a snapshot from a list of numbers (deterministic ordering kept)."""
    values = list(numbers)
    if not values:
        raise WorldStateError("Number list was empty.")
    body = ",".join(repr(float(v)) for v in values)
    return Snapshot(origin="numbers:literal", payload=body.encode("utf-8"))


def _default_stdin():
    """Return the process's binary stdin buffer."""
    import sys

    return getattr(sys.stdin, "buffer", sys.stdin)
