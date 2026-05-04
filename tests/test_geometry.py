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
