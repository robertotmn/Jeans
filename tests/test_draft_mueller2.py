import pytest
from shapely.geometry import Polygon

from jeans_pattern.draft_mueller import MuellerMeasurements
from jeans_pattern.draft_mueller2 import (
    build_mueller2_front, build_mueller2_back,
    Mueller2FrontPoints, Mueller2BackPoints,
    load_template,
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


@pytest.fixture
def m_size60():
    return MuellerMeasurements.from_cm(
        waistband=110, hip_girth=120, knee_girth=50, hem_width=44,
        outseam=106, inseam=86,
    )


def test_template_loads():
    t = load_template()
    assert "front" in t and "back" in t
    assert "paths" in t["front"]
    assert "anchors" in t["front"]
    assert len(t["front"]["paths"]) > 0


def test_front_returns_mueller2front(m_size50):
    f = build_mueller2_front(m_size50)
    assert isinstance(f, Mueller2FrontPoints)
    assert len(f.outline) >= 4
    assert len(f.paths) > 0
    assert "Ftw" in f.anchors


def test_back_returns_mueller2back(m_size50):
    b = build_mueller2_back(m_size50)
    assert isinstance(b, Mueller2BackPoints)
    assert len(b.outline) >= 4
    assert "Btw" in b.anchors
    assert "c.b." in b.anchors


def test_front_anchors_at_target_positions(m_size50):
    f = build_mueller2_front(m_size50)
    # Anchors are placed exactly at the target formulas
    assert f.anchors["A"].x == pytest.approx(0.0)
    assert f.anchors["A"].y == pytest.approx(m_size50.outseam_mm)   # 1020 mm
    assert f.anchors["Ftw"].x == pytest.approx(m_size50.front_trouser_width_mm)
    # Sl is the waist level = (0, 0)
    assert f.anchors["Sl"].x == pytest.approx(0.0)
    assert f.anchors["Sl"].y == pytest.approx(0.0)


def test_back_centre_back_raised(m_size50):
    b = build_mueller2_back(m_size50)
    # c.b. is raised 3.5 cm above waist line
    assert b.anchors["c.b."].y == pytest.approx(-35.0)


def test_outline_is_simple_polygon_size50(m_size50):
    f = build_mueller2_front(m_size50)
    poly = Polygon([(p.x, p.y) for p in f.outline])
    assert poly.is_simple, "front outline must be simple after warp"

    b = build_mueller2_back(m_size50)
    poly = Polygon([(p.x, p.y) for p in b.outline])
    assert poly.is_simple, "back outline must be simple after warp"


def test_outline_is_simple_polygon_size38(m_size38):
    f = build_mueller2_front(m_size38)
    poly = Polygon([(p.x, p.y) for p in f.outline])
    assert poly.is_simple

    b = build_mueller2_back(m_size38)
    poly = Polygon([(p.x, p.y) for p in b.outline])
    assert poly.is_simple


def test_outline_is_simple_polygon_size60(m_size60):
    f = build_mueller2_front(m_size60)
    poly = Polygon([(p.x, p.y) for p in f.outline])
    assert poly.is_simple

    b = build_mueller2_back(m_size60)
    poly = Polygon([(p.x, p.y) for p in b.outline])
    assert poly.is_simple


def test_front_scales_with_outseam(m_size50, m_size38, m_size60):
    """Larger outseam -> outline reaches lower y (hem further down)."""
    f50 = build_mueller2_front(m_size50)
    f38 = build_mueller2_front(m_size38)
    f60 = build_mueller2_front(m_size60)
    max_y_50 = max(p.y for p in f50.outline)
    max_y_38 = max(p.y for p in f38.outline)
    max_y_60 = max(p.y for p in f60.outline)
    assert max_y_38 < max_y_50 < max_y_60


def test_front_scales_with_hip_girth(m_size50, m_size38, m_size60):
    """Larger hip girth -> Ftw anchor x is further right."""
    f50 = build_mueller2_front(m_size50)
    f38 = build_mueller2_front(m_size38)
    f60 = build_mueller2_front(m_size60)
    # Use Ftw anchor x as a proxy
    assert f38.anchors["Ftw"].x < f50.anchors["Ftw"].x < f60.anchors["Ftw"].x
