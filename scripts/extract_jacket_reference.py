"""Extract size-50 reference geometry for the Classic Denim Jacket (M&S 4041).

Pages 11-12 (basic denim jacket block) and 14-15 (Design 4041) of the booklet
are drawn to scale for size 50. This script measures their vectors and freezes
the result into tests/data/ms_jacket_reference_size50.json so the jacket draft
tests have ground truth without needing the PDF at test time.

Coordinates are millimetres in the frames of the implementation plan
(docs/superpowers/plans/2026-08-19-ms-denim-jacket.md, "Sistemi di coordinate"):

  body     x=0 at the c.b., x grows toward the front, y=0 at the back neck
           point N, y grows down (the page draws the c.b. on the right, so the
           page x axis is mirrored).
  sleeve   x=0/y=0 at the construction point A, x toward the back of the sleeve.
  p14fr    the Design 4041 front is drawn apart from the back: own frame with
           x=0 on the front pitch line (x toward the c.f.), y=0 on the chest line.
  collar   x=0 at the c.f., x toward the c.b. fold, y=0 on the baseline, y up.
  strip    waistband/cuff rectangles: x from the left edge, y down from the top.

Page 14 draws every element twice, the second copy shifted 548.70 pt down and
therefore off the 841.89 pt page: only the upper copy is kept.

Usage:  python scripts/extract_jacket_reference.py [path-to-pdf]
"""
import json
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_ms_reference as ms  # noqa: E402  (helpers: chains, merging, similarity)

PDF_DEFAULT = Path("docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf")
OUT_PATH = Path("tests/data/ms_jacket_reference_size50.json")

# Size-50 chart (booklet pp. 12-13) the drawings are built on.
M = dict(Bh=179.0, Cg=100.0, Wg=90.0, Hg=102.0, Sl=64.0)

# Drawing frames, measured on the vectors (see the plan, "Sistemi di coordinate").
P11 = dict(scale=4.7250, x0=527.9, y0=467.9, x_sign=-1.0)
P12 = dict(scale=4.72656, x0=415.06, y0=464.23, x_sign=1.0)
P14_BACK = dict(scale=4.7242, x0=545.11, y0=124.00, x_sign=-1.0)
P14_FRONT = dict(scale=4.7242, x0=356.40, y0=242.16, x_sign=-1.0)
P14_COLLAR = dict(scale=4.7242, x0=344.70, y0=49.90, x_sign=1.0, y_sign=-1.0)
P14_SHIFT = 548.70   # page-14 duplicate offset
P15_SCALE = 4.7267

# Stroke widths: the booklet draws net outlines at 1.2, design/detail lines at
# 0.75, construction and dimension lines below 0.5.
NET = (1.1, 1.3)
DETAIL = (0.5, 0.99)
THIN = (0.0, 0.49)

LANDMARK_TOL_MM = 8.0   # snap radius: expected value -> nearest drawn vertex


class Frame:
    """PDF points -> jacket frame millimetres (x_sign/y_sign mirror the axes)."""

    def __init__(self, scale, x0, y0, x_sign=1.0, y_sign=1.0):
        self.scale = scale
        self.x0 = x0
        self.y0 = y0
        self.x_sign = x_sign
        self.y_sign = y_sign

    def to_mm(self, p):
        return ((p[0] - self.x0) * self.x_sign / self.scale * 10.0,
                (p[1] - self.y0) * self.y_sign / self.scale * 10.0)

    def chain_mm(self, pts):
        return [self.to_mm(p) for p in pts]


def chains_mm(page, frame, wmin, wmax):
    """Merged stroked chains of the given width band, in frame millimetres."""
    raw = ms.merge_chains([pts for _w, pts in ms.drawing_chains(page, wmin, wmax)])
    return [frame.chain_mm(c) for c in raw]


def bbox(chain):
    xs = [p[0] for p in chain]
    ys = [p[1] for p in chain]
    return min(xs), min(ys), max(xs), max(ys)


def dedupe_shifted(chains, shift):
    """Page 14 duplicates every element `shift` points further down, past the
    bottom of the sheet. Keep the upper (visible) copy of each pair."""
    out = []
    for c in chains:
        b = bbox(c)
        twin = any(abs(bbox(k)[0] - b[0]) < 1.0 and abs(bbox(k)[2] - b[2]) < 1.0
                   and abs((b[1] - bbox(k)[1]) - shift) < 1.5
                   and abs(ms.arc_len(k) - ms.arc_len(c)) < 1.5
                   for k in chains if k is not c)
        if not twin:
            out.append(c)
    return out


def longest(chains, n=1):
    return sorted(chains, key=ms.arc_len, reverse=True)[:n]


def take_landmarks(chain, expected, label):
    """Snap every expected point to the nearest vertex of `chain`, reporting the
    deviation of the drawing from the plan."""
    out = {}
    print(f"  {label}:")
    for name, exp in expected.items():
        v = min(chain, key=lambda p: ms.dist(p, exp))
        d = ms.dist(v, exp)
        assert d <= LANDMARK_TOL_MM, f"{label}.{name}: nearest vertex {d:.1f} mm from {exp}"
        out[name] = [round(v[0], 2), round(v[1], 2)]
        print(f"    {name:16s} ({v[0]:7.1f},{v[1]:7.1f})  vs plan {d:4.1f} mm")
    return out


def cut(chain, a, b):
    """Sub-polyline from the vertex nearest `a` to the one nearest `b`; on a
    closed chain the shorter way round."""
    ia = min(range(len(chain)), key=lambda i: ms.dist(chain[i], a))
    ib = min(range(len(chain)), key=lambda i: ms.dist(chain[i], b))
    lo, hi = min(ia, ib), max(ia, ib)
    seg = chain[lo:hi + 1]
    if ms.dist(chain[0], chain[-1]) < 1.0:
        other = chain[hi:] + chain[1:lo + 1]
        if ms.arc_len(other) < ms.arc_len(seg):
            seg = other[::-1]
    return seg if ia <= ib else seg[::-1]


def take_edges(chain, lm, specs, label):
    out = {}
    print(f"  {label} edges:")
    for name, a, b in specs:
        seg = cut(chain, lm[a], lm[b])
        out[name] = [[round(p[0], 2), round(p[1], 2)] for p in seg]
        print(f"    {name:14s} {a}->{b}  len={ms.arc_len(seg)/10:6.2f} cm  pts={len(seg)}")
    return out


def find_chain(chains, a, b, tol=3.0):
    """The chain whose endpoints match a and b, oriented a->b."""
    for c in chains:
        if ms.dist(c[0], a) < tol and ms.dist(c[-1], b) < tol:
            return c
        if ms.dist(c[0], b) < tol and ms.dist(c[-1], a) < tol:
            return c[::-1]
    return None


def find_through(chains, a, b, tol=3.0):
    """The a->b stretch of the chain that passes through both points (the PDF
    merges some construction lines with their dimension arrows)."""
    for c in chains:
        if min(ms.dist(p, a) for p in c) < tol and min(ms.dist(p, b) for p in c) < tol:
            return cut(c, a, b)
    return None


def nearest_vertex(chains, target):
    return min((p for c in chains for p in c), key=lambda p: ms.dist(p, target))


def take_lines(chains, specs, label):
    out = {}
    print(f"  {label}:")
    for name, a, b in specs:
        c = find_chain(chains, a, b)
        assert c is not None, f"{label}.{name}: no chain between {a} and {b}"
        out[name] = [[round(p[0], 2), round(p[1], 2)] for p in c]
        print(f"    {name:22s} ({c[0][0]:7.1f},{c[0][1]:7.1f})->({c[-1][0]:7.1f},{c[-1][1]:7.1f})"
              f"  len={ms.arc_len(c)/10:6.2f} cm  pts={len(c)}")
    return out


def centre_pt(chain, x_mm, y_mm):
    """Centre of a mark drawn in PDF points, mapped through a strip frame."""
    x0, y0, x1, y1 = bbox(chain)
    return [x_mm((x0 + x1) / 2), y_mm((y0 + y1) / 2)]


def centre(chain):
    x0, y0, x1, y1 = bbox(chain)
    return [round((x0 + x1) / 2, 2), round((y0 + y1) / 2, 2)]


def line_intersection(p1, p2, p3, p4):
    d = ((p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0]))
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    return [round(p1[0] + t * (p2[0] - p1[0]), 2), round(p1[1] + t * (p2[1] - p1[1]), 2)]


# ---------------------------------------------------------------- page 11

BACK_LM = {
    "N": (0.0, 0.0), "A2": (79.9, -20.1), "E": (86.0, -28.0), "HSP_b": (91.2, -36.7),
    "SP_b": (238.8, 16.2), "SP0": (236.1, 26.2), "G1": (231.8, 187.4),
    "armhole_min": (226.8, 122.5), "U_b": (314.3, 249.9), "W_b": (307.3, 447.9),
    "H_b": (314.3, 628.6), "K": (24.9, 639.9),
}
BACK_EDGES = [
    ("neck", "HSP_b", "N"), ("shoulder", "HSP_b", "SP_b"), ("armhole", "SP_b", "U_b"),
    ("side_upper", "U_b", "W_b"), ("side_lower", "W_b", "H_b"),
    ("hem", "H_b", "K"), ("cb", "K", "N"),
]
FRONT_LM = {
    "HSP_f": (541.2, -16.6), "SP_f": (402.4, 44.9), "quarter_Sd": (436.8, 187.4),
    "U_f": (374.3, 249.9), "W_f": (381.4, 447.9), "H_f": (374.3, 628.6),
    "C0": (638.9, 52.8), "C1": (644.9, 249.9), "C2": (648.8, 447.9), "C3": (648.8, 633.8),
}
FRONT_EDGES = [
    ("neck", "HSP_f", "C0"), ("shoulder", "HSP_f", "SP_f"), ("armhole", "SP_f", "U_f"),
    ("side_upper", "U_f", "W_f"), ("side_lower", "W_f", "H_f"),
    ("hem", "H_f", "C3"), ("cf_upper", "C0", "C2"), ("cf_lower", "C2", "C3"),
]


def extract_body_block(doc):
    """Basic denim jacket block, page 11: back and front in the body frame."""
    print("PAGE 11 - body block")
    page = doc[10]
    frame = Frame(**P11)
    net = chains_mm(page, frame, *NET)
    thin = chains_mm(page, frame, *THIN)
    detail = chains_mm(page, frame, *DETAIL)

    back_outline, front_outline = longest(net, 2)
    back_lm = take_landmarks(back_outline, BACK_LM, "back")
    front_lm = take_landmarks(front_outline, FRONT_LM, "front")

    # FAN is a 1 cm tick sitting on the front armhole.
    fan = min((c for c in net if len(c) == 2), key=lambda c: ms.dist(c[0], (436.4, 210.9)))
    front_lm["FAN"] = [round(fan[0][0], 2), round(fan[0][1], 2)]
    print(f"    FAN              ({fan[0][0]:7.1f},{fan[0][1]:7.1f})  "
          f"tick {ms.arc_len(fan)/10:.2f} cm")

    # Construction guides: the back shoulder guideline A2->SP0 meets the back
    # width vertical in S1; the front auxiliary meets the pitch line in S2.
    aux_f = find_chain(thin, (398.4, 35.7), (542.9, 447.9), tol=8.0)
    pitch = find_chain(thin, (436.8, 37.0), (436.8, -25.1), tol=8.0)
    assert aux_f and pitch, "page-11 construction guides not found"
    back_lm["S1"] = line_intersection(back_lm["A2"], back_lm["SP0"],
                                      (221.8, 0.0), (221.8, 249.9))
    front_lm["Cn"] = [round(aux_f[1][0], 2), round(aux_f[1][1], 2)]
    front_lm["SP0_f"] = [round(aux_f[0][0], 2), round(aux_f[0][1], 2)]
    front_lm["P_top"] = [round(pitch[-1][0], 2), round(pitch[-1][1], 2)]
    front_lm["S2"] = line_intersection(aux_f[0], aux_f[1], pitch[0], pitch[-1])
    for name, src in (("S1", back_lm), ("Cn", front_lm), ("SP0_f", front_lm),
                      ("P_top", front_lm), ("S2", front_lm)):
        print(f"    {name:16s} ({src[name][0]:7.1f},{src[name][1]:7.1f})  (construction)")

    back_edges = take_edges(back_outline, back_lm, BACK_EDGES, "back")
    front_edges = take_edges(front_outline, front_lm, FRONT_EDGES, "front")

    # Armhole-height transfer lines the sleeve is built on (0.75 width).
    transfers = take_lines(detail, [
        ("back_ah", (238.8, 16.2), (238.8, 249.9)),
        ("front_ah", (402.4, 44.9), (436.8, 249.9)),
        ("quarter_sd", (231.8, 187.4), (436.8, 187.4)),
    ], "transfer lines")

    return {
        "back": {"landmarks": back_lm, "edges": back_edges},
        "front": {"landmarks": front_lm, "edges": front_edges},
        "transfers": transfers,
    }


# ---------------------------------------------------------------- page 12

SLEEVE_UPPER_LM = {
    "Sp": (111.4, 0.0), "Q": (202.8, 39.0), "U22": (219.1, 53.9),
    "belly_back": (224.3, 190.8), "F_b": (210.0, 378.0), "merge_back": (190.2, 467.6),
    "B_hem": (147.5, 655.0), "fold_hem": (-30.0, 625.0), "fold_elbow_front": (-10.1, 378.0),
    "FST": (-27.5, 163.6), "FAN": (0.0, 132.0), "M2": (27.8, 66.0),
}
SLEEVE_UPPER_EDGES = [
    ("cap_front", "FST", "FAN"), ("cap", "FAN", "U22"), ("back_seam", "U22", "F_b"),
    ("back_fold", "F_b", "B_hem"), ("hem", "B_hem", "fold_hem"),
    ("front_seam", "fold_hem", "FST"),
]
SLEEVE_UNDER_LM = {
    "B_hem": (147.5, 655.0), "hem_front": (30.2, 625.1), "elbow_front": (50.1, 378.0),
    "UST": (32.3, 158.8), "U2": (188.7, 53.9), "belly_back": (208.5, 299.7),
    "merge_back": (190.2, 467.6),
}
# The under sleeve stops at merge_back: from there to B_hem it runs on the back
# fold, drawn once as part of the upper sleeve.
SLEEVE_UNDER_EDGES = [
    ("cap", "UST", "U2"), ("back_seam", "U2", "merge_back"),
    ("hem", "B_hem", "hem_front"), ("front_seam", "hem_front", "UST"),
]


def extract_sleeve_block(doc):
    """Basic sleeve block, page 12, in the sleeve frame (origin A)."""
    print("\nPAGE 12 - sleeve block")
    page = doc[11]
    frame = Frame(**P12)
    net = chains_mm(page, frame, *NET)
    thin = chains_mm(page, frame, *THIN)
    detail = chains_mm(page, frame, *DETAIL)

    upper, under = longest(net, 2)
    upper_lm = take_landmarks(upper, SLEEVE_UPPER_LM, "upper")

    # Construction points: E ends the Scw diagonal, T ends the Q guide, M1 and
    # the elbow point of the front fold are vertices of the thin guides.
    for name, target in (("E", (202.8, 0.0)), ("T", (86.4, 161.0)),
                         ("M1", (55.7, 0.0)), ("fold_elbow", (20.0, 378.0))):
        v = nearest_vertex(thin + detail, target)
        d = ms.dist(v, target)
        assert d <= LANDMARK_TOL_MM, f"sleeve.{name}: nearest vertex {d:.1f} mm off"
        upper_lm[name] = [round(v[0], 2), round(v[1], 2)]
        print(f"    {name:16s} ({v[0]:7.1f},{v[1]:7.1f})  (construction)")

    under_lm = take_landmarks(under, SLEEVE_UNDER_LM, "under")

    return {
        "upper": {"landmarks": upper_lm,
                  "edges": take_edges(upper, upper_lm, SLEEVE_UPPER_EDGES, "upper")},
        "under": {"landmarks": under_lm,
                  "edges": take_edges(under, under_lm, SLEEVE_UNDER_EDGES, "under")},
        "guides": take_lines(detail + thin, [
            ("scw_diagonal", (0.0, 132.0), (202.8, 0.0)),
            ("q_to_t", (202.8, 39.0), (86.4, 161.0)),
        ], "guides"),
    }


# ---------------------------------------------------------------- page 14

D_BACK_LM = {
    "neck_cb": (0.2, 5.0), "neck_shoulder": (100.9, -33.2), "shoulder_end": (238.9, 16.3),
    "BAN": (232.0, 187.6), "side_chest": (314.5, 250.1), "side_waist": (307.5, 448.1),
    "side_hem": (312.7, 583.9), "hem_cb": (23.3, 595.2),
}
D_BACK_EDGES = [
    ("neck", "neck_cb", "neck_shoulder"), ("shoulder", "neck_shoulder", "shoulder_end"),
    ("armhole", "shoulder_end", "side_chest"), ("side", "side_chest", "side_hem"),
    ("hem", "side_hem", "hem_cb"), ("cb", "hem_cb", "neck_cb"),
]
D_FRONT_LM = {
    "edge_top": (222.6, -182.5), "neck_cf": (202.6, -182.1), "neck_shoulder": (95.3, -262.6),
    "shoulder_end": (-34.4, -205.1), "pitch_tangent": (0.0, -62.6),
    "side_chest": (-62.5, 0.0), "side_waist": (-55.4, 198.0), "side_hem": (-60.7, 333.8),
    "hem_cf": (212.1, 338.9), "hem_edge": (232.1, 338.5),
}
D_FRONT_EDGES = [
    ("neck_overlap", "edge_top", "neck_cf"), ("neck", "neck_cf", "neck_shoulder"),
    ("shoulder", "neck_shoulder", "shoulder_end"),
    ("armhole", "shoulder_end", "side_chest"), ("side", "side_chest", "side_hem"),
    ("hem", "side_hem", "hem_edge"),
]
COLLAR_LM = {
    "cb_seam": (260.2, 15.0), "cf_seam": (0.0, 10.0), "baseline_touch": (86.0, 0.1),
    "point": (-25.0, 75.1), "cb_top": (260.3, 95.1),
}


def extract_design_body(doc):
    """Design 4041 body, page 14: back, front, collar and waistband."""
    print("\nPAGE 14 - Design 4041 body")
    page = doc[13]
    back_fr, front_fr = Frame(**P14_BACK), Frame(**P14_FRONT)
    collar_fr = Frame(**P14_COLLAR)

    def merged(wmin, wmax):
        return dedupe_shifted(
            ms.merge_chains([pts for _w, pts in ms.drawing_chains(page, wmin, wmax)]),
            P14_SHIFT)

    def part(chains, frame, keep):
        return [frame.chain_mm(c) for c in chains if keep(bbox(c))]

    # The page stacks collar (top), back and front (middle), waistband (bottom).
    def is_back(b):
        return b[0] > 390 and 60 < b[1] and b[3] < 460

    def is_front(b):
        return b[2] < 395 and 60 < b[1] and b[3] < 460

    def is_collar(b):
        return b[3] < 100

    net, detail, thin = merged(*NET), merged(*DETAIL), merged(*THIN)
    detail_back = part(detail, back_fr, is_back)
    detail_front = part(detail, front_fr, is_front)
    thin_front = part(thin, front_fr, is_front)

    back_outline = max(part(net, back_fr, is_back), key=ms.arc_len)
    front_outline = max(part(net, front_fr, is_front), key=ms.arc_len)
    collar_outline = max(part(net, collar_fr, is_collar), key=ms.arc_len)

    back_lm = take_landmarks(back_outline, D_BACK_LM, "back")
    front_lm = take_landmarks(front_outline, D_FRONT_LM, "front")
    collar_lm = take_landmarks(collar_outline, COLLAR_LM, "collar")

    back_lines = take_lines(detail_back, [
        ("yoke", (5.3, 135.1), (226.9, 126.4)),
        ("panel_seam", (192.0, 127.6), (188.0, 588.9)),
    ], "back design lines")
    front_lines = take_lines(detail_front + thin_front, [
        ("yoke", (-0.2, -71.2), (224.6, -71.2)),
        ("cf", (202.6, -182.1), (212.1, 338.9)),
        ("placket_topstitch", (177.7, -183.4), (187.2, 338.8)),
        ("pintuck_inner", (169.6, -71.2), (177.2, 338.8)),
        ("pintuck_outer", (159.6, -71.2), (167.0, 338.8)),
        ("panel_seam_cf", (129.5, -61.2), (109.6, 338.8)),
        ("panel_seam_side", (39.6, -61.2), (59.7, 337.9)),
        ("pocket_opening", (24.6, -61.2), (144.6, -61.2)),
        ("pocket_flap", (19.5, -71.2), (149.7, -71.2)),
        ("pocket_bag", (24.6, -71.2), (144.6, -71.2)),
        ("pocket_axis", (84.6, -18.3), (84.6, 338.6)),
    ], "front design lines")

    welt = min((c for c in detail_front if 340 < ms.arc_len(c) < 360), key=ms.arc_len)
    front_lines["side_pocket_welt"] = [[round(p[0], 2), round(p[1], 2)] for p in welt]
    print(f"    side_pocket_welt       {len(welt)} pts, perimeter {ms.arc_len(welt)/10:.2f} cm")

    holes = sorted((c for c in thin_front if 40 < ms.arc_len(c) < 55
                    and ms.dist(c[0], c[-1]) < 3.0), key=lambda c: bbox(c)[1])
    assert len(holes) == 5, f"expected 5 buttonholes, found {len(holes)}"
    front_lm["buttonholes"] = [centre(c) for c in holes]
    print("    buttonholes      "
          + " ".join(f"({p[0]:.1f},{p[1]:.1f})" for p in front_lm["buttonholes"]))

    button = min((c for c in detail_front if 50 < ms.arc_len(c) < 60), key=ms.arc_len)
    front_lm["pocket_button"] = centre(button)
    pb = front_lm["pocket_button"]
    print(f"    pocket_button    ({pb[0]:.1f},{pb[1]:.1f})")

    collar_roll = find_through(part(thin, collar_fr, is_collar), (0.0, 10.0), (260.2, 45.1))
    assert collar_roll is not None, "collar roll line not found"
    collar_lines = {"roll": [[round(p[0], 2), round(p[1], 2)] for p in collar_roll]}
    print(f"    collar roll      cf {collar_roll[0][1]:.1f} -> cb {collar_roll[-1][1]:.1f} mm")

    return {
        "back": {"landmarks": back_lm,
                 "edges": take_edges(back_outline, back_lm, D_BACK_EDGES, "back"),
                 "lines": back_lines},
        "front": {"landmarks": front_lm,
                  "edges": take_edges(front_outline, front_lm, D_FRONT_EDGES, "front"),
                  "lines": front_lines},
        "collar": {"landmarks": collar_lm, "lines": collar_lines,
                   "outline": [[round(p[0], 2), round(p[1], 2)] for p in collar_outline]},
        "waistband": extract_waistband(page),
    }


def extract_waistband(page):
    """The waistband strip is drawn as a plain rectangle with its marks inside."""
    s = P14_BACK["scale"]
    band = None
    for dr in page.get_drawings():
        for it in dr["items"]:
            wide = it[0] == "re" and (dr.get("width") or 0) > 1.05 and it[1].width > 200
            if wide and (band is None or it[1].y0 < band.y0):
                band = it[1]
    tab = None
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "re" and 0.5 < (dr.get("width") or 0) < 1.0 and 30 < it[1].width < 45:
                tab = it[1]
    assert band is not None and tab is not None, "waistband/tab rectangles not found"

    def x_mm(x):
        return round((x - band.x0) / s * 10.0, 2)

    def y_mm(y):
        return round((y - band.y0) / s * 10.0, 2)

    # Notches are the only verticals that start on the top edge of the strip;
    # the buttons are the filled circles, the buttonhole a pair of hairlines.
    notches, holes = [], []
    for dr in page.get_drawings():
        w = dr.get("width") or 0.0
        for it in dr["items"]:
            if it[0] != "l" or w > 0.5:
                continue
            a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
            if not all(band.x0 - 1 < q[0] < band.x1 + 1 for q in (a, b)):
                continue
            if abs(a[0] - b[0]) < 0.3 and abs(min(a[1], b[1]) - band.y0) < 0.5:
                notches.append(x_mm(a[0]))
            elif (abs(a[1] - b[1]) < 0.3 and abs(a[0] - b[0]) > 8
                  and band.y0 < a[1] < band.y1):
                holes.append((min(a[0], b[0]), max(a[0], b[0]), a[1]))
    notches = sorted(set(round(x, 1) for x in notches))
    # The buttonhole is the only pair of hairlines sharing an x span; the rest
    # of the horizontals inside the strip are dimension lines.
    slot = [h for h in holes if sum(abs(h[0] - k[0]) < 0.5 and abs(h[1] - k[1]) < 0.5
                                    and abs(h[2] - k[2]) < 2.0 for k in holes) > 1]
    buttons = sorted({tuple(centre_pt(c, x_mm, y_mm)) for c in ms.merge_chains(
        [pts for _w, pts in ms.drawing_chains(page, *DETAIL)])
        if band.x0 < bbox(c)[0] and bbox(c)[2] < band.x1
        and band.y0 < bbox(c)[1] and bbox(c)[3] < band.y1
        and len(c) > 20})

    out = {
        "length_mm": round(band.width / s * 10.0, 2),
        "height_mm": round(band.height / s * 10.0, 2),
        "cf_from_edge_mm": notches[0],
        "notches_from_edge_mm": notches[1:],
        "tab_from_edge_mm": [x_mm(tab.x0), x_mm(tab.x1)],
        "tab_height_mm": round(tab.height / s * 10.0, 2),
        "buttons_mm": [list(b) for b in buttons],
        "buttonhole_from_edge_mm": [x_mm(min(h[0] for h in slot)),
                                    x_mm(max(h[1] for h in slot))],
    }
    print(f"  waistband: {out['length_mm']/10:.2f} x {out['height_mm']/10:.2f} cm; "
          f"c.f. {out['cf_from_edge_mm']}, notches {out['notches_from_edge_mm']}, "
          f"tab {out['tab_from_edge_mm']}, buttons {out['buttons_mm']}, "
          f"buttonhole {out['buttonhole_from_edge_mm']}")
    return out


# ---------------------------------------------------------------- page 15

D_SLEEVE_UPPER_LM = {
    "FST": (-27.5, 163.6), "FAN": (0.0, 132.0), "Sp": (111.4, 0.0), "Q": (202.9, 39.0),
    "U22": (219.0, 53.8), "F_b": (210.0, 378.0), "pivot": (190.3, 467.5),
    "hem_back": (157.5, 611.1), "hem_front": (-26.3, 580.0), "elbow_front": (-10.0, 378.0),
}
D_SLEEVE_UPPER_EDGES = [
    ("cap_front", "FST", "FAN"), ("cap", "FAN", "U22"), ("back_seam", "U22", "F_b"),
    ("back_fold", "F_b", "hem_back"), ("hem", "hem_back", "hem_front"),
    ("front_seam", "hem_front", "FST"),
]
D_SLEEVE_UNDER_LM = {
    "UST": (32.3, 158.8), "U2": (188.7, 53.9), "pivot": (190.1, 467.6),
    "hem_back": (157.3, 611.2), "hem_front": (33.6, 579.6), "elbow_front": (50.0, 378.0),
}
D_SLEEVE_UNDER_EDGES = [
    ("cap", "UST", "U2"), ("back_seam", "U2", "pivot"), ("back_fold", "pivot", "hem_back"),
    ("hem", "hem_back", "hem_front"), ("front_seam", "hem_front", "UST"),
]


def extract_design_sleeve(doc):
    """Design 4041 sleeve, page 15. The two pieces are drawn apart (the under
    sleeve mirrored), so each is registered onto the block frame through the two
    marks it shares with page 12."""
    print("\nPAGE 15 - Design 4041 sleeve")
    page = doc[14]
    raw = ms.merge_chains([pts for _w, pts in ms.drawing_chains(page, *NET)])
    raw.sort(key=ms.arc_len, reverse=True)
    upper_raw, under_raw = raw[0], raw[1]

    sim_up = ms.Similarity((361.12, 77.65), (111.4, 0.0), (308.47, 140.02), (0.0, 132.0))
    sim_un = ms.Similarity((443.45, 103.10), (188.7, 53.9), (517.34, 152.69), (32.3, 158.8),
                           mirror=True)
    for tag, sim in (("upper", sim_up), ("under", sim_un)):
        print(f"  {tag} registered at {sim.scale_pt_per_cm:.4f} pt/cm "
              f"(page scale {P15_SCALE})")
        assert abs(sim.scale_pt_per_cm - P15_SCALE) < 0.01

    upper = [sim_up.to_mm(p) for p in upper_raw]
    under = [sim_un.to_mm(p) for p in under_raw]
    upper_lm = take_landmarks(upper, D_SLEEVE_UPPER_LM, "upper")
    under_lm = take_landmarks(under, D_SLEEVE_UNDER_LM, "under")

    return {
        "upper": {"landmarks": upper_lm,
                  "edges": take_edges(upper, upper_lm, D_SLEEVE_UPPER_EDGES, "upper")},
        "under": {"landmarks": under_lm,
                  "edges": take_edges(under, under_lm, D_SLEEVE_UNDER_EDGES, "under")},
        "cuff": extract_cuff(page),
    }


def extract_cuff(page):
    """The cuff is drawn as a plain rectangle below the sleeves, with the
    buttonhole on the vent end and the button on the front end."""
    rect = None
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "re" and (dr.get("width") or 0) > 1.05 and it[1].width > 100:
                rect = it[1]
    assert rect is not None, "cuff rectangle not found"

    def x_mm(x):
        return round((x - rect.x0) / P15_SCALE * 10.0, 2)

    slot = []
    for dr in page.get_drawings():
        w = dr.get("width") or 0.0
        for it in dr["items"]:
            if it[0] != "l" or w > 0.5:
                continue
            a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
            inside = all(rect.x0 < q[0] < rect.x1 and rect.y0 < q[1] < rect.y1
                         for q in (a, b))
            if inside and abs(a[1] - b[1]) < 0.5 and abs(a[0] - b[0]) > 5:
                slot += [a[0], b[0]]
    button = min((c for c in ms.merge_chains(
        [pts for _w, pts in ms.drawing_chains(page, *DETAIL)])
        if rect.x0 < bbox(c)[0] and bbox(c)[2] < rect.x1
        and rect.y0 < bbox(c)[1] and bbox(c)[3] < rect.y1), key=ms.arc_len)

    out = {
        "length_mm": round(rect.width / P15_SCALE * 10.0, 2),
        "height_mm": round(rect.height / P15_SCALE * 10.0, 2),
        "buttonhole_from_edge_mm": [x_mm(min(slot)), x_mm(max(slot))],
        "button_from_edge_mm": x_mm((bbox(button)[0] + bbox(button)[2]) / 2),
    }
    print(f"  cuff: {out['length_mm']/10:.2f} x {out['height_mm']/10:.2f} cm, "
          f"buttonhole {out['buttonhole_from_edge_mm']}, button {out['button_from_edge_mm']}")
    return out


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_DEFAULT
    doc = fitz.open(pdf)
    data = {
        "source": {"pdf": pdf.name, "pages": [11, 12, 14, 15], "size": "50",
                   "measurements_cm": M},
        "units": "mm",
        "frames": {
            "body": "x=0 c.b., x toward the front, y=0 at N, y down (pages 11 and 14 back)",
            "sleeve": "x=0/y=0 at A, x toward the back of the sleeve (pages 12 and 15)",
            "design_front": "x=0 front pitch line, x toward the c.f., y=0 chest line (page 14)",
            "collar": "x=0 c.f., x toward the c.b. fold, y=0 baseline, y up (page 14)",
            "strip": "x from the left edge, y down from the top (waistband, cuff)",
        },
        "scales_pt_per_cm": {"p11": P11["scale"], "p12": P12["scale"],
                             "p14": P14_BACK["scale"], "p15": P15_SCALE},
    }
    data["body_block"] = extract_body_block(doc)
    data["sleeve_block"] = extract_sleeve_block(doc)
    data["design_body"] = extract_design_body(doc)
    data["design_sleeve"] = extract_design_sleeve(doc)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"\nwritten: {OUT_PATH}")


if __name__ == "__main__":
    main()
