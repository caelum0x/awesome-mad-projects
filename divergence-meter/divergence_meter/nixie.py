"""Render a divergence number on a nixie-tube style ASCII display.

Each digit is drawn in a 3-wide, 5-tall cell using a classic seven-segment
font. Tubes are boxed to evoke the orange glow of the Divergence Meter without
requiring any colour support -- pure ASCII, works in any terminal.
"""

from __future__ import annotations

# Seven-segment definitions. Each digit maps to five rows of exactly three
# characters. Segments are drawn with '_' (horizontal) and '|' (vertical).
_DIGITS: dict[str, tuple[str, str, str, str, str]] = {
    "0": (" _ ", "| |", "| |", "| |", "|_|"),
    "1": ("   ", "  |", "  |", "  |", "  |"),
    "2": (" _ ", "  |", " _|", "|  ", "|_ "),
    "3": (" _ ", "  |", " _|", "  |", "._|"),
    "4": ("   ", "| |", "|_|", "  |", "  |"),
    "5": (" _ ", "|  ", "|_ ", "  |", "._|"),
    "6": (" _ ", "|  ", "|_ ", "| |", "|_|"),
    "7": (" _ ", "  |", "  |", "  |", "  |"),
    "8": (" _ ", "| |", "|_|", "| |", "|_|"),
    "9": (" _ ", "| |", "|_|", "  |", "._|"),
}

# The decimal point occupies its own narrow tube.
_DOT = ("   ", "   ", "   ", "   ", " . ")

_ROWS = 5
_CELL_WIDTH = 3


def _cell_for(char: str) -> tuple[str, ...]:
    """Return the 5-row glyph for a single character."""
    if char == ".":
        return _DOT
    if char in _DIGITS:
        return _DIGITS[char]
    # Unknown characters render as blank tubes rather than crashing.
    return ("   ",) * _ROWS


def render(display: str) -> str:
    """Render a numeric string (e.g. '1.048596') as ASCII nixie tubes.

    Args:
        display: A string of digits and at most the usual decimal point.

    Returns:
        A multi-line string framed with a border, ready to print.
    """
    if not display:
        raise ValueError("Nothing to render: display string was empty.")

    cells = [_cell_for(ch) for ch in display]

    # Assemble each of the five rows by concatenating the corresponding row of
    # every cell, separated by a single space for tube spacing.
    body_rows = []
    for row_index in range(_ROWS):
        row = " ".join(cell[row_index] for cell in cells)
        body_rows.append(row)

    inner_width = len(body_rows[0])
    top = "+" + "-" * (inner_width + 2) + "+"
    framed = [top]
    framed.extend(f"| {row} |" for row in body_rows)
    framed.append(top)
    return "\n".join(framed)


def render_reading(display: str, *, label: str = "DIVERGENCE") -> str:
    """Render the nixie display with a small caption underneath."""
    art = render(display)
    caption = f"      {label}: {display}"
    return f"{art}\n{caption}"
