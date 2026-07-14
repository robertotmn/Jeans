"""Design 3069 accessory pieces (M&S pages 4-5) plus derived sewing pieces.

Book-drafted pieces: yoke (darts closed by rotation), waistband, back patch
pocket, front pocket bag/facing and the pocket-opening/topstitch marks.
Derived pieces the booklet does NOT draft (approximate, standard 5-pocket
construction): zip fly facing and shield, coin pocket, belt-loop strip.

Placement numbers for the pockets and the waistband notches come from the
measured page-5 drawing (tests/data/ms_reference_size50.json) reconciled with
the printed quotes; see docs/superpowers/plans/2026-07-15-ms-jeans-draft.md.
"""
from dataclasses import dataclass, field
from math import atan2, cos, radians, sin

from .draft_ms import BackDraft, FrontDraft
from .geometry import (
    Point,
    arc_length,
    chain_outline,
    cubic_with_tangents,
    curve_through,
    distance,
    point_at_arc_length,
    smooth_polyline,
    unit_vector,
)
from .measurements import Measurements

WAISTBAND_HEIGHT_MM = 40.0
WAISTBAND_EXTENSION_MM = 40.0     # button underlap beyond c.f. (derived, not in book)
BELT_LOOP_WIDTH_MM = 12.0
POCKET_OPENING_FROM_SIDE_MM = 130.0   # start on the waist (drawn: 130, band notch agrees)
POCKET_OPENING_SIDE_DEPTH_MM = 80.0   # end on the outseam (printed quote "8")
POCKET_ENTRY_EXTENSION_MM = 6.0
FLY_TOPSTITCH_MM = 34.0
FLY_VENT_MM = 150.0


@dataclass
class PieceDraft:
    """A pattern piece as named edge chains, ready for assembly + allowances."""
    name: str
    edges: list[tuple[str, list[Point]]]
    construction_lines: list[list[Point]] = field(default_factory=list)
    labels: list[tuple[Point, str]] = field(default_factory=list)
    report: dict = field(default_factory=dict)

    def outline(self) -> list[Point]:
        return chain_outline(self.edges)


def _rotate(p: Point, center: Point, ang_rad: float) -> Point:
    c, s = cos(ang_rad), sin(ang_rad)
    dx, dy = p.x - center.x, p.y - center.y
    return Point(center.x + dx * c - dy * s, center.y + dx * s + dy * c)


def _rot_dir(u: tuple[float, float], deg: float) -> tuple[float, float]:
    r = radians(deg)
    return (u[0] * cos(r) - u[1] * sin(r), u[0] * sin(r) + u[1] * cos(r))


# ---------------------------------------------------------------------------
# Yoke (carre): separate at the yoke line and close the darts (page 4 step 1)
# ---------------------------------------------------------------------------

def build_yoke(back: BackDraft) -> PieceDraft:
    d1, d2 = back.darts
    w_fin, cb_corner = back.waist_line
    yoke_out, yoke_cb = back.yoke_line

    # closing dart 1 rotates everything on its c.b. side about its tip so that
    # leg tip->b lands on tip->a (isosceles by construction)
    ang1 = atan2(d1.a.y - d1.tip.y, d1.a.x - d1.tip.x) - atan2(d1.b.y - d1.tip.y, d1.b.x - d1.tip.x)
    r1 = lambda p: _rotate(p, d1.tip, ang1)
    d2r_a, d2r_tip, d2r_b = r1(d2.a), r1(d2.tip), r1(d2.b)
    ang2 = atan2(d2r_a.y - d2r_tip.y, d2r_a.x - d2r_tip.x) - atan2(d2r_b.y - d2r_tip.y, d2r_b.x - d2r_tip.x)
    r21 = lambda p: _rotate(r1(p), d2r_tip, ang2)

    top = smooth_polyline([w_fin, d1.a, d2r_a, r21(cb_corner)], n_per_seg=8)
    bottom = smooth_polyline([yoke_out, d1.tip, d2r_tip, r21(yoke_cb)], n_per_seg=8)

    kinked_len = (distance(yoke_out, d1.tip) + distance(d1.tip, d2r_tip)
                  + distance(d2r_tip, r21(yoke_cb)))
    edges = [
        ("waist", top),
        ("cb", [r21(cb_corner), r21(yoke_cb)]),
        ("yoke_seam", bottom[::-1]),
        ("outseam", back.outseam_top[::-1]),   # yoke_out -> w_fin
    ]
    back_seam_len = distance(yoke_out, yoke_cb)
    mid = point_at_arc_length(bottom, arc_length(bottom) / 2)
    return PieceDraft(
        name="carre",
        edges=edges,
        labels=[(Point(mid.x, mid.y - 12), "CARRE x 2 (specchiato)")],
        report={
            "yoke_seam_len_mm": arc_length(bottom),
            "back_yoke_len_mm": back_seam_len,
            "kinked_len_mm": kinked_len,
        },
    )


# ---------------------------------------------------------------------------
# Waistband (page 5: exactly W/2 x 4 cm, notches and belt-loop marks)
# ---------------------------------------------------------------------------

def build_waistband(m: Measurements, front: FrontDraft) -> PieceDraft:
    h = WAISTBAND_HEIGHT_MM
    net_len = m.waistband_mm / 2
    x0 = -WAISTBAND_EXTENSION_MM
    front_waist = front.report["waist_len_mm"]
    ss = front_waist                                    # side-seam notch (drawn: = front waist)
    pocket = front_waist - POCKET_OPENING_FROM_SIDE_MM  # pocket-opening notch

    outline = [Point(x0, 0), Point(net_len, 0), Point(net_len, h), Point(x0, h)]
    ticks = []
    for x in (0.0, pocket, ss):
        ticks.append([Point(x, 0), Point(x, h)])
    for loop_start in (pocket - 10 - BELT_LOOP_WIDTH_MM, ss + 20):
        ticks.append([Point(loop_start, 0), Point(loop_start, h)])
        ticks.append([Point(loop_start + BELT_LOOP_WIDTH_MM, 0), Point(loop_start + BELT_LOOP_WIDTH_MM, h)])
    ticks.append([Point(net_len - BELT_LOOP_WIDTH_MM / 2, 0), Point(net_len - BELT_LOOP_WIDTH_MM / 2, h)])
    return PieceDraft(
        name="cinturino",
        edges=[("seam", outline + [outline[0]])],
        construction_lines=ticks,
        labels=[
            (Point(x0 + 5, h / 2), "bottone"),
            (Point(2, h + 8), "c.f."),
            (Point(pocket - 18, h / 2), "passante"),
            (Point(ss + 2, h + 8), "Ss"),
            (Point(net_len - 30, h + 8), "c.b."),
            (Point(net_len / 3, h / 2), "CINTURINO x 2"),
        ],
        report={"length_mm": net_len - x0, "net_len_mm": net_len,
                "pocket_notch_mm": pocket, "ss_notch_mm": ss},
    )


# ---------------------------------------------------------------------------
# Back patch pocket (page 5: 17 top / 18 centre, 6.5-7.5 bottom, 3 point)
# placed 4-5 cm below the yoke, point axis 1 cm outseam-side of the crease
# ---------------------------------------------------------------------------

def build_back_pocket(back: BackDraft) -> PieceDraft:
    yoke_out, yoke_cb = back.yoke_line
    crease_x = (back.landmarks["hem_out"].x + back.landmarks["hem_in"].x) / 2
    axis_x = crease_x - 10.0

    def yoke_y(x: float) -> float:
        t = (x - yoke_out.x) / (yoke_cb.x - yoke_out.x)
        return yoke_out.y + t * (yoke_cb.y - yoke_out.y)

    tr = Point(axis_x + 75.0, yoke_y(axis_x + 75.0) + 40.0)
    tl_anchor = Point(axis_x - 95.0, yoke_y(axis_x - 95.0) + 50.0)
    u = unit_vector(tl_anchor.x - tr.x, tl_anchor.y - tr.y)
    tl = Point(tr.x + u[0] * 170.0, tr.y + u[1] * 170.0)   # top edge exactly 17 cm
    t_axis = tl.y + (tr.y - tl.y) * (axis_x - tl.x) / (tr.x - tl.x)
    point = Point(axis_x, t_axis + 180.0)
    bl = Point(axis_x - 65.0, point.y - 30.0)
    br = Point(axis_x + 75.0, point.y - 30.0)

    edges = [
        ("hem", [tl, tr]),                       # top edge: folded hem
        ("seam", [tr, br, point, bl, tl]),
    ]
    # decorative "seagull" double topstitch across the pocket
    deco = []
    for dy in (0.0, 6.0):
        mid_y = (tl.y + bl.y) / 2 + dy
        deco.append([Point(tl.x + 8, mid_y), Point(axis_x, mid_y + 14), Point(tr.x - 8, mid_y - 4)])
    return PieceDraft(
        name="tasca_posteriore",
        edges=edges,
        construction_lines=deco,
        labels=[(Point(axis_x - 30, t_axis + 90), "TASCA POST. x 2")],
        report={"top_mm": distance(tl, tr),
                "centre_len_mm": distance(Point((tl.x + tr.x) / 2, (tl.y + tr.y) / 2), point)},
    )


# ---------------------------------------------------------------------------
# Front pocket: opening curve, bag (sacchetto) and facing (paramontura)
# ---------------------------------------------------------------------------

def pocket_opening_curve(front: FrontDraft) -> list[Point]:
    """Scoop from the waist to the side seam (+6 mm entry extension).
    Shape calibrated on the page-5 drawing (cubic, 2.6 mm max deviation)."""
    waist = front.edge("waist")
    start = point_at_arc_length(waist, POCKET_OPENING_FROM_SIDE_MM)
    from_top = front.edge("outseam")[::-1]      # waist corner -> knee
    e0 = point_at_arc_length(from_top, POCKET_OPENING_SIDE_DEPTH_MM)
    seg = _dir_at_arc(from_top, POCKET_OPENING_SIDE_DEPTH_MM)
    nx, ny = seg[1], -seg[0]
    if nx > 0:
        nx, ny = -nx, -ny                        # outward = away from the piece
    end = Point(e0.x + nx * POCKET_ENTRY_EXTENSION_MM, e0.y + ny * POCKET_ENTRY_EXTENSION_MM)
    chord = distance(start, end)
    cd = unit_vector(end.x - start.x, end.y - start.y)
    return cubic_with_tangents(start, end, _rot_dir(cd, -70.0), _rot_dir(cd, 30.0),
                               alpha=0.5 * chord, beta=0.5 * chord, n=32)


def build_front_pocket_bag(m: Measurements, front: FrontDraft) -> PieceDraft:
    """Pocket bag: hangs from the waist and side seam, ~24 cm deep, c.f.-side
    edge 1.5 cm past the crease (page 5 drawing)."""
    waist = front.edge("waist")
    crease_x = front.report["crease_x_mm"]
    left_x = crease_x - 15.0
    top_left = _point_at_x(waist, left_x)
    waist_slice = [top_left] + [p for p in waist if p.x < left_x][::-1]  # top_left -> waist_out
    bottom_y = top_left.y + 240.0

    from_top = front.edge("outseam")[::-1]
    side_depth = bottom_y - 60.0 - waist[0].y
    side_end = point_at_arc_length(from_top, side_depth)
    side_slice = [p for p in from_top if p.y < side_end.y] + [side_end]

    bl = Point(left_x, bottom_y)
    bottom = curve_through(side_end, Point((side_end.x + bl.x) / 2, bottom_y + 15), bl, n=20)
    edges = [
        ("waist", waist_slice),
        ("side", side_slice),
        ("bottom", bottom),
        ("cf_edge", [bl, top_left]),
    ]
    return PieceDraft(
        name="sacchetto_tasca",
        edges=edges,
        labels=[(Point(left_x + 25, top_left.y + 120), "SACCHETTO x 2")],
        report={"depth_mm": bottom_y - top_left.y},
    )


def build_front_pocket_facing(m: Measurements, front: FrontDraft) -> PieceDraft:
    """Facing behind the pocket opening: bounded by the opening curve, a 45 mm
    strip of waist and side seam, and a straight free inner edge (the inner
    edge is overlocked, its exact shape is unconstrained)."""
    opening = pocket_opening_curve(front)
    waist = front.edge("waist")
    from_top = front.edge("outseam")[::-1]
    s2 = point_at_arc_length(waist, POCKET_OPENING_FROM_SIDE_MM + 45.0)
    e2 = point_at_arc_length(from_top, POCKET_OPENING_SIDE_DEPTH_MM + 45.0)
    # inner edge: the opening shifted 45 mm straight down (cannot cross the
    # opening by construction), clipped clear of the e2/s2 connectors
    shifted = [Point(p.x, p.y + 45.0) for p in opening
               if e2.x + 5.0 < p.x < s2.x - 5.0]
    edges = [
        ("waist", [s2, opening[0]]),
        ("opening", opening),
        ("side", [opening[-1], e2]),
        ("inner", [e2] + shifted[::-1] + [s2]),
    ]
    return PieceDraft(
        name="paramontura_tasca",
        edges=edges,
        labels=[(Point((s2.x + e2.x) / 2, (s2.y + e2.y) / 2), "PARAM. TASCA x 2")],
    )


def front_design_marks(front: FrontDraft) -> list[list[Point]]:
    """Marks drawn ON the front piece: pocket opening, fly topstitch (3.4 cm,
    vent 15 cm), per page 5."""
    marks = [pocket_opening_curve(front)]
    cf = front.edge("cf_crotch")
    stitch = []
    for k in range(len(cf) - 1):
        walked = arc_length(cf[:k + 1])
        if walked > FLY_VENT_MM + 10:
            break
        u = unit_vector(cf[k + 1].x - cf[k].x, cf[k + 1].y - cf[k].y)
        # offset 3.4 cm inside the piece (toward the crease), J-closing at the bottom
        stitch.append(Point(cf[k].x - u[1] * FLY_TOPSTITCH_MM, cf[k].y + u[0] * FLY_TOPSTITCH_MM))
    stitch.append(point_at_arc_length(cf, FLY_VENT_MM + 10 + FLY_TOPSTITCH_MM))
    marks.append(stitch)
    return marks


# ---------------------------------------------------------------------------
# Derived pieces (not drafted in the booklet, standard 5-pocket construction)
# ---------------------------------------------------------------------------

def build_fly_facing() -> PieceDraft:
    w, length = FLY_TOPSTITCH_MM + 6.0, FLY_VENT_MM + 20.0
    body = [Point(0, 0), Point(w, 0), Point(w, length - 35)]
    curve = curve_through(Point(w, length - 35), Point(w - 4, length - 6), Point(10, length), n=12)
    outline = body + curve[1:] + [Point(0, length)]
    return PieceDraft(
        name="paramontura_patta",
        edges=[("seam", outline + [outline[0]])],
        labels=[(Point(4, length / 2), "PATTA x 1")],
    )


def build_fly_shield() -> PieceDraft:
    w, length = 50.0, FLY_VENT_MM + 30.0
    body = [Point(0, 0), Point(w, 0), Point(w, length - 35)]
    curve = curve_through(Point(w, length - 35), Point(w - 4, length - 6), Point(12, length), n=12)
    outline = body + curve[1:] + [Point(0, length)]
    return PieceDraft(
        name="scudo_patta",
        edges=[("seam", outline + [outline[0]])],
        construction_lines=[[Point(0, 0), Point(0, length)]],
        labels=[(Point(4, length / 2), "SCUDO x 1 (doppio, piega sul lato)")],
    )


def build_coin_pocket() -> PieceDraft:
    w, body, hem_fold = 95.0, 105.0, 25.0
    total = body + hem_fold
    outline = [Point(0, 0), Point(w, 0), Point(w, total - 12),
               Point(w - 12, total), Point(12, total), Point(0, total - 12)]
    return PieceDraft(
        name="taschino",
        edges=[("seam", outline + [outline[0]])],
        construction_lines=[[Point(0, hem_fold), Point(w, hem_fold)]],
        labels=[(Point(10, 60), "TASCHINO x 1")],
    )


def build_belt_loop_strip() -> PieceDraft:
    loop_len, n = 95.0, 5
    w = 32.0
    outline = [Point(0, 0), Point(loop_len * n, 0), Point(loop_len * n, w), Point(0, w)]
    cuts = [[Point(loop_len * i, 0), Point(loop_len * i, w)] for i in range(1, n)]
    return PieceDraft(
        name="passanti",
        edges=[("seam", outline + [outline[0]])],
        construction_lines=cuts,
        labels=[(Point(10, w / 2), f"PASSANTI x 1 ({n} pezzi da {loop_len:.0f} mm)")],
    )


# ---------------------------------------------------------------------------

def _dir_at_arc(pts: list[Point], s: float) -> tuple[float, float]:
    walked = 0.0
    for p, q in zip(pts, pts[1:]):
        seg = distance(p, q)
        if walked + seg >= s:
            return unit_vector(q.x - p.x, q.y - p.y)
        walked += seg
    p, q = pts[-2], pts[-1]
    return unit_vector(q.x - p.x, q.y - p.y)


def _point_at_x(pts: list[Point], x: float) -> Point:
    for p, q in zip(pts, pts[1:]):
        if (p.x - x) * (q.x - x) <= 0 and abs(q.x - p.x) > 1e-12:
            t = (x - p.x) / (q.x - p.x)
            return Point(x, p.y + t * (q.y - p.y))
    raise ValueError(f"polyline does not cross x={x}")
