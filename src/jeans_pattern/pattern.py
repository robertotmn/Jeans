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


def _outline_validate(piece: PatternPiece) -> PatternPiece:
    if len(piece.outline) < 3:
        raise ValueError(f"piece {piece.name!r}: outline needs >=3 points, got {len(piece.outline)}")
    return piece


def build_full_pattern(m: "Measurements", style: str = "updated") -> Pattern:
    """Assemble all jeans pattern pieces from the given measurements.

    style: "basic" (1900s-style straight-leg draft) or "updated" (501 silhouette).

    Returns a Pattern containing the front, back, waistband, fly halves,
    pocket bag/facing, back pocket, yoke, and one belt loop strip.
    """
    # Lazy imports to avoid circular import: draft_extras imports PatternPiece
    # from this module at top level.
    from .draft_basic import build_basic_front, build_basic_back
    from .draft_updated import build_updated_front, build_updated_back
    from .draft_extras import (
        build_waistband, build_belt_loop, build_button_fly,
        build_front_pocket, build_back_pocket, build_yoke,
    )

    if style == "basic":
        front_pts = build_basic_front(m)
        back_pts = build_basic_back(m, front=front_pts)
    elif style == "updated":
        front_pts = build_updated_front(m)
        # Pass the underlying basic FrontPoints so build_basic_back doesn't recompute
        back_pts = build_updated_back(m, front=front_pts.base)
    else:
        raise ValueError(f"unknown style {style!r}; expected 'basic' or 'updated'")

    front_piece = PatternPiece(
        name="front",
        outline=front_pts.outline_polygon(),
        labels=[(front_pts.K, "FRONT x 2 (mirror)")],
    )
    back_piece = PatternPiece(
        name="back",
        outline=back_pts.outline_polygon(),
        labels=[(back_pts.G, "BACK x 2 (mirror)")],
    )

    fly = build_button_fly(m)
    pocket = build_front_pocket(m)

    pieces = [
        _outline_validate(front_piece),
        _outline_validate(back_piece),
        _outline_validate(build_waistband(m)),
        _outline_validate(fly["buttonhole_side"]),
        _outline_validate(fly["button_stand"]),
        _outline_validate(pocket["pocket_bag"]),
        _outline_validate(pocket["pocket_facing"]),
        _outline_validate(build_back_pocket(m)),
        _outline_validate(build_yoke(m)),
        _outline_validate(build_belt_loop()),
    ]
    return Pattern(pieces=pieces)
