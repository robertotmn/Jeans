"""Pattern piece model and full-pattern assembly.

A PatternPiece carries the NET seam outline (mm) plus an optional CUT outline
(net + seam allowances), construction lines and text labels. The assemblers
`build_full_pattern` and `build_jacket_pattern` produce every Design 3069 resp.
Design 4041 piece from the measurements.
"""
from dataclasses import dataclass, field

from .draft_jacket import draft_jacket_back, draft_jacket_front, draft_jacket_sleeve
from .draft_jacket_design import (
    build_back_centre,
    build_back_side_panel,
    build_back_yoke,
    build_chest_pocket_bag,
    build_chest_pocket_flap,
    build_collar,
    build_cuff,
    build_front_centre,
    build_front_chest_panel,
    build_front_side_panel,
    build_front_yoke,
    build_jacket_waistband,
    build_side_pocket_bag,
    build_side_pocket_welt,
    build_tab,
    design_body,
    front_jacket_marks,
    split_sleeve,
)
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
from .geometry import Point, arc_length, chain_outline, offset_outline
from .measurements import Measurements
from .measurements_jacket import JacketMeasurements


@dataclass(frozen=True)
class SeamAllowances:
    """Cut-line configuration by edge name: `fold*` edges lie on a fold and get
    nothing, `hem` gets hem_mm, every other edge seam_mm.
    Set both to 0 to export the net pattern only."""
    seam_mm: float = 15.0
    hem_mm: float = 30.0

    @property
    def enabled(self) -> bool:
        return self.seam_mm > 0 or self.hem_mm > 0

    def for_edges(self, edges: list[tuple[str, list[Point]]]) -> dict[str, float]:
        return {name: (0.0 if name.startswith("fold")
                       else self.hem_mm if name == "hem" else self.seam_mm)
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


SEAM_MATCH_TOL_MM = 2.5    # two edges sewn together may differ by this much


def build_jacket_pattern(m: JacketMeasurements,
                         sa: SeamAllowances | None = None) -> Pattern:
    """All Design 4041 pieces from the given jacket measurements.

    Returns the pattern plus a report with the booklet's checks (chest and hip
    ease, cap ease, collar length) and the derived values shown in the UI. The
    matched seams are re-measured on the assembled pieces and any mismatch
    beyond SEAM_MATCH_TOL_MM lands in the warnings.
    """
    sa = sa if sa is not None else SeamAllowances()

    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    sleeve = draft_jacket_sleeve(m, back, front)
    db = design_body(back, front)
    marks = front_jacket_marks(db)
    upper, under = split_sleeve(sleeve)

    front_yoke = build_front_yoke(db, marks)
    front_centre = build_front_centre(db, marks)
    chest_panel = build_front_chest_panel(db, marks)
    front_side = build_front_side_panel(db, marks)
    back_yoke = build_back_yoke(db)
    back_centre = build_back_centre(db)
    back_side = build_back_side_panel(db)
    cuff = build_cuff(upper, under)
    collar = build_collar(db)
    band = build_jacket_waistband(db)

    drafts = [front_yoke, front_centre, chest_panel, front_side,
              back_yoke, back_centre, back_side,
              upper, under, cuff, collar, band,
              build_chest_pocket_flap(), build_chest_pocket_bag(),
              build_side_pocket_welt(), build_side_pocket_bag(), build_tab()]
    warnings = list(front.report["warnings"]) + list(db.report["warnings"])
    warnings += list(collar.report["warnings"]) + list(upper.report["warnings"])

    def piece(d) -> PatternPiece:
        """An allowance wider than the local curvature folds the cut line onto
        itself; the piece is still usable, so it ships with the net line only."""
        try:
            return _make_piece(d.name, d.edges, sa,
                               construction_lines=d.construction_lines, labels=d.labels)
        except ValueError:
            warnings.append(f"margine troppo largo per {d.name}: "
                            f"contorno di taglio non generato")
            return _make_piece(d.name, d.edges, SeamAllowances(0.0, 0.0),
                               construction_lines=d.construction_lines, labels=d.labels)

    pieces = [piece(d) for d in drafts]

    def seam(draft, name: str) -> float:
        return sum(arc_length(pts) for n, pts in draft.edges if n == name)

    # Each pair measures a whole against the parts it was cut into, a slashed
    # edge against the untouched copy of itself, or two seams drafted apart, so
    # a mismatch can really happen. Three more couplings of the design are left
    # out because both members would be the same segment: the cuff is built as
    # the sum of the two `cuff_seam` edges it would be checked against, and the
    # back and the front-side panel seam are shared landmark for landmark by the
    # two pieces that meet on them.
    # The pintuck opens the centre front panel, so its yoke and waistband edges
    # carry 2 cm of cloth that the tuck folds away before assembly (D18).
    spread = front_centre.report["pintuck_spread_mm"]
    body = [front_yoke, front_centre, chest_panel, front_side,
            back_yoke, back_centre, back_side]
    checks = [
        ("cinturino/orlo", seam(band, "body_seam"),
         sum(seam(p, "waistband_seam") for p in body) - spread),
        ("carre dietro", seam(back_yoke, "yoke_seam"),
         seam(back_centre, "yoke_seam") + seam(back_side, "yoke_seam")),
        ("carre davanti", seam(front_yoke, "yoke_seam"),
         seam(front_centre, "yoke_seam") + seam(chest_panel, "yoke_seam")
         + seam(front_side, "yoke_seam") - spread),
        ("pannello davanti c.f.", seam(front_centre, "panel_seam"),
         seam(chest_panel, "panel_seam_cf")),
        ("fianchi", seam(back_side, "side"), seam(front_side, "side")),
    ]
    for label, a, b in checks:
        if abs(a - b) > SEAM_MATCH_TOL_MM:
            warnings.append(f"{label}: {a / 10:.1f} cm contro {b / 10:.1f} cm")

    report = {
        "model": "jacket",
        "scye_depth_mm": m.scye_depth_mm,
        "length_mm": m.jacket_length_mm,
        "chest_ease_mm": front.report["chest_ease_mm"],
        "hip_ease_mm": front.report["hip_ease_mm"],
        "armhole_circ_mm": front.report["armhole_circ_mm"],
        "sleeve_cap_height_mm": sleeve.report["sleeve_cap_height_mm"],
        "sleeve_cap_ease_mm": upper.report["cap_ease_mm"],
        "neckline_mm": db.report["neckline_mm"],
        "collar_correction_mm": collar.report["correction_mm"],
        "waistband_len_mm": band.report["length_mm"],
        "cuff_len_mm": cuff.report["length_mm"],
        "warnings": warnings,
    }
    return Pattern(pieces=pieces, report=report)
