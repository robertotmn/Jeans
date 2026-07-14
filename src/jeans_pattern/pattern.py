"""Pattern piece model and pattern assembly.

A PatternPiece is a named polygon (the NET seam line, in mm) plus optional
construction lines and text labels. The assembler `build_full_pattern` is the
single entry point used by the UI and the exporters.
"""
from dataclasses import dataclass, field

from .geometry import Point


@dataclass
class PatternPiece:
    name: str
    outline: list[Point]                                  # closed polygon (first point not repeated)
    construction_lines: list[list[Point]] = field(default_factory=list)
    labels: list[tuple[Point, str]] = field(default_factory=list)

    def __post_init__(self):
        if len(self.outline) < 3:
            raise ValueError(
                f"piece {self.name!r}: outline needs >=3 points, got {len(self.outline)}"
            )
        # Reject self-intersecting polygons: catches vertex-ordering bugs at
        # construction time, before they propagate to SVG/PDF rendering.
        from shapely.geometry import Polygon
        poly = Polygon([(p.x, p.y) for p in self.outline])
        if not poly.is_simple:
            raise ValueError(
                f"piece {self.name!r}: outline is self-intersecting (non-simple polygon). "
                f"Likely a vertex-ordering bug."
            )

    def bbox(self) -> tuple[float, float, float, float]:
        """Bounding box of the outline UNION the construction lines, so the
        exporters reserve room for helper lines extending past the polygon."""
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        for line in self.construction_lines:
            for p in line:
                xs.append(p.x)
                ys.append(p.y)
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class Pattern:
    pieces: list[PatternPiece]

    def __iter__(self):
        return iter(self.pieces)


def build_full_pattern(m) -> Pattern:
    """Assemble all jeans pattern pieces from the given M&S Measurements.

    Transitional stub: the M&S draft modules are being rebuilt (see
    docs/superpowers/plans/2026-07-15-ms-jeans-draft.md). Returns an empty
    pattern until draft_ms.py / draft_ms_extras.py land.
    """
    return Pattern(pieces=[])
