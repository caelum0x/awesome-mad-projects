"""Map a world-state snapshot to a worldline divergence number.

The Divergence Meter in *Steins;Gate* famously reads ``1.048596`` -- the border
between the Alpha and Beta attractor-field clusters. We reproduce the *format* (a
value in the range ``[0, 2)`` printed to six decimals) and derive it honestly
from a cryptographic hash of the snapshot so that it is:

    deterministic   -- same snapshot -> same number, always
    well-distributed -- SHA-256 avalanche means tiny input changes move the
                        number unpredictably across the whole range
    reproducible across machines -- no reliance on Python's salted ``hash()``

Math core
---------
1. digest   = SHA-256(payload)                       # 256 bits
2. word     = first 8 bytes of digest, big-endian    # a 64-bit integer
3. fraction = word / 2**64                            # a real in [0, 1)
4. value    = fraction * 2.0                          # a real in [0, 2)
5. display  = round(value, 6)                         # show-style 1.048596

The EXACT value is ``word / 2**63`` as a rational -- exposed losslessly via
:attr:`DivergenceReading.exact_value` using :mod:`commons.core.exact`, so the
number can be reasoned about with no floating-point rounding.

This module is part of the pure ``core`` layer (stdlib + ``commons.core`` only).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

from commons.core.exact import half_power, to_fraction

from divergence_meter.core.worldstate import Snapshot

# The classic worldline that divides the major attractor fields.
STEINS_GATE_VALUE = 1.048596

# Divergence values are rendered with this many fractional digits, matching the
# seven-tube nixie display used in the anime (1 integer + 6 fractional).
DECIMAL_PLACES = 6
_SCALE = 2.0  # value range is [0, _SCALE)
_WORD_BITS = 64  # first 8 bytes of the digest -> a 64-bit integer


@dataclass(frozen=True)
class DivergenceReading:
    """An immutable divergence measurement.

    Attributes:
        value: The exact divergence value in ``[0, 2)``, rounded to 6 dp.
        digest: Full hex SHA-256 digest of the snapshot payload.
        word: The 64-bit integer extracted from the digest.
        origin: Where the snapshot came from (copied from the Snapshot).
    """

    value: float
    digest: str
    word: int
    origin: str

    @property
    def display(self) -> str:
        """The value formatted exactly as shown on the meter, e.g. ``'1.048596'``."""
        return f"{self.value:.{DECIMAL_PLACES}f}"

    @property
    def digits(self) -> str:
        """The displayed digits with the decimal point removed, e.g. ``'1048596'``."""
        return self.display.replace(".", "")

    @property
    def exact_value(self) -> Fraction:
        """The lossless rational divergence ``word / 2**63`` in ``[0, 2)``.

        Computed with exact arithmetic (:func:`commons.core.exact.to_fraction`
        times :func:`commons.core.exact.half_power`) so it carries no
        floating-point rounding; :attr:`value` is this quantity rounded to
        :data:`DECIMAL_PLACES`.
        """
        # value = word / 2**64 * 2 = word / 2**63 = word * (1 / 2**63).
        return to_fraction(self.word) * half_power(_WORD_BITS - 1)

    def is_steins_gate(self, *, tolerance: float = 5e-7) -> bool:
        """Whether this reading sits on the Steins;Gate worldline."""
        return abs(self.value - STEINS_GATE_VALUE) <= tolerance


def compute_divergence(snapshot: Snapshot) -> DivergenceReading:
    """Compute the :class:`DivergenceReading` for a snapshot.

    Args:
        snapshot: A world-state snapshot.

    Raises:
        TypeError: If ``snapshot`` is not a :class:`Snapshot` instance.
    """
    if not isinstance(snapshot, Snapshot):
        raise TypeError(f"Expected Snapshot, got {type(snapshot).__name__}.")

    digest = hashlib.sha256(snapshot.payload).digest()
    word = int.from_bytes(digest[:8], byteorder="big")
    fraction = word / 2 ** _WORD_BITS  # in [0, 1)
    value = round(fraction * _SCALE, DECIMAL_PLACES)

    return DivergenceReading(
        value=value,
        digest=digest.hex(),
        word=word,
        origin=snapshot.origin,
    )
