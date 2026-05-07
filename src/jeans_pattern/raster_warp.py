"""Raster TPS warp.

Warps a region of a source PIL image so that named pixel anchors land at
target millimetre coordinates. Uses the inverse-mapping + bilinear-sampling
recipe so the output canvas is filled densely without holes.

The source is the M&S diagram raster bundled in templates/. The TPS solver is
the same pure-numpy implementation used by the vector mueller2 system.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from .warp import tps_solve, tps_apply


MM_PER_INCH = 25.4


@dataclass(frozen=True)
class RasterWarpResult:
    image: Image.Image
    bbox_mm: tuple[float, float, float, float]
    dpi: float


def _output_bbox_mm(target_anchors_mm: np.ndarray, padding_mm: float) -> tuple[float, float, float, float]:
    xs = target_anchors_mm[:, 0]
    ys = target_anchors_mm[:, 1]
    return (
        float(xs.min()) - padding_mm,
        float(ys.min()) - padding_mm,
        float(xs.max()) + padding_mm,
        float(ys.max()) + padding_mm,
    )


def _bilinear_sample(src: np.ndarray, src_xy: np.ndarray, roi: tuple[int, int, int, int]) -> np.ndarray:
    """Sample src (H, W, C) at fractional coords src_xy (M, 2). Returns (M, C) uint8 RGBA.

    Pixels whose source coord falls outside roi (x0, y0, x1, y1) get alpha=0.
    """
    H, W = src.shape[:2]
    x = src_xy[:, 0]
    y = src_xy[:, 1]

    x0_f = np.floor(x)
    y0_f = np.floor(y)
    fx = (x - x0_f).astype(np.float32)
    fy = (y - y0_f).astype(np.float32)
    x0 = x0_f.astype(np.int32)
    y0 = y0_f.astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1

    in_roi = (x >= roi[0]) & (x <= roi[2] - 1) & (y >= roi[1]) & (y <= roi[3] - 1)

    x0c = np.clip(x0, 0, W - 1)
    x1c = np.clip(x1, 0, W - 1)
    y0c = np.clip(y0, 0, H - 1)
    y1c = np.clip(y1, 0, H - 1)

    p00 = src[y0c, x0c].astype(np.float32)
    p01 = src[y0c, x1c].astype(np.float32)
    p10 = src[y1c, x0c].astype(np.float32)
    p11 = src[y1c, x1c].astype(np.float32)

    fx2 = fx[:, None]
    fy2 = fy[:, None]
    out = (1 - fx2) * (1 - fy2) * p00 + fx2 * (1 - fy2) * p01 + (1 - fx2) * fy2 * p10 + fx2 * fy2 * p11
    out = np.clip(out, 0, 255).astype(np.uint8)

    if out.shape[1] >= 4:
        alpha = out[:, 3].copy()
        alpha[~in_roi] = 0
        out[:, 3] = alpha
    else:
        rgba = np.concatenate([out, np.full((out.shape[0], 1), 255, dtype=np.uint8)], axis=1)
        rgba[~in_roi, 3] = 0
        out = rgba

    return out


def warp_raster_tps(
    src_image: Image.Image,
    src_anchors_px: np.ndarray,
    tgt_anchors_mm: np.ndarray,
    src_roi_px: tuple[int, int, int, int],
    dpi: float = 100.0,
    padding_mm: float = 5.0,
    chunk_rows: int = 256,
) -> RasterWarpResult:
    """Warp src_image so each src_anchors_px maps to the matching tgt_anchors_mm.

    Args:
        src_image: PIL Image (any mode; converted to RGBA internally).
        src_anchors_px: (N, 2) anchor pixel coords in src_image (x, y, top-left origin).
        tgt_anchors_mm: (N, 2) target anchor coords in mm (app coords; y grows down).
        src_roi_px: (x0, y0, x1, y1) — sample region inside src_image. Pixels outside
            this rectangle become fully transparent in the output.
        dpi: output raster resolution. 100 keeps memory modest; 150-200 sharper.
        padding_mm: extra mm added to the output bbox on every side so warped lines
            near the edge of the anchor convex hull aren't clipped.
        chunk_rows: number of output rows processed per vectorised chunk. Trades
            wall time for peak memory.

    Returns:
        RasterWarpResult(image=..., bbox_mm=(x0, y0, x1, y1) in app coords, dpi=dpi).
    """
    src_anchors_px = np.asarray(src_anchors_px, dtype=float)
    tgt_anchors_mm = np.asarray(tgt_anchors_mm, dtype=float)
    if src_anchors_px.shape != tgt_anchors_mm.shape:
        raise ValueError(
            f"anchor count mismatch: {src_anchors_px.shape} vs {tgt_anchors_mm.shape}"
        )
    if src_anchors_px.shape[0] < 4:
        raise ValueError(
            f"need >=4 anchors for stable TPS, got {src_anchors_px.shape[0]}"
        )

    bbox_mm = _output_bbox_mm(tgt_anchors_mm, padding_mm=padding_mm)
    x0_mm, y0_mm, x1_mm, y1_mm = bbox_mm
    px_per_mm = dpi / MM_PER_INCH
    W_out = max(1, int(round((x1_mm - x0_mm) * px_per_mm)))
    H_out = max(1, int(round((y1_mm - y0_mm) * px_per_mm)))

    W, A = tps_solve(tgt_anchors_mm, src_anchors_px)

    src = np.array(src_image.convert("RGBA"))
    out = np.zeros((H_out, W_out, 4), dtype=np.uint8)

    cols = np.arange(W_out, dtype=np.float64)
    x_mm_row = x0_mm + (cols + 0.5) / px_per_mm

    for r0 in range(0, H_out, chunk_rows):
        r1 = min(H_out, r0 + chunk_rows)
        rows_local = np.arange(r0, r1, dtype=np.float64)
        y_mm_col = y0_mm + (rows_local + 0.5) / px_per_mm
        gx, gy = np.meshgrid(x_mm_row, y_mm_col, indexing="xy")
        coords_mm = np.stack([gx.ravel(), gy.ravel()], axis=1)

        src_xy = tps_apply(coords_mm, tgt_anchors_mm, W, A)
        sampled = _bilinear_sample(src, src_xy, src_roi_px)
        out[r0:r1] = sampled.reshape(r1 - r0, W_out, 4)

    image = Image.fromarray(out, mode="RGBA")
    return RasterWarpResult(image=image, bbox_mm=bbox_mm, dpi=dpi)
