import pytest

from jeans_pattern.draft_mueller import MuellerMeasurements
from jeans_pattern.draft_mueller_extras import (
    build_mueller_waistband, build_mueller_belt_loop, build_mueller_zipper_fly,
    build_mueller_front_pocket, build_mueller_back_pocket, build_mueller_yoke,
)


@pytest.fixture
def m_size50():
    return MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )


def test_waistband_dimensions(m_size50):
    wb = build_mueller_waistband(m_size50)
    width = max(p.x for p in wb.outline) - min(p.x for p in wb.outline)
    height = max(p.y for p in wb.outline) - min(p.y for p in wb.outline)
    # 90 cm waist + 4 cm fly extension + ~2*0.95 cm SA
    assert width == pytest.approx(900 + 40 + 2 * 9.525, abs=1)
    # 4 cm + 2*SA
    assert height == pytest.approx(40 + 2 * 9.525, abs=1)


def test_belt_loop_dimensions():
    bl = build_mueller_belt_loop()
    width = max(p.x for p in bl.outline) - min(p.x for p in bl.outline)
    height = max(p.y for p in bl.outline) - min(p.y for p in bl.outline)
    assert width == pytest.approx(60.0)
    assert height == pytest.approx(48.0)   # 1.2 cm x 4


def test_zipper_fly_returns_two_pieces(m_size50):
    pieces = build_mueller_zipper_fly(m_size50)
    assert "shield" in pieces and "facing" in pieces
    assert pieces["shield"].name == "fly_shield"
    assert pieces["facing"].name == "fly_facing"


def test_front_pocket_returns_two_pieces(m_size50):
    pieces = build_mueller_front_pocket(m_size50)
    assert "pocket_bag" in pieces and "pocket_facing" in pieces
    bag_h = max(p.y for p in pieces["pocket_bag"].outline)
    assert bag_h == pytest.approx(240.0)   # 24 cm


def test_back_pocket_dimensions(m_size50):
    bp = build_mueller_back_pocket(m_size50)
    width = max(p.x for p in bp.outline) - min(p.x for p in bp.outline)
    assert width == pytest.approx(170.0)   # 17 cm at top


def test_yoke_seam_allowance(m_size50):
    yk = build_mueller_yoke(m_size50)
    from jeans_pattern.constants import SA_5_8_IN_MM
    assert yk.seam_allowance_mm == pytest.approx(SA_5_8_IN_MM)
