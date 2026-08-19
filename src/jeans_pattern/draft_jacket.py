"""M. Mueller & Sohn "Jeans-Basics" drafting: Basic Denim Jacket Block, body
(pages 11-12).

Coordinate frame (mm): origin = back neck point N; y grows downward, so the
chest line is y = Sd, the waist line y = Bwl and the hem line y = Lg. x grows
from the centre back TOWARD THE FRONT: every "measure ... to the left" of the
booklet is +x here. Back and front share one frame exactly as the booklet
draws them, the front side seam sitting BODY_GAP_MM to the right of the back
one, so the generated draft overlays the scale drawing 1:1.

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
