"""M. Mueller & Sohn "Jeans-Basics" drafting: Basic Denim Jacket Block, body
(pages 11-12) and sleeve (pages 12-13).

Coordinate frame (mm): origin = back neck point N; y grows downward, so the
chest line is y = Sd, the waist line y = Bwl and the hem line y = Lg. x grows
from the centre back TOWARD THE FRONT: every "measure ... to the left" of the
booklet is +x here. Back and front share one frame exactly as the booklet
draws them, the front side seam sitting BODY_GAP_MM to the right of the back
one, so the generated draft overlays the scale drawing 1:1.

The sleeve has a frame of its own (page 12, drawing "2"): origin = the starting
point A, y down along the sleeve, x toward the back of the sleeve.

Every construction rule and curve-shape constant in this module was validated
against the vector geometry of the booklet's own size-50 scale drawing
(tests/data/ms_jacket_reference_size50.json, extracted by
scripts/extract_jacket_reference.py). Landmark agreement is <= ~1.3 mm (the
worst cases are landmarks the drawing itself prints off its own construction,
see the module tests); curve agreement <= ~1 mm.
"""
from dataclasses import dataclass
from math import cos, radians, sin

from .geometry import (
    Point,
    arc_length,
    chain_outline,
    cubic_bezier,
    cubic_with_tangents,
    distance,
    horizontal_line_through,
    line_intersection,
    point_along,
    point_at_arc_length,
    unit_vector,
)
from .measurements_jacket import JacketMeasurements

# ---- drafting amounts quoted by the booklet (pages 11-12) ------------------
CB_TAPER_MM = 25.0             # "taper the centre back 2.5 cm at the hip"
NECK_RISE_MM = 20.0            # "square up 2 cm" from the neck width point
NECK_EXTEND_MM = 10.0          # "lengthen the neckline 1 cm"
SHOULDER_SLOPE_BACK_MM = 22.0  # book range 2 - 2.5 cm; 2.2 is what is drawn (D2)
SHOULDER_WIDTH_ADD_MM = 15.0   # "measure 1.5 cm from the back width to the left"
ARMHOLE_GUIDE_OUT_MM = 10.0    # "square out 1 cm" at 1/4 scye depth
BACK_SIDE_ADD_MM = 15.0        # "the 1/2 scye width plus 1.5 cm on the chest line"
SEAM_RELOCATION_MM = 10.0      # "shift the shoulder seam 1 cm to the front"
BODY_GAP_MM = 60.0             # "leave about 6 cm space between back and front"
FRONT_PITCH_SUB_MM = 15.0      # front pitch line = 1/2 scye width minus 1.5 cm
FRONT_SHOULDER_SLOPE_MM = 45.0  # "measure 4.5 cm downward for the front shoulder slope"
FRONT_SHOULDER_SUB_MM = 5.0    # "transfer the shoulder width of the back minus 0.5 - 1 cm" (D3)
FRONT_NECK_ADD_MM = 20.0       # front neckline width = Nw + 2 cm
CF_HEM_ADD_MM = 5.0            # c.f. below the waist = side seam plus 0.5 cm
HIP_EASE_MIN_MM = 50.0         # "Check Hg: at least Hg + 5 - 6 cm"

# ---- sleeve amounts quoted by the booklet (pages 12-13) -------------------
SCH_SUB_MM = 40.0              # Sch = 1/2 Ah minus (1/10 of 1/2 Ah + 4.0)
SCW_SUB_MM = 25.0              # Scw = 1/2 Ac minus 2.5
SLEEVE_HEM_MM = 310.0          # Sh, a style choice taken from the chart (D13)
SLEEVE_LENGTH_SPLIT_MM = 15.0  # "measure 1.5 cm up and down" for front/back length
ELBOW_UP_MM = 15.0             # elbow = midway biceps/front sleeve length, minus 1.5
FAN_UP_SUB_MM = 10.0           # FAN = 1/4 scye width minus 1 cm above the biceps
SP_ADD_MM = 10.0               # Sp = half of A -> E plus 1 cm
T_BACK_MM = 25.0               # low cap guide runs from Q to 2.5 cm left of Sp
U2_ALONG_MM = 20.0             # "measure 2 cm downward ... along the guideline"
U22_FROM_Q_MM = 22.0           # "measure 2.2 cm ... to the right for a better transition"
FRONT_TAPER_ELBOW_MM = 20.0    # "taper the front sleeve 2 cm at the elbow line"
FRONT_SEAM_OFFSET_MM = 30.0    # "measure 3 cm from the front sleeve fold ... outside and inside"
BACK_FOLD_ADD_MM = 35.0        # back fold at the elbow = front fold + 1/2 Sh + 3.5 (D14)
BACK_MERGE_BELOW_ELBOW_MM = 90.0  # under-sleeve back seam rejoins the fold here (D16)

# Ah and Ac are measured on the block just drafted, not taken from the chart.
# Both come out ~0.5% shorter than the booklet's own numbers (Ah 439.9 vs 442,
# Ac 531.2 vs 534), and the chart is besides internally inconsistent (Ah 44.2
# but 1/2 Ah 22.3). These two constants absorb both gaps and reproduce the
# drawn sleeve cap height 16.10 and cap width 24.2 (D12, recalibrated here).
AH_HALF_CAL_MM = 3.4
SCW_CAL_MM = 1.4

# ---- calibrated curve-shape constants (size-50 drawing fit) ---------------
# back neckline: ONE cubic leaving N square to the centre back seam and
# arriving at A2 at -46.5 deg; the 1 cm lengthening and the 1 cm seam
# relocation are the natural continuation of the same stroke (the booklet
# lengthens the neckline with the French curve, not along the tangent), so the
# curve is sampled past t = 1. Fit: 0.3 mm.
BACK_NECK_END_DEG = -46.5
BACK_NECK_CTRL = 0.35
BACK_NECK_T_MAX = 1.5
# back armhole: cubic SP0 -> G1 leaving square to the shoulder line and
# arriving 11.4 deg off vertical, then cubic G1 -> U_b arriving horizontal.
# Fit: 0.4 mm (the hollow settles ~0.5 cm past the back width line, as drawn).
BACK_AH_G1_DEG = -11.4
BACK_AH_UPPER_ALPHA, BACK_AH_UPPER_BETA = 0.194, 0.260
BACK_AH_LOWER_ALPHA, BACK_AH_LOWER_BETA = 0.534, 0.161
# front neckline: cubic from the neckline corner Cn to the c.f. neck point,
# leaving 6.7 deg off the perpendicular to the shoulder guideline and arriving
# square to the c.f. Fit: 0.2 mm.
FRONT_NECK_START_DEG = 6.7
FRONT_NECK_ALPHA, FRONT_NECK_BETA = 0.572, 0.331
# front armhole: cubic SP_f -> 1/4 scye depth point, square to the shoulder
# line at the start and tangent to the front pitch line at the end, then cubic
# on to U_f arriving horizontal. Fit: 0.7 mm.
FRONT_AH_UPPER_ALPHA, FRONT_AH_UPPER_BETA = 0.128, 0.361
FRONT_AH_LOWER_ALPHA, FRONT_AH_LOWER_BETA = 0.612, 0.264
# front hem: cubic square to the side seam and to the c.f. Fit: 0.1 mm.
FRONT_HEM_CTRL = 0.474
# upper sleeve cap, FST -> FAN: cubic leaving the front seam 24 deg off its
# perpendicular and arriving along the FAN -> M1 guideline. Fit: 0.2 mm.
CAP_FRONT_START_DEG = -24.0
CAP_FRONT_ALPHA, CAP_FRONT_BETA = 0.385, 0.412
# upper sleeve cap, M2 -> Sp: cubic continuing the straight FAN -> M2 stretch
# and arriving horizontal at Sp, bowing ~1.7 cm out over the M2 -> Sp guide.
# Fit: 0.4 mm.
CAP_TOP_ALPHA, CAP_TOP_BETA = 0.229, 0.467
# upper sleeve cap, Sp -> Q: cubic leaving Sp horizontal and arriving at Q
# already aimed at U22 (the last stretch Q -> U22 is straight). Fit: 0.4 mm.
CAP_BACK_ALPHA, CAP_BACK_BETA = 0.111, 0.604
# under sleeve cap, UST -> U2: cubic leaving the front seam 14.8 deg off its
# perpendicular - which is what makes it graze the biceps line - and arriving
# tangent to the Q -> T guideline. Fit: 0.6 mm.
UNDER_CAP_START_DEG = 14.8
UNDER_CAP_ALPHA, UNDER_CAP_BETA = 0.288, 0.632
# sleeve back seams: both leave their cap point squared down and arrive tangent
# to the back fold. Fit: 0.6 mm (upper, belly 22.5) / 1.1 mm (under, belly 20.9).
UPPER_BACK_ALPHA, UPPER_BACK_BETA = 0.100, 0.400
UNDER_BACK_ALPHA, UNDER_BACK_BETA = 0.080, 0.480


def _rot(u: tuple[float, float], deg: float) -> tuple[float, float]:
    r = radians(deg)
    return (u[0] * cos(r) - u[1] * sin(r), u[0] * sin(r) + u[1] * cos(r))


def _cubic_past_end(p0: Point, p1: Point, p2: Point, p3: Point,
                    t_max: float, n: int) -> list[Point]:
    """The same cubic Bezier evaluated from t=1 to t=t_max.

    Beyond t=1 the polynomial keeps position, tangent and curvature, which is
    what a French curve does when the booklet lengthens a neckline past its
    construction point. Returns n points, the first one being p3.
    """
    pts = []
    for i in range(n):
        t = 1.0 + (t_max - 1.0) * i / (n - 1)
        u = 1 - t
        pts.append(Point(
            u**3 * p0.x + 3 * u*u * t * p1.x + 3 * u * t*t * p2.x + t**3 * p3.x,
            u**3 * p0.y + 3 * u*u * t * p1.y + 3 * u * t*t * p2.y + t**3 * p3.y))
    return pts


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


def _offset_corner(a: Point, b: Point, c: Point, d: float) -> Point:
    """Corner of the polyline a-b-c offset by d square to both legs (mitre join).

    Positive d offsets to the right of the travel direction a -> b -> c, which
    in this frame (y down) is +x for a line running downward.
    """
    ua = unit_vector(b.x - a.x, b.y - a.y)
    uc = unit_vector(c.x - b.x, c.y - b.y)
    return line_intersection(
        Point(a.x + ua[1] * d, a.y - ua[0] * d), Point(b.x + ua[1] * d, b.y - ua[0] * d),
        Point(b.x + uc[1] * d, b.y - uc[0] * d), Point(c.x + uc[1] * d, c.y - uc[0] * d))


@dataclass(frozen=True)
class JacketBackDraft:
    """Jacket back block: named landmarks, ordered edge chains, helper lines.

    edges: closed chain neck -> shoulder -> armhole -> side_upper ->
    side_lower -> hem -> cb (neck travels N -> HSP_b, hem H_b -> K).
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


@dataclass(frozen=True)
class JacketFrontDraft:
    """Jacket front block, drafted beside the back in the same frame.

    edges: closed chain shoulder -> armhole -> side_upper -> side_lower ->
    hem -> cf_lower -> cf_upper -> neck (shoulder travels HSP_f -> SP_f).
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


def draft_jacket_back(m: JacketMeasurements) -> JacketBackDraft:
    sd, bwl, lg = m.scye_depth_mm, m.back_waist_length_mm, m.jacket_length_mm

    # 1. centre back: the seam is a single straight line from N to the hem,
    # tapered 2.5 cm, so the c.b. sits at x_cb(y) = taper * y / Lg.
    n_pt = Point(0.0, 0.0)
    k_pt = Point(CB_TAPER_MM, lg)
    cb_dir = unit_vector(k_pt.x - n_pt.x, k_pt.y - n_pt.y)
    cb_perp = (cb_dir[1], -cb_dir[0])            # square to the c.b., toward the front
    x_cb_chest = CB_TAPER_MM * sd / lg
    x_cb_waist = CB_TAPER_MM * bwl / lg

    # 2. neckline: Nw toward the front on the y=0 line, squared up 2 cm. The
    # curve leaves N square to the c.b. seam and is continued past A2 for the
    # 1 cm lengthening (E) and the 1 cm seam relocation (HSP_b).
    a2 = Point(m.neck_width_mm, -NECK_RISE_MM)
    neck_chord = distance(n_pt, a2)
    end_dir = (cos(radians(BACK_NECK_END_DEG)), sin(radians(BACK_NECK_END_DEG)))
    ctrl1 = Point(n_pt.x + cb_perp[0] * BACK_NECK_CTRL * neck_chord,
                  n_pt.y + cb_perp[1] * BACK_NECK_CTRL * neck_chord)
    ctrl2 = Point(a2.x - end_dir[0] * BACK_NECK_CTRL * neck_chord,
                  a2.y - end_dir[1] * BACK_NECK_CTRL * neck_chord)
    neck_main = cubic_bezier(n_pt, ctrl1, ctrl2, a2, n=33)
    neck_tail = _cubic_past_end(n_pt, ctrl1, ctrl2, a2, BACK_NECK_T_MAX, n=25)
    e_pt = point_at_arc_length(neck_tail, NECK_EXTEND_MM)
    hsp_b = point_at_arc_length(neck_tail, NECK_EXTEND_MM + SEAM_RELOCATION_MM)
    neck_edge = neck_main + _truncate_at_arc(neck_tail, NECK_EXTEND_MM + SEAM_RELOCATION_MM)[1:]

    # 3. back width on the chest line, measured FROM THE C.B. SEAM; shoulder
    # slope 2.2 cm down on that vertical, guideline back to A2 extended 1.5 cm.
    x_bw = x_cb_chest + m.back_width_mm
    s1 = Point(x_bw, SHOULDER_SLOPE_BACK_MM)
    sh_dir = unit_vector(s1.x - a2.x, s1.y - a2.y)
    sp0 = point_along(a2, s1, distance(a2, s1) + SHOULDER_WIDTH_ADD_MM)
    sh_perp = (-sh_dir[1], sh_dir[0])            # square to the shoulder, toward the armhole

    # 4. seam relocation: the shoulder point moves 1 cm square to the shoulder
    # line, the neck point 1 cm along the neckline (step 2) - together they
    # shift the whole shoulder seam 1 cm toward the front.
    sp_b = Point(sp0.x - sh_perp[0] * SEAM_RELOCATION_MM,
                 sp0.y - sh_perp[1] * SEAM_RELOCATION_MM)

    # 5. armhole guides and the side seam position
    g1 = Point(x_bw + ARMHOLE_GUIDE_OUT_MM, sd - sd / 4)
    x_side = x_bw + m.scye_width_mm / 2 + BACK_SIDE_ADD_MM
    u_b = Point(x_side, sd)

    # 6. armhole: SP0 -> G1 -> U_b (the relocated stub SP_b -> SP0 opens it)
    ah_up_chord = distance(sp0, g1)
    g1_dir = _rot((0.0, 1.0), BACK_AH_G1_DEG)
    ah_upper = cubic_with_tangents(
        sp0, g1, sh_perp, g1_dir,
        alpha=BACK_AH_UPPER_ALPHA * ah_up_chord, beta=BACK_AH_UPPER_BETA * ah_up_chord, n=32)
    ah_low_chord = distance(g1, u_b)
    ah_lower = cubic_with_tangents(
        g1, u_b, g1_dir, (1.0, 0.0),
        alpha=BACK_AH_LOWER_ALPHA * ah_low_chord, beta=BACK_AH_LOWER_BETA * ah_low_chord, n=32)
    armhole = [sp_b] + ah_upper + ah_lower[1:]

    # 7. hem square to the c.b. seam, side seam square to the hem: the waist
    # taper t is the geometric consequence of those two right angles (D8).
    h_b = Point(x_side, k_pt.y + cb_perp[1] * (x_side - k_pt.x) / cb_perp[0])
    w_b = Point(h_b.x - cb_dir[0] * (h_b.y - bwl) / cb_dir[1], bwl)

    edges = [
        ("neck", neck_edge),                     # N -> HSP_b
        ("shoulder", [hsp_b, sp_b]),
        ("armhole", armhole),                    # SP_b -> U_b
        ("side_upper", [u_b, w_b]),
        ("side_lower", [w_b, h_b]),
        ("hem", [h_b, k_pt]),
        ("cb", [k_pt, n_pt]),
    ]
    landmarks = {
        "N": n_pt, "A2": a2, "E": e_pt, "HSP_b": hsp_b,
        "S1": s1, "SP0": sp0, "SP_b": sp_b, "G1": g1,
        "U_b": u_b, "W_b": w_b, "H_b": h_b, "K": k_pt,
    }
    construction_lines = [
        [n_pt, Point(0.0, lg)],                                  # c.b. vertical / grainline
        [Point(x_cb_chest, sd), u_b],                            # chest line
        [Point(x_cb_waist, bwl), w_b],                           # waist line
        [Point(x_bw, 0.0), Point(x_bw, sd)],                     # back width line
        [a2, sp0],                                               # shoulder guideline
        [Point(x_bw, g1.y), g1],                                 # 1/4 Sd square-out
    ]
    report = {
        "levels_y_mm": {"chest": sd, "waist": bwl, "hem": lg},
        "x_back_width_mm": x_bw,
        "x_side_mm": x_side,
        "shoulder_len_mm": distance(hsp_b, sp_b),
        "neck_arc_mm": arc_length(neck_edge),                    # N -> HSP_b, the finished neckline
        "armhole_arc_mm": arc_length(armhole),
        "armhole_height_mm": sd - sp_b.y,                        # back ah, transfer for the sleeve
        "chest_len_mm": u_b.x - x_cb_chest,
        "hem_len_mm": distance(k_pt, h_b),
        "side_lower_len_mm": distance(w_b, h_b),
        "side_upper_len_mm": distance(u_b, w_b),
        "waist_taper_mm": h_b.x - w_b.x,
    }
    return JacketBackDraft(landmarks=landmarks, edges=edges,
                           construction_lines=construction_lines, report=report)


def draft_jacket_front(m: JacketMeasurements, back: JacketBackDraft) -> JacketFrontDraft:
    sd, bwl = m.scye_depth_mm, m.back_waist_length_mm

    # 8. side seam 6 cm past the back one; front pitch line 1/2 Sw - 1.5 cm
    # further, carrying the armhole depth, 1/4 scye depth and FAN levels.
    x_side = back.landmarks["U_b"].x + BODY_GAP_MM
    u_f = Point(x_side, sd)
    x_pitch = x_side + m.scye_width_mm / 2 - FRONT_PITCH_SUB_MM
    p_top = Point(x_pitch, sd - m.armhole_depth_mm)
    quarter_sd = Point(x_pitch, sd - sd / 4)
    fan = Point(x_pitch, sd - m.scye_width_mm / 4)

    # 9. chest width and abdomen width toward the c.f.; the line through the
    # half-points, extended up to the armhole depth level, gives the neckline
    # corner Cn.
    c1 = Point(x_pitch + m.chest_width_mm, sd)
    c2 = Point(x_pitch + m.abdomen_width_mm, bwl)
    mid_chest = Point(x_pitch + m.chest_width_mm / 2, sd)
    mid_waist = Point(x_pitch + m.abdomen_width_mm / 2, bwl)
    cn = line_intersection(mid_chest, mid_waist, *horizontal_line_through(p_top.y))
    s2 = Point(x_pitch, p_top.y + FRONT_SHOULDER_SLOPE_MM)
    aux_dir = unit_vector(s2.x - cn.x, s2.y - cn.y)
    aux_perp = (aux_dir[1], -aux_dir[0])         # square to the guideline, away from the neck

    # 10. front neckline: Nw down the half-points line, then Nw + 2 cm square
    # out to the c.f. neck point; the curve arrives square to the c.f. HSP_f
    # is 1 cm along it - the front half of the seam relocation.
    q1 = point_along(cn, mid_waist, m.neck_width_mm)
    down = unit_vector(mid_waist.x - mid_chest.x, mid_waist.y - mid_chest.y)
    c0 = Point(q1.x + down[1] * (m.neck_width_mm + FRONT_NECK_ADD_MM),
               q1.y - down[0] * (m.neck_width_mm + FRONT_NECK_ADD_MM))
    cf_dir = unit_vector(c1.x - c0.x, c1.y - c0.y)
    neck_chord = distance(cn, c0)
    neck_full = cubic_with_tangents(
        cn, c0, _rot(aux_perp, FRONT_NECK_START_DEG), (cf_dir[1], -cf_dir[0]),
        alpha=FRONT_NECK_ALPHA * neck_chord, beta=FRONT_NECK_BETA * neck_chord, n=48)
    hsp_f = point_at_arc_length(neck_full, SEAM_RELOCATION_MM)
    neck_edge = _truncate_at_arc(neck_full[::-1],
                                 arc_length(neck_full) - SEAM_RELOCATION_MM)[::-1]

    # 11. front shoulder: SP_f sits on the RELOCATED guideline (the Cn -> S2
    # line moved 1 cm square to itself) at the finished back shoulder length
    # minus 0.5 cm from HSP_f. Solved as a line/circle intersection because
    # the two 1 cm relocations are not parallel, so the raw guideline lengths
    # do not carry the rule (D3, amended).
    target = back.report["shoulder_len_mm"] - FRONT_SHOULDER_SUB_MM
    origin = Point(cn.x + aux_perp[0] * SEAM_RELOCATION_MM,
                   cn.y + aux_perp[1] * SEAM_RELOCATION_MM)
    ox, oy = origin.x - hsp_f.x, origin.y - hsp_f.y
    b_lin = 2 * (ox * aux_dir[0] + oy * aux_dir[1])
    c_con = ox * ox + oy * oy - target * target
    tau = (-b_lin + (b_lin * b_lin - 4 * c_con) ** 0.5) / 2
    sp_f = Point(origin.x + aux_dir[0] * tau, origin.y + aux_dir[1] * tau)
    sp0_f = Point(sp_f.x - aux_perp[0] * SEAM_RELOCATION_MM,
                  sp_f.y - aux_perp[1] * SEAM_RELOCATION_MM)

    # 12. front armhole: square to the shoulder at SP_f, tangent to the front
    # pitch line at the 1/4 scye depth point, horizontal into U_f.
    ah_up_chord = distance(sp_f, quarter_sd)
    ah_upper = cubic_with_tangents(
        sp_f, quarter_sd, aux_perp, (0.0, 1.0),
        alpha=FRONT_AH_UPPER_ALPHA * ah_up_chord, beta=FRONT_AH_UPPER_BETA * ah_up_chord, n=32)
    ah_low_chord = distance(quarter_sd, u_f)
    ah_lower = cubic_with_tangents(
        quarter_sd, u_f, (0.0, 1.0), (-1.0, 0.0),
        alpha=FRONT_AH_LOWER_ALPHA * ah_low_chord, beta=FRONT_AH_LOWER_BETA * ah_low_chord, n=32)
    armhole = ah_upper + ah_lower[1:]

    # 13. side seam: same waist taper as the back, same waist-to-hem length
    # (mirrored); the c.f. below the waist is that length plus 0.5 cm.
    taper = back.report["waist_taper_mm"]
    w_f = Point(x_side + taper, bwl)
    h_f = Point(x_side, back.landmarks["H_b"].y)
    c3 = Point(c2.x, bwl + back.report["side_lower_len_mm"] + CF_HEM_ADD_MM)
    side_dir = unit_vector(h_f.x - w_f.x, h_f.y - w_f.y)
    hem_chord = distance(h_f, c3)
    hem_edge = cubic_with_tangents(
        h_f, c3, (side_dir[1], -side_dir[0]), (1.0, 0.0),
        alpha=FRONT_HEM_CTRL * hem_chord, beta=FRONT_HEM_CTRL * hem_chord, n=32)

    edges = [
        ("shoulder", [hsp_f, sp_f]),
        ("armhole", armhole),                    # SP_f -> U_f
        ("side_upper", [u_f, w_f]),
        ("side_lower", [w_f, h_f]),
        ("hem", hem_edge),                       # H_f -> C3
        ("cf_lower", [c3, c2]),
        ("cf_upper", [c2, c1, c0]),
        ("neck", neck_edge[::-1]),               # C0 -> HSP_f
    ]
    landmarks = {
        "P_top": p_top, "Cn": cn, "S2": s2, "SP0_f": sp0_f, "SP_f": sp_f,
        "HSP_f": hsp_f, "C0": c0, "C1": c1, "C2": c2, "C3": c3,
        "FAN": fan, "quarter_Sd": quarter_sd,
        "U_f": u_f, "W_f": w_f, "H_f": h_f,
    }
    construction_lines = [
        [p_top, Point(x_pitch, c3.y)],                           # front pitch line
        [u_f, c1],                                               # chest line
        [w_f, c2],                                               # waist line
        [cn, mid_waist],                                         # half-points line
        [cn, s2],                                                # shoulder guideline
        [q1, c0],                                                # front neck square-out
    ]

    # The chart states both checks on the HALF pattern: "Total chest = 1/2 Cg
    # + ease" and "Check Hg: at least Hg + 5 - 6" read on the back plus front
    # hem, i.e. 1/2 Hg plus HIP_EASE_MIN_MM.
    total_chest = back.report["chest_len_mm"] + (c1.x - u_f.x)
    total_hem = back.report["hem_len_mm"] + arc_length(hem_edge)
    hip_ease = total_hem - m.hip_girth_mm / 2
    report = {
        "shoulder_len_mm": distance(hsp_f, sp_f),
        "neck_arc_mm": arc_length(neck_edge),
        "armhole_arc_mm": arc_length(armhole),
        "armhole_height_mm": distance(sp_f, Point(x_pitch, sd)),  # front ah, oblique
        "chest_len_mm": c1.x - u_f.x,
        "hem_len_mm": arc_length(hem_edge),
        "side_lower_len_mm": distance(w_f, h_f),
        "cf_lower_len_mm": distance(c2, c3),
        "total_chest_mm": total_chest,
        "chest_ease_mm": total_chest - m.chest_girth_mm / 2,
        "total_hem_mm": total_hem,
        "hip_ease_mm": hip_ease,
        # transfers for the sleeve block (page 12 step 2)
        "armhole_circ_mm": back.report["armhole_arc_mm"] + arc_length(armhole),
        "armhole_height_total_mm": back.report["armhole_height_mm"]
        + distance(sp_f, Point(x_pitch, sd)),
        "warnings": (
            [f"Check Hg: orlo {total_hem / 10:.1f} cm, servono almeno "
             f"{(m.hip_girth_mm / 2 + HIP_EASE_MIN_MM) / 10:.1f} cm (1/2 Hg + 5)"]
            if hip_ease < HIP_EASE_MIN_MM else []
        ),
    }
    return JacketFrontDraft(landmarks=landmarks, edges=edges,
                            construction_lines=construction_lines, report=report)


@dataclass(frozen=True)
class JacketSleeveDraft:
    """Jacket sleeve block: upper and under sleeve drafted in the same frame.

    upper: closed chain cap_front -> cap -> back_seam -> back_fold -> hem ->
    front_seam (FST -> FAN -> U22 -> F_b -> B_hem -> fold_hem -> FST).
    under: closed chain cap -> back_seam -> back_fold -> hem -> front_seam
    (UST -> U2 -> merge_back -> B_hem -> hem_front -> UST).
    """
    landmarks: dict[str, Point]
    upper: list[tuple[str, list[Point]]]
    under: list[tuple[str, list[Point]]]
    construction_lines: list[list[Point]]
    notches: dict[str, Point]
    report: dict

    def outline(self, part: str) -> list[Point]:
        return chain_outline(self._part(part))

    def edge(self, part: str, name: str) -> list[Point]:
        for n, pts in self._part(part):
            if n == name:
                return pts
        raise KeyError(name)

    def _part(self, part: str) -> list[tuple[str, list[Point]]]:
        if part == "upper":
            return self.upper
        if part == "under":
            return self.under
        raise KeyError(part)


def draft_jacket_sleeve(m: JacketMeasurements, back: JacketBackDraft,
                        front: JacketFrontDraft) -> JacketSleeveDraft:
    sw, sl, sh = m.scye_width_mm, m.sleeve_length_mm, SLEEVE_HEM_MM

    # 1. sleeve measurements, read off the block just drafted (page 12 step 2):
    # "measure the front and back armhole height as shown and add both".
    ah = back.report["armhole_height_mm"] + front.report["armhole_height_mm"]
    ac = back.report["armhole_arc_mm"] + front.report["armhole_arc_mm"]
    half_ah = ah / 2 + AH_HALF_CAL_MM
    sch = half_ah - (half_ah / 10 + SCH_SUB_MM)
    scw = ac / 2 - SCW_SUB_MM + SCW_CAL_MM

    # 2. levels on the vertical from A: biceps, elbow, front and back hem
    a_pt = Point(0.0, 0.0)
    y_biceps = sch
    y_front, y_back = sl - SLEEVE_LENGTH_SPLIT_MM, sl + SLEEVE_LENGTH_SPLIT_MM
    y_elbow = (y_biceps + y_front) / 2 - ELBOW_UP_MM

    # 3. the original line y = 0 and its divisions: the cap width measured
    # diagonally from FAN lands on E, Sp is half of A -> E plus 1 cm.
    fan = Point(0.0, y_biceps - (sw / 4 - FAN_UP_SUB_MM))
    e_pt = Point((scw * scw - fan.y * fan.y) ** 0.5, 0.0)
    sp = Point(e_pt.x / 2 + SP_ADD_MM, 0.0)
    m1 = Point(sp.x / 2, 0.0)
    third1 = Point(sp.x + (e_pt.x - sp.x) / 3, 0.0)
    m2 = Point(m1.x / 2, fan.y / 2)                  # midpoint of the M1 -> FAN guide
    q_pt = Point(e_pt.x, sw / 4)
    t_pt = Point(sp.x - T_BACK_MM, y_biceps)

    # 4. back cap ends: U2 2 cm down the Q -> T guide, U22 2.2 cm from Q on the
    # horizontal squared out from U2.
    u2 = point_along(q_pt, t_pt, U2_ALONG_MM)
    u22 = Point(q_pt.x + (U22_FROM_Q_MM ** 2 - (u2.y - q_pt.y) ** 2) ** 0.5, u2.y)

    # 5. front sleeve fold, tapered 2 cm at the elbow; the front seams are its
    # +/- 3 cm parallels, mitred at the elbow and squared off at the hem.
    fold_elbow = Point(FRONT_TAPER_ELBOW_MM, y_elbow)
    fold_hem_mid = Point(0.0, y_front)
    fold_dir = unit_vector(fold_elbow.x - fan.x, fold_elbow.y - fan.y)
    fold_perp = (fold_dir[1], -fold_dir[0])          # toward the under sleeve
    on_biceps = Point(fan.x + fold_dir[0] * (y_biceps - fan.y) / fold_dir[1], y_biceps)
    fst = Point(on_biceps.x - fold_perp[0] * FRONT_SEAM_OFFSET_MM,
                on_biceps.y - fold_perp[1] * FRONT_SEAM_OFFSET_MM)
    ust = Point(on_biceps.x + fold_perp[0] * FRONT_SEAM_OFFSET_MM,
                on_biceps.y + fold_perp[1] * FRONT_SEAM_OFFSET_MM)
    fold_elbow_front = _offset_corner(fan, fold_elbow, fold_hem_mid, -FRONT_SEAM_OFFSET_MM)
    elbow_front = _offset_corner(fan, fold_elbow, fold_hem_mid, FRONT_SEAM_OFFSET_MM)
    fold_hem = Point(-FRONT_SEAM_OFFSET_MM, y_front)
    hem_front = Point(FRONT_SEAM_OFFSET_MM, y_front)

    # 6. hem corner and back fold: 1/2 Sh diagonally from the front to the back
    # sleeve length, back fold at the elbow 1/2 Sh + 3.5 cm right of the front.
    b_hem = Point(((sh / 2) ** 2 - (y_back - y_front) ** 2) ** 0.5, y_back)
    f_b = Point(fold_elbow.x + sh / 2 + BACK_FOLD_ADD_MM, y_elbow)
    back_fold_dir = unit_vector(b_hem.x - f_b.x, b_hem.y - f_b.y)
    merge_back = Point(
        f_b.x + back_fold_dir[0] * BACK_MERGE_BELOW_ELBOW_MM / back_fold_dir[1],
        y_elbow + BACK_MERGE_BELOW_ELBOW_MM)

    # 7. upper sleeve cap: hollow up to FAN, straight along the M1 guide to M2,
    # over Sp and down through Q to U22.
    g1_dir = unit_vector(m1.x - fan.x, m1.y - fan.y)
    chord = distance(fst, fan)
    cap_front = cubic_with_tangents(
        fst, fan, _rot(fold_perp, CAP_FRONT_START_DEG), g1_dir,
        alpha=CAP_FRONT_ALPHA * chord, beta=CAP_FRONT_BETA * chord, n=24)
    chord = distance(m2, sp)
    cap_top = cubic_with_tangents(
        m2, sp, g1_dir, (1.0, 0.0),
        alpha=CAP_TOP_ALPHA * chord, beta=CAP_TOP_BETA * chord, n=32)
    chord = distance(sp, q_pt)
    cap_back = cubic_with_tangents(
        sp, q_pt, (1.0, 0.0), unit_vector(u22.x - q_pt.x, u22.y - q_pt.y),
        alpha=CAP_BACK_ALPHA * chord, beta=CAP_BACK_BETA * chord, n=32)
    cap_upper = [fan, m2] + cap_top[1:] + cap_back[1:] + [u22]

    # 8. under sleeve cap: grazes the biceps line, then follows the Q -> T guide
    chord = distance(ust, u2)
    cap_under = cubic_with_tangents(
        ust, u2, _rot(fold_perp, UNDER_CAP_START_DEG),
        unit_vector(q_pt.x - t_pt.x, q_pt.y - t_pt.y),
        alpha=UNDER_CAP_ALPHA * chord, beta=UNDER_CAP_BETA * chord, n=40)

    # 9. back seams: both squared down off the cap, bellied out, then running
    # into the back fold - the upper at the elbow, the under 9 cm below it.
    chord = distance(u22, f_b)
    back_upper = cubic_with_tangents(
        u22, f_b, (0.0, 1.0), back_fold_dir,
        alpha=UPPER_BACK_ALPHA * chord, beta=UPPER_BACK_BETA * chord, n=40)
    chord = distance(u2, merge_back)
    back_under = cubic_with_tangents(
        u2, merge_back, (0.0, 1.0), back_fold_dir,
        alpha=UNDER_BACK_ALPHA * chord, beta=UNDER_BACK_BETA * chord, n=40)

    upper = [
        ("cap_front", cap_front),                    # FST -> FAN
        ("cap", cap_upper),                          # FAN -> U22
        ("back_seam", back_upper),                   # U22 -> F_b
        ("back_fold", [f_b, b_hem]),
        ("hem", [b_hem, fold_hem]),
        ("front_seam", [fold_hem, fold_elbow_front, fst]),
    ]
    under = [
        ("cap", cap_under),                          # UST -> U2
        ("back_seam", back_under),                   # U2 -> merge_back
        ("back_fold", [merge_back, b_hem]),
        ("hem", [b_hem, hem_front]),
        ("front_seam", [hem_front, elbow_front, ust]),
    ]
    landmarks = {
        "A": a_pt, "E": e_pt, "Sp": sp, "M1": m1, "M2": m2, "FAN": fan,
        "Q": q_pt, "T": t_pt, "U2": u2, "U22": u22, "FST": fst, "UST": ust,
        "fold_elbow": fold_elbow, "fold_elbow_front": fold_elbow_front,
        "elbow_front": elbow_front, "fold_hem": fold_hem, "hem_front": hem_front,
        "F_b": f_b, "B_hem": b_hem, "merge_back": merge_back,
    }
    construction_lines = [
        [a_pt, Point(0.0, y_back)],                              # sleeve vertical
        [a_pt, e_pt],                                            # original line
        [Point(0.0, y_biceps), Point(e_pt.x, y_biceps)],         # biceps line
        [Point(0.0, y_elbow), Point(f_b.x, y_elbow)],            # elbow line
        [fold_hem, hem_front],                                   # front sleeve length
        [fan, e_pt],                                             # sleeve cap width diagonal
        [m1, fan],                                               # G1
        [m2, sp],                                                # G2
        [third1, q_pt],                                          # G3
        [q_pt, t_pt],                                            # low cap guideline
        [e_pt, q_pt],                                            # 1/4 scye width down from E
        [fan, fold_elbow, fold_hem_mid],                         # front sleeve fold
        [f_b, b_hem],                                            # back sleeve fold
    ]

    cap_len = arc_length(cap_front) + arc_length(cap_upper) + arc_length(cap_under)
    report = {
        "sleeve_cap_height_mm": sch,                 # Sch
        "sleeve_cap_width_mm": scw,                  # Scw
        "armhole_height_mm": ah,                     # Ah, transferred from the body
        "armhole_circ_mm": ac,                       # Ac, transferred from the body
        "levels_y_mm": {"biceps": y_biceps, "elbow": y_elbow,
                        "front_hem": y_front, "back_hem": y_back},
        "cap_len_mm": cap_len,
        # The booklet asks for 4 - 6 %; its own size-50 drawing sits at 2.8 %,
        # so the block only reports the figure - Design 4041 normalises it (D17).
        "cap_ease_mm": cap_len - ac,
        "cap_ease_pct": 100.0 * (cap_len - ac) / ac,
        "back_seam_upper_mm": arc_length(back_upper) + distance(f_b, b_hem),
        "back_seam_under_mm": arc_length(back_under) + distance(merge_back, b_hem),
        "front_seam_upper_mm": arc_length([fold_hem, fold_elbow_front, fst]),
        "front_seam_under_mm": arc_length([hem_front, elbow_front, ust]),
        "hem_len_mm": distance(b_hem, fold_hem) + distance(b_hem, hem_front),
    }
    # The sleeve is set in matching FAN to the front armhole notch and Sp to the
    # shoulder point; both marks travel on the upper sleeve.
    notches = {"FAN": fan, "Sp": sp}
    return JacketSleeveDraft(landmarks=landmarks, upper=upper, under=under,
                             construction_lines=construction_lines,
                             notches=notches, report=report)
