"""Overlay the generated size-50 draft on the booklet's own scale drawing.

Draws the reference geometry (extracted from PDF page 3 into
tests/data/ms_reference_size50.json) in RED and the generated draft in BLUE
into verification_ms_size50.pdf at 1:1 scale, and prints the per-edge maximum
deviations. Exits non-zero if any deviation exceeds the thresholds, so it can
run as a gate.

Usage:  python scripts/verify_ms_overlay.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from jeans_pattern.draft_ms import draft_back, draft_front
from jeans_pattern.geometry import Point
from jeans_pattern.measurements import Measurements

REF_PATH = Path(__file__).resolve().parents[1] / "tests" / "data" / "ms_reference_size50.json"
OUT_PATH = Path(__file__).resolve().parents[1] / "verification_ms_size50.pdf"

LANDMARK_TOL_MM = 2.5
CURVE_TOL_MM = 3.0

EDGE_MAP = {
    "front": [
        ("waist", ["waist"]),
        ("cf_crotch", ["cf_crotch"]),
        ("inseam", ["inseam_upper", "inseam_lower"]),
        ("hem", ["hem"]),
        ("outseam", ["outseam_lower", "outseam_upper"]),
    ],
    "back": [
        ("cb_seat", ["cb_seat"]),
        ("inseam", ["inseam_upper", "inseam_lower"]),
        ("hem", ["hem"]),
        ("outseam", ["outseam_lower", "outseam_upper"]),
    ],
}


def max_dev(gen: list[Point], ref: list[Point]) -> float:
    def d_pt(p):
        best = float("inf")
        for a, b in zip(ref, ref[1:]):
            vx, vy = b.x - a.x, b.y - a.y
            l2 = vx * vx + vy * vy
            if l2 < 1e-12:
                continue
            t = max(0.0, min(1.0, ((p.x - a.x) * vx + (p.y - a.y) * vy) / l2))
            best = min(best, math.hypot(p.x - a.x - t * vx, p.y - a.y - t * vy))
        return best
    return max(d_pt(p) for p in gen)


def main() -> int:
    ref = json.loads(REF_PATH.read_text(encoding="utf-8"))
    chart = ref["source"]["measurements_cm"]
    m = Measurements.from_cm(
        waistband=chart["W"], hip_girth=chart["Hg"], knee_girth=chart["Kg"],
        hem_width=chart["Hw"], outseam=chart["Os"], inseam=chart["Is"],
    )
    front = draft_front(m)
    back = draft_back(m, front)
    drafts = {"front": front, "back": back}

    # layout: both sides share the app frame; back extends left of x=0
    all_x = [p[0] for side in ("front", "back") for e in ref[side]["edges"].values() for p in e]
    all_y = [p[1] for side in ("front", "back") for e in ref[side]["edges"].values() for p in e]
    x0, x1 = min(all_x) - 30, max(all_x) + 30
    y0, y1 = min(all_y) - 30, max(all_y) + 30
    w_mm, h_mm = x1 - x0, y1 - y0

    c = canvas.Canvas(str(OUT_PATH), pagesize=(w_mm * mm, h_mm * mm))

    def draw(pts, rgb, width=0.4):
        c.setStrokeColorRGB(*rgb)
        c.setLineWidth(width * mm)
        path = c.beginPath()
        path.moveTo((pts[0][0] - x0) * mm, (y1 - pts[0][1]) * mm)
        for p in pts[1:]:
            path.lineTo((p[0] - x0) * mm, (y1 - p[1]) * mm)
        c.drawPath(path)

    failures = []
    print(f"{'side':6s} {'edge':10s} {'dev mm':>8s}")
    for side, mapping in EDGE_MAP.items():
        for ref_name, ref_pts in ref[side]["edges"].items():
            draw(ref_pts, (0.85, 0.1, 0.1))
        for gen_name, ref_names in mapping:
            gen = drafts[side].edge(gen_name)
            ref_pts = [Point(*p) for name in ref_names for p in ref[side]["edges"][name]]
            dev = max_dev(gen, ref_pts)
            status = "" if dev <= CURVE_TOL_MM else "  <-- FAIL"
            print(f"{side:6s} {gen_name:10s} {dev:8.2f}{status}")
            if dev > CURVE_TOL_MM:
                failures.append((side, gen_name, dev))
            draw([(p.x, p.y) for p in gen], (0.1, 0.2, 0.9))

    # back waist + yoke line (generated only, book waist includes darts)
    draw([(p.x, p.y) for p in back.waist_line], (0.1, 0.2, 0.9))
    draw([(p.x, p.y) for p in back.yoke_line], (0.1, 0.2, 0.9))
    for d in back.darts:
        draw([(d.a.x, d.a.y), (d.tip.x, d.tip.y), (d.b.x, d.b.y)], (0.1, 0.2, 0.9), 0.25)
    for pts in (ref["back"]["edges"].get("yoke_line"), ref["back"]["edges"].get("waist")):
        if pts:
            draw(pts, (0.85, 0.1, 0.1), 0.25)

    # landmarks
    worst_lm = 0.0
    for side in ("front", "back"):
        for name, xy in ref[side]["landmarks"].items():
            gen_lm = drafts[side].landmarks.get(name)
            book = Point(*xy)
            if gen_lm is None:
                continue
            dev = math.hypot(gen_lm.x - book.x, gen_lm.y - book.y)
            worst_lm = max(worst_lm, dev)
            if dev > LANDMARK_TOL_MM:
                failures.append((side, f"landmark {name}", dev))
            c.setStrokeColorRGB(0.85, 0.1, 0.1)
            c.setLineWidth(0.2 * mm)
            bx, by = (book.x - x0) * mm, (y1 - book.y) * mm
            c.line(bx - 2 * mm, by, bx + 2 * mm, by)
            c.line(bx, by - 2 * mm, bx, by + 2 * mm)

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(10 * mm, 8 * mm,
                 f"ROSSO = libro M&S (taglia 50)  BLU = generato  |  "
                 f"landmark max {worst_lm:.2f} mm  |  {'OK' if not failures else 'FAIL'}")
    c.showPage()
    c.save()
    print(f"\nlandmark worst: {worst_lm:.2f} mm")
    print(f"written: {OUT_PATH}")
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
