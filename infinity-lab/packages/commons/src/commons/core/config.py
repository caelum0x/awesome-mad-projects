"""Immutable configuration primitives (stdlib only).

Provides a frozen-dataclass base pattern so downstream packages declare their
configuration once, get value-equality and hashing for free, and update it only
by producing *new* copies -- never by mutating shared state.

Usage::

    from dataclasses import dataclass
    from commons.core.config import FrozenConfig

    @dataclass(frozen=True)
    class GridConfig(FrozenConfig):
        n_u: int = 49
        n_v: int = 17

    cfg = GridConfig()
    finer = cfg.with_changes(n_u=97)   # cfg is untouched; finer is a new object
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, TypeVar

T = TypeVar("T", bound="FrozenConfig")


@dataclasses.dataclass(frozen=True)
class FrozenConfig:
    """Base for immutable, hashable configuration dataclasses.

    Subclass with ``@dataclass(frozen=True)``. Attempting to assign to a field
    raises :class:`dataclasses.FrozenInstanceError`; use :meth:`with_changes` to
    derive an updated copy instead.
    """

    def with_changes(self: T, **changes: Any) -> T:
        """Return a new instance with ``changes`` applied; ``self`` is untouched.

        Wraps :func:`dataclasses.replace`. Unknown field names raise
        :class:`TypeError`, so typos fail fast rather than silently no-op.
        """
        return dataclasses.replace(self, **changes)

    def to_dict(self: T) -> Dict[str, Any]:
        """Return a shallow ``{field: value}`` dict of this config's fields."""
        return dict(dataclasses.asdict(self))


def immutable_replace(instance: T, **changes: Any) -> T:
    """Free-function form of :meth:`FrozenConfig.with_changes`.

    Works on *any* frozen dataclass instance (not only :class:`FrozenConfig`
    subclasses). Returns a new instance; the original is never mutated. Raises
    :class:`TypeError` if ``instance`` is not a dataclass instance.
    """
    if not dataclasses.is_dataclass(instance) or isinstance(instance, type):
        raise TypeError("immutable_replace requires a dataclass instance")
    return dataclasses.replace(instance, **changes)
