"""One-shot extraction: read M&S Jeans-Basics PDF page 3 and produce
templates/mueller_template.json.

Run with the venv python:
    .venv/Scripts/python.exe scripts/extract_mueller_template.py

The PDF path can be overridden via PDF_PATH env var. Default is
`C:/Users/rober/Downloads/Metric-pattern-techniques_Jeans-Basics (1).pdf`.

PDF coordinate system in PyMuPDF: y grows DOWN (top-left origin), units
are PDF points (72/inch). We KEEP these coordinates in the JSON. The
runtime warp will map them to user-measurement-derived positions in mm.
"""
import json
import os
import sys
from pathlib import Path

import fitz   # PyMuPDF

PDF_DEFAULT = r"C:\Users\rober\Downloads\Metric-pattern-techniques_Jeans-Basics (1).pdf"
PDF_PATH = os.environ.get("PDF_PATH", PDF_DEFAULT)
PAGE_INDEX = 2   # Page 3 (0-indexed)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "templates" / "mueller_template.json"

FRONT_X_LIMIT = 300.0   # text labels with bbox.x < 300 = FRONT region
                         # (verified empirically: front piece spans ~70-280, back ~310-560)


def sample_bezier(p0, p1, p2, p3, n=20):
    """Sample a cubic Bezier with N points (endpoints included)."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append([x, y])
    return pts


def path_to_polyline(items):
    """Convert PyMuPDF drawing items to a flat polyline (list of [x, y])."""
    poly = []
    for it in items:
        kind = it[0]
        if kind == "l":   # line: ('l', p1, p2)
            p1, p2 = it[1], it[2]
            poly.append([p1.x, p1.y])
            poly.append([p2.x, p2.y])
        elif kind == "c":   # cubic Bezier: ('c', p1, p2, p3, p4)
            p1, p2, p3, p4 = it[1], it[2], it[3], it[4]
            poly.extend(sample_bezier(
                [p1.x, p1.y], [p2.x, p2.y], [p3.x, p3.y], [p4.x, p4.y], n=20
            ))
        elif kind == "re":   # rectangle: ('re', rect)
            r = it[1]
            poly.append([r.x0, r.y0])
            poly.append([r.x1, r.y0])
            poly.append([r.x1, r.y1])
            poly.append([r.x0, r.y1])
            poly.append([r.x0, r.y0])
        elif kind == "qu":   # quadrilateral: ('qu', quad)
            q = it[1]
            for p in [q.ul, q.ur, q.lr, q.ll, q.ul]:
                poly.append([p.x, p.y])
        # Skip "h" (close path) and others
    return poly


def extract_labels(page):
    """Return list of (text, x_center, y_center, bbox)."""
    labels = []
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text or len(text) > 30:
                    continue
                bb = span["bbox"]
                cx = (bb[0] + bb[2]) / 2
                cy = (bb[1] + bb[3]) / 2
                labels.append({
                    "text": text,
                    "x": cx, "y": cy,
                    "bbox": [bb[0], bb[1], bb[2], bb[3]],
                })
    return labels


def assign_region(labels, paths):
    """Split labels into front (x < FRONT_X_LIMIT) and back (x >= FRONT_X_LIMIT).
    Same for paths (use bbox center)."""
    front_labels = [l for l in labels if l["x"] < FRONT_X_LIMIT]
    back_labels = [l for l in labels if l["x"] >= FRONT_X_LIMIT]

    front_paths = []
    back_paths = []
    for poly in paths:
        if not poly:
            continue
        xs = [p[0] for p in poly]
        cx = sum(xs) / len(xs)
        if cx < FRONT_X_LIMIT:
            front_paths.append(poly)
        else:
            back_paths.append(poly)
    return (front_labels, back_labels), (front_paths, back_paths)


def derive_anchors(labels):
    """Heuristic: extract named anchors from label text. Some labels are values
    (e.g. 'Ftw 25.5'), some are markers (e.g. 'A', 'c.f.', 'c.b.'). We use the
    LABEL POSITION as the anchor coordinate.

    For values like 'Ftw 25.5', the anchor name is 'Ftw' and the position is
    the label center (the label sits NEXT TO the actual point on the diagram,
    typically slightly offset; runtime can correct via target-formula offset).
    """
    anchors = {}
    for lab in labels:
        text = lab["text"]
        # Strip numeric values from anchor names: "Ftw 25.5" -> "Ftw"
        # Skip pure numbers (1, 1.5, 0.5, etc.) and fractions (1/3, 1/2)
        first_word = text.split()[0] if text.split() else text
        # Anchor name patterns we care about:
        if first_word in {"A", "Ftw", "Fcw", "Btw", "Bcw", "Kl", "Is", "Sl", "c.f.", "c.b."}:
            anchors[first_word] = [lab["x"], lab["y"]]
        elif first_word == "Check":
            # "Check 1/4" - special: skip (it's a verification annotation)
            pass
        elif first_word == "1/10":
            # "1/10 1/2 Hg +3" - hip depth marker; we'll call this anchor "hip_depth"
            anchors["hip_depth"] = [lab["x"], lab["y"]]
        elif first_word == "measure":
            anchors["measure_arrow"] = [lab["x"], lab["y"]]
        elif first_word == "transfer":
            anchors["transfer_arrow"] = [lab["x"], lab["y"]]
        # Generic catch-all for diagrammatic markers
        # Keep simple to start; refine later if needed
    return anchors


def main():
    print(f"Reading PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    page = doc[PAGE_INDEX]
    print(f"Page {PAGE_INDEX + 1}: {page.rect.width:.1f} x {page.rect.height:.1f} pt")

    # Extract paths
    drawings = page.get_drawings()
    print(f"Vector paths in page: {len(drawings)}")
    paths = []
    for d in drawings:
        items = d.get("items", [])
        poly = path_to_polyline(items)
        if len(poly) >= 2:
            paths.append(poly)
    print(f"Polylines extracted: {len(paths)}")

    # Extract labels
    labels = extract_labels(page)
    print(f"Text labels: {len(labels)}")

    # Split into front/back
    (front_labels, back_labels), (front_paths, back_paths) = assign_region(labels, paths)
    print(f"Front: {len(front_paths)} paths, {len(front_labels)} labels")
    print(f"Back:  {len(back_paths)} paths, {len(back_labels)} labels")

    # Derive anchors per region
    front_anchors = derive_anchors(front_labels)
    back_anchors = derive_anchors(back_labels)
    print(f"Front anchors: {sorted(front_anchors.keys())}")
    print(f"Back anchors:  {sorted(back_anchors.keys())}")

    # Build template JSON
    template = {
        "source": {
            "pdf": Path(PDF_PATH).name,
            "page": PAGE_INDEX + 1,
            "size": "50",
            "measurements_cm": {
                "waistband": 90.0, "hip_girth": 102.0, "knee_girth": 43.0,
                "hem_width": 38.0, "outseam": 102.0, "inseam": 82.0,
            },
        },
        "coordinate_units": "pdf_points",
        "front": {
            "paths": front_paths,
            "labels": front_labels,
            "anchors": front_anchors,
        },
        "back": {
            "paths": back_paths,
            "labels": back_labels,
            "anchors": back_anchors,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"\nWritten: {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    sys.exit(main() or 0)
