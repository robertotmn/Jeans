import pytest
from PIL import Image

from jeans_pattern.draft_mueller import MuellerMeasurements
from jeans_pattern.draft_mueller3 import (
    build_mueller3_front, build_mueller3_back,
    Mueller3Piece, load_anchors, load_image,
    _front_anchor_targets, _back_anchor_targets,
)


@pytest.fixture
def m_size50():
    return MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )


@pytest.fixture
def m_size38():
    return MuellerMeasurements.from_cm(
        waistband=72, hip_girth=88, knee_girth=37, hem_width=33,
        outseam=98, inseam=78,
    )


def test_anchors_json_loads():
    cfg = load_anchors()
    assert "front" in cfg and "back" in cfg
    assert "anchors_px" in cfg["front"]
    assert "roi_px" in cfg["front"]
    assert len(cfg["front"]["anchors_px"]) >= 4


def test_template_image_loads():
    img = load_image()
    assert isinstance(img, Image.Image)
    cfg = load_anchors()
    assert list(img.size) == cfg["image_size_px"]


def test_front_anchor_targets_match_anchor_keys(m_size50):
    cfg = load_anchors()
    targets = _front_anchor_targets(m_size50)
    src_keys = set(cfg["front"]["anchors_px"])
    assert len(src_keys & set(targets)) >= 4


def test_back_anchor_targets_include_hem(m_size50):
    targets = _back_anchor_targets(m_size50)
    assert "B_hem_outseam" in targets
    assert "B_hem_inseam" in targets
    hem_y = targets["B_hem_outseam"][1]
    assert hem_y == m_size50.outseam_mm


def test_build_front_returns_piece(m_size50):
    p = build_mueller3_front(m_size50, dpi=72)
    assert isinstance(p, Mueller3Piece)
    assert isinstance(p.image, Image.Image)
    assert p.image.mode == "RGBA"
    x0, y0, x1, y1 = p.bbox_mm
    assert x1 > x0
    assert y1 > y0
    assert "A" in p.anchors


def test_build_back_returns_piece(m_size50):
    p = build_mueller3_back(m_size50, dpi=72)
    assert isinstance(p, Mueller3Piece)
    assert p.image.mode == "RGBA"
    assert "Btw" in p.anchors
    assert "B_hem_outseam" in p.anchors


def test_back_bbox_covers_full_outseam_length(m_size50):
    p = build_mueller3_back(m_size50, dpi=72)
    _, y0, _, y1 = p.bbox_mm
    assert (y1 - y0) >= m_size50.outseam_mm * 0.95


def test_smaller_size_produces_smaller_image(m_size38, m_size50):
    p38 = build_mueller3_front(m_size38, dpi=72)
    p50 = build_mueller3_front(m_size50, dpi=72)
    w38 = p38.bbox_mm[2] - p38.bbox_mm[0]
    w50 = p50.bbox_mm[2] - p50.bbox_mm[0]
    assert w38 < w50


def test_output_image_dimensions_match_bbox(m_size50):
    p = build_mueller3_front(m_size50, dpi=72)
    px_per_mm = p.dpi / 25.4
    bbox_w_mm = p.bbox_mm[2] - p.bbox_mm[0]
    bbox_h_mm = p.bbox_mm[3] - p.bbox_mm[1]
    expected_w = round(bbox_w_mm * px_per_mm)
    expected_h = round(bbox_h_mm * px_per_mm)
    assert abs(p.image.width - expected_w) <= 1
    assert abs(p.image.height - expected_h) <= 1
