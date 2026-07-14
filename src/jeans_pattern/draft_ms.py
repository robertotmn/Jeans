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
    point_at_arc_length,
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

# ---- back constants (same size-50 calibration) -----------------------------
# The back waistline drawn by the booklet is STRAIGHT from the trimmed outseam
# corner to the c.b. corner (collinear to 0.3 mm), so no curve constant needed.
BACK_CB_ADDITION_MM = 35.0        # "transfer + 3 to 4 cm" (mid value; 87 deg at c.b., as drawn)
BACK_STRETCH_MM = 7.0             # inseam transfer: front inseam minus 0.7 cm
BACK_REST_MAX_MM = 15.0           # leftover absorbed into the hip curve (warn beyond)
# outseam: quadratic knee->P_out hollowed 6 mm toward the crease, then a cubic
# P_out->waist corner arriving 5 deg off vertical (0.30/0.20 controls). Fit: 1.7 mm.
BACK_OUTSEAM_HOLLOW_MM = 6.0
BACK_OUTSEAM_END_ROT_DEG = -5.0
BACK_OUTSEAM_ALPHA, BACK_OUTSEAM_BETA = 0.30, 0.20
# seat J-curve from the Btw point to the back crotch point: starts along the
# c.b. direction, arrives at 30 deg below horizontal; controls 0.5/0.3 of the
# chord. Fit: 0.6 mm, arc length matches the drawing to 0.1 mm.
SEAT_END_ANGLE_DEG = 30.0
SEAT_ALPHA, SEAT_BETA = 0.5, 0.3
# back inseam: quadratic hollow, control 45% down the chord, 32 mm toward the
# crease (~16 mm actual hollow, as drawn). Fit: 0.5 mm.
BACK_INSEAM_HOLLOW_MM = 32.0
BACK_INSEAM_HOLLOW_FRAC = 0.45
# yoke line: 3.5 cm below the waist along the outseam, 7 cm along the c.b.
YOKE_BELOW_WAIST_OUTSEAM_MM = 35.0
YOKE_BELOW_WAIST_CB_MM = 70.0
# two waist darts at the thirds of the back waist, tips on the yoke line
DART_INTAKES_MM = (8.0, 12.0)     # outer dart 0.8 cm, inner dart 1.2 cm


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


@dataclass(frozen=True)
class Dart:
    a: Point      # waist leg toward the outseam
    tip: Point    # on the yoke line
    b: Point      # waist leg toward the c.b.


@dataclass(frozen=True)
class BackDraft:
    """Back trouser, drafted over the front in the same frame.

    edges: the BACK PIECE (cut at the yoke line): yoke_seam -> cb_seat ->
    inseam -> hem -> outseam. The yoke region geometry (waistline, darts,
    upper c.b./outseam stubs) is exposed separately for the yoke builder.
    """
    landmarks: dict[str, Point]
    edges: list[tuple[str, list[Point]]]
    construction_lines: list[list[Point]]
    report: dict
    # yoke-region geometry (between waistline and yoke line)
    waist_line: list[Point]          # W_fin -> cb_corner (straight, per the drawing)
    darts: tuple[Dart, Dart]
    yoke_line: list[Point]           # yoke_out -> yoke_cb
    outseam_top: list[Point]         # W_fin -> yoke_out along the outseam curve
    cb_top: list[Point]              # cb_corner -> yoke_cb along the c.b. line

    def outline(self) -> list[Point]:
        return chain_outline(self.edges)

    def edge(self, name: str) -> list[Point]:
        for n, pts in self.edges:
            if n == name:
                return pts
        raise KeyError(name)


def draft_back(m: Measurements, front: FrontDraft) -> BackDraft:
    hem_y = m.outseam_mm
    knee_y = m.outseam_mm - m.knee_length_mm
    crotch_y = m.body_rise_mm
    hip_y = crotch_y - m.hip_depth_above_crotch_mm
    crease_x = front.report["crease_x_mm"]

    # 1. below the knee: 1 cm outside the front on both sides
    hem_half = m.hem_width_mm / 4 - 5.0 + 10.0
    knee_half = m.knee_girth_mm / 4 - 5.0 + 10.0
    hem_out, hem_in = Point(crease_x - hem_half, hem_y), Point(crease_x + hem_half, hem_y)
    knee_out, knee_in = Point(crease_x - knee_half, knee_y), Point(crease_x + knee_half, knee_y)

    # 2. hip line extended 2 cm; Btw and Bcw measured horizontally on it
    p_out = Point(-20.0, hip_y)
    p_btw = Point(-20.0 + m.back_trouser_width_mm, hip_y)
    p_bcw = Point(p_btw.x + m.back_crotch_width_mm, hip_y)

    # 3. slant: auxiliary line from 1 cm above the crotch on the base line to
    # the Btw point; the c.b. is perpendicular to it through the Btw point
    p1 = Point(0.0, crotch_y - 10.0)
    aux_dir = unit_vector(p_btw.x - p1.x, p_btw.y - p1.y)
    cb_up = (aux_dir[1], -aux_dir[0])
    if cb_up[1] > 0:
        cb_up = (-cb_up[0], -cb_up[1])
    cb_down = (-cb_up[0], -cb_up[1])

    # 4. transfers
    # 4a. raw outseam corner: front outseam length up the outseam guideline
    m_front = front.report["outseam_upper_len_mm"]
    w_raw = point_along(knee_out, p_out, m_front)

    # 4b. back crotch point: on the inseam guideline, positioned so the
    # HOLLOWED inseam curve measures front inseam minus 0.7 cm
    t_target = front.report["inseam_upper_len_mm"] - BACK_STRETCH_MM

    def inseam_curve(crotch_pt: Point) -> list[Point]:
        u = unit_vector(knee_in.x - crotch_pt.x, knee_in.y - crotch_pt.y)
        ctrl = Point(
            crotch_pt.x + (knee_in.x - crotch_pt.x) * BACK_INSEAM_HOLLOW_FRAC - u[1] * BACK_INSEAM_HOLLOW_MM,
            crotch_pt.y + (knee_in.y - crotch_pt.y) * BACK_INSEAM_HOLLOW_FRAC + u[0] * BACK_INSEAM_HOLLOW_MM,
        )
        return curve_through(crotch_pt, ctrl, knee_in, n=48)

    s = t_target
    crotch_pt = point_along(knee_in, p_bcw, s)
    for _ in range(6):
        s += t_target - arc_length(inseam_curve(crotch_pt))
        crotch_pt = point_along(knee_in, p_bcw, s)
    inseam_upper = inseam_curve(crotch_pt)

    # 4c. c.b. waist corner: on the c.b. line, at (crease@knee -> w_raw) + 3.5 cm
    # from the crease@knee point
    k = Point(crease_x, knee_y)
    target = distance(k, w_raw) + BACK_CB_ADDITION_MM
    ax, ay = p_btw.x - k.x, p_btw.y - k.y
    b_lin = 2 * (ax * cb_up[0] + ay * cb_up[1])
    c_con = ax * ax + ay * ay - target * target
    tau = (-b_lin + (b_lin * b_lin - 4 * c_con) ** 0.5) / 2
    cb_corner = Point(p_btw.x + cb_up[0] * tau, p_btw.y + cb_up[1] * tau)

    # 5. waistline: straight toward w_raw; needed length = W/2 + 2 cm of darts
    # minus the front waist; the leftover is absorbed into the hip curve
    back_waist = (m.waistband_mm / 2 + 20.0) - front.report["waist_len_mm"]
    w_fin = point_along(cb_corner, w_raw, back_waist)
    rest = distance(w_fin, w_raw)
    waist_line = [w_fin, cb_corner]
    waist_dir = unit_vector(cb_corner.x - w_fin.x, cb_corner.y - w_fin.y)

    # 6. outseam: hollowed quadratic knee -> P_out, cubic P_out -> w_fin
    guide_dir = unit_vector(p_out.x - knee_out.x, p_out.y - knee_out.y)
    mid = Point((knee_out.x + p_out.x) / 2 - guide_dir[1] * BACK_OUTSEAM_HOLLOW_MM,
                (knee_out.y + p_out.y) / 2 + guide_dir[0] * BACK_OUTSEAM_HOLLOW_MM)
    outseam_lower = curve_through(knee_out, mid, p_out, n=24)
    ch = distance(p_out, w_fin)
    end_dir = (sin(radians(BACK_OUTSEAM_END_ROT_DEG)), -cos(radians(BACK_OUTSEAM_END_ROT_DEG)))
    outseam_upper = cubic_with_tangents(
        p_out, w_fin, guide_dir, end_dir,
        alpha=BACK_OUTSEAM_ALPHA * ch, beta=BACK_OUTSEAM_BETA * ch, n=24,
    )
    outseam_full = outseam_lower + outseam_upper[1:]        # knee -> w_fin

    # 7. yoke line: 3.5 cm below the waist along the outseam, 7 cm along c.b.
    from_wfin = outseam_full[::-1]                           # w_fin -> knee
    yoke_out = point_at_arc_length(from_wfin, YOKE_BELOW_WAIST_OUTSEAM_MM)
    yoke_cb = Point(cb_corner.x + cb_down[0] * YOKE_BELOW_WAIST_CB_MM,
                    cb_corner.y + cb_down[1] * YOKE_BELOW_WAIST_CB_MM)
    yoke_line = [yoke_out, yoke_cb]

    # 8. darts at the thirds of the back waist, perpendicular to it, tips on
    # the yoke line
    axis_dir = (-waist_dir[1], waist_dir[0])
    if axis_dir[1] < 0:
        axis_dir = (-axis_dir[0], -axis_dir[1])
    darts = []
    for i, intake in enumerate(DART_INTAKES_MM, start=1):
        center = point_along(w_fin, cb_corner, back_waist * i / 3)
        tip = line_intersection(center,
                                Point(center.x + axis_dir[0], center.y + axis_dir[1]),
                                yoke_out, yoke_cb)
        darts.append(Dart(
            a=Point(center.x - waist_dir[0] * intake / 2, center.y - waist_dir[1] * intake / 2),
            tip=tip,
            b=Point(center.x + waist_dir[0] * intake / 2, center.y + waist_dir[1] * intake / 2),
        ))
    darts = tuple(darts)

    # 9. seat: straight c.b. from the corner to the Btw point, then the
    # J-curve to the crotch point
    seat_ch = distance(p_btw, crotch_pt)
    seat_end = (cos(radians(SEAT_END_ANGLE_DEG)), sin(radians(SEAT_END_ANGLE_DEG)))
    seat_j = cubic_with_tangents(p_btw, crotch_pt, cb_down, seat_end,
                                 alpha=SEAT_ALPHA * seat_ch, beta=SEAT_BETA * seat_ch, n=36)

    # 10. the back PIECE is cut at the yoke line
    outseam_piece = _truncate_at_arc(outseam_full, arc_length(outseam_full) - YOKE_BELOW_WAIST_OUTSEAM_MM)
    edges = [
        ("yoke_seam", [yoke_out, yoke_cb]),
        ("cb_seat", [yoke_cb, p_btw] + seat_j[1:]),
        ("inseam", inseam_upper + [hem_in]),                 # crotch -> knee -> hem
        ("hem", [hem_in, hem_out]),
        ("outseam", [hem_out] + outseam_piece),              # hem -> knee -> yoke_out
    ]

    hip_width_b = p_btw.x - _x_at_y(outseam_full, hip_y)
    landmarks = {
        "hem_out": hem_out, "hem_in": hem_in,
        "knee_out": knee_out, "knee_in": knee_in,
        "p_out": p_out, "p_btw": p_btw, "p_bcw": p_bcw, "slant_p1": p1,
        "crotch_pt": crotch_pt, "waist_raw": w_raw, "waist_out": w_fin,
        "cb_corner": cb_corner, "yoke_out": yoke_out, "yoke_cb": yoke_cb,
        "dart1_a": darts[0].a, "dart1_tip": darts[0].tip, "dart1_b": darts[0].b,
        "dart2_a": darts[1].a, "dart2_tip": darts[1].tip, "dart2_b": darts[1].b,
    }
    construction_lines = [
        [Point(_x_at_y(outseam_full, hip_y), hip_y), p_bcw],       # hip line
        [Point(_x_at_y(outseam_full, crotch_y), crotch_y), Point(crease_x + knee_half, crotch_y)],
        [knee_out, knee_in],                                        # knee line
        [Point(crease_x, hip_y), Point(crease_x, hem_y)],           # crease / grainline
    ]
    waist_cb_angle = _angle_deg(waist_dir, cb_up)
    report = {
        "back_waist_mm": back_waist,
        "rest_mm": rest,
        "hip_width_b_mm": hip_width_b,
        "inseam_upper_len_mm": arc_length(inseam_upper),
        "outseam_full_len_mm": arc_length(outseam_full),
        "waist_cb_angle_deg": waist_cb_angle,
        "warnings": (
            [f"resto vita {rest / 10:.1f} cm > 1.5 cm: curva fianco forzata"]
            if rest > BACK_REST_MAX_MM else []
        ),
    }
    return BackDraft(landmarks=landmarks, edges=edges,
                     construction_lines=construction_lines, report=report,
                     waist_line=waist_line, darts=darts, yoke_line=yoke_line,
                     outseam_top=_truncate_at_arc(from_wfin, YOKE_BELOW_WAIST_OUTSEAM_MM),
                     cb_top=[cb_corner, yoke_cb])


def _truncate_at_arc(pts: list[Point], s: float) -> list[Point]:
    """Initial portion of the polyline up to arc length s (last point interpolated)."""
    out = [pts[0]]
    walked = 0.0
    for p, q in zip(pts, pts[1:]):
        seg = distance(p, q)
        if walked + seg >= s:
            out.append(point_at_arc_length([p, q], s - walked))
            return out
        out.append(q)
        walked += seg
    return out


def _angle_deg(u: tuple[float, float], v: tuple[float, float]) -> float:
    from math import acos, degrees
    dot = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
    return degrees(acos(dot))
