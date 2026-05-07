from dataclasses import dataclass, field
from typing import Union
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
        """Bounding box of the outline UNION the construction lines, so SVG/PDF
        layout reserves enough room for dashed helper lines that extend past
        the cut polygon (e.g. waist/hip/knee/hem horizontals)."""
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        for line in self.construction_lines:
            for p in line:
                xs.append(p.x)
                ys.append(p.y)
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class RasterPiece:
    """A pattern piece backed by a raster image instead of a polygon outline.

    Used by the mueller3 system: the M&S diagram is warped pixel-by-pixel via
    TPS so the original drawing (with its labels, hatching, etc.) is preserved
    rather than vectorised. PDF/SVG exporters dispatch on type and embed the
    image at its bbox_mm position.
    """
    name: str
    image: object                          # PIL.Image.Image — typed loosely to avoid forcing a hard PIL import here
    bbox_mm: tuple[float, float, float, float]
    dpi: float = 100.0
    labels: list[tuple[Point, str]] = field(default_factory=list)

    def bbox(self) -> tuple[float, float, float, float]:
        """Match PatternPiece API so layout code is shared between vector and raster pieces."""
        return self.bbox_mm


PieceLike = Union[PatternPiece, RasterPiece]


@dataclass
class Pattern:
    pieces: list[PieceLike]

    def __iter__(self):
        return iter(self.pieces)


def build_full_pattern(m, style: str = "updated") -> Pattern:
    """Assemble all jeans pattern pieces from the given measurements.

    style: "basic" or "updated" use the J.E. Landis draft and require
    `m: Measurements`. style: "mueller" uses the M. Mueller & Sohn draft
    (Design 3069 - formula-based) and requires `m: MuellerMeasurements`.
    style: "mueller2" uses the M. Mueller & Sohn template-based system (TPS
    warp of the extracted M&S diagram) and also requires `m: MuellerMeasurements`.

    For the Landis styles, returns a Pattern containing the front, back,
    waistband, fly halves, pocket bag/facing, back pocket, yoke, and one
    belt loop strip. Both Mueller variants share the same accessory set.
    """
    # Lazy imports to avoid circular import: draft_extras imports PatternPiece
    # from this module at top level.
    from .draft_basic import build_basic_front, build_basic_back
    from .draft_updated import build_updated_front, build_updated_back
    from .draft_extras import (
        build_waistband, build_belt_loop, build_button_fly,
        build_front_pocket, build_back_pocket, build_yoke,
    )

    if style == "mueller3":
        from .draft_mueller import MuellerMeasurements
        from .draft_mueller3 import build_mueller3_front, build_mueller3_back
        from .draft_mueller_extras import (
            build_mueller_waistband, build_mueller_belt_loop,
            build_mueller_zipper_fly, build_mueller_front_pocket,
            build_mueller_back_pocket, build_mueller_yoke,
        )
        if not isinstance(m, MuellerMeasurements):
            raise TypeError(
                f"style='mueller3' requires MuellerMeasurements, "
                f"got {type(m).__name__}"
            )
        front_piece = build_mueller3_front(m)
        back_piece = build_mueller3_back(m)
        front_labels = [(pt, name) for name, pt in front_piece.labeled_points().items()]
        front_labels.append((front_piece.anchors["Ftw"], "FRONT (Mueller3) x 2 (mirror)"))
        back_labels = [(pt, name) for name, pt in back_piece.labeled_points().items()]
        back_labels.append((back_piece.anchors["Btw"], "BACK (Mueller3) x 2 (mirror)"))
        fly = build_mueller_zipper_fly(m)
        pocket = build_mueller_front_pocket(m)
        return Pattern(pieces=[
            RasterPiece(
                name="front",
                image=front_piece.image,
                bbox_mm=front_piece.bbox_mm,
                dpi=front_piece.dpi,
                labels=front_labels,
            ),
            RasterPiece(
                name="back",
                image=back_piece.image,
                bbox_mm=back_piece.bbox_mm,
                dpi=back_piece.dpi,
                labels=back_labels,
            ),
            build_mueller_waistband(m),
            fly["shield"],
            fly["facing"],
            pocket["pocket_bag"],
            pocket["pocket_facing"],
            build_mueller_back_pocket(m),
            build_mueller_yoke(m),
            build_mueller_belt_loop(),
        ])

    if style == "mueller2":
        from .draft_mueller import MuellerMeasurements
        from .draft_mueller2 import build_mueller2_front, build_mueller2_back
        from .draft_mueller_extras import (
            build_mueller_waistband, build_mueller_belt_loop,
            build_mueller_zipper_fly, build_mueller_front_pocket,
            build_mueller_back_pocket, build_mueller_yoke,
        )
        if not isinstance(m, MuellerMeasurements):
            raise TypeError(
                f"style='mueller2' requires MuellerMeasurements, "
                f"got {type(m).__name__}"
            )
        front_pts = build_mueller2_front(m)
        back_pts = build_mueller2_back(m)
        front_labels = [(pt, name) for name, pt in front_pts.labeled_points().items()]
        front_labels.append((front_pts.anchors["Ftw"], "FRONT (Mueller2) x 2 (mirror)"))
        back_labels = [(pt, name) for name, pt in back_pts.labeled_points().items()]
        back_labels.append((back_pts.anchors["Btw"], "BACK (Mueller2) x 2 (mirror)"))
        fly = build_mueller_zipper_fly(m)
        pocket = build_mueller_front_pocket(m)
        return Pattern(pieces=[
            PatternPiece(
                name="front",
                outline=front_pts.outline_polygon(),
                labels=front_labels,
            ),
            PatternPiece(
                name="back",
                outline=back_pts.outline_polygon(),
                labels=back_labels,
            ),
            build_mueller_waistband(m),
            fly["shield"],
            fly["facing"],
            pocket["pocket_bag"],
            pocket["pocket_facing"],
            build_mueller_back_pocket(m),
            build_mueller_yoke(m),
            build_mueller_belt_loop(),
        ])

    if style == "mueller":
        from .draft_mueller import (
            MuellerMeasurements, build_mueller_front, build_mueller_back,
        )
        from .draft_mueller_extras import (
            build_mueller_waistband, build_mueller_belt_loop,
            build_mueller_zipper_fly, build_mueller_front_pocket,
            build_mueller_back_pocket, build_mueller_yoke,
        )
        if not isinstance(m, MuellerMeasurements):
            raise TypeError(
                f"style='mueller' requires MuellerMeasurements, "
                f"got {type(m).__name__}"
            )
        front_pts = build_mueller_front(m)
        back_pts = build_mueller_back(m, front=front_pts)
        front_labels = [(pt, name) for name, pt in front_pts.labeled_points().items()]
        front_labels.append((front_pts.F1, "FRONT (Mueller) x 2 (mirror)"))
        back_labels = [(pt, name) for name, pt in back_pts.labeled_points().items()]
        back_labels.append((back_pts.crotch_corner, "BACK (Mueller) x 2 (mirror)"))
        fly = build_mueller_zipper_fly(m)
        pocket = build_mueller_front_pocket(m)
        return Pattern(pieces=[
            PatternPiece(
                name="front",
                outline=front_pts.outline_polygon(),
                labels=front_labels,
            ),
            PatternPiece(
                name="back",
                outline=back_pts.outline_polygon(),
                labels=back_labels,
            ),
            build_mueller_waistband(m),
            fly["shield"],
            fly["facing"],
            pocket["pocket_bag"],
            pocket["pocket_facing"],
            build_mueller_back_pocket(m),
            build_mueller_yoke(m),
            build_mueller_belt_loop(),
        ])

    if style == "basic":
        front_pts = build_basic_front(m)
        back_pts = build_basic_back(m, front=front_pts)
    elif style == "updated":
        front_pts = build_updated_front(m)
        # Pass the underlying basic FrontPoints so build_basic_back doesn't recompute
        back_pts = build_updated_back(m, front=front_pts.base)
    else:
        raise ValueError(
            f"unknown style {style!r}; expected 'basic', 'updated', 'mueller', 'mueller2', or 'mueller3'"
        )

    front_labels = [(pt, name) for name, pt in front_pts.labeled_points().items()]
    front_labels.append((front_pts.K, "FRONT x 2 (mirror)"))
    front_piece = PatternPiece(
        name="front",
        outline=front_pts.outline_polygon(),
        construction_lines=front_pts.construction_lines(),
        labels=front_labels,
    )

    back_labels = [(pt, name) for name, pt in back_pts.labeled_points().items()]
    back_labels.append((back_pts.G, "BACK x 2 (mirror)"))
    back_piece = PatternPiece(
        name="back",
        outline=back_pts.outline_polygon(),
        construction_lines=back_pts.construction_lines(),
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
