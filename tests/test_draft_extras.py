import pytest
from jeans_pattern.draft_extras import (
    build_waistband, build_belt_loop, build_button_fly,
    build_front_pocket, build_back_pocket, build_yoke,
)

INCH = 25.4

def test_waistband_dimensions(default_measurements):
    wb = build_waistband(default_measurements)
    width = max(p.x for p in wb.outline) - min(p.x for p in wb.outline)
    height = max(p.y for p in wb.outline) - min(p.y for p in wb.outline)
    # waist + 1-3/8" fly stand + 3/8" SA x 2
    assert width == pytest.approx((34.5 + 1.375 + 0.375 * 2) * INCH, abs=0.5)
    # 1-1/2" finished + 3/8" SA x 2
    assert height == pytest.approx((1.5 + 0.375 * 2) * INCH, abs=0.5)
    assert wb.name == "waistband"

def test_belt_loop_dimensions():
    bl = build_belt_loop()
    w = max(p.x for p in bl.outline) - min(p.x for p in bl.outline)
    h = max(p.y for p in bl.outline) - min(p.y for p in bl.outline)
    # 3" length x 1-1/4" pre-fold strip
    assert w == pytest.approx(3.0 * INCH, abs=0.5)
    assert h == pytest.approx(1.25 * INCH, abs=0.5)
    assert bl.name == "belt_loop"

def test_front_pocket_returns_two_pieces(default_measurements):
    pieces = build_front_pocket(default_measurements)
    assert "pocket_bag" in pieces
    assert "pocket_facing" in pieces
    assert pieces["pocket_bag"].name == "pocket_bag"
    assert pieces["pocket_facing"].name == "pocket_facing"

def test_yoke_basic(default_measurements):
    yk = build_yoke(default_measurements)
    h = max(p.y for p in yk.outline) - min(p.y for p in yk.outline)
    # 1-1/2" finished + 5/8" SA x 2 ~ 2.75"
    assert h == pytest.approx(1.5 * INCH + 0.625 * 2 * INCH, abs=2)
    assert yk.name == "yoke"

def test_back_pocket(default_measurements):
    bp = build_back_pocket(default_measurements)
    w = max(p.x for p in bp.outline) - min(p.x for p in bp.outline)
    # 3-3/8" finished width
    assert w == pytest.approx(3.375 * INCH, abs=2)
    assert bp.name == "back_pocket"

def test_button_fly_two_pieces(default_measurements):
    pieces = build_button_fly(default_measurements)
    assert "buttonhole_side" in pieces
    assert "button_stand" in pieces
    assert pieces["buttonhole_side"].name == "fly_buttonhole_side"
    assert pieces["button_stand"].name == "fly_button_stand"
