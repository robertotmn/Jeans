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

    def __post_init__(self):
        if len(self.outline) < 3:
            raise ValueError(
                f"piece {self.name!r}: outline needs >=3 points, got {len(self.outline)}"
            )
        # Reject self-intersecting polygons. Catches vertex-ordering bugs at
        # construction time before they propagate to SVG/PDF rendering.
        from shapely.geometry import Polygon
        poly = Polygon([(p.x, p.y) for p in self.outline])
        if not poly.is_simple:
            raise ValueError(
                f"piece {self.name!r}: outline is self-intersecting (non-simple polygon). "
                f"Likely a vertex-ordering bug."
            )

    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        return (min(xs), min(ys), max(xs), max(ys))

@dataclass
class Pattern:
    pieces: list[PatternPiece]

    def __iter__(self):
        return iter(self.pieces)


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

    front_labels = [(pt, name) for name, pt in front_pts.labeled_points().items()]
    front_labels.append((front_pts.K, "FRONT x 2 (mirror)"))
    front_piece = PatternPiece(
        name="front",
        outline=front_pts.outline_polygon(),
        labels=front_labels,
    )

    back_labels = [(pt, name) for name, pt in back_pts.labeled_points().items()]
    back_labels.append((back_pts.G, "BACK x 2 (mirror)"))
    back_piece = PatternPiece(
        name="back",
        outline=back_pts.outline_polygon(),
        labels=back_labels,
    )

    fly = build_button_fly(m)
    pocket = build_front_pocket(m)

    pieces = [
        front_piece,
        back_piece,
        build_waistband(m),
        fly["buttonhole_side"],
        fly["button_stand"],
        pocket["pocket_bag"],
        pocket["pocket_facing"],
        build_back_pocket(m),
        build_yoke(m),
        build_belt_loop(),
    ]
    return Pattern(pieces=pieces)
