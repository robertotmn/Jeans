"""Pattern piece model and full-pattern assembly.

A PatternPiece carries the NET seam outline (mm) plus an optional CUT outline
(net + seam allowances), construction lines and text labels. The assembler
`build_full_pattern` produces every Design 3069 piece from the measurements.
"""
from dataclasses import dataclass, field

from .draft_ms import draft_back, draft_front
from .draft_ms_extras import (
    build_back_pocket,
    build_belt_loop_strip,
    build_coin_pocket,
    build_fly_facing,
    build_fly_shield,
    build_front_pocket_bag,
    build_front_pocket_facing,
    build_waistband,
    build_yoke,
    front_design_marks,
)
from .geometry import Point, chain_outline, offset_outline
from .measurements import Measurements


@dataclass(frozen=True)
class SeamAllowances:
    """Cut-line configuration: hem edges get hem_mm, every other edge seam_mm.
    Set both to 0 to export the net pattern only."""
    seam_mm: float = 10.0
    hem_mm: float = 30.0

    @property
    def enabled(self) -> bool:
        return self.seam_mm > 0 or self.hem_mm > 0

    def for_edges(self, edges: list[tuple[str, list[Point]]]) -> dict[str, float]:
        return {name: (self.hem_mm if name == "hem" else self.seam_mm)
                for name, _pts in edges}


@dataclass
class PatternPiece:
    name: str
    outline: list[Point]                                  # closed net polygon
    construction_lines: list[list[Point]] = field(default_factory=list)
    labels: list[tuple[Point, str]] = field(default_factory=list)
    cut_outline: list[Point] | None = None                # net + allowances

    def __post_init__(self):
        if len(self.outline) < 3:
            raise ValueError(
                f"piece {self.name!r}: outline needs >=3 points, got {len(self.outline)}"
            )
        # Reject self-intersecting polygons: catches vertex-ordering bugs at
        # construction time, before they propagate to SVG/PDF rendering.
        from shapely.geometry import Polygon
        for label, pts in (("outline", self.outline), ("cut_outline", self.cut_outline)):
            if pts is None:
                continue
            poly = Polygon([(p.x, p.y) for p in pts])
            if not poly.is_simple:
                raise ValueError(
                    f"piece {self.name!r}: {label} is self-intersecting (non-simple polygon)."
                )

    def bbox(self) -> tuple[float, float, float, float]:
        """Bounding box over outline, cut outline and construction lines."""
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        for line in self.construction_lines:
            for p in line:
                xs.append(p.x)
                ys.append(p.y)
        if self.cut_outline:
            xs += [p.x for p in self.cut_outline]
            ys += [p.y for p in self.cut_outline]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class Pattern:
    pieces: list[PatternPiece]
    report: dict = field(default_factory=dict)

    def __iter__(self):
        return iter(self.pieces)


def _make_piece(name, edges, sa: SeamAllowances,
                construction_lines=None, labels=None) -> PatternPiece:
    return PatternPiece(
        name=name,
        outline=chain_outline(edges),
        construction_lines=list(construction_lines or []),
        labels=list(labels or []),
        cut_outline=offset_outline(edges, sa.for_edges(edges)) if sa.enabled else None,
    )


def build_full_pattern(m: Measurements, sa: SeamAllowances | None = None) -> Pattern:
    """All Design 3069 pieces from the given measurements.

    Returns the pattern plus a report with the booklet's checks (hip ease,
    waist rest) and the derived body values shown in the UI.
    """
    sa = sa if sa is not None else SeamAllowances()

    front = draft_front(m)
    back = draft_back(m, front)
    yoke = build_yoke(back)
    band = build_waistband(m, front)
    b_pocket = build_back_pocket(back)
    bag = build_front_pocket_bag(m, front)
    facing = build_front_pocket_facing(m, front)

    crease = front.report["crease_x_mm"]
    front_piece = _make_piece(
        "davanti", front.edges, sa,
        construction_lines=front.construction_lines + front_design_marks(front),
        labels=[(Point(crease, 400), "DAVANTI x 2 (specchiato)")],
    )
    pocket_outline = b_pocket.outline()
    back_piece = _make_piece(
        "dietro", back.edges, sa,
        construction_lines=back.construction_lines + [pocket_outline + [pocket_outline[0]]],
        labels=[(Point(crease, 400), "DIETRO x 2 (specchiato)")],
    )

    pieces = [front_piece, back_piece]
    for draft in (yoke, band, b_pocket, bag, facing,
                  build_fly_facing(), build_fly_shield(),
                  build_coin_pocket(), build_belt_loop_strip()):
        pieces.append(_make_piece(draft.name, draft.edges, sa,
                                  construction_lines=draft.construction_lines,
                                  labels=draft.labels))

    ease = front.report["hip_width_a_mm"] + back.report["hip_width_b_mm"] - m.hip_girth_mm / 2
    warnings = list(back.report["warnings"])
    if front.report["cf_taper_clamped"]:
        warnings.append(
            "giro vita molto fuori proporzione rispetto ai fianchi: "
            "il davanti ha esaurito la regolazione al c.f., il resto va sul dietro"
        )
    if ease < 10.0:
        warnings.append(
            f"agio fianchi {ease / 10:.1f} cm < 1 cm: usare tessuto elasticizzato (M&S p. 4)"
        )
    yoke_delta = yoke.report["yoke_seam_len_mm"] - yoke.report["back_yoke_len_mm"]
    if abs(yoke_delta) > 2.5:
        warnings.append(f"cucitura carre fuori misura di {yoke_delta:.1f} mm")

    report = {
        "body_rise_mm": m.body_rise_mm,
        "knee_length_mm": m.knee_length_mm,
        "hip_ease_mm": ease,
        "front_waist_mm": front.report["waist_len_mm"],
        "back_waist_mm": back.report["back_waist_mm"],
        "waist_rest_mm": back.report["rest_mm"],
        "warnings": warnings,
    }
    return Pattern(pieces=pieces, report=report)
