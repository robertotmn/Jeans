"""M. Mueller & Sohn "Jeans-Basics" drafting: Design 4041, the Classic Denim
Jacket worked out of the basic block (pages 14-15).

The body keeps the block frame of `draft_jacket` (mm, origin at the back neck
point N, y down, x from the centre back toward the front), so the design
outlines and the pieces cut out of them - yokes, centre and side panels -
overlay the page-14 drawing 1:1. The free pieces (collar, waistband, cuff,
flap, welt, bags, tab) have a local frame of their own, like the jeans
accessory pieces. The collar frame is the one the booklet draws: x = 0 at the
c.f., x toward the c.b. fold, y = 0 on the baseline and y UP.

Edge names drive the seam allowances (`SeamAllowances.for_edges`): edges that
fall on a fold are named `fold_*` and get no allowance, and no edge is called
`hem` - the body hem is sewn to the waistband and the sleeve hem to the cuff,
so both take the plain seam allowance (D27).

Every amount below is quoted by the booklet unless marked as calibrated; the
calibrated ones were fitted against the page-14/15 vectors in
tests/data/ms_jacket_reference_size50.json.
"""
from dataclasses import dataclass
from math import asin, cos, degrees, radians, sin

from shapely.geometry import LineString, Polygon

from .draft_jacket import (
    FRONT_HEM_CTRL, JacketBackDraft, JacketFrontDraft, JacketSleeveDraft)
from .draft_ms_extras import PieceDraft
from .geometry import (
    Point,
    arc_length,
    chain_outline,
    cubic_with_tangents,
    distance,
    horizontal_line_through,
    line_intersection,
    point_along,
    point_at_arc_length,
    smooth_polyline,
    unit_vector,
)

# ---- body design amounts quoted by the booklet (page 14) ------------------
WAISTBAND_HEIGHT_MM = 45.0        # "shorten the hem 4.5 cm for the waistband"
NECK_LOWER_CB_MM = 5.0            # "lower the neckline 0.5 cm at the centre back"
NECK_LOWER_SHOULDER_MM = 10.0     # "1 cm at the shoulder"
NECK_LOWER_CF_MM = 15.0           # "1.5 cm at the centre front"
BACK_YOKE_DOWN_MM = 130.0         # "measure 13 cm downward along the centre back"
BACK_PANEL_FROM_ARMHOLE_MM = 35.0  # "mark the back panel seam 3.5 cm away from the armhole"
BACK_PANEL_AT_HEM_MM = 20.0       # hem split 1/2 - 2 cm on the side, 1/2 + 2 at the c.b.
OVERLAP_MM = 20.0                 # "add 2 cm overlap parallel to the centre front"
PLACKET_TOPSTITCH_MM = 45.0       # "4.5 cm parallel to the front edge"
PINTUCK_INNER_MM = 10.0           # tuck lines 1 and 2 cm off the placket topstitch
PINTUCK_OUTER_MM = 20.0
PINTUCK_SPREAD_MM = 20.0          # a 1 cm tuck eats 2 cm of cloth, slashed in (D18)
BUTTONHOLE_BELOW_NECK_MM = 20.0   # "mark the upper buttonhole 2 cm below the neckline"
FRONT_YOKE_ABOVE_BH2_MM = 40.0    # "mark the front yoke 4 cm above the second buttonhole"
FLAP_FROM_PINTUCK_MM = 10.0       # "position for the pocket flap 1 cm away from the pintuck"
FLAP_WIDTH_MM = 130.0
FLAP_SIDE_MM = 40.0
FLAP_POINT_MM = 60.0
FLAP_BUTTON_MM = 42.0             # button on the flap axis (drawn 4.2 below the yoke)
POCKET_OPENING_BELOW_YOKE_MM = 10.0
POCKET_OPENING_WIDTH_MM = 120.0
POCKET_WELT_MM = 10.0
POCKET_BAG_SIDE_MM = 120.0        # bag sides 12 cm below the entry
POCKET_BAG_POINT_MM = 140.0       # bag point 14 cm below the entry
FRONT_PANEL_AT_OPENING_MM = 45.0  # panel seams +/- 4.5 cm off the entry midpoint
FRONT_PANEL_AT_HEM_MM = 25.0      # and +/- 2.5 cm off the pocket axis at the hem
SIDE_POCKET_LEN_MM = 160.0
SIDE_POCKET_WELT_MM = 15.0
SIDE_POCKET_ABOVE_HEM_MM = 35.0
SIDE_POCKET_TOP_FROM_PITCH_MM = 15.0
TAB_LEN_MM = 80.0
TAB_HEIGHT_MM = 35.0
TAB_BUTTONS_MM = (65.0, 95.0)     # from the side-seam notch, 3 cm apart
TAB_BUTTONHOLE_FROM_END_MM = 15.0
TAB_BUTTONHOLE_LEN_MM = 25.0
BUTTON_MARK_R_MM = 5.0

# The drawn buttonhole is a 2.2 cm slot whose rounded end sits 0.55 cm past the
# c.f. toward the front edge - on the fronts and on the waistband alike - while
# the button itself is marked on the c.f. (D21/D22, both measured off the page).
BUTTONHOLE_LEN_MM = 22.0
BUTTONHOLE_PAST_CF_MM = 5.5

# The booklet draws the yoke and the panel seams off the buttonhole spacing,
# which assumes a chest wide enough for the pocket to fit between the placket
# and the armhole. On a big waist over a narrow chest it stops fitting: these
# two clamps keep the front panels constructible and put a warning in the
# report, the way the jeans draft degrades on out-of-proportion measurements.
FRONT_YOKE_MARGIN_MM = 20.0      # the yoke line stays this far inside the armhole
FRONT_PANEL_MIN_WIDTH_MM = 5.0   # and the side panel this wide at the yoke (the
                                 # book's own sizes 44-62 keep 20 to 72 mm there)

# ---- collar amounts quoted by the booklet (page 14, step 2) ---------------
COLLAR_CF_SEAM_MM = 10.0          # "measure 1 cm upward at the centre front"
COLLAR_CB_SEAM_MM = 15.0          # "1.5 cm ... for the roll of the collar stand"
COLLAR_STAND_MM = 30.0            # "and 3 cm for the collar stand"
COLLAR_WIDTH_MM = 50.0            # "5 cm for the collar width upward at the centre back"
COLLAR_CF_WIDTH_MM = 75.0         # "7.5 cm upward at the centre front"
COLLAR_POINT_EXT_MM = 25.0        # "extend the collar point 2.5 cm to the left"
COLLAR_TOUCH_FRACTION = 1.0 / 3.0  # the neck seam touches the baseline at 1/3
COLLAR_TOL_MM = 2.5               # "verify the collar length and adjust ... if necessary"

# ---- sleeve design amounts quoted by the booklet (page 15) ----------------
CUFF_HEIGHT_MM = 45.0             # "shorten the sleeve pattern around the cuff width"
SLEEVE_VENT_MM = 90.0             # "mark the slit 9 cm long"
CUFF_MARK_INSET_MM = 15.0         # button and buttonhole 1.5 cm from the ends
CAP_EASE_TOL_MM = 1.0             # "without any ease for the denim construction"
CAP_EASE_CLAMP_MM = 25.0          # never slash more than this in total
CAP_EASE_MAX_ITER = 10

# ---- calibrated curve-shape constants (size-50 drawing fit) ---------------
# lowered back neckline: cubic leaving the new c.b. neck point square to the
# c.b. seam and arriving at the lowered shoulder point along the tangent of the
# block neckline (the fit asked for no extra rotation there). Fit: 0.5 mm.
BACK_NECK_ALPHA, BACK_NECK_BETA = 0.300, 0.400
# lowered front neckline: cubic leaving the lowered shoulder point along the
# block neckline tangent and arriving square to the straightened c.f. Fit: 1.2 mm,
# of which ~1.1 mm is the slop the front block already carries.
FRONT_NECK_CTRL = 0.405
# collar neck seam: two cubics, down to the baseline at 1/3 of it and back up to
# the c.b., horizontal where they touch the baseline and the c.b. Fit: 0.5 mm.
COLLAR_SEAM_START_DEG = -14.4
COLLAR_SEAM_FRONT_ALPHA, COLLAR_SEAM_FRONT_BETA = 0.086, 0.500
COLLAR_SEAM_BACK_ALPHA, COLLAR_SEAM_BACK_BETA = 0.213, 0.485
# collar outer edge and roll line: cubics arriving horizontal at the c.b. fold.
# Fit: 0.4 mm and 0.2 mm.
COLLAR_OUTER_START_DEG = 6.9
COLLAR_OUTER_ALPHA, COLLAR_OUTER_BETA = 0.439, 0.461
COLLAR_ROLL_START_DEG = 15.1
COLLAR_ROLL_ALPHA, COLLAR_ROLL_BETA = 0.328, 0.383


# ---------------------------------------------------------------------------
# Small geometric helpers used all over the design step
# ---------------------------------------------------------------------------

def _dir(deg: float) -> tuple[float, float]:
    return (cos(radians(deg)), sin(radians(deg)))


def _dist_to_seg(p: Point, a: Point, b: Point) -> float:
    vx, vy = b.x - a.x, b.y - a.y
    l2 = vx * vx + vy * vy
    if l2 < 1e-12:
        return distance(p, a)
    t = max(0.0, min(1.0, ((p.x - a.x) * vx + (p.y - a.y) * vy) / l2))
    return distance(p, Point(a.x + t * vx, a.y + t * vy))


def _cut(pts: list[Point], p: Point) -> tuple[list[Point], list[Point]]:
    """Split a polyline at a point lying on it; both halves end/start at p."""
    i = min(range(len(pts) - 1), key=lambda k: _dist_to_seg(p, pts[k], pts[k + 1]))
    return pts[:i + 1] + [p], [p] + pts[i + 1:]


def _cross(pts: list[Point], a: Point, b: Point) -> Point:
    """First point where a polyline crosses the infinite line through a and b."""
    for p, q in zip(pts, pts[1:]):
        s1 = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)
        s2 = (b.x - a.x) * (q.y - a.y) - (b.y - a.y) * (q.x - a.x)
        if s1 * s2 <= 0 and abs(s1 - s2) > 1e-12:
            return line_intersection(a, b, p, q)
    raise ValueError("polyline does not cross the line")


def _at_y(pts: list[Point], y: float) -> Point:
    return _cross(pts, *horizontal_line_through(y))


def _at_x(pts: list[Point], x: float) -> Point:
    return _cross(pts, Point(x, -10000.0), Point(x, 10000.0))


def _rotate(p: Point, centre: Point, ang: float) -> Point:
    c, s = cos(ang), sin(ang)
    dx, dy = p.x - centre.x, p.y - centre.y
    return Point(centre.x + dx * c - dy * s, centre.y + dx * s + dy * c)


def _drop_arc(pts: list[Point], s: float) -> list[Point]:
    """Polyline with its first `s` of arc length removed (s <= 0: unchanged)."""
    if s <= 0.0:
        return list(pts)
    walked = 0.0
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        walked += distance(p, q)
        if walked >= s:
            return [point_at_arc_length(pts, s)] + pts[i + 1:]
    raise ValueError("cannot drop more than the whole polyline")


def _segment(base: Point, u: tuple[float, float], d0: float, d1: float) -> list[Point]:
    """Segment through `base` along the direction u, from d0 to d1 (grainlines)."""
    return [Point(base.x + u[0] * d, base.y + u[1] * d) for d in (d0, d1)]


def _notch(p: Point, direction: tuple[float, float], length: float = 10.0) -> list[Point]:
    return [p, Point(p.x + direction[0] * length, p.y + direction[1] * length)]


def _button(p: Point) -> list[list[Point]]:
    """Button mark: a small circle with a cross through it."""
    r = BUTTON_MARK_R_MM
    circle = [Point(p.x + r * cos(radians(a)), p.y + r * sin(radians(a)))
              for a in range(0, 361, 30)]
    return [circle, [Point(p.x - r, p.y), Point(p.x + r, p.y)],
            [Point(p.x, p.y - r), Point(p.x, p.y + r)]]


def _slot(a: Point, b: Point, width: float = 3.0) -> list[Point]:
    """Buttonhole mark: the slot outline from a to b, rounded at the a end."""
    u = unit_vector(b.x - a.x, b.y - a.y)
    n = (u[1] * width / 2, -u[0] * width / 2)
    cap = [Point(a.x + n[0] * cos(radians(t)) - u[0] * width / 2 * sin(radians(t)),
                 a.y + n[1] * cos(radians(t)) - u[1] * width / 2 * sin(radians(t)))
           for t in range(0, 181, 30)]
    return ([Point(b.x + n[0], b.y + n[1])] + cap
            + [Point(b.x - n[0], b.y - n[1]), Point(b.x + n[0], b.y + n[1])])


def _clip(marks: list[list[Point]], outline: list[Point]) -> list[list[Point]]:
    """The portions of each mark that fall inside the piece (D20)."""
    poly = Polygon([(p.x, p.y) for p in outline]).buffer(0)
    out = []
    for mark in marks:
        clipped = LineString([(p.x, p.y) for p in mark]).intersection(poly)
        for geom in getattr(clipped, "geoms", [clipped]):
            coords = list(getattr(geom, "coords", []))
            if len(coords) >= 2:
                out.append([Point(x, y) for x, y in coords])
    return out


def _spread(pts: list[Point], a: Point, b: Point,
            delta: tuple[float, float]) -> list[Point]:
    """Slash a polyline along the line a-b and move its left side by `delta`.

    A closed chain crossing the slash twice gains the two lips of the cut, so
    the piece opens up by |delta| and stays closed (D18).
    """
    def side(p: Point) -> float:
        return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)

    def moved(p: Point) -> Point:
        return Point(p.x + delta[0], p.y + delta[1])

    out = [moved(pts[0]) if side(pts[0]) > 0 else pts[0]]
    for p, q in zip(pts, pts[1:]):
        if side(p) * side(q) < 0:
            c = line_intersection(a, b, p, q)
            out += [moved(c), c] if side(p) > 0 else [c, moved(c)]
        out.append(moved(q) if side(q) > 0 else q)
    return out


# ---------------------------------------------------------------------------
# Step 1 (page 14): the design body
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DesignBody:
    """Design 4041 body: the two design outlines plus everything drawn on them.

    back/front: closed edge chains in the block frame. `lines` holds the
    internal design lines (yoke, panel seams, c.f., placket, pintucks, pocket
    marks), `landmarks` the points the piece builders cut on.
    """
    back: list[tuple[str, list[Point]]]
    front: list[tuple[str, list[Point]]]
    landmarks: dict[str, Point]
    lines: dict[str, list[Point]]
    report: dict

    def edge(self, part: str, name: str) -> list[Point]:
        if part not in ("back", "front"):
            raise KeyError(part)
        for n, pts in (self.back if part == "back" else self.front):
            if n == name:
                return pts
        raise KeyError(name)


def design_body(back: JacketBackDraft, front: JacketFrontDraft) -> DesignBody:
    """Reshape the block into the Design 4041 body (page 14, step 1)."""
    lm, fm = back.landmarks, front.landmarks

    # ---- back: hem up 4.5, neckline lowered, yoke and panel seam -----------
    n_pt, k_pt = lm["N"], lm["K"]
    cb_dir = unit_vector(k_pt.x - n_pt.x, k_pt.y - n_pt.y)
    cb_perp = (cb_dir[1], -cb_dir[0])              # square to the c.b., toward the front

    def along_cb(p: Point, d: float) -> Point:
        return Point(p.x + cb_dir[0] * d, p.y + cb_dir[1] * d)

    neck_cb = along_cb(n_pt, NECK_LOWER_CB_MM)
    hem_cb = along_cb(k_pt, -WAISTBAND_HEIGHT_MM)
    side_hem_b = along_cb(lm["H_b"], -WAISTBAND_HEIGHT_MM)
    neck_sh_b = point_along(lm["HSP_b"], lm["SP_b"], NECK_LOWER_SHOULDER_MM)

    blk_neck = back.edge("neck")
    tan_b = unit_vector(blk_neck[-1].x - blk_neck[-2].x, blk_neck[-1].y - blk_neck[-2].y)
    chord = distance(neck_cb, neck_sh_b)
    neck_b = cubic_with_tangents(neck_cb, neck_sh_b, cb_perp, tan_b,
                                 alpha=BACK_NECK_ALPHA * chord,
                                 beta=BACK_NECK_BETA * chord, n=40)

    armhole_b = back.edge("armhole")
    yoke_cb = along_cb(neck_cb, BACK_YOKE_DOWN_MM)
    yoke_ah_b = _cross(armhole_b, yoke_cb,
                       Point(yoke_cb.x + cb_perp[0], yoke_cb.y + cb_perp[1]))
    panel_top_b = point_along(yoke_ah_b, yoke_cb, BACK_PANEL_FROM_ARMHOLE_MM)
    hem_len_b = distance(side_hem_b, hem_cb)
    panel_hem_b = point_along(side_hem_b, hem_cb, hem_len_b / 2 - BACK_PANEL_AT_HEM_MM)

    back_edges = [
        ("neck", neck_b),                                        # neck_cb -> neck_sh_b
        ("shoulder", [neck_sh_b, lm["SP_b"]]),
        ("armhole", armhole_b),                                  # SP_b -> U_b
        ("side", [lm["U_b"], lm["W_b"], side_hem_b]),
        ("waistband_seam", [side_hem_b, hem_cb]),
        ("fold_cb", [hem_cb, neck_cb]),
    ]

    # ---- front: hem up 4.5, neckline lowered, c.f. straightened, overlap ---
    c0, c1, c3 = fm["C0"], fm["C1"], fm["C3"]
    h_f, w_f = fm["H_f"], fm["W_f"]
    side_dir = unit_vector(h_f.x - w_f.x, h_f.y - w_f.y)
    side_hem_f = Point(h_f.x - side_dir[0] * WAISTBAND_HEIGHT_MM,
                       h_f.y - side_dir[1] * WAISTBAND_HEIGHT_MM)
    hem_cf = Point(c3.x, c3.y - WAISTBAND_HEIGHT_MM)
    neck_cf = point_along(c0, c1, NECK_LOWER_CF_MM)
    neck_sh_f = point_along(fm["HSP_f"], fm["SP_f"], NECK_LOWER_SHOULDER_MM)

    chord = distance(side_hem_f, hem_cf)           # the hem keeps the block shape
    hem_f = cubic_with_tangents(side_hem_f, hem_cf, (side_dir[1], -side_dir[0]), (1.0, 0.0),
                                alpha=FRONT_HEM_CTRL * chord,
                                beta=FRONT_HEM_CTRL * chord, n=32)

    cf_dir = unit_vector(hem_cf.x - neck_cf.x, hem_cf.y - neck_cf.y)
    cf_perp = (cf_dir[1], -cf_dir[0])              # square to the c.f., toward the edge

    def off_cf(p: Point, d: float) -> Point:
        return Point(p.x + cf_perp[0] * d, p.y + cf_perp[1] * d)

    edge_top, edge_hem = off_cf(neck_cf, OVERLAP_MM), off_cf(hem_cf, OVERLAP_MM)

    blk_neck_f = front.edge("neck")                                  # C0 -> HSP_f
    tan_f = unit_vector(blk_neck_f[-2].x - blk_neck_f[-1].x,
                        blk_neck_f[-2].y - blk_neck_f[-1].y)
    chord = distance(neck_sh_f, neck_cf)
    neck_f = cubic_with_tangents(neck_sh_f, neck_cf, tan_f, cf_perp,
                                 alpha=FRONT_NECK_CTRL * chord,
                                 beta=FRONT_NECK_CTRL * chord, n=48)

    front_edges = [
        ("neck_overlap", [edge_top, neck_cf]),
        ("neck", neck_f[::-1]),                                  # neck_cf -> neck_sh_f
        ("shoulder", [neck_sh_f, fm["SP_f"]]),
        ("armhole", front.edge("armhole")),                      # SP_f -> U_f
        ("side", [fm["U_f"], w_f, side_hem_f]),
        ("waistband_seam", hem_f + [edge_hem]),                  # side_hem_f -> edge_hem
        ("fold_edge", [edge_hem, edge_top]),
    ]

    # ---- front design lines: buttonholes, yoke, pintuck, pockets, panels ---
    x_placket = OVERLAP_MM - PLACKET_TOPSTITCH_MM      # signed offset from the c.f.
    bh1 = Point(neck_cf.x + cf_dir[0] * BUTTONHOLE_BELOW_NECK_MM,
                neck_cf.y + cf_dir[1] * BUTTONHOLE_BELOW_NECK_MM)
    bh5 = Point(hem_cf.x + cf_dir[0] * WAISTBAND_HEIGHT_MM / 2,
                hem_cf.y + cf_dir[1] * WAISTBAND_HEIGHT_MM / 2)
    buttons = [Point(bh1.x + (bh5.x - bh1.x) * i / 4, bh1.y + (bh5.y - bh1.y) * i / 4)
               for i in range(5)]

    armhole_f = front.edge("armhole")
    warnings = []
    y_yoke = buttons[1].y - FRONT_YOKE_ABOVE_BH2_MM
    y_lo = min(p.y for p in armhole_f) + FRONT_YOKE_MARGIN_MM
    y_hi = max(p.y for p in armhole_f) - FRONT_YOKE_MARGIN_MM
    if not y_lo <= y_yoke <= y_hi:
        clamped = min(max(y_yoke, y_lo), y_hi)
        warnings.append(
            f"carre davanti fuori dal giromanica: linea alzata/abbassata di "
            f"{abs(clamped - y_yoke) / 10:.1f} cm rispetto all'occhiello n. 2"
        )
        y_yoke = clamped
    yoke_ah_f = _at_y(armhole_f, y_yoke)
    yoke_edge_f = _at_y([edge_top, edge_hem], y_yoke)
    cf_at_yoke = _at_y([neck_cf, hem_cf], y_yoke)
    tuck_inner_top = off_cf(cf_at_yoke, x_placket - PINTUCK_INNER_MM)
    tuck_outer_top = off_cf(cf_at_yoke, x_placket - PINTUCK_OUTER_MM)

    x_flap_r = tuck_outer_top.x - FLAP_FROM_PINTUCK_MM
    x_axis = x_flap_r - FLAP_WIDTH_MM / 2
    y_open = y_yoke + POCKET_OPENING_BELOW_YOKE_MM
    x_open_l = x_axis - POCKET_OPENING_WIDTH_MM / 2
    x_open_r = x_axis + POCKET_OPENING_WIDTH_MM / 2

    def panel_seam(sign: float) -> list[Point]:
        """Panel seam: entry line to hem, extended up to the yoke line (D19)."""
        top = Point(x_axis + sign * FRONT_PANEL_AT_OPENING_MM, y_open)
        bottom = _at_x(hem_f, x_axis + sign * FRONT_PANEL_AT_HEM_MM)
        return [line_intersection(top, bottom, *horizontal_line_through(y_yoke)), bottom]

    seam_cf, seam_side = panel_seam(1.0), panel_seam(-1.0)
    # measured against the widest point of the armhole below the yoke, which is
    # where the side panel is narrowest; both seams move together so the pocket
    # keeps straddling them, as far as the centre front panel can give way
    x_armhole = max(p.x for p in armhole_f if p.y >= y_yoke)
    short = min(x_armhole + FRONT_PANEL_MIN_WIDTH_MM - seam_side[0].x,
                yoke_edge_f.x - FRONT_PANEL_MIN_WIDTH_MM - seam_cf[0].x)
    if short > 0.0:
        seam_cf, seam_side = ([Point(seam[0].x + short, seam[0].y),
                               _at_x(hem_f, seam[1].x + short)]
                              for seam in (seam_cf, seam_side))
        warnings.append(
            f"cuciture del pannello davanti spostate di {short / 10:.1f} cm verso "
            f"il c.f.: petto stretto rispetto alla vita"
        )

    welt_lo = Point(fm["P_top"].x, _at_x(hem_f, fm["P_top"].x).y - SIDE_POCKET_ABOVE_HEM_MM)
    dx = SIDE_POCKET_TOP_FROM_PITCH_MM
    welt_hi = Point(welt_lo.x + dx, welt_lo.y - (SIDE_POCKET_LEN_MM ** 2 - dx * dx) ** 0.5)
    welt_dir = unit_vector(welt_hi.x - welt_lo.x, welt_hi.y - welt_lo.y)
    welt_off = (-welt_dir[1] * SIDE_POCKET_WELT_MM, welt_dir[0] * SIDE_POCKET_WELT_MM)

    lines = {
        "cf": [neck_cf, hem_cf],
        "fold_edge": [edge_top, edge_hem],
        "placket": [off_cf(neck_cf, x_placket), off_cf(hem_cf, x_placket)],
        "pintuck_inner": [tuck_inner_top, off_cf(hem_cf, x_placket - PINTUCK_INNER_MM)],
        "pintuck_outer": [tuck_outer_top, off_cf(hem_cf, x_placket - PINTUCK_OUTER_MM)],
        "yoke_back": [yoke_ah_b, yoke_cb],
        "panel_back": [panel_top_b, panel_hem_b],
        "yoke_front": [yoke_ah_f, yoke_edge_f],
        "panel_cf": seam_cf,
        "panel_side": seam_side,
        "pocket_flap": [Point(x_flap_r - FLAP_WIDTH_MM, y_yoke),
                        Point(x_flap_r - FLAP_WIDTH_MM, y_yoke + FLAP_SIDE_MM),
                        Point(x_axis, y_yoke + FLAP_POINT_MM),
                        Point(x_flap_r, y_yoke + FLAP_SIDE_MM), Point(x_flap_r, y_yoke)],
        "pocket_opening": [Point(x_open_l, y_open), Point(x_open_r, y_open),
                           Point(x_open_r, y_open + POCKET_WELT_MM),
                           Point(x_open_l, y_open + POCKET_WELT_MM),
                           Point(x_open_l, y_open)],
        "pocket_bag": [Point(x_open_l, y_yoke),
                       Point(x_open_l, y_open + POCKET_BAG_SIDE_MM),
                       Point(x_axis, y_open + POCKET_BAG_POINT_MM),
                       Point(x_open_r, y_open + POCKET_BAG_SIDE_MM),
                       Point(x_open_r, y_yoke)],
        "pocket_axis": [Point(x_axis, y_yoke + FLAP_POINT_MM), _at_x(hem_f, x_axis)],
        "side_pocket_welt": [welt_lo, welt_hi,
                             Point(welt_hi.x + welt_off[0], welt_hi.y + welt_off[1]),
                             Point(welt_lo.x + welt_off[0], welt_lo.y + welt_off[1]),
                             welt_lo],
    }

    landmarks = {
        "neck_cb": neck_cb, "neck_shoulder_b": neck_sh_b, "hem_cb": hem_cb,
        "side_hem_b": side_hem_b, "yoke_cb": yoke_cb, "yoke_ah_b": yoke_ah_b,
        "panel_top_b": panel_top_b, "panel_hem_b": panel_hem_b, "BAN": lm["G1"],
        "neck_cf": neck_cf, "neck_shoulder_f": neck_sh_f, "edge_top": edge_top,
        "edge_hem": edge_hem, "hem_cf": hem_cf, "side_hem_f": side_hem_f,
        "yoke_ah_f": yoke_ah_f, "yoke_edge_f": yoke_edge_f,
        "panel_cf_top": seam_cf[0], "panel_cf_hem": seam_cf[1],
        "panel_side_top": seam_side[0], "panel_side_hem": seam_side[1],
        "FAN": _at_y(armhole_f, fm["FAN"].y),
        "flap_point": Point(x_axis, y_yoke + FLAP_POINT_MM),
        "flap_button": Point(x_axis, y_yoke + FLAP_BUTTON_MM),
        "welt_lo": welt_lo, "welt_hi": welt_hi,
    }
    for i, p in enumerate(buttons, start=1):
        landmarks[f"button{i}"] = p

    hem_len_f = arc_length(hem_f) + distance(hem_cf, edge_hem)
    report = {
        "neckline_mm": arc_length(neck_b) + arc_length(neck_f),   # half the lowered neckline
        "back_neck_mm": arc_length(neck_b),
        "front_neck_mm": arc_length(neck_f),
        "shoulder_back_mm": distance(neck_sh_b, lm["SP_b"]),
        "shoulder_front_mm": distance(neck_sh_f, fm["SP_f"]),
        "back_hem_mm": hem_len_b,
        "front_hem_mm": hem_len_f,
        "waistband_len_mm": hem_len_b + hem_len_f,
        "back_yoke_mm": distance(yoke_cb, yoke_ah_b),
        "front_yoke_mm": distance(yoke_edge_f, yoke_ah_f),
        "back_panel_mm": distance(panel_top_b, panel_hem_b),
        "armhole_circ_mm": front.report["armhole_circ_mm"],
        "buttonhole_pitch_mm": distance(buttons[0], buttons[4]) / 4,
        "panel_notch_mm": hem_len_b / 2 - BACK_PANEL_AT_HEM_MM,
        "warnings": warnings,
    }
    return DesignBody(back=back_edges, front=front_edges, landmarks=landmarks,
                      lines=lines, report=report)


# ---------------------------------------------------------------------------
# Back pieces: yoke, centre back panel, side panel
# ---------------------------------------------------------------------------

def _cb_dir(db: DesignBody) -> tuple[float, float]:
    lm = db.landmarks
    return unit_vector(lm["hem_cb"].x - lm["neck_cb"].x, lm["hem_cb"].y - lm["neck_cb"].y)


def build_back_yoke(db: DesignBody) -> PieceDraft:
    lm = db.landmarks
    upper, _ = _cut(db.edge("back", "armhole"), lm["yoke_ah_b"])
    edges = [
        ("neck", db.edge("back", "neck")),
        ("shoulder", db.edge("back", "shoulder")),
        ("armhole", upper),
        ("yoke_seam", [lm["yoke_ah_b"], lm["yoke_cb"]]),
        ("fold_cb", [lm["yoke_cb"], lm["neck_cb"]]),
    ]
    return PieceDraft(
        name="carre_dietro", edges=edges,
        construction_lines=[_segment(lm["neck_cb"], _cb_dir(db), 15.0,
                                     BACK_YOKE_DOWN_MM - 15.0)],
        labels=[(Point(lm["yoke_cb"].x + 60, lm["yoke_cb"].y - 45),
                 "CARRE DIETRO x 1 (piega c.b.)")],
        report={"yoke_seam_mm": distance(lm["yoke_ah_b"], lm["yoke_cb"])},
    )


def build_back_centre(db: DesignBody) -> PieceDraft:
    lm = db.landmarks
    edges = [
        ("yoke_seam", [lm["yoke_cb"], lm["panel_top_b"]]),
        ("panel_seam", [lm["panel_top_b"], lm["panel_hem_b"]]),
        ("waistband_seam", [lm["panel_hem_b"], lm["hem_cb"]]),
        ("fold_cb", [lm["hem_cb"], lm["yoke_cb"]]),
    ]
    return PieceDraft(
        name="dietro", edges=edges,
        construction_lines=[_segment(lm["yoke_cb"], _cb_dir(db), 25.0,
                                     distance(lm["yoke_cb"], lm["hem_cb"]) - 25.0)],
        labels=[(Point(lm["yoke_cb"].x + 50, lm["yoke_cb"].y + 130),
                 "DIETRO x 1 (piega c.b.)")],
        report={"panel_seam_mm": distance(lm["panel_top_b"], lm["panel_hem_b"])},
    )


def build_back_side_panel(db: DesignBody) -> PieceDraft:
    lm = db.landmarks
    _, lower = _cut(db.edge("back", "armhole"), lm["yoke_ah_b"])
    edges = [
        ("yoke_seam", [lm["panel_top_b"], lm["yoke_ah_b"]]),
        ("armhole", lower),
        ("side", db.edge("back", "side")),
        ("waistband_seam", [lm["side_hem_b"], lm["panel_hem_b"]]),
        ("panel_seam", [lm["panel_hem_b"], lm["panel_top_b"]]),
    ]
    ban = lm["BAN"]
    mid_hem = Point((lm["panel_hem_b"].x + lm["side_hem_b"].x) / 2,
                    (lm["panel_hem_b"].y + lm["side_hem_b"].y) / 2)
    return PieceDraft(
        name="fianchetto_dietro", edges=edges,
        construction_lines=[_notch(ban, (-1.0, 0.0)),
                            _segment(mid_hem, _cb_dir(db), -300.0, -40.0)],
        labels=[(Point(ban.x - 60, ban.y + 140), "FIANCHETTO DIETRO x 2 (specchiato)"),
                (Point(ban.x - 24, ban.y - 6), "BAN")],
        report={"armhole_mm": arc_length(lower)},
    )


# ---------------------------------------------------------------------------
# Front pieces: yoke, centre front panel (with the pintuck), chest and side
# ---------------------------------------------------------------------------

def front_jacket_marks(db: DesignBody) -> list[list[Point]]:
    """Every design mark drawn on the front, in the block frame.

    The panel builders clip this list to their own outline, so a mark that
    straddles a panel seam - the pocket entry, the flap, the bag - reaches both
    pieces, each with its own portion (D20).
    """
    lm, ln = db.landmarks, db.lines
    marks = [ln["cf"], ln["placket"], ln["pintuck_inner"], ln["pintuck_outer"],
             ln["pocket_flap"], ln["pocket_opening"], ln["pocket_bag"],
             ln["pocket_axis"], ln["side_pocket_welt"]]
    cf_dir = unit_vector(ln["cf"][1].x - ln["cf"][0].x, ln["cf"][1].y - ln["cf"][0].y)
    out = (cf_dir[1], -cf_dir[0])
    inward = BUTTONHOLE_LEN_MM - BUTTONHOLE_PAST_CF_MM
    for i in range(1, 6):
        p = lm[f"button{i}"]
        marks.append(_slot(Point(p.x + out[0] * BUTTONHOLE_PAST_CF_MM,
                                 p.y + out[1] * BUTTONHOLE_PAST_CF_MM),
                           Point(p.x - out[0] * inward, p.y - out[1] * inward)))
        marks += _button(p)
    marks += _button(lm["flap_button"])
    return marks


def _front_grainline(db: DesignBody, y0: float, y1: float) -> list[Point]:
    """Grainline parallel to the front fold edge, 2.5 cm inside the piece."""
    edge = db.lines["fold_edge"]
    u = unit_vector(edge[1].x - edge[0].x, edge[1].y - edge[0].y)
    top = _at_y(edge, y0)
    return _segment(Point(top.x - u[1] * 25.0, top.y + u[0] * 25.0), u, 0.0, y1 - y0)


def build_front_yoke(db: DesignBody, marks: list[list[Point]]) -> PieceDraft:
    lm = db.landmarks
    upper, _ = _cut(db.edge("front", "armhole"), lm["yoke_ah_f"])
    edges = [
        ("neck_overlap", db.edge("front", "neck_overlap")),
        ("neck", db.edge("front", "neck")),
        ("shoulder", db.edge("front", "shoulder")),
        ("armhole", upper),
        ("yoke_seam", [lm["yoke_ah_f"], lm["yoke_edge_f"]]),
        ("fold_edge", [lm["yoke_edge_f"], lm["edge_top"]]),
    ]
    return PieceDraft(
        name="carre_davanti", edges=edges,
        construction_lines=_clip(marks, chain_outline(edges))
        + [_front_grainline(db, lm["edge_top"].y + 35.0, lm["yoke_edge_f"].y - 20.0)],
        labels=[(Point(lm["yoke_edge_f"].x - 130, lm["yoke_edge_f"].y - 60),
                 "CARRE DAVANTI x 2 (specchiato)")],
        report={"yoke_seam_mm": distance(lm["yoke_ah_f"], lm["yoke_edge_f"])},
    )


def build_front_centre(db: DesignBody, marks: list[list[Point]]) -> PieceDraft:
    """Centre front panel, slashed open 2 cm along the outer tuck line (D18)."""
    lm = db.landmarks
    _, tail = _cut(db.edge("front", "waistband_seam"), lm["panel_cf_hem"])
    edges = [
        ("yoke_seam", [lm["yoke_edge_f"], lm["panel_cf_top"]]),
        ("panel_seam", [lm["panel_cf_top"], lm["panel_cf_hem"]]),
        ("waistband_seam", tail),
        ("fold_edge", [lm["edge_hem"], lm["yoke_edge_f"]]),
    ]
    inside = _clip(marks, chain_outline(edges))
    grain = _front_grainline(db, lm["yoke_edge_f"].y + 45.0, lm["edge_hem"].y - 45.0)

    # the slash runs bottom-to-top so that the c.f. side of the tuck is the one
    # that moves, carrying the placket, the buttonholes and the folded edge
    tuck = db.lines["pintuck_outer"]
    u = unit_vector(tuck[1].x - tuck[0].x, tuck[1].y - tuck[0].y)
    delta = (u[1] * PINTUCK_SPREAD_MM, -u[0] * PINTUCK_SPREAD_MM)
    slash = (tuck[1], tuck[0])
    return PieceDraft(
        name="davanti",
        edges=[(name, _spread(pts, *slash, delta)) for name, pts in edges],
        construction_lines=[_spread(pts, *slash, delta) for pts in inside + [grain]],
        labels=[(Point(lm["edge_hem"].x - 100, lm["edge_hem"].y - 220),
                 "DAVANTI x 2 (specchiato)")],
        report={"pintuck_spread_mm": PINTUCK_SPREAD_MM},
    )


def build_front_chest_panel(db: DesignBody, marks: list[list[Point]]) -> PieceDraft:
    lm = db.landmarks
    head, _ = _cut(db.edge("front", "waistband_seam"), lm["panel_cf_hem"])
    _, middle = _cut(head, lm["panel_side_hem"])
    edges = [
        ("yoke_seam", [lm["panel_cf_top"], lm["panel_side_top"]]),
        ("panel_seam_side", [lm["panel_side_top"], lm["panel_side_hem"]]),
        ("waistband_seam", middle),
        ("panel_seam_cf", [lm["panel_cf_hem"], lm["panel_cf_top"]]),
    ]
    return PieceDraft(
        name="pannello_petto", edges=edges,
        construction_lines=_clip(marks, chain_outline(edges)),
        labels=[(Point(lm["panel_cf_top"].x - 95, lm["panel_cf_top"].y + 260),
                 "PANNELLO PETTO x 2 (specchiato)")],
        report={"pocket_opening_mm": POCKET_OPENING_WIDTH_MM,
                "flap_width_mm": FLAP_WIDTH_MM},
    )


def build_front_side_panel(db: DesignBody, marks: list[list[Point]]) -> PieceDraft:
    lm = db.landmarks
    _, lower = _cut(db.edge("front", "armhole"), lm["yoke_ah_f"])
    head, _ = _cut(db.edge("front", "waistband_seam"), lm["panel_side_hem"])
    edges = [
        ("yoke_seam", [lm["panel_side_top"], lm["yoke_ah_f"]]),
        ("armhole", lower),
        ("side", db.edge("front", "side")),
        ("waistband_seam", head),
        ("panel_seam", [lm["panel_side_hem"], lm["panel_side_top"]]),
    ]
    fan = lm["FAN"]
    return PieceDraft(
        name="fianchetto_davanti", edges=edges,
        construction_lines=_clip(marks, chain_outline(edges)) + [_notch(fan, (1.0, 0.0))],
        labels=[(Point(fan.x + 25, fan.y + 150), "FIANCHETTO DAVANTI x 2 (specchiato)"),
                (Point(fan.x + 12, fan.y - 6), "FAN")],
        report={"armhole_mm": arc_length(lower)},
    )


# ---------------------------------------------------------------------------
# Convertible collar (page 14, step 2)
# ---------------------------------------------------------------------------

def build_collar(db: DesignBody) -> PieceDraft:
    """Collar drawn on a baseline as long as half the lowered neckline.

    Cut twice on the c.b. fold (top and under collar) with the roll line
    marked; there is no under-collar reduction in this design (D10). The
    booklet asks for the neck seam to be verified against the neckline and
    corrected parallel at the c.b.: the correction is reported, not applied,
    because the drawing itself leaves it out.
    """
    length = db.report["neckline_mm"]
    cf_seam = Point(0.0, COLLAR_CF_SEAM_MM)
    cb_seam = Point(length, COLLAR_CB_SEAM_MM)
    touch = Point(length * COLLAR_TOUCH_FRACTION, 0.0)
    cb_roll = Point(length, COLLAR_CB_SEAM_MM + COLLAR_STAND_MM)
    cb_top = Point(length, COLLAR_CB_SEAM_MM + COLLAR_STAND_MM + COLLAR_WIDTH_MM)
    point = Point(-COLLAR_POINT_EXT_MM, COLLAR_CF_WIDTH_MM)

    ch1, ch2 = distance(cf_seam, touch), distance(touch, cb_seam)
    seam = (cubic_with_tangents(cf_seam, touch, _dir(COLLAR_SEAM_START_DEG), (1.0, 0.0),
                                alpha=COLLAR_SEAM_FRONT_ALPHA * ch1,
                                beta=COLLAR_SEAM_FRONT_BETA * ch1, n=24)
            + cubic_with_tangents(touch, cb_seam, (1.0, 0.0), (1.0, 0.0),
                                  alpha=COLLAR_SEAM_BACK_ALPHA * ch2,
                                  beta=COLLAR_SEAM_BACK_BETA * ch2, n=24)[1:])
    ch = distance(point, cb_top)
    outer = cubic_with_tangents(point, cb_top, _dir(COLLAR_OUTER_START_DEG), (1.0, 0.0),
                                alpha=COLLAR_OUTER_ALPHA * ch,
                                beta=COLLAR_OUTER_BETA * ch, n=32)
    ch = distance(cf_seam, cb_roll)
    roll = cubic_with_tangents(cf_seam, cb_roll, _dir(COLLAR_ROLL_START_DEG), (1.0, 0.0),
                               alpha=COLLAR_ROLL_ALPHA * ch,
                               beta=COLLAR_ROLL_BETA * ch, n=32)

    edges = [
        ("neck_seam", seam),                        # c.f. -> c.b.
        ("fold_cb", [cb_seam, cb_top]),
        ("outer", outer[::-1]),                     # c.b. -> collar point
        ("front", [point, cf_seam]),
    ]
    seam_len = arc_length(seam)
    correction = length - seam_len
    warnings = []
    if abs(correction) > COLLAR_TOL_MM:
        warnings.append(
            f"colletto: cucitura collo {seam_len / 10:.1f} cm contro scollo "
            f"{length / 10:.1f} cm, allungare di {correction / 10:.1f} cm al c.b."
        )
    return PieceDraft(
        name="colletto", edges=edges,
        construction_lines=[roll, [touch, Point(touch.x, -8.0)],
                            _segment(Point(length - 30.0, 20.0), (0.0, 1.0), 0.0, 65.0)],
        labels=[(Point(length / 2, 62.0), "COLLETTO x 2 (piega c.b.)"),
                (Point(length / 3, 26.0), "linea di rollo")],
        report={"baseline_mm": length, "neck_seam_mm": seam_len,
                "neckline_mm": length, "correction_mm": correction,
                "warnings": warnings},
    )


# ---------------------------------------------------------------------------
# Waistband and adjustable tab (page 14, step 1)
# ---------------------------------------------------------------------------

def build_jacket_waistband(db: DesignBody) -> PieceDraft:
    """Waistband 4.5 cm high, as long as the front hem (measured from the fold
    edge) plus the back hem, cut on the c.b. fold. Local frame: x from the
    front edge, y down."""
    h = WAISTBAND_HEIGHT_MM
    x_side = db.report["front_hem_mm"]
    length = x_side + db.report["back_hem_mm"]
    x_cf = OVERLAP_MM
    x_panel = x_side + db.report["panel_notch_mm"]

    corners = [Point(0.0, 0.0), Point(length, 0.0), Point(length, h), Point(0.0, h)]
    edges = [
        ("body_seam", [corners[0], corners[1]]),
        ("fold_cb", [corners[1], corners[2]]),
        ("lower_seam", [corners[2], corners[3]]),
        ("front", [corners[3], corners[0]]),
    ]
    marks = [[Point(x, 0.0), Point(x, h)] for x in (x_cf, x_side, x_panel)]
    marks.append([Point(x_side, (h - TAB_HEIGHT_MM) / 2),
                  Point(x_side + TAB_LEN_MM, (h - TAB_HEIGHT_MM) / 2),
                  Point(x_side + TAB_LEN_MM, (h + TAB_HEIGHT_MM) / 2),
                  Point(x_side, (h + TAB_HEIGHT_MM) / 2),
                  Point(x_side, (h - TAB_HEIGHT_MM) / 2)])
    marks.append(_slot(Point(x_cf - BUTTONHOLE_PAST_CF_MM, h / 2),
                       Point(x_cf + BUTTONHOLE_LEN_MM - BUTTONHOLE_PAST_CF_MM, h / 2)))
    marks += _button(Point(x_cf, h / 2))
    for d in TAB_BUTTONS_MM:
        marks += _button(Point(x_side + d, h / 2))
    return PieceDraft(
        name="cinturino", edges=edges, construction_lines=marks,
        labels=[(Point(length / 4, h / 2 + 15), "CINTURINO x 2 (piega c.b.)"),
                (Point(x_cf + 3, h + 11), "c.f."),
                (Point(x_side + 3, h + 11), "fianco"),
                (Point(x_panel + 3, h + 11), "pannello")],
        report={"length_mm": length, "height_mm": h, "cf_from_edge_mm": x_cf,
                "side_notch_mm": x_side, "panel_notch_mm": x_panel},
    )


def build_tab() -> PieceDraft:
    """Adjustable tab on the side seam: 8 x 3.5 cm with a vertical buttonhole
    1.5 cm from the free end (D24)."""
    w, h = TAB_LEN_MM, TAB_HEIGHT_MM
    corners = [Point(0.0, 0.0), Point(w, 0.0), Point(w, h), Point(0.0, h)]
    x_hole = w - TAB_BUTTONHOLE_FROM_END_MM
    return PieceDraft(
        name="linguetta",
        edges=[("seam", corners + [corners[0]])],
        construction_lines=[_slot(Point(x_hole, (h + TAB_BUTTONHOLE_LEN_MM) / 2),
                                  Point(x_hole, (h - TAB_BUTTONHOLE_LEN_MM) / 2))],
        labels=[(Point(8.0, h / 2), "LINGUETTA x 4")],
        report={"length_mm": w, "height_mm": h},
    )


# ---------------------------------------------------------------------------
# Pocket pieces (chest pocket flap and bag, side pocket welt and bag)
# ---------------------------------------------------------------------------

def build_chest_pocket_flap() -> PieceDraft:
    """Flap of the chest pocket: four flat pieces, two per pocket, so the top
    edge is the one sewn onto the yoke and takes its seam allowance like the
    other three."""
    w, side, tip = FLAP_WIDTH_MM, FLAP_SIDE_MM, FLAP_POINT_MM
    corners = [Point(0.0, 0.0), Point(w, 0.0), Point(w, side),
               Point(w / 2, tip), Point(0.0, side)]
    return PieceDraft(
        name="patta_taschino",
        edges=[("seam", corners + [corners[0]])],
        construction_lines=_button(Point(w / 2, FLAP_BUTTON_MM)),
        labels=[(Point(w / 2 - 35, side / 2), "PATTA TASCHINO x 4")],
        report={"width_mm": w, "side_mm": side, "point_mm": tip},
    )


def build_chest_pocket_bag() -> PieceDraft:
    """Bag under the chest pocket entry: the stitching pentagon of the drawing,
    carried 1 cm above the entry up to the yoke line (derived, D23)."""
    w, top = POCKET_OPENING_WIDTH_MM, POCKET_OPENING_BELOW_YOKE_MM
    side, tip = top + POCKET_BAG_SIDE_MM, top + POCKET_BAG_POINT_MM
    corners = [Point(0.0, 0.0), Point(w, 0.0), Point(w, side),
               Point(w / 2, tip), Point(0.0, side)]
    return PieceDraft(
        name="sacchetto_taschino",
        edges=[("seam", corners + [corners[0]])],
        construction_lines=[[Point(0.0, top), Point(w, top)]],
        labels=[(Point(w / 2 - 35, side / 2), "SACCHETTO TASCHINO x 4")],
        report={"width_mm": w, "depth_mm": tip},
    )


def build_side_pocket_welt() -> PieceDraft:
    """Welt of the slanted side pocket: 16 x 1.5 cm, cut double on the fold."""
    w, h = SIDE_POCKET_LEN_MM, SIDE_POCKET_WELT_MM
    corners = [Point(0.0, 0.0), Point(w, 0.0), Point(w, 2 * h), Point(0.0, 2 * h)]
    return PieceDraft(
        name="listino_tasca_laterale",
        edges=[("seam", corners + [corners[0]])],
        construction_lines=[[Point(0.0, h), Point(w, h)]],
        labels=[(Point(12.0, h), "LISTINO TASCA LAT. x 2 (piega a meta)")],
        report={"length_mm": w, "welt_mm": h},
    )


def build_side_pocket_bag() -> PieceDraft:
    """Bag hanging from the slanted side pocket entry (derived, D23)."""
    w, h, r = SIDE_POCKET_LEN_MM + 10.0, SIDE_POCKET_LEN_MM, 25.0
    corners = [Point(0.0, 0.0), Point(w, 0.0), Point(w, h - r),
               Point(w - r, h), Point(r, h), Point(0.0, h - r)]
    return PieceDraft(
        name="sacchetto_tasca_laterale",
        edges=[("seam", corners + [corners[0]])],
        labels=[(Point(25.0, h / 2), "SACCHETTO TASCA LAT. x 4")],
        report={"width_mm": w, "depth_mm": h},
    )


# ---------------------------------------------------------------------------
# Sleeve (page 15): shorten for the cuff, blend the front seam, kill the ease
# ---------------------------------------------------------------------------

def _sleeve_halves(sleeve: JacketSleeveDraft, ang: float) -> list[list[tuple[str, list[Point]]]]:
    """Both sleeve pieces shortened for the cuff, the upper one pivoted by `ang`.

    The slash runs from the hem corner of the back seam - the drawing's pivot
    point - up to Sp, and everything in front of it turns about the hem corner.
    A POSITIVE angle swings that half toward the back, so the cap swallows that
    much of itself (less ease); a negative one opens a wedge at Sp and
    lengthens the cap (D17). The under sleeve is only shortened and blended:
    its own slash ends on the cap corner UST, where turning the front seam
    would push the corner out past the cap instead of taking cap away.
    """
    lm = sleeve.landmarks
    pivot = point_along(lm["B_hem"], lm["F_b"], CUFF_HEIGHT_MM)
    out = []
    for part, turn, elbow, hem_pt, tip in (
            ("upper", ang, lm["fold_elbow_front"], lm["fold_hem"], lm["FST"]),
            ("under", 0.0, lm["elbow_front"], lm["hem_front"], lm["UST"])):
        hem_corner = point_along(hem_pt, elbow, CUFF_HEIGHT_MM)
        # "draw the front sleeve seam nicely shaped": a single smooth curve
        # through the elbow corner instead of the block's two straight legs
        front_seam = [_rotate(p, pivot, turn)
                      for p in smooth_polyline([hem_corner, elbow, tip], n_per_seg=10)]

        if part == "upper":
            head, tail = _cut(sleeve.edge("upper", "cap"), lm["Sp"])
            swallowed = distance(_rotate(lm["Sp"], pivot, ang), lm["Sp"]) if ang > 0 else 0.0
            cap = [("cap_front", [_rotate(p, pivot, ang)
                                  for p in sleeve.edge("upper", "cap_front")]),
                   ("cap", [_rotate(p, pivot, ang) for p in head] + _drop_arc(tail, swallowed))]
            back = sleeve.edge("upper", "back_seam") + sleeve.edge("upper", "back_fold")[1:]
        else:
            cap = [("cap", sleeve.edge("under", "cap"))]
            back = sleeve.edge("under", "back_seam") + sleeve.edge("under", "back_fold")[1:]
        back, _ = _cut(back, pivot)
        out.append(cap + [("back_seam", back),
                          ("cuff_seam", [pivot, _rotate(hem_corner, pivot, turn)]),
                          ("front_seam", front_seam)])
    return out


def _cap_len(edges: list[tuple[str, list[Point]]]) -> float:
    return sum(arc_length(pts) for name, pts in edges if name.startswith("cap"))


def split_sleeve(sleeve: JacketSleeveDraft) -> tuple[PieceDraft, PieceDraft]:
    """Upper and under sleeve of Design 4041, with the cap ease taken out.

    The booklet wants the denim sleeve set in with no ease at all, so the
    upper sleeve is slashed from Sp to the hemline and pivoted on the hem
    corner until the cap seam matches the armhole (D17). The loop is needed
    because swallowing the cap moves the cut point along a curve rather than
    along the chord; it settles in one or two passes.
    """
    target = sleeve.report["armhole_circ_mm"]
    lm = sleeve.landmarks
    pivot = point_along(lm["B_hem"], lm["F_b"], CUFF_HEIGHT_MM)
    lever = distance(lm["Sp"], pivot)
    clamp = 2.0 * asin(CAP_EASE_CLAMP_MM / (2.0 * lever))

    ang, clamped = 0.0, False
    for _ in range(CAP_EASE_MAX_ITER):
        halves = _sleeve_halves(sleeve, ang)
        ease = sum(_cap_len(e) for e in halves) - target
        if abs(ease) < CAP_EASE_TOL_MM:
            break
        step = ease / lever
        if abs(ang + step) > clamp:
            ang, clamped = clamp if step > 0 else -clamp, True
            halves = _sleeve_halves(sleeve, ang)
            ease = sum(_cap_len(e) for e in halves) - target
            break
        ang += step
    warnings = []
    if clamped or abs(ease) > CAP_EASE_TOL_MM:
        warnings.append(
            f"agio testa manica non annullato: residuo {ease / 10:.1f} cm"
            + (" (slash limitato a 2.5 cm)" if clamped else "")
        )

    y_elbow = sleeve.report["levels_y_mm"]["elbow"]
    pieces = []
    for name, edges in zip(("sopramanica", "sottomanica"), halves):
        back = dict(edges)["back_seam"]
        vent = point_at_arc_length(back[::-1], SLEEVE_VENT_MM)
        u = unit_vector(back[-1].x - back[-2].x, back[-1].y - back[-2].y)
        hem_front = dict(edges)["cuff_seam"][1]
        x_mid = (pivot.x + hem_front.x) / 2
        pieces.append(PieceDraft(
            name=name, edges=edges,
            construction_lines=[_notch(vent, (-u[1], u[0])),
                                [Point(x_mid, y_elbow - 150.0), Point(x_mid, y_elbow + 150.0)],
                                [Point(x_mid - 20.0, y_elbow), Point(x_mid + 20.0, y_elbow)]],
            labels=[(Point(x_mid - 45, y_elbow - 70), f"{name.upper()} x 2 (specchiato)"),
                    (Point(vent.x - 35, vent.y + 22), "spacco 9")],
            report={"cap_len_mm": _cap_len(edges),
                    "hem_len_mm": distance(pivot, hem_front),
                    "vent_mm": SLEEVE_VENT_MM, "cap_ease_mm": ease,
                    "pivot_deg": degrees(ang), "warnings": warnings},
        ))
    return pieces[0], pieces[1]


def build_cuff(upper: PieceDraft, under: PieceDraft) -> PieceDraft:
    """Cuff 4.5 cm high, matched to the hem of the two shortened sleeve pieces.

    Cut double on the long fold; buttonhole at the vent end, button at the
    front end, both 1.5 cm in and centred on the height (D24).
    """
    h = CUFF_HEIGHT_MM
    length = upper.report["hem_len_mm"] + under.report["hem_len_mm"]
    corners = [Point(0.0, 0.0), Point(length, 0.0), Point(length, h), Point(0.0, h)]
    edges = [
        ("sleeve_seam", [corners[0], corners[1]]),
        ("vent_end", [corners[1], corners[2]]),
        ("fold_edge", [corners[2], corners[3]]),
        ("front_end", [corners[3], corners[0]]),
    ]
    marks = [_slot(Point(length - CUFF_MARK_INSET_MM, h / 2),
                   Point(length - CUFF_MARK_INSET_MM - BUTTONHOLE_LEN_MM, h / 2))]
    marks += _button(Point(CUFF_MARK_INSET_MM, h / 2))
    return PieceDraft(
        name="polsino", edges=edges, construction_lines=marks,
        labels=[(Point(length / 3, h / 2 + 15), "POLSINO x 2 (doppio, piega sul lato)")],
        report={"length_mm": length, "height_mm": h},
    )
