"""Overlay the generated size-50 jacket draft on the booklet's own scale drawings.

Draws the reference geometry (extracted from PDF pages 11, 12 and 14 into
tests/data/ms_jacket_reference_size50.json) in RED and the generated draft in
BLUE into verification_jacket_size50.pdf at 1:1 scale, and prints the per-item
maximum deviations. Exits non-zero if any deviation exceeds the thresholds, so
it can run as a gate.

Four panels: the body block (page 11), the sleeve block (page 12), the Design
4041 body (page 14, step 1) and the convertible collar (page 14, step 2).

Usage:  python scripts/verify_jacket_overlay.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from jeans_pattern.draft_jacket import (
    draft_jacket_back, draft_jacket_front, draft_jacket_sleeve)
from jeans_pattern.draft_jacket_design import build_collar, design_body
from jeans_pattern.measurements_jacket import JacketMeasurements

REF_PATH = Path(__file__).resolve().parents[1] / "tests" / "data" / "ms_jacket_reference_size50.json"
OUT_PATH = Path(__file__).resolve().parents[1] / "verification_jacket_size50.pdf"

LANDMARK_TOL_MM = 2.5
CURVE_TOL_MM = 3.0
PANEL_GAP_MM = 70.0

# Documented exceptions (plan "Emendamenti dalla calibrazione", size-50 values).
# E4.2: the drawn buttonhole slot reaches 0.55 cm past the c.f., so the marks
# sit that far off the c.f. the booklet prescribes; the y placement - the part
# the booklet actually quotes - stays inside the landmark tolerance.
BUTTONHOLE_TOL_MM = 6.0
BUTTONHOLE_ITEMS = {f"button{i}" for i in range(1, 6)}
# D19/E4.7: the front panel seams are extended 1 cm up to the yoke line to close
# the three panels, while the drawing stops them on the pocket entry line. The
# extension is collinear, so these two are measured book-to-generated.
REVERSED_ITEMS = {"panel_cf", "panel_side"}


def tolerance(name: str, default: float) -> float:
    if name in BUTTONHOLE_ITEMS:
        return BUTTONHOLE_TOL_MM
    return default


def max_dev(gen, ref) -> float:
    """Max over the points of `gen` of the distance to the polyline `ref`."""
    def d_pt(p):
        best = float("inf")
        for a, b in zip(ref, ref[1:]):
            vx, vy = b[0] - a[0], b[1] - a[1]
            l2 = vx * vx + vy * vy
            if l2 < 1e-12:
                continue
            t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2))
            best = min(best, math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy))
        return best
    return max(d_pt(p) for p in gen)


def main() -> int:
    ref = json.loads(REF_PATH.read_text(encoding="utf-8"))
    chart = ref["source"]["measurements_cm"]
    m = JacketMeasurements.from_cm(
        body_height=chart["Bh"], chest_girth=chart["Cg"], waist_girth=chart["Wg"],
        hip_girth=chart["Hg"], sleeve_length=chart["Sl"],
    )
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    sleeve = draft_jacket_sleeve(m, back, front)
    db = design_body(back, front)
    collar = build_collar(db)
    collar_edges = dict(collar.edges)

    def pts(seq):
        return [(p.x, p.y) for p in seq]

    # page 14 draws the front in a frame of its own (x on the pitch line, y on
    # the chest line); the collar frame has y pointing up.
    x_pitch, sd = front.landmarks["P_top"].x, m.scye_depth_mm

    def to_body(p):
        return (p[0] + x_pitch, p[1] + sd)

    def flip(p):
        return (p[0], -p[1])

    block, sleeve_ref = ref["body_block"], ref["sleeve_block"]
    design, collar_ref = ref["design_body"], ref["design_body"]["collar"]

    panels = []

    # ---- panel 1: body block (page 11) -------------------------------------
    curves, marks, gen_only = [], [], []
    for side, draft in (("back", back), ("front", front)):
        for name, ref_pts in block[side]["edges"].items():
            curves.append((f"{side} {name}", pts(draft.edge(name)), ref_pts))
        for name, xy in block[side]["landmarks"].items():
            if name in draft.landmarks:
                marks.append((name, (draft.landmarks[name].x, draft.landmarks[name].y), tuple(xy)))
    panels.append(("blocco corpo (p. 11)", curves, marks, gen_only))

    # ---- panel 2: sleeve block (page 12) -----------------------------------
    curves, marks, gen_only = [], [], []
    for part in ("upper", "under"):
        for name, ref_pts in sleeve_ref[part]["edges"].items():
            if name == "back_fold" and part == "under":
                continue        # not extracted: it runs on top of the upper fold
            curves.append((f"{part} {name}", pts(sleeve.edge(part, name)), ref_pts))
        for name, xy in sleeve_ref[part]["landmarks"].items():
            if name in sleeve.landmarks:
                marks.append((name, (sleeve.landmarks[name].x, sleeve.landmarks[name].y), tuple(xy)))
    panels.append(("blocco manica (p. 12)", curves, marks, gen_only))

    # ---- panel 3: Design 4041 body (page 14, step 1) -----------------------
    curves, marks, gen_only = [], [], []
    for name, ours in (("neck", "neck"), ("shoulder", "shoulder"),
                       ("armhole", "armhole"), ("side", "side"),
                       ("hem", "waistband_seam"), ("cb", "fold_cb")):
        curves.append((f"dietro {name}", pts(db.edge("back", ours)),
                       design["back"]["edges"][name]))
    for name, ours in (("yoke", "yoke_back"), ("panel_seam", "panel_back")):
        curves.append((f"dietro {name}", pts(db.lines[ours]),
                       design["back"]["lines"][name]))
    for name, ours in (("neck_overlap", "neck_overlap"), ("neck", "neck"),
                       ("shoulder", "shoulder"), ("armhole", "armhole"),
                       ("side", "side"), ("hem", "waistband_seam")):
        curves.append((f"davanti {name}", pts(db.edge("front", ours)),
                       [to_body(p) for p in design["front"]["edges"][name]]))
    for name, ours in (("yoke", "yoke_front"), ("cf", "cf"),
                       ("placket_topstitch", "placket"),
                       ("pintuck_inner", "pintuck_inner"),
                       ("pintuck_outer", "pintuck_outer"),
                       ("panel_seam_cf", "panel_cf"),
                       ("panel_seam_side", "panel_side"),
                       ("pocket_opening", "pocket_opening"),
                       ("pocket_flap", "pocket_flap"), ("pocket_bag", "pocket_bag"),
                       ("pocket_axis", "pocket_axis"),
                       ("side_pocket_welt", "side_pocket_welt")):
        # the drawing carries only the 12 cm entry line of the chest pocket,
        # while our mark closes the 1 cm welt rectangle around it
        ours_pts = pts(db.lines[ours])[:2] if ours == "pocket_opening" else pts(db.lines[ours])
        curves.append((ours, ours_pts,
                       [to_body(p) for p in design["front"]["lines"][name]]))
    for ours, name in (("neck_cb", "neck_cb"), ("neck_shoulder_b", "neck_shoulder"),
                       ("hem_cb", "hem_cb"), ("side_hem_b", "side_hem"), ("BAN", "BAN")):
        marks.append((ours, (db.landmarks[ours].x, db.landmarks[ours].y),
                      tuple(design["back"]["landmarks"][name])))
    for ours, name in (("neck_cf", "neck_cf"), ("edge_top", "edge_top"),
                       ("neck_shoulder_f", "neck_shoulder"), ("hem_cf", "hem_cf"),
                       ("edge_hem", "hem_edge"), ("side_hem_f", "side_hem")):
        marks.append((ours, (db.landmarks[ours].x, db.landmarks[ours].y),
                      to_body(design["front"]["landmarks"][name])))
    for i, p in enumerate(design["front"]["landmarks"]["buttonholes"], start=1):
        marks.append((f"button{i}", (db.landmarks[f"button{i}"].x, db.landmarks[f"button{i}"].y),
                      to_body(p)))
    gen_only.append(pts(db.lines["fold_edge"]))
    gen_only.append(pts(db.lines["pocket_opening"]))
    panels.append(("design 4041 corpo (p. 14)", curves, marks, gen_only))

    # ---- panel 4: convertible collar (page 14, step 2) ---------------------
    outline = [flip(p) for p in collar_ref["outline"]]
    curves = [(f"colletto {name}", [flip(p) for p in pts(collar_edges[name])], outline)
              for name in ("neck_seam", "fold_cb", "outer", "front")]
    curves.append(("colletto roll", [flip(p) for p in pts(collar.construction_lines[0])],
                   [flip(p) for p in collar_ref["lines"]["roll"]]))
    panels.append(("colletto (p. 14)", curves, [], []))

    # ---- layout: panels side by side, each on its own bbox -----------------
    origins, x_cursor, y_lo, y_hi = [], 0.0, [], []
    for _title, curves, marks, gen_only in panels:
        all_pts = [p for _n, g, r in curves for p in g + [tuple(q) for q in r]]
        all_pts += [p for _n, g, r in marks for p in (g, r)]
        all_pts += [p for line in gen_only for p in line]
        x0 = min(p[0] for p in all_pts)
        origins.append(x_cursor - x0)
        x_cursor += max(p[0] for p in all_pts) - x0 + PANEL_GAP_MM
        y_lo.append(min(p[1] for p in all_pts))
        y_hi.append(max(p[1] for p in all_pts))

    margin = 25.0
    w_mm = x_cursor - PANEL_GAP_MM + 2 * margin
    y0, y1 = min(y_lo) - margin, max(y_hi) + margin + 15.0
    h_mm = y1 - y0

    c = canvas.Canvas(str(OUT_PATH), pagesize=(w_mm * mm, h_mm * mm))

    def draw(points, dx, rgb, width=0.4):
        c.setStrokeColorRGB(*rgb)
        c.setLineWidth(width * mm)
        path = c.beginPath()
        path.moveTo((points[0][0] + dx + margin) * mm, (y1 - points[0][1]) * mm)
        for p in points[1:]:
            path.lineTo((p[0] + dx + margin) * mm, (y1 - p[1]) * mm)
        c.drawPath(path)

    def cross(p, dx, rgb):
        c.setStrokeColorRGB(*rgb)
        c.setLineWidth(0.2 * mm)
        bx, by = (p[0] + dx + margin) * mm, (y1 - p[1]) * mm
        c.line(bx - 2 * mm, by, bx + 2 * mm, by)
        c.line(bx, by - 2 * mm, bx, by + 2 * mm)

    red, blue = (0.85, 0.1, 0.1), (0.1, 0.2, 0.9)
    failures = []
    headroom = (float("inf"), "")      # smallest margin left on any tolerance
    for (title, curves, marks, gen_only), dx in zip(panels, origins):
        print(f"\n== {title} ==")
        print(f"{'item':28s} {'dev mm':>8s}")
        for name, gen, ref_pts in curves:
            ref_pts = [tuple(p) for p in ref_pts]
            dev = (max_dev(ref_pts, gen) if name in REVERSED_ITEMS
                   else max_dev(gen, ref_pts))
            tol = tolerance(name, CURVE_TOL_MM)
            print(f"{name:28s} {dev:8.2f}{'' if dev <= tol else '  <-- FAIL'}")
            headroom = min(headroom, (tol - dev, name))
            if dev > tol:
                failures.append((title, name, dev, tol))
            draw(ref_pts, dx, red)
            draw(gen, dx, blue)
        for line in gen_only:
            draw(line, dx, blue)
        for name, gen, ref_pt in marks:
            dev = math.hypot(gen[0] - ref_pt[0], gen[1] - ref_pt[1])
            tol = tolerance(name, LANDMARK_TOL_MM)
            print(f"{'* ' + name:28s} {dev:8.2f}{'' if dev <= tol else '  <-- FAIL'}")
            headroom = min(headroom, (tol - dev, name))
            if dev > tol:
                failures.append((title, name, dev, tol))
            cross(ref_pt, dx, red)
            cross(gen, dx, blue)
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0, 0, 0)
        c.drawString((dx + margin) * mm, (y1 - min(y_lo) + 12.0) * mm, title)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin * mm, 8 * mm,
                 f"ROSSO = libro M&S (taglia 50)  BLU = generato  |  "
                 f"margine minimo {headroom[0]:.2f} mm su {headroom[1]}  |  "
                 f"{'OK' if not failures else 'FAIL'}")
    c.showPage()
    c.save()
    print(f"\nmargine minimo sulle soglie: {headroom[0]:.2f} mm ({headroom[1]})")
    print(f"written: {OUT_PATH}")
    if failures:
        print("FAILURES:")
        for title, name, dev, tol in failures:
            print(f"  {title} / {name}: {dev:.2f} mm > {tol:.1f} mm")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
