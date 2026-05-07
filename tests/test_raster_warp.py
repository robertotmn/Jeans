import numpy as np
import pytest
from PIL import Image

from jeans_pattern.raster_warp import warp_raster_tps, RasterWarpResult


def _checkerboard(w: int, h: int) -> Image.Image:
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = 255
    cell = 32
    yy, xx = np.indices((h, w))
    mask = ((xx // cell + yy // cell) % 2 == 0)
    arr[mask, 0] = 255
    return Image.fromarray(arr, mode="RGBA")


def test_identity_warp_preserves_anchor_count():
    img = _checkerboard(200, 200)
    src = np.array([[10.0, 10.0], [190.0, 10.0], [190.0, 190.0], [10.0, 190.0]])
    tgt = src.copy() / 4   # mm = px/4 for a 1:1 mm:px scenario at ~100 DPI
    result = warp_raster_tps(img, src, tgt, src_roi_px=(0, 0, 200, 200), dpi=100, padding_mm=0)
    assert isinstance(result, RasterWarpResult)
    assert result.image.mode == "RGBA"
    assert result.bbox_mm[2] > result.bbox_mm[0]
    assert result.bbox_mm[3] > result.bbox_mm[1]


def test_anchor_count_mismatch_raises():
    img = _checkerboard(100, 100)
    src = np.array([[0, 0], [100, 0], [100, 100], [0, 100]])
    tgt = np.array([[0, 0], [10, 0], [10, 10]])    # only 3
    with pytest.raises(ValueError, match="anchor count mismatch"):
        warp_raster_tps(img, src, tgt, src_roi_px=(0, 0, 100, 100), dpi=100)


def test_too_few_anchors_raises():
    img = _checkerboard(100, 100)
    src = np.array([[0, 0], [100, 0], [50, 50]])
    tgt = src.copy() / 4
    with pytest.raises(ValueError, match=">=4 anchors"):
        warp_raster_tps(img, src, tgt, src_roi_px=(0, 0, 100, 100), dpi=100)


def test_outside_roi_pixels_become_transparent():
    img = _checkerboard(200, 200)
    src = np.array([[50.0, 50.0], [150.0, 50.0], [150.0, 150.0], [50.0, 150.0]])
    tgt = src.copy() / 4
    result = warp_raster_tps(img, src, tgt, src_roi_px=(50, 50, 150, 150), dpi=100, padding_mm=20)
    arr = np.array(result.image)
    assert arr.shape[2] == 4
    edges = np.concatenate([arr[0, :, 3], arr[-1, :, 3], arr[:, 0, 3], arr[:, -1, 3]])
    assert (edges == 0).any(), "expected some fully-transparent edge pixels outside ROI"


def test_output_size_scales_with_dpi():
    img = _checkerboard(200, 200)
    src = np.array([[20.0, 20.0], [180.0, 20.0], [180.0, 180.0], [20.0, 180.0]])
    tgt = np.array([[0.0, 0.0], [40.0, 0.0], [40.0, 40.0], [0.0, 40.0]])
    r100 = warp_raster_tps(img, src, tgt, src_roi_px=(0, 0, 200, 200), dpi=100, padding_mm=0)
    r200 = warp_raster_tps(img, src, tgt, src_roi_px=(0, 0, 200, 200), dpi=200, padding_mm=0)
    w100, h100 = r100.image.size
    w200, h200 = r200.image.size
    assert abs(w200 / w100 - 2.0) < 0.05
    assert abs(h200 / h100 - 2.0) < 0.05
