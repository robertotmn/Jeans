"""Mueller & Sohn 3: raster template-based drafting.

Identical anchor layout and target formulas to mueller2, but the underlying
diagram is a bundled raster image (templates/mueller3_template.png) rather
than vector polylines extracted from the PDF. The TPS warp is applied to the
image pixels and the output is a (lossy) raster of the same draft scaled and
shaped to the user's measurements.

Use this when faithful reproduction of the original M&S diagram annotations
(labels, hatching, dimension markers) matters more than vector cleanness.
"""
from __future__ import annotations

import functools
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .draft_mueller import MuellerMeasurements
from .draft_mueller2 import _front_anchor_targets as _mueller2_front_targets
from .draft_mueller2 import _back_anchor_targets as _mueller2_back_targets
from .geometry import Point
from .raster_warp import warp_raster_tps


TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
ANCHORS_PATH = TEMPLATES_DIR / "mueller3_anchors.json"


@functools.lru_cache(maxsize=1)
def load_anchors() -> dict:
    with open(ANCHORS_PATH, encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def load_image() -> Image.Image:
    cfg = load_anchors()
    img_path = TEMPLATES_DIR / cfg["image"]
    return Image.open(img_path).convert("RGBA")


@dataclass(frozen=True)
class Mueller3Piece:
    """Warped raster piece with anchors in mm.

    bbox_mm: (x0, y0, x1, y1) in app coordinates (y down) — the full extent
    of the warped output canvas, with the piece occupying it.
    """

    image: Image.Image
    bbox_mm: tuple[float, float, float, float]
    anchors: dict[str, Point]
    dpi: float

    def labeled_points(self) -> dict[str, Point]:
        return self.anchors


def _front_anchor_targets(m: MuellerMeasurements) -> dict[str, tuple[float, float]]:
    return _mueller2_front_targets(m)


def _back_anchor_targets(m: MuellerMeasurements) -> dict[str, tuple[float, float]]:
    """Extend mueller2's back targets with hem corners so the raster warp
    covers the full back trouser length. mueller2's set stops near hip because
    its vector polyline warp can extrapolate the hem; for raster the bbox is
    derived from target anchors and would otherwise truncate the piece.

    Coords match draft_mueller's back frame (origin at outseam-waist, x grows
    toward c.b., y grows down).
    """
    base = dict(_mueller2_back_targets(m))
    Btw = m.back_trouser_width_mm
    Hw = m.hem_width_mm
    back_hem_width = (Hw / 2 - 5.0) + 20.0     # 1/2 Hw - 0.5 cm + 1 cm extra back/side (2 cm total back/front)
    hem_y = m.outseam_mm
    base["B_hem_outseam"] = (Btw - back_hem_width, hem_y)
    base["B_hem_inseam"] = (Btw, hem_y)
    return base


def _common_anchors(
    src: dict[str, list[float]],
    tgt: dict[str, tuple[float, float]],
) -> tuple[list[str], np.ndarray, np.ndarray]:
    keys = sorted(set(src) & set(tgt))
    if len(keys) < 4:
        raise ValueError(
            f"need >=4 common anchors for TPS, got {len(keys)}: {keys}"
        )
    src_arr = np.array([src[k] for k in keys], dtype=float)
    tgt_arr = np.array([tgt[k] for k in keys], dtype=float)
    return keys, src_arr, tgt_arr


def _build_piece(
    section_name: str,
    target_anchors_mm: dict[str, tuple[float, float]],
    dpi: float,
) -> Mueller3Piece:
    cfg = load_anchors()
    section = cfg[section_name]
    src_px = section["anchors_px"]
    roi_px = tuple(section["roi_px"])

    keys, src_arr, tgt_arr = _common_anchors(src_px, target_anchors_mm)
    img = load_image()
    result = warp_raster_tps(
        src_image=img,
        src_anchors_px=src_arr,
        tgt_anchors_mm=tgt_arr,
        src_roi_px=roi_px,
        dpi=dpi,
    )
    anchors = {k: Point(*target_anchors_mm[k]) for k in target_anchors_mm}
    return Mueller3Piece(
        image=result.image,
        bbox_mm=result.bbox_mm,
        anchors=anchors,
        dpi=result.dpi,
    )


def build_mueller3_front(m: MuellerMeasurements, dpi: float = 100.0) -> Mueller3Piece:
    """Build the warped raster front piece for the given measurements."""
    return _build_piece("front", _front_anchor_targets(m), dpi=dpi)


def build_mueller3_back(m: MuellerMeasurements, dpi: float = 100.0) -> Mueller3Piece:
    """Build the warped raster back piece for the given measurements."""
    return _build_piece("back", _back_anchor_targets(m), dpi=dpi)
