"""Extract size-50 reference geometry from the M&S "Jeans-Basics" PDF.

Pages 3 (basic block) and 5 (Design 3069) of the booklet are drawn TO SCALE
for size 50. This script measures them and freezes the result into
tests/data/ms_reference_size50.json so the draft tests have ground truth
without needing the PDF at test time.

All output coordinates are in the app frame: millimetres, x=0 at the front
base line (outseam side), y=0 at the waist line, y grows toward the hem.

Usage:  python scripts/extract_ms_reference.py [path-to-pdf]
"""
import json
import math
import sys
from pathlib import Path

import fitz

PDF_DEFAULT = Path("docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf")
OUT_PATH = Path("tests/data/ms_reference_size50.json")

# Size-50 chart (PDF page 2) used to locate the drawing frames.
M = dict(W=90.0, Hg=102.0, Kg=43.0, Hw=38.0, Os=102.0, Is=82.0)
FTW = M["Hg"] / 4                      # 25.5
FCW = M["Hg"] / 20                     # 5.1
KL = M["Is"] / 2 + M["Is"] / 10 - 2    # 47.2
HIP_ABOVE_CROTCH = M["Hg"] / 20 + 3    # 8.1
CREASE_X_CM = (FTW + FCW) / 2 - 2      # 13.3


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def sample_cubic(p0, p1, p2, p3, n=16):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t**3 * p3.y
        pts.append((x, y))
    return pts


def drawing_chains(page, min_w=0.0, max_w=99.0):
    """Sampled polylines for every stroked path with width in [min_w, max_w].
    Consecutive items of one path are joined when their endpoints touch."""
    chains = []
    for dr in page.get_drawings():
        w = dr.get("width") or 0.0
        if not (min_w <= w <= max_w):
            continue
        pts = []
        for it in dr["items"]:
            if it[0] == "l":
                seg = [(it[1].x, it[1].y), (it[2].x, it[2].y)]
            elif it[0] == "c":
                seg = sample_cubic(it[1], it[2], it[3], it[4])
            else:
                continue
            if pts and dist(pts[-1], seg[0]) < 0.6:
                pts.extend(seg[1:])
            elif not pts:
                pts = seg
            else:
                chains.append((w, pts))
                pts = seg
        if pts:
            chains.append((w, pts))
    return chains


def merge_chains(chains, tol=0.6):
    """Join chains whose endpoints coincide (any orientation)."""
    chains = [list(c) for c in chains]
    merged = True
    while merged:
        merged = False
        for i in range(len(chains)):
            for j in range(i + 1, len(chains)):
                a, b = chains[i], chains[j]
                if dist(a[-1], b[0]) < tol:
                    chains[i] = a + b[1:]
                elif dist(a[-1], b[-1]) < tol:
                    chains[i] = a + b[-2::-1]
                elif dist(a[0], b[-1]) < tol:
                    chains[i] = b + a[1:]
                elif dist(a[0], b[0]) < tol:
                    chains[i] = b[::-1] + a[1:]
                else:
                    continue
                del chains[j]
                merged = True
                break
            if merged:
                break
    return chains


def long_straight_lines(page):
    """(p1, p2, width) for every straight 'l' item on the page."""
    out = []
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                out.append(((it[1].x, it[1].y), (it[2].x, it[2].y), dr.get("width") or 0))
    return out


class Frame:
    """Maps PDF points to app frame (mm, x from front base line, y down from waist)."""

    def __init__(self, base_x, waist_y, scale_pt_per_cm):
        self.base_x = base_x
        self.waist_y = waist_y
        self.s = scale_pt_per_cm

    def to_mm(self, p):
        return ((p[0] - self.base_x) / self.s * 10.0, (p[1] - self.waist_y) / self.s * 10.0)

    def chain_mm(self, pts):
        return [self.to_mm(p) for p in pts]


def detect_frames(page):
    """Locate front and back drawing frames on page 3 via the long verticals."""
    lines = long_straight_lines(page)
    raw = [(min(a[1], b[1]), max(a[1], b[1]), (a[0] + b[0]) / 2)
           for a, b, _w in lines
           if abs(a[0] - b[0]) < 1.0 and abs(a[1] - b[1]) > 90]
    # Group collinear pieces (drawn split by labels) by x and union their spans.
    groups: dict[float, list[float]] = {}
    for y0, y1, x in raw:
        for gx in groups:
            if abs(gx - x) < 1.0:
                groups[gx][0] = min(groups[gx][0], y0)
                groups[gx][1] = max(groups[gx][1], y1)
                break
        else:
            groups[x] = [y0, y1]
    verts = [(y0, y1, x) for x, (y0, y1) in groups.items()]

    # Front: among the full-height verticals in the left half, find the
    # (base, crease) pair with crease - base == 13.3 cm at the scale implied
    # by the base span (dimension lines like "Sl 102" fail this relation).
    front_cands = sorted(v for v in verts if v[2] < 300 and v[1] - v[0] > 400)
    base = None
    for cand in front_cands:
        sc = (cand[1] - cand[0]) / M["Os"]
        for other in front_cands:
            if abs((other[2] - cand[2]) - CREASE_X_CM * sc) < 1.5:
                base = cand
                break
        if base:
            break
    assert base, f"front base line not found among {front_cands}"
    span = base[1] - base[0]
    scale = span / M["Os"]
    front = Frame(base[2], base[0], scale)

    # Back: the full-height vertical in the right half is the creaseline.
    back_cands = [v for v in verts if v[2] > 300 and v[1] - v[0] > 350]
    crease_b = max(back_cands, key=lambda v: v[1] - v[0])
    hem_b = crease_b[1]
    back = Frame(crease_b[2] - CREASE_X_CM * scale, hem_b - M["Os"] * scale, scale)

    # Sanity: front creaseline must sit at CREASE_X_CM from the base line.
    crease_f = [v for v in front_cands if abs(v[2] - (base[2] + CREASE_X_CM * scale)) < 2]
    assert crease_f, "front creaseline not found where expected"
    return front, back, scale


def nearest_vertex(chains, target, tol_cm=0.5, scale=None):
    """Nearest polyline vertex to target (pdf pts) among chains. Returns pdf point."""
    best, best_d = None, tol_cm * scale
    for _w, pts in chains:
        for p in pts:
            d = dist(p, target)
            if d < best_d:
                best, best_d = p, d
    return best


def chain_between(chains, a, b, tol=3.0):
    """Find a chain whose endpoints match a and b (pdf pts); return oriented a->b."""
    cands = []
    for _w, pts in chains:
        if dist(pts[0], a) < tol and dist(pts[-1], b) < tol:
            cands.append(pts)
        elif dist(pts[0], b) < tol and dist(pts[-1], a) < tol:
            cands.append(pts[::-1])
    return cands


def slice_chain(chains, a, b):
    """Slice a merged chain between the vertices nearest to a and b.
    Returns both direction candidates (for closed chains) as list of polylines."""
    out = []
    for _w, pts in chains:
        ia = min(range(len(pts)), key=lambda i: dist(pts[i], a))
        ib = min(range(len(pts)), key=lambda i: dist(pts[i], b))
        if dist(pts[ia], a) > 3 or dist(pts[ib], b) > 3:
            continue
        lo, hi = min(ia, ib), max(ia, ib)
        seg = pts[lo:hi + 1]
        if ia > ib:
            seg = seg[::-1]
        if len(seg) >= 2:
            out.append(seg)
        closed = dist(pts[0], pts[-1]) < 1.0
        if closed:
            other = pts[hi:] + pts[1:lo + 1]
            if ia < ib:
                other = other[::-1]
            if len(other) >= 2:
                out.append(other)
    return out


def arc_len(pts):
    return sum(dist(a, b) for a, b in zip(pts, pts[1:]))


def fmt(p):
    return f"({p[0]:7.1f},{p[1]:7.1f})"


def extract_page3(doc):
    page = doc[2]
    front_fr, back_fr, scale = detect_frames(page)
    print(f"scale: {scale:.4f} pt/cm   front base x={front_fr.base_x:.2f} waist y={front_fr.waist_y:.2f}")
    print(f"back frame: base x={back_fr.base_x:.2f} waist y={back_fr.waist_y:.2f}")

    thick = drawing_chains(page, min_w=1.0)          # pattern outlines
    mid = drawing_chains(page, min_w=0.5, max_w=0.99)  # yoke line, dashed measures
    thin = drawing_chains(page, min_w=0.0, max_w=0.49)  # construction lines

    def split(chains, left=True):
        res = []
        for w, pts in chains:
            xs = [p[0] for p in pts]
            mid_x = (min(xs) + max(xs)) / 2
            if (mid_x < 300) == left:
                res.append((w, pts))
        return res

    f_thick = merge_chains([pts for _w, pts in split(thick, True)])
    b_thick = merge_chains([pts for _w, pts in split(thick, False)])
    f_thick = [(1.2, c) for c in f_thick]
    b_thick = [(1.2, c) for c in b_thick]

    print(f"front thick chains: {len(f_thick)}  lens(cm): "
          f"{sorted(round(arc_len(c)/scale,1) for _w,c in f_thick)}")
    print(f"back thick chains:  {len(b_thick)}  lens(cm): "
          f"{sorted(round(arc_len(c)/scale,1) for _w,c in b_thick)}")

    s = scale

    def F(x_cm, y_cm_from_waist):
        """expected pdf point in front frame from cm coords (x from base, y down from waist)"""
        return (front_fr.base_x + x_cm * s, front_fr.waist_y + y_cm_from_waist * s)

    def B(x_cm, y_cm_from_waist):
        return (back_fr.base_x + x_cm * s, back_fr.waist_y + y_cm_from_waist * s)

    crotch_y = M["Br"] if "Br" in M else M["Os"] - M["Is"]   # 20 from waist
    knee_y = M["Os"] - KL                                     # 54.8
    hip_y = crotch_y - HIP_ABOVE_CROTCH                       # 11.9
    hem_y = M["Os"]
    crease = CREASE_X_CM

    # ---- FRONT landmarks (expected positions -> snap to drawn vertices) ----
    # Crotch point rule (verified on the drawing): the inseam guideline runs
    # from the knee inseam point to the Fcw point ON THE HIP LINE; the crotch
    # point is its intersection with the crotch line.
    knee_in_x = crease + (M["Kg"] / 4 - 0.5)
    fcw_x = FTW + FCW
    crotch_x = knee_in_x + (fcw_x - knee_in_x) * (knee_y - crotch_y) / (knee_y - hip_y)
    exp_front = {
        "waist_out": F(1.0, 0.0),
        "waist_cf": F(FTW - 1.5, 1.0),
        "crotch_pt": F(crotch_x, crotch_y),
        "knee_out": F(crease - (M["Kg"] / 4 - 0.5), knee_y),
        "knee_in": F(knee_in_x, knee_y),
        "hem_out": F(crease - (M["Hw"] / 4 - 0.5), hem_y),
        "hem_in": F(crease + (M["Hw"] / 4 - 0.5), hem_y),
    }
    front_lm = {}
    print("\nFRONT landmarks (mm, app frame):")
    for name, tgt in exp_front.items():
        v = nearest_vertex(f_thick, tgt, tol_cm=0.8, scale=s)
        if v is None:
            print(f"  {name}: NOT FOUND near expected {fmt(front_fr.to_mm(tgt))}")
            continue
        front_lm[name] = front_fr.to_mm(v)
        d = dist(v, tgt) / s * 10
        print(f"  {name:12s} {fmt(front_lm[name])}  (drawn vs formula: {d:5.1f} mm)")

    # Crotch-curve construction guides (thin lines, verified on the drawing):
    # d = horizontal distance on the crotch line from the c.f. VERTICAL (x=Ftw)
    # to the crotch point; half of d is transferred up along the c.f. vertical.
    f_thin = split(thin, True)
    front_meta = {"crease_x_mm": crease * 10.0,
                  "d_crotch_mm": front_lm["crotch_pt"][0] - FTW * 10.0}
    print(f"  d (crotch -> c.f. vertical) = {front_meta['d_crotch_mm']:.1f} mm")
    halfd_seg = chain_between(f_thin, F(FTW, crotch_y - (crotch_x - FTW) / 2),
                              F(crotch_x, crotch_y), tol=4.0)
    if halfd_seg:
        p = min(halfd_seg[0][0], halfd_seg[0][-1], key=lambda q: q[0])
        front_lm["halfd_pt"] = front_fr.to_mm(p)
        print(f"  halfd_pt     {fmt(front_lm['halfd_pt'])}")

    # ---- FRONT edges ----
    front_edges = {}
    edge_specs = [
        ("waist", "waist_out", "waist_cf"),
        ("cf_crotch", "waist_cf", "crotch_pt"),
        ("inseam_upper", "crotch_pt", "knee_in"),
        ("inseam_lower", "knee_in", "hem_in"),
        ("hem", "hem_in", "hem_out"),
        ("outseam_lower", "hem_out", "knee_out"),
        ("outseam_upper", "knee_out", "waist_out"),
    ]
    print("\nFRONT edges:")
    for name, a, b in edge_specs:
        if a not in front_lm or b not in front_lm:
            continue
        pa = (front_fr.base_x + front_lm[a][0] / 10 * s, front_fr.waist_y + front_lm[a][1] / 10 * s)
        pb = (front_fr.base_x + front_lm[b][0] / 10 * s, front_fr.waist_y + front_lm[b][1] / 10 * s)
        cands = chain_between(f_thick, pa, pb) or slice_chain(f_thick, pa, pb)
        if not cands:
            print(f"  {name}: NOT FOUND")
            continue
        best = min(cands, key=lambda c: arc_len(c))
        front_edges[name] = front_fr.chain_mm(best)
        print(f"  {name:14s} len={arc_len(best)/s:6.2f} cm  pts={len(best)}")

    # ---- BACK landmarks ----
    # Decoded expected values (cm, app frame = crease frame + 13.3)
    exp_back = {
        "hem_out": B(crease - 10.0, hem_y),
        "hem_in": B(crease + 10.0, hem_y),
        "knee_out": B(crease - (M["Kg"] / 4 - 0.5 + 1), knee_y),
        "knee_in": B(crease + (M["Kg"] / 4 - 0.5 + 1), knee_y),
        "crotch_pt": B(crease + 21.7, 102 - 80.0),
        "waist_out": B(crease - 15.4, 102 - 102.2),
        "cb_corner": B(crease + 8.0, 102 - 107.3),
        "cb_hip": B(crease + 12.7, hip_y),
        "dart1_a": B(crease - 8.0, 102 - 103.8),
        "dart1_tip": B(crease - 6.6, 102 - 99.25),
        "dart1_b": B(crease - 7.2, 102 - 103.95),
        "dart2_a": B(crease - 0.4, 102 - 105.44),
        "dart2_tip": B(crease + 1.43, 102 - 99.87),
        "dart2_b": B(crease + 0.77, 102 - 105.70),
    }
    back_lm = {}
    print("\nBACK landmarks (mm, app frame):")
    for name, tgt in exp_back.items():
        v = nearest_vertex(b_thick, tgt, tol_cm=0.7, scale=s)
        if v is None:
            print(f"  {name}: NOT FOUND near expected {fmt(back_fr.to_mm(tgt))}")
            continue
        back_lm[name] = back_fr.to_mm(v)
        d = dist(v, tgt) / s * 10
        print(f"  {name:12s} {fmt(back_lm[name])}  (drawn vs expected: {d:5.1f} mm)")

    # yoke line: the w=0.75 line
    b_mid = split(mid, False)
    yoke = None
    for _w, pts in b_mid:
        L = arc_len(pts) / s
        if 23 < L < 28 and abs(pts[0][1] - pts[-1][1]) < 3 * s:
            yoke = pts if pts[0][0] < pts[-1][0] else pts[::-1]
    if yoke:
        back_lm["yoke_out"] = back_fr.to_mm(yoke[0])
        back_lm["yoke_cb"] = back_fr.to_mm(yoke[-1])
        print(f"  yoke_out     {fmt(back_lm['yoke_out'])}")
        print(f"  yoke_cb      {fmt(back_lm['yoke_cb'])}")

    # thin construction landmarks: P_btw on hip line, slant point
    b_thin = split(thin, False)
    slant_cands = chain_between(b_thin, B(0.0, crotch_y - 1.0), B(crease + 12.7, hip_y), tol=4.0)
    if slant_cands:
        sl = slant_cands[0]
        back_lm["slant_p1"] = back_fr.to_mm(sl[0])
        back_lm["p_btw"] = back_fr.to_mm(sl[-1])
        print(f"  slant_p1     {fmt(back_lm['slant_p1'])}")
        print(f"  p_btw        {fmt(back_lm['p_btw'])}")

    # ---- BACK edges ----
    back_edges = {}
    back_specs = [
        ("hem", "hem_in", "hem_out"),
        ("outseam_lower", "hem_out", "knee_out"),
        ("outseam_upper", "knee_out", "waist_out"),
        ("waist", "waist_out", "cb_corner"),
        ("cb_seat", "cb_corner", "crotch_pt"),
        ("inseam_upper", "crotch_pt", "knee_in"),
        ("inseam_lower", "knee_in", "hem_in"),
    ]
    print("\nBACK edges:")
    for name, a, b in back_specs:
        if a not in back_lm or b not in back_lm:
            continue
        pa = (back_fr.base_x + back_lm[a][0] / 10 * s, back_fr.waist_y + back_lm[a][1] / 10 * s)
        pb = (back_fr.base_x + back_lm[b][0] / 10 * s, back_fr.waist_y + back_lm[b][1] / 10 * s)
        cands = chain_between(b_thick, pa, pb) or slice_chain(b_thick, pa, pb)
        if not cands:
            print(f"  {name}: NOT FOUND")
            continue
        best = min(cands, key=lambda c: arc_len(c))
        back_edges[name] = back_fr.chain_mm(best)
        print(f"  {name:14s} len={arc_len(best)/s:6.2f} cm  pts={len(best)}")
    if yoke:
        back_edges["yoke_line"] = back_fr.chain_mm(yoke)

    return {
        "front": {"landmarks": {k: list(v) for k, v in front_lm.items()},
                  "edges": front_edges, "meta": front_meta},
        "back": {"landmarks": {k: list(v) for k, v in back_lm.items()},
                 "edges": back_edges},
        "scale_pt_per_cm": scale,
    }


def chain_bbox(c):
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    return min(xs), min(ys), max(xs), max(ys)


def dedupe_shifted(chains):
    """Page 5 draws every element twice, the duplicate shifted ~17.7pt down.
    Keep the upper copy of each pair."""
    out = []
    for c in sorted(chains, key=lambda c: chain_bbox(c)[1]):
        dup = any(abs(arc_len(c) - arc_len(k)) < 2.0
                  and abs(chain_bbox(c)[0] - chain_bbox(k)[0]) < 2.5
                  and 15.0 < chain_bbox(c)[1] - chain_bbox(k)[1] < 20.5
                  for k in out)
        if not dup:
            out.append(c)
    return out


class Similarity:
    """2-point similarity map (rotation+scale+translation, optional mirror)
    from page-5 pdf coords to app mm coords."""

    def __init__(self, s1, t1, s2, t2, mirror=False):
        sz1, sz2 = complex(*s1), complex(*s2)
        tz1, tz2 = complex(*t1), complex(*t2)
        if mirror:
            sz1, sz2 = sz1.conjugate(), sz2.conjugate()
        self.a = (tz2 - tz1) / (sz2 - sz1)
        self.b = tz1 - self.a * sz1
        self.mirror = mirror

    def to_mm(self, p):
        z = complex(*p)
        if self.mirror:
            z = z.conjugate()
        w = self.a * z + self.b
        return (w.real, w.imag)

    @property
    def scale_pt_per_cm(self):
        return 10.0 / abs(self.a)


def extract_page5(doc, p3):
    """Design 3069 quotes: front pocket, back pocket, waistband."""
    page = doc[4]
    thick = dedupe_shifted(merge_chains([p for _w, p in drawing_chains(page, 1.0, 9)]))
    mid = dedupe_shifted(merge_chains([p for _w, p in drawing_chains(page, 0.5, 0.99)]))

    def in_box(c, box):
        x0, y0, x1, y1 = chain_bbox(c)
        return box[0] <= x0 and x1 <= box[2] and box[1] <= y0 and y1 <= box[3]

    design = {}

    # ---- FRONT piece (mirrored vs page 3: c.f. on the left) ----
    f_chains = [c for c in thick if in_box(c, (35, 215, 195, 510)) and arc_len(c) > 50]
    outline = max(f_chains, key=arc_len)
    top_y = chain_bbox(outline)[1]
    waist_band = [p for p in outline if p[1] < top_y + 15]
    cf5 = min(waist_band, key=lambda p: p[0])
    side5 = max(waist_band, key=lambda p: p[0])
    lm_f = p3["front"]["landmarks"]
    sim_f = Similarity(cf5, lm_f["waist_cf"], side5, lm_f["waist_out"], mirror=True)
    print(f"\nPAGE 5 front: waist chord {dist(cf5, side5) / sim_f.scale_pt_per_cm:.2f} cm "
          f"(p3: {dist(lm_f['waist_cf'], lm_f['waist_out']) / 10:.2f}) -> registered")

    # pocket opening + redrawn side seam: the open chain starting on the waist
    pocket_chain = None
    for c in f_chains:
        if c is outline or dist(c[0], c[-1]) < 1:
            continue
        ends = sorted([c[0], c[-1]], key=lambda p: p[1])
        if ends[0][1] < top_y + 12 and arc_len(c) > 150:
            pocket_chain = c if c[0][1] < c[-1][1] else c[::-1]
    assert pocket_chain is not None, "front pocket chain not found"
    # The chain is pocket-opening + redrawn side seam. The opening ends at the
    # entry point on the side seam = the max-x vertex (page frame, c.f. left).
    i_end = max(range(len(pocket_chain)), key=lambda i: pocket_chain[i][0])
    opening = pocket_chain[:i_end + 1]
    opening_mm = [sim_f.to_mm(p) for p in opening]
    # NOTE: the page-5 front illustration has ~2% scale slop and ~2.5 deg of
    # inconsistency between grainline and waist slope; the drawn curve is kept
    # as a SHAPE reference, the printed quotes are authoritative.
    design["front_pocket"] = {
        "drawn_approx": True,
        "opening_chain_app": [list(p) for p in opening_mm],
        "opening_start_app": list(opening_mm[0]),
        "opening_end_app": list(opening_mm[-1]),
        "printed_quotes_mm": {"along_waist_span": 120, "side_depth": 80,
                              "entry_extension": 6, "bag_length_approx": 240},
    }
    print(f"  pocket opening: start {fmt(opening_mm[0])} end {fmt(opening_mm[-1])} "
          f"span {dist(opening_mm[0], opening_mm[-1]) / 10:.1f} cm")

    # ---- BACK piece (same orientation as page 3) ----
    b_chains = [c for c in thick if in_box(c, (215, 225, 410, 495)) and arc_len(c) > 50]
    outline_b = max(b_chains, key=arc_len)
    top_yb = chain_bbox(outline_b)[1]
    band_b = [p for p in outline_b if p[1] < top_yb + 15]
    l5 = min(band_b, key=lambda p: p[0])
    r5 = max(band_b, key=lambda p: p[0])
    lm_b = p3["back"]["landmarks"]
    sim_b = Similarity(l5, lm_b["yoke_out"], r5, lm_b["yoke_cb"], mirror=False)
    print(f"back: yoke chord {dist(l5, r5) / sim_b.scale_pt_per_cm:.2f} cm "
          f"(p3: {dist(lm_b['yoke_out'], lm_b['yoke_cb']) / 10:.2f}) -> registered")

    pocket_b = [c for c in mid if in_box(c, (215, 225, 410, 495))
                and dist(c[0], c[-1]) < 1 and 250 < arc_len(c) < 330]
    assert pocket_b, "back pocket pentagon not found"
    verts = [sim_b.to_mm(p) for p in pocket_b[0][:-1]]
    # order: top-left, top-right, right-bottom, point, left-bottom (as drawn)
    verts_sorted = sorted(verts, key=lambda p: p[1])
    top_l, top_r = sorted(verts_sorted[:2], key=lambda p: p[0])
    point = max(verts, key=lambda p: p[1])
    others = [v for v in verts if v not in (top_l, top_r, point)]
    bot_l, bot_r = sorted(others, key=lambda p: p[0])
    # placement relative to yoke line, c.b. seam and grainline (crease x)
    yo, yc = lm_b["yoke_out"], lm_b["yoke_cb"]
    yoke_dir = ((yc[0] - yo[0]), (yc[1] - yo[1]))
    yoke_len = math.hypot(*yoke_dir)
    yoke_u = (yoke_dir[0] / yoke_len, yoke_dir[1] / yoke_len)

    def below_yoke(p):
        v = (p[0] - yo[0], p[1] - yo[1])
        return v[1] * yoke_u[0] - v[0] * yoke_u[1]   # perpendicular distance, +down

    crease_x = p3["front"]["meta"]["crease_x_mm"]
    design["back_pocket"] = {
        "corners_app": {"top_left": list(top_l), "top_right": list(top_r),
                        "bottom_left": list(bot_l), "bottom_right": list(bot_r),
                        "point": list(point)},
        "placement_mm": {
            "top_left_below_yoke": round(below_yoke(top_l), 1),
            "top_right_below_yoke": round(below_yoke(top_r), 1),
            "point_axis_offset_from_crease": round(point[0] - crease_x, 1),
        },
    }
    print(f"  back pocket: top {dist(top_l, top_r) / 10:.2f} cm, "
          f"center len {dist(midpt(top_l, top_r), point) / 10:.2f} cm")
    print(f"    corners: TL{fmt(top_l)} TR{fmt(top_r)} BL{fmt(bot_l)} BR{fmt(bot_r)} P{fmt(point)}")
    print(f"    below yoke: TL {below_yoke(top_l):.1f} mm, TR {below_yoke(top_r):.1f} mm; "
          f"point axis offset from crease {point[0] - crease_x:+.1f} mm")

    # ---- WAISTBAND (top strip, drawn in true size: 45 x 4 cm) ----
    s3 = p3["scale_pt_per_cm"]
    band = None
    for dr in page.get_drawings():
        r = dr["rect"]
        if (dr.get("width") or 0) > 1.05 and r.y1 < 165 and r.width > 180:
            band = r
            break
    assert band is not None, "waistband rect not found"
    marks = []
    for dr in page.get_drawings():
        w = dr.get("width") or 0
        for it in dr["items"]:
            if it[0] != "l":
                continue
            a, b = (it[1].x, it[1].y), (it[2].x, it[2].y)
            if abs(a[0] - b[0]) < 0.6 and abs(a[1] - b[1]) > 2.5 \
                    and band.y0 - 1.5 < min(a[1], b[1]) and max(a[1], b[1]) < band.y1 + 1.5 \
                    and band.x0 + 2 < a[0] < band.x1 - 2:
                marks.append((round((a[0] - band.x0) / s3 * 10, 1), round(w, 2)))
    marks = sorted(set(marks))
    # 0.8-width full-height pairs 1.2 cm apart = belt loops; the rest = notches
    loops, notches, i = [], [], 0
    while i < len(marks):
        x, w = marks[i]
        if w >= 0.5 and i + 1 < len(marks) and marks[i + 1][1] >= 0.5 \
                and 10 <= marks[i + 1][0] - x <= 14:
            loops.append((x, round(marks[i + 1][0] - x, 1)))
            i += 2
        else:
            notches.append(x)
            i += 1
    length_mm = round(band.width / s3 * 10, 1)

    def nearest(cands, target, tol):
        hits = [x for x in cands if abs(x - target) < tol]
        return round(min(hits, key=lambda x: abs(x - target)), 1) if hits else None

    ss = nearest(notches, dist(lm_f["waist_cf"], lm_f["waist_out"]), 8)
    pocket_notch = nearest(notches, 100, 8)
    cb_loop_edge = nearest(notches, length_mm - 6, 10)
    design["waistband"] = {
        "length_mm": length_mm,
        "height_mm": round(band.height / s3 * 10, 1),
        "ss_notch_from_cf_mm": ss,
        "pocket_notch_from_cf_mm": pocket_notch,
        "belt_loops_from_cf_mm": loops,
        "cb_loop_edge_from_cf_mm": cb_loop_edge,
    }
    print(f"waistband: {length_mm / 10:.1f} x {design['waistband']['height_mm'] / 10:.1f} cm; "
          f"Ss notch {ss}, pocket notch {pocket_notch}, loops {loops}, cb loop edge {cb_loop_edge}")
    return design


def midpt(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_DEFAULT
    doc = fitz.open(pdf)
    data = {
        "source": {"pdf": pdf.name, "pages": [3, 5], "size": "50", "measurements_cm": M},
        "units": "mm, app frame: x=0 front base line, y=0 waist line, y down",
    }
    data.update(extract_page3(doc))
    data["design"] = extract_page5(doc, data)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"\nwritten: {OUT_PATH}")


if __name__ == "__main__":
    main()
