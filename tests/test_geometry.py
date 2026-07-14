import pytest
from jeans_pattern.geometry import Point, distance, square_out, midpoint, line_intersection, bezier_curve

def test_point_equality():
    assert Point(1, 2) == Point(1, 2)

def test_distance():
    assert distance(Point(0, 0), Point(3, 4)) == pytest.approx(5)

def test_square_out_horizontal_right():
    p = Point(10, 20)
    q = square_out(p, length=5, direction="right")
    assert q == Point(15, 20)

def test_square_out_horizontal_left():
    assert square_out(Point(10, 20), 5, "left") == Point(5, 20)

def test_square_out_vertical_up():
    assert square_out(Point(10, 20), 5, "up") == Point(10, 15)

def test_square_out_vertical_down():
    assert square_out(Point(10, 20), 5, "down") == Point(10, 25)

def test_midpoint():
    assert midpoint(Point(0, 0), Point(10, 20)) == Point(5, 10)

def test_line_intersection():
    p = line_intersection(Point(0, 0), Point(10, 10), Point(0, 10), Point(10, 0))
    assert p.x == pytest.approx(5)
    assert p.y == pytest.approx(5)

def test_bezier_curve_endpoints():
    pts = bezier_curve(Point(0, 0), Point(5, -5), Point(10, 0), n=20)
    assert pts[0] == Point(0, 0)
    assert pts[-1].x == pytest.approx(10)
    assert pts[-1].y == pytest.approx(0)
    assert len(pts) == 20

def test_points_equal_within_tolerance():
    from jeans_pattern.geometry import points_equal
    a = Point(1.0, 2.0)
    b = Point(1.0 + 5e-10, 2.0 - 5e-10)
    assert a != b               # exact equality: different
    assert points_equal(a, b)   # tolerance helper: same

def test_points_equal_outside_tolerance():
    from jeans_pattern.geometry import points_equal
    a = Point(1.0, 2.0)
    b = Point(1.0 + 1e-3, 2.0)
    assert not points_equal(a, b)

def test_horizontal_line_through():
    from jeans_pattern.geometry import horizontal_line_through
    p1, p2 = horizontal_line_through(50)
    assert p1.y == 50
    assert p2.y == 50
    assert p1.x != p2.x


def test_curve_segment_bow():
    from jeans_pattern.geometry import curve_segment, distance
    a = Point(0, 0)
    b = Point(100, 0)
    pts = curve_segment(a, b, bow_mm=10, perp_x=0, perp_y=1, n=20)
    assert pts[0] == Point(0, 0)
    assert pts[-1].x == pytest.approx(100, abs=0.01)
    assert pts[-1].y == pytest.approx(0, abs=0.01)
    # Apex should be near (50, 5) - quadratic Bezier midpoint formula gives 5 (half the bow)
    apex = pts[len(pts) // 2]
    assert apex.y == pytest.approx(5.0, abs=0.5)


def test_curve_through_explicit_control():
    from jeans_pattern.geometry import curve_through
    pts = curve_through(Point(0, 0), Point(50, 50), Point(100, 0), n=10)
    assert pts[0] == Point(0, 0)
    assert pts[-1] == Point(100, 0)


# ---- arc length ----------------------------------------------------------

def test_arc_length_straight_polyline():
    from jeans_pattern.geometry import arc_length
    pts = [Point(0, 0), Point(30, 40), Point(30, 140)]
    assert arc_length(pts) == pytest.approx(50 + 100)


def test_point_at_arc_length_within():
    from jeans_pattern.geometry import point_at_arc_length
    pts = [Point(0, 0), Point(100, 0), Point(100, 100)]
    assert point_at_arc_length(pts, 50) == Point(50, 0)
    p = point_at_arc_length(pts, 150)
    assert p.x == pytest.approx(100)
    assert p.y == pytest.approx(50)


def test_point_at_arc_length_extrapolates_past_end():
    from jeans_pattern.geometry import point_at_arc_length
    pts = [Point(0, 0), Point(100, 0), Point(100, 100)]
    p = point_at_arc_length(pts, 250)
    assert p.x == pytest.approx(100)
    assert p.y == pytest.approx(150)


def test_point_at_arc_length_negative_raises():
    from jeans_pattern.geometry import point_at_arc_length
    with pytest.raises(ValueError):
        point_at_arc_length([Point(0, 0), Point(1, 0)], -1)


# ---- edge chains and seam-allowance offset --------------------------------

def _square_edges():
    """Unit test shape: 100x100 square split into 4 named edges (CW in y-down)."""
    return [
        ("top", [Point(0, 0), Point(100, 0)]),
        ("right", [Point(100, 0), Point(100, 100)]),
        ("bottom", [Point(100, 100), Point(0, 100)]),
        ("left", [Point(0, 100), Point(0, 0)]),
    ]


def test_chain_outline_dedups_shared_corners():
    from jeans_pattern.geometry import chain_outline
    outline = chain_outline(_square_edges())
    assert len(outline) == 4
    assert outline[0] == Point(0, 0)
    assert outline[2] == Point(100, 100)


def test_offset_outline_uniform():
    from jeans_pattern.geometry import offset_outline
    sa = {"top": 10, "right": 10, "bottom": 10, "left": 10}
    cut = offset_outline(_square_edges(), sa)
    xs = [p.x for p in cut]
    ys = [p.y for p in cut]
    assert min(xs) == pytest.approx(-10)
    assert max(xs) == pytest.approx(110)
    assert min(ys) == pytest.approx(-10)
    assert max(ys) == pytest.approx(110)


def test_offset_outline_per_edge():
    """Hem-style asymmetry: bottom edge 30, everything else 10."""
    from jeans_pattern.geometry import offset_outline
    sa = {"top": 10, "right": 10, "bottom": 30, "left": 10}
    cut = offset_outline(_square_edges(), sa)
    ys = [p.y for p in cut]
    xs = [p.x for p in cut]
    assert max(ys) == pytest.approx(130)   # bottom pushed by 30
    assert min(ys) == pytest.approx(-10)   # top by 10
    assert min(xs) == pytest.approx(-10)
    assert max(xs) == pytest.approx(110)


def test_offset_outline_zero_allowance_stays_on_net():
    from jeans_pattern.geometry import offset_outline
    sa = {"top": 0, "right": 0, "bottom": 0, "left": 0}
    cut = offset_outline(_square_edges(), sa)
    assert {(round(p.x), round(p.y)) for p in cut} == {(0, 0), (100, 0), (100, 100), (0, 100)}


def test_offset_outline_orientation_independent():
    """Same square wound the other way must still offset OUTWARD."""
    from jeans_pattern.geometry import offset_outline
    edges = [(name, pts[::-1]) for name, pts in reversed(_square_edges())]
    sa = {"top": 10, "right": 10, "bottom": 10, "left": 10}
    cut = offset_outline(edges, sa)
    assert min(p.x for p in cut) == pytest.approx(-10)
    assert max(p.y for p in cut) == pytest.approx(110)


def test_offset_outline_polygon_is_simple():
    """Offsetting a realistic curved edge set stays a simple polygon."""
    from shapely.geometry import Polygon
    from jeans_pattern.geometry import curved_edge, offset_outline
    top = [Point(0, 0), Point(200, 0)]
    right = curved_edge(Point(200, 0), Point(180, 600), bow_mm=15, side="left")
    bottom = [Point(180, 600), Point(20, 600)]
    left = curved_edge(Point(20, 600), Point(0, 0), bow_mm=15, side="left")
    edges = [("waist", top), ("inseam", right), ("hem", bottom), ("outseam", left)]
    cut = offset_outline(edges, {"waist": 10, "inseam": 10, "hem": 30, "outseam": 10})
    poly = Polygon([(p.x, p.y) for p in cut])
    assert poly.is_simple
    net = Polygon([(p.x, p.y) for pts in [top, right, bottom, left] for p in pts])
    assert poly.contains(net.buffer(-0.01))


def test_offset_outline_missing_edge_name_raises():
    from jeans_pattern.geometry import offset_outline
    with pytest.raises(KeyError):
        offset_outline(_square_edges(), {"top": 10})


def test_point_along():
    from jeans_pattern.geometry import point_along
    p = point_along(Point(0, 0), Point(3, 4), 10)
    assert p.x == pytest.approx(6)
    assert p.y == pytest.approx(8)
