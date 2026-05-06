import pytest

from jeans_pattern.draft_mueller import (
    MuellerMeasurements,
    build_mueller_front,
    build_mueller_back,
    MuellerFrontPoints,
    MuellerBackPoints,
)


@pytest.fixture
def size50():
    """M&S Size 50 reference example from PDF page 2."""
    return MuellerMeasurements.from_cm(
        waistband=90.0,
        hip_girth=102.0,
        knee_girth=43.0,
        hem_width=38.0,
        outseam=102.0,
        inseam=82.0,
    )


def test_size50_auxiliary_measurements(size50):
    """Verify derived auxiliary measurements match PDF Size 50 chart."""
    assert size50.front_trouser_width_mm == pytest.approx(255.0)  # 1/4 x 102 cm in mm
    assert size50.front_crotch_width_mm == pytest.approx(51.0)    # 1/10 x 1/2 x 102 cm
    assert size50.back_crotch_width_mm == pytest.approx(122.0)    # 1/10 x 102 + 2.0 cm
    assert size50.back_trouser_width_mm == pytest.approx(280.0)   # 1/4 x 102 + 2.5 cm
    assert size50.hip_depth_mm == pytest.approx(81.0)             # 1/10 x 1/2 x 102 + 3.0 cm
    assert size50.knee_length_mm == pytest.approx(472.0)          # 1/2 x 82 + 1/10 x 82 - 2 cm
    assert size50.body_rise_mm == pytest.approx(200.0)            # Os - Is = 102 - 82 = 20 cm


def test_front_axis_levels(size50):
    """Verify y-coordinates of waist/hip/crotch/knee/hem in app frame."""
    f = build_mueller_front(size50)
    # In app frame y=0 at waist, y grows down:
    assert f.waist_outseam.y == pytest.approx(0.0)
    # hip_y = (Os - Is - hip_depth) = (102 - 82 - 8.1) cm = 11.9 cm = 119 mm
    assert f.F1.y == pytest.approx(119.0, abs=0.5)
    assert f.crotch_inseam_top.y == pytest.approx(200.0)  # crotch at Os - Is = 200 mm
    assert f.knee_left.y == pytest.approx((102 - 47.2) * 10)  # = 548 mm
    assert f.hem_left.y == pytest.approx(1020.0)


def test_front_creaseline(size50):
    f = build_mueller_front(size50)
    # x_crease = (Ftw + Fcw)/2 - 2 cm = (255 + 51)/2 - 20 = 153 - 20 = 133 mm
    assert f.creaseline_x == pytest.approx(133.0)


def test_front_horizontal_distances(size50):
    f = build_mueller_front(size50)
    Hw = 380.0   # 38 cm in mm
    Kg = 430.0
    expected_hem_half = (Hw / 2 - 5.0) / 2   # 92.5 mm
    expected_knee_half = (Kg / 2 - 5.0) / 2  # 105 mm
    assert (f.hem_right.x - f.creaseline_x) == pytest.approx(expected_hem_half)
    assert (f.creaseline_x - f.hem_left.x) == pytest.approx(expected_hem_half)
    assert (f.knee_right.x - f.creaseline_x) == pytest.approx(expected_knee_half)


def test_front_outline_simple(size50):
    from shapely.geometry import Polygon
    f = build_mueller_front(size50)
    poly = Polygon([(p.x, p.y) for p in f.outline_polygon()])
    assert poly.is_simple, "Mueller front outline must be simple (non-self-intersecting)"
    # Outline is now sampled with curves (hip + fly): >= 8 vertices
    assert len(f.outline_polygon()) >= 8


def test_back_outline_simple(size50):
    from shapely.geometry import Polygon
    b = build_mueller_back(size50)
    poly = Polygon([(p.x, p.y) for p in b.outline_polygon()])
    assert poly.is_simple
    # Outline is now sampled with curves (hip + back-crotch): >= 8 vertices
    assert len(b.outline_polygon()) >= 8


def test_back_wedge_centre_back_raised(size50):
    b = build_mueller_back(size50)
    # Centre back is raised above outseam waist by 35 mm (3.5 cm)
    assert b.centre_back_waist.y == pytest.approx(-35.0)
    assert b.outseam_waist.y == pytest.approx(0.0)
    # Higher (smaller y in y-down coords)
    assert b.centre_back_waist.y < b.outseam_waist.y


def test_back_wedge_horizontal_extent(size50):
    b = build_mueller_back(size50)
    # Back hip width = Btw + Bcw = 280 + 122 = 402 mm
    assert b.centre_back_waist.x == pytest.approx(402.0)
    assert b.crotch_corner.x == pytest.approx(402.0)


def test_back_crotch_inseam_top_position(size50):
    b = build_mueller_back(size50)
    # crotch_inseam_top at (Btw, crotch_y) = (280, 200)
    assert b.crotch_inseam_top.x == pytest.approx(280.0)
    assert b.crotch_inseam_top.y == pytest.approx(200.0)


def test_back_outline_simple_wedge(size50):
    from shapely.geometry import Polygon
    b = build_mueller_back(size50)
    poly = Polygon([(p.x, p.y) for p in b.outline_polygon()])
    assert poly.is_simple


def test_back_inseam_levels_match_front(size50):
    """Back inseam shares the same y-levels (knee, hem) as the front, since
    both are drafted from the same outseam/inseam/knee_length measurements.
    The back is in its own coord frame so x-positions differ."""
    b = build_mueller_back(size50)
    f = build_mueller_front(size50)
    assert b.knee_inseam.y == pytest.approx(f.knee_left.y)
    assert b.hem_inseam.y == pytest.approx(f.hem_left.y)


def test_front_curves_keep_polygon_simple(size50):
    from shapely.geometry import Polygon
    f = build_mueller_front(size50)
    poly = Polygon([(p.x, p.y) for p in f.outline_polygon()])
    assert poly.is_simple


def test_back_curves_keep_polygon_simple(size50):
    from shapely.geometry import Polygon
    b = build_mueller_back(size50)
    poly = Polygon([(p.x, p.y) for p in b.outline_polygon()])
    assert poly.is_simple


def test_negative_measurement_rejected():
    with pytest.raises(ValueError):
        MuellerMeasurements.from_cm(
            waistband=-1, hip_girth=100, knee_girth=43, hem_width=38,
            outseam=100, inseam=80,
        )
