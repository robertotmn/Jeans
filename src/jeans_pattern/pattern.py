from dataclasses import dataclass, field
from .geometry import Point
from .constants import SA_3_8_IN_MM

@dataclass
class PatternPiece:
    name: str
    outline: list[Point]                                  # poligono chiuso (no ripetere primo punto)
    construction_lines: list[list[Point]] = field(default_factory=list)
    labels: list[tuple[Point, str]] = field(default_factory=list)
    seam_allowance_mm: float = SA_3_8_IN_MM                # 3/8" default

    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        return (min(xs), min(ys), max(xs), max(ys))

@dataclass
class Pattern:
    pieces: list[PatternPiece]

    def __iter__(self):
        return iter(self.pieces)
