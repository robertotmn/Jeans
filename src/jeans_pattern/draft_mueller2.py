"""Mueller & Sohn 2: template-based drafting.

Loads the M&S diagram (extracted as polylines from PDF page 3 to
templates/mueller_template.json), computes target anchor positions from the
user's MuellerMeasurements, and warps the template via Thin-Plate Spline so
the named landmarks sit where the formulas dictate.

Output format matches the rest of the app (Point objects, list[Point] outline).
"""
from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .draft_mueller import MuellerMeasurements
from .geometry import Point
from .warp import tps_solve, tps_apply


TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "templates" / "mueller_template.json"
)


@functools.lru_cache(maxsize=1)
def load_template() -> dict:
    """Load and cache the M&S template JSON."""
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        return json.load(f)


# Anchor target formulas. Each takes MuellerMeasurements and returns (x_mm, y_mm)
# in app coordinates (y=0 at waist, y grows DOWN).
def _front_anchor_targets(m: MuellerMeasurements) -> dict[str, tuple[float, float]]:
    Os, Is, hip_depth = m.outseam_mm, m.inseam_mm, m.hip_depth_mm
    Kl = m.knee_length_mm
    Ftw = m.front_trouser_width_mm
    Fcw = m.front_crotch_width_mm
    hip_y = Os - Is - hip_depth
    crotch_y = Os - Is
    knee_y = Os - Kl
    hem_y = Os
    return {
        "A": (0.0, hem_y),
        "Ftw": (Ftw, hip_y),
        "Fcw": (Ftw + Fcw, hip_y),
        "Is": (0.0, crotch_y),
        "Kl": (0.0, knee_y),
        "Sl": (0.0, 0.0),
        "c.f.": (Ftw * 0.5, 0.0),
        "hip_depth": (0.0, hip_y),
    }


def _back_anchor_targets(m: MuellerMeasurements) -> dict[str, tuple[float, float]]:
    Os, Is, hip_depth = m.outseam_mm, m.inseam_mm, m.hip_depth_mm
    Kl = m.knee_length_mm
    Btw = m.back_trouser_width_mm
    Bcw = m.back_crotch_width_mm
    hip_y = Os - Is - hip_depth
    knee_y = Os - Kl
    return {
        "Btw": (Btw, hip_y),
        "Bcw": (Btw + Bcw, hip_y),
        "c.b.": (Btw + Bcw, -35.0),     # raised 3.5 cm above waist
        "measure_arrow": (Btw * 0.3, knee_y),
        "transfer_arrow": (Btw * 0.7, knee_y - 50.0),
    }


@dataclass(frozen=True)
class Mueller2FrontPoints:
    """Front pattern derived from the warped M&S template."""
    paths: tuple[tuple[Point, ...], ...]
    outline: tuple[Point, ...]
    anchors: dict[str, Point]

    def labeled_points(self) -> dict[str, Point]:
        return self.anchors

    def outline_polygon(self) -> list[Point]:
        return list(self.outline)


@dataclass(frozen=True)
class Mueller2BackPoints:
    paths: tuple[tuple[Point, ...], ...]
    outline: tuple[Point, ...]
    anchors: dict[str, Point]

    def labeled_points(self) -> dict[str, Point]:
        return self.anchors

    def outline_polygon(self) -> list[Point]:
        return list(self.outline)


def _polyline_bbox_area(poly) -> float:
    if not poly:
        return 0.0
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (max(xs) - min(xs)) * (max(ys) - min(ys))


def _identify_outline_path(paths: list[list[list[float]]]) -> int:
    """Return the index of the path most likely to be the cut outline.
    Heuristic: largest bbox area among paths with >= 10 points (the cut
    outline is sampled densely from PDF curves; tiny markers and arrows
    have only a few points)."""
    candidates = [(i, _polyline_bbox_area(p)) for i, p in enumerate(paths) if len(p) >= 10]
    if not candidates:
        # fallback: any path with >= 4 points
        candidates = [(i, _polyline_bbox_area(p)) for i, p in enumerate(paths) if len(p) >= 4]
    if not candidates:
        return -1
    candidates.sort(key=lambda x: -x[1])
    return candidates[0][0]


def _simplify_polyline(poly: list[Point], tolerance_mm: float = 1.0) -> list[Point]:
    """Drop near-duplicate consecutive points."""
    if not poly:
        return poly
    out = [poly[0]]
    for p in poly[1:]:
        if abs(p.x - out[-1].x) > tolerance_mm or abs(p.y - out[-1].y) > tolerance_mm:
            out.append(p)
    return out


def _build_piece(
    template_section: dict,
    target_anchors: dict[str, tuple[float, float]],
) -> tuple[tuple[tuple[Point, ...], ...], tuple[Point, ...], dict[str, Point]]:
    """Apply TPS warp to all paths in a template section (front or back).

    Returns (warped_paths, outline_polygon, warped_anchors).
    """
    src_anchors = template_section["anchors"]
    paths = template_section["paths"]

    # Common anchor keys
    common_keys = sorted(set(src_anchors) & set(target_anchors))
    if len(common_keys) < 4:
        raise ValueError(
            f"Need at least 4 common anchors for TPS, got {len(common_keys)}: {common_keys}"
        )

    src = np.array([src_anchors[k] for k in common_keys])
    tgt = np.array([target_anchors[k] for k in common_keys])

    W, A = tps_solve(src, tgt)

    # Warp every path
    warped_paths = []
    for poly in paths:
        if not poly:
            continue
        coords = np.array(poly)
        warped = tps_apply(coords, src, W, A)
        warped_pts = tuple(Point(float(x), float(y)) for x, y in warped)
        warped_paths.append(warped_pts)

    # Identify the outline path (largest bbox in warped space, dense polyline)
    outline_idx = _identify_outline_path(
        [[(p.x, p.y) for p in path] for path in warped_paths]
    )
    if outline_idx < 0:
        raise ValueError("Could not identify outline path")
    outline_raw = list(warped_paths[outline_idx])
    outline = tuple(_simplify_polyline(outline_raw, tolerance_mm=1.0))

    # Warped anchor positions (just the target positions, since they ARE the targets)
    warped_anchors = {k: Point(*xy) for k, xy in target_anchors.items()}

    return tuple(warped_paths), outline, warped_anchors


def build_mueller2_front(m: MuellerMeasurements) -> Mueller2FrontPoints:
    template = load_template()
    target_anchors = _front_anchor_targets(m)
    paths, outline, anchors = _build_piece(template["front"], target_anchors)
    return Mueller2FrontPoints(paths=paths, outline=outline, anchors=anchors)


def build_mueller2_back(m: MuellerMeasurements) -> Mueller2BackPoints:
    template = load_template()
    target_anchors = _back_anchor_targets(m)
    paths, outline, anchors = _build_piece(template["back"], target_anchors)
    return Mueller2BackPoints(paths=paths, outline=outline, anchors=anchors)
