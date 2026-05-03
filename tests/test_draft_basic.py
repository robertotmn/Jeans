import pytest
from jeans_pattern.draft_basic import build_basic_front, FrontPoints

INCH = 25.4

def test_front_axis_distances(default_measurements):
    front: FrontPoints = build_basic_front(default_measurements)
    assert front.A.y == 0
    assert (front.B.y - front.A.y) == pytest.approx(9.75 * INCH)         # rise
    assert (front.C.y - front.B.y) == pytest.approx(34.5 * INCH)         # length + 0.5"
    assert (front.E.y - front.C.y) == pytest.approx(1.0 * INCH)          # hem
    assert (front.D.y - front.B.y) == pytest.approx(((34.0 + 0.5)/2 - 2.0) * INCH)

def test_front_seat_and_waist(default_measurements):
    front = build_basic_front(default_measurements)
    assert front.F.x == pytest.approx(44.0 / 4 * INCH)                   # seat/4 from B
    assert (front.G.x - front.F.x) == pytest.approx(2.0 * INCH)
    assert (front.H.x - front.I.x) == pytest.approx((34.5 / 4 + 0.5) * INCH)  # waist/4+0.5

def test_front_K_and_N(default_measurements):
    front = build_basic_front(default_measurements)
    expected_K_x = (front.B.x + front.G.x) / 2
    assert front.K.x == pytest.approx(expected_K_x)
    assert front.N.x == pytest.approx(front.K.x)
    assert front.N.y == pytest.approx(front.E.y)

def test_front_hem_half_width(default_measurements):
    front = build_basic_front(default_measurements)
    half_hem = 9.75 / 2 * INCH
    assert (front.M.x - front.N.x) == pytest.approx(half_hem)
    assert (front.N.x - front.L.x) == pytest.approx(half_hem)

def test_front_outline_is_closed_polygon(default_measurements):
    front = build_basic_front(default_measurements)
    poly = front.outline_polygon()
    assert len(poly) >= 6
    assert poly[0] != poly[-1]   # convenzione: poligono chiuso senza ripetere

def test_matches_excel_calculator(default_measurements):
    """Pin absolute mm values to catch unit-conversion bugs (cm/mm/inch swaps,
    INCH typos, formula transcription errors). Values derived from the Excel
    calculator with default inputs (waist=34.5", seat=44", rise=9.75",
    knee=10.375", bottom=9.75", length=34")."""
    f = build_basic_front(default_measurements)
    # Vertical axis (mm)
    assert f.A.y == pytest.approx(0)
    assert f.B.y == pytest.approx(247.65)        # rise
    assert f.C.y == pytest.approx(1123.95)       # rise + (length + 0.5")
    assert f.E.y == pytest.approx(1149.35)       # + 1" hem
    assert f.D.y == pytest.approx(635.0)         # knee line: rise + (length+0.5")/2 - 2"
    # Horizontal seat / waist (mm)
    assert f.F.x == pytest.approx(279.4)         # seat/4
    assert f.G.x == pytest.approx(330.2)         # F + 2"
    assert f.I.x == pytest.approx(279.4)         # above F
    assert f.H.x == pytest.approx(511.175)       # I + waist/4 + 0.5"
    # Hem distribution (mm)
    assert f.K.x == pytest.approx(165.1)         # midpoint B-G on hip line
    assert f.N.x == pytest.approx(165.1)         # below K
    assert (f.M.x - f.L.x) == pytest.approx(247.65)  # bottom width
