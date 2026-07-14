"""M. Mueller & Sohn "Jeans-Basics" drafting: Basic Jeans Block (pages 2-3).

Coordinate frame (mm): x=0 on the front base line (outseam side), y=0 on the
waist line, y grows toward the hem. The back is drafted over the front in the
same frame, exactly as the booklet does.

Every construction rule and curve-shape constant in this module was validated
against the vector geometry of the booklet's own size-50 scale drawing
(tests/data/ms_reference_size50.json, extracted by scripts/extract_ms_reference.py).
Landmark agreement is ~0.5 mm; curve agreement <= ~1 mm.
"""
from dataclasses import dataclass
from math import cos, radians, sin

from .geometry import (
    Point,
    arc_length,
    chain_outline,
    cubic_with_tangents,
    curve_through,
    distance,
    line_intersection,
    point_along,
    unit_vector,
)
from .measurements import Measurements

# ---- calibrated curve-shape constants (size-50 drawing fit) ---------------
# waist: cubic, start tangent = chord rotated +6 deg, end tangent perpendicular
# to the c.f. line; control distances 0.40/0.20 of the chord. Fit: 0.8 mm.
WAIST_START_ROT_DEG = 6.0
WAIST_ALPHA, WAIST_BETA = 0.40, 0.20
# crotch curve: leaves the straight c.f. line at hip + 32% of (crotch - hip);
# tangents c.f.-direction -> slant-guideline direction; controls 0.35 of the
# chord. Fit: 0.5 mm.
CF_CURVE_START_FRAC = 0.32
CF_ALPHA = CF_BETA = 0.35
# inseam: quadratic through a control point 40% down the chord, hollowed
# 19 mm toward the creaseline (fixed drafting amount, ~10 mm actual hollow).
# Fit: 0.6 mm, arc length matches the drawing to 0.1 mm.
INSEAM_HOLLOW_MM = 19.0
INSEAM_HOLLOW_FRAC = 0.40
# outseam: straight on the guideline from the knee to the guideline top, then
# a cubic to the waist corner arriving 5 deg off vertical; controls 0.25 of
# the chord. Fit: 0.8 mm.
OUTSEAM_END_ROT_DEG = 5.0
OUTSEAM_ALPHA = OUTSEAM_BETA = 0.25


def _rot(u: tuple[float, float], deg: float) -> tuple[float, float]:
    r = radians(deg)
    return (u[0] * cos(r) - u[1] * sin(r), u[0] * sin(r) + u[1] * cos(r))


@dataclass(frozen=True)
class FrontDraft:
    """Front trouser: named landmarks, ordered edge chains, helper lines.

    edges: closed chain in order waist -> cf_crotch -> inseam -> hem -> outseam
    (waist travels outseam corner -> c.f.; inseam travels crotch -> hem).
    """
    landmarks: dict[str, Point]
    edges: list[tuple[str, list[Point]]]
    construction_lines: list[list[Point]]
    report: dict

    def outline(self) -> list[Point]:
        return chain_outline(self.edges)

    def edge(self, name: str) -> list[Point]:
        for n, pts in self.edges:
            if n == name:
                return pts
        raise KeyError(name)


def draft_front(m: Measurements) -> FrontDraft:
    ftw = m.front_trouser_width_mm
    fcw = m.front_crotch_width_mm

    # 1. horizontal levels (page 2 step 1)
    hem_y = m.outseam_mm
    knee_y = m.outseam_mm - m.knee_length_mm
    crotch_y = m.body_rise_mm
    hip_y = crotch_y - m.hip_depth_above_crotch_mm

    # 2. widths: Ftw and Fcw are measured ON THE HIP LINE; the creaseline
    # halves the total front width minus 2 cm.
    crease_x = (ftw + fcw) / 2 - 20.0
    hip_cf = Point(ftw, hip_y)
    fcw_pt = Point(ftw + fcw, hip_y)

    # 3. hem and knee: half widths minus 0.5 cm each side of the crease
    hem_half = m.hem_width_mm / 4 - 5.0
    knee_half = m.knee_girth_mm / 4 - 5.0
    hem_out, hem_in = Point(crease_x - hem_half, hem_y), Point(crease_x + hem_half, hem_y)
    knee_out, knee_in = Point(crease_x - knee_half, knee_y), Point(crease_x + knee_half, knee_y)

    # 4. guidelines: the inseam guideline joins the knee to the Fcw point on
    # the hip line; the crotch point is its intersection with the crotch line.
    # The outseam guideline ends on the base line midway hip-to-crotch.
    crotch_pt = line_intersection(knee_in, fcw_pt, Point(0, crotch_y), Point(100, crotch_y))
    guide_top = Point(0.0, (hip_y + crotch_y) / 2)

    # 5. waist: c.f. lowered 1 cm and tapered 1.5 cm; outseam side tapered 1 cm
    waist_cf = Point(ftw - 15.0, 10.0)
    waist_out = Point(10.0, 0.0)
    cf_dir = unit_vector(hip_cf.x - waist_cf.x, hip_cf.y - waist_cf.y)

    # 6. crotch curve construction: d measured on the crotch line from the
    # c.f. VERTICAL to the crotch point; half of d up along the vertical
    d = crotch_pt.x - ftw
    halfd_pt = Point(ftw, crotch_y - d / 2)
    slant_dir = unit_vector(crotch_pt.x - halfd_pt.x, crotch_pt.y - halfd_pt.y)

    cf_curve_start_y = hip_y + CF_CURVE_START_FRAC * (crotch_y - hip_y)
    cf_curve_start = Point(
        waist_cf.x + cf_dir[0] / cf_dir[1] * (cf_curve_start_y - waist_cf.y),
        cf_curve_start_y,
    )
    cf_chord = distance(cf_curve_start, crotch_pt)
    cf_crotch_edge = [waist_cf] + cubic_with_tangents(
        cf_curve_start, crotch_pt, cf_dir, slant_dir,
        alpha=CF_ALPHA * cf_chord, beta=CF_BETA * cf_chord, n=32,
    )

    # 7. waist curve: perpendicular to the c.f. at the c.f. end
    waist_chord = distance(waist_out, waist_cf)
    chord_dir = unit_vector(waist_cf.x - waist_out.x, waist_cf.y - waist_out.y)
    waist_edge = cubic_with_tangents(
        waist_out, waist_cf, _rot(chord_dir, WAIST_START_ROT_DEG),
        (cf_dir[1], -cf_dir[0]),
        alpha=WAIST_ALPHA * waist_chord, beta=WAIST_BETA * waist_chord, n=24,
    )

    # 8. inseam: hollowed toward the crease between crotch point and knee,
    # then straight to the hem
    in_dir = unit_vector(knee_in.x - crotch_pt.x, knee_in.y - crotch_pt.y)
    hollow_ctrl = Point(
        crotch_pt.x + (knee_in.x - crotch_pt.x) * INSEAM_HOLLOW_FRAC - in_dir[1] * INSEAM_HOLLOW_MM,
        crotch_pt.y + (knee_in.y - crotch_pt.y) * INSEAM_HOLLOW_FRAC + in_dir[0] * INSEAM_HOLLOW_MM,
    )
    inseam_upper = curve_through(crotch_pt, hollow_ctrl, knee_in, n=48)
    inseam_edge = inseam_upper + [hem_in]

    # 9. outseam: straight along the guideline knee -> guide_top, then a cubic
    # up to the waist corner
    guide_dir = unit_vector(guide_top.x - knee_out.x, guide_top.y - knee_out.y)
    out_chord = distance(guide_top, waist_out)
    end_dir = (sin(radians(OUTSEAM_END_ROT_DEG)), -cos(radians(OUTSEAM_END_ROT_DEG)))
    outseam_upper = [knee_out] + cubic_with_tangents(
        guide_top, waist_out, guide_dir, end_dir,
        alpha=OUTSEAM_ALPHA * out_chord, beta=OUTSEAM_BETA * out_chord, n=32,
    )

    # Assemble the closed chain: waist -> cf_crotch -> inseam -> hem -> outseam
    edges = [
        ("waist", waist_edge),
        ("cf_crotch", cf_crotch_edge),
        ("inseam", inseam_edge),
        ("hem", [hem_in, hem_out]),
        ("outseam", [hem_out] + outseam_upper),
    ]

    # hip width A (outseam curve x at the hip line -> c.f.), for the ease check
    outseam_x_at_hip = _x_at_y(outseam_upper, hip_y)
    hip_width_a = ftw - outseam_x_at_hip

    landmarks = {
        "waist_out": waist_out, "waist_cf": waist_cf,
        "hip_cf": hip_cf, "fcw_pt": fcw_pt, "halfd_pt": halfd_pt,
        "crotch_pt": crotch_pt,
        "knee_out": knee_out, "knee_in": knee_in,
        "hem_out": hem_out, "hem_in": hem_in,
    }
    construction_lines = [
        [Point(outseam_x_at_hip, hip_y), fcw_pt],                    # hip line
        [Point(_x_at_y(outseam_upper, crotch_y), crotch_y), crotch_pt],  # crotch line
        [knee_out, knee_in],                                          # knee line
        [Point(crease_x, hip_y), Point(crease_x, hem_y)],             # crease / grainline
    ]
    report = {
        "crease_x_mm": crease_x,
        "d_crotch_mm": d,
        "waist_len_mm": arc_length(waist_edge),
        "outseam_upper_len_mm": arc_length(outseam_upper),   # waist->knee transfer (m)
        "inseam_upper_len_mm": arc_length(inseam_upper),     # crotch->knee transfer (t)
        "hip_width_a_mm": hip_width_a,
        "levels_y_mm": {"hip": hip_y, "crotch": crotch_y, "knee": knee_y, "hem": hem_y},
    }
    return FrontDraft(landmarks=landmarks, edges=edges,
                      construction_lines=construction_lines, report=report)


def _x_at_y(pts: list[Point], y: float) -> float:
    """x of the polyline where it crosses the horizontal at y (first hit)."""
    for p, q in zip(pts, pts[1:]):
        if (p.y - y) * (q.y - y) <= 0 and abs(q.y - p.y) > 1e-12:
            t = (y - p.y) / (q.y - p.y)
            return p.x + t * (q.x - p.x)
    raise ValueError(f"polyline does not cross y={y}")
