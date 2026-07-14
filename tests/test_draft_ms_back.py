"""Back draft vs the booklet's size-50 drawing plus parametric invariants."""
import pytest
from shapely.geometry import Polygon

from tests.conftest import max_deviation_to_polyline
from tests.test_draft_ms import SIZES
from jeans_pattern.draft_ms import draft_back, draft_front
from jeans_pattern.geometry import Point, arc_length, distance
from jeans_pattern.measurements import Measurements

LANDMARK_TOL_MM = 1.5
CURVE_TOL_MM = 2.5


@pytest.fixture(scope="module")
def drafts50():
    m = Measurements.from_cm(waistband=90, hip_girth=102, knee_girth=43,
                             hem_width=38, outseam=102, inseam=82)
    f = draft_front(m)
    return f, draft_back(m, f)


# ---- landmarks vs the book drawing -----------------------------------------

@pytest.mark.parametrize("name,tol", [
    ("hem_out", 1.5), ("hem_in", 1.5),
    ("knee_out", 1.5), ("knee_in", 1.5),
    ("p_btw", 1.5), ("slant_p1", 1.5),
    ("crotch_pt", 1.5),
    ("cb_corner", 1.5),
    ("waist_out", 1.5),
    # yoke_out sits ON the outseam curve 3.5 cm below the waist: it inherits
    # the curve-fit deviation (<=1.7 mm) on top of the corner's 0.6 mm
    ("yoke_out", 2.5), ("yoke_cb", 1.5),
    ("dart1_a", 1.5), ("dart1_tip", 1.5), ("dart1_b", 1.5),
    ("dart2_a", 1.5), ("dart2_tip", 1.5), ("dart2_b", 1.5),
])
def test_back_landmark_matches_book(drafts50, reference, name, tol):
    _f, b = drafts50
    ours = b.landmarks[name]
    book = Point(*reference["back"]["landmarks"][name])
    assert distance(ours, book) < tol, \
        f"{name}: ours ({ours.x:.1f},{ours.y:.1f}) vs book ({book.x:.1f},{book.y:.1f})"


# ---- curve shapes vs the book drawing ---------------------------------------

def test_back_outseam_matches_book(drafts50, reference):
    _f, b = drafts50
    ref = reference["back"]["edges"]["outseam_lower"] + reference["back"]["edges"]["outseam_upper"]
    dev = max_deviation_to_polyline(b.edge("outseam"), ref)
    assert dev < CURVE_TOL_MM, f"outseam deviates {dev:.2f} mm"


def test_back_seat_matches_book(drafts50, reference):
    _f, b = drafts50
    # our cb_seat starts at the yoke; the drawn edge starts at the cb corner
    dev = max_deviation_to_polyline(b.edge("cb_seat"), reference["back"]["edges"]["cb_seat"])
    assert dev < CURVE_TOL_MM, f"seat deviates {dev:.2f} mm"


def test_back_inseam_matches_book(drafts50, reference):
    _f, b = drafts50
    ref = reference["back"]["edges"]["inseam_upper"] + reference["back"]["edges"]["inseam_lower"]
    dev = max_deviation_to_polyline(b.edge("inseam"), ref)
    assert dev < CURVE_TOL_MM, f"inseam deviates {dev:.2f} mm"


def test_back_waist_matches_book(drafts50, reference):
    """The drawn waistline (dart corners included) is straight; ours too."""
    _f, b = drafts50
    lm = reference["back"]["landmarks"]
    ref = [lm["waist_out"], lm["dart1_a"], lm["dart1_b"], lm["dart2_a"], lm["dart2_b"], lm["cb_corner"]]
    dev = max_deviation_to_polyline(b.waist_line, ref)
    assert dev < 2.0, f"waist deviates {dev:.2f} mm"


# ---- the booklet's own checks -----------------------------------------------

def test_back_transfers(drafts50):
    f, b = drafts50
    # inseam: front minus 0.7 cm, measured along the hollowed curves
    assert b.report["inseam_upper_len_mm"] == pytest.approx(
        f.report["inseam_upper_len_mm"] - 7.0, abs=0.5)
    # outseam: the raw corner sits at the front outseam length on the guideline;
    # the final curve through the trimmed corner stays within a few mm
    assert b.report["outseam_full_len_mm"] == pytest.approx(
        f.report["outseam_upper_len_mm"], abs=4.0)


def test_back_waist_length_rule(drafts50):
    f, b = drafts50
    m_w = 900.0
    assert distance(b.waist_line[0], b.waist_line[1]) == pytest.approx(
        m_w / 2 + 20.0 - f.report["waist_len_mm"], abs=0.01)
    assert b.report["rest_mm"] < 15.0
    assert b.report["waist_cb_angle_deg"] == pytest.approx(90.0, abs=4.0)


def test_back_darts_at_thirds_with_book_intakes(drafts50):
    _f, b = drafts50
    w = b.report["back_waist_mm"]
    d1, d2 = b.darts
    c1 = Point((d1.a.x + d1.b.x) / 2, (d1.a.y + d1.b.y) / 2)
    c2 = Point((d2.a.x + d2.b.x) / 2, (d2.a.y + d2.b.y) / 2)
    assert distance(b.waist_line[0], c1) == pytest.approx(w / 3, abs=0.5)
    assert distance(b.waist_line[0], c2) == pytest.approx(2 * w / 3, abs=0.5)
    assert distance(d1.a, d1.b) == pytest.approx(8.0, abs=0.01)
    assert distance(d2.a, d2.b) == pytest.approx(12.0, abs=0.01)


def test_hip_ease_check(drafts50):
    """Design step 1 (page 4): A + B minus 1/2 Hg = included ease (~2-2.5 cm
    for size 50; the drawing itself measures 2.5)."""
    f, b = drafts50
    ease = f.report["hip_width_a_mm"] + b.report["hip_width_b_mm"] - 1020.0 / 2
    assert 15.0 < ease < 30.0


# ---- parametric invariants ---------------------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_back_invariants(size):
    m = Measurements.from_cm(**SIZES[size])
    f = draft_front(m)
    b = draft_back(m, f)

    # front + back hem = Hw; front + back knee = Kg (halves of the garment)
    front_hem = distance(f.landmarks["hem_out"], f.landmarks["hem_in"])
    back_hem = distance(b.landmarks["hem_out"], b.landmarks["hem_in"])
    assert front_hem + back_hem == pytest.approx(m.hem_width_mm)
    front_knee = distance(f.landmarks["knee_out"], f.landmarks["knee_in"])
    back_knee = distance(b.landmarks["knee_out"], b.landmarks["knee_in"])
    assert front_knee + back_knee == pytest.approx(m.knee_girth_mm)

    # inseam transfer holds for every size
    assert b.report["inseam_upper_len_mm"] == pytest.approx(
        f.report["inseam_upper_len_mm"] - 7.0, abs=0.5)

    # sewn waist (pattern waists minus dart intakes) equals W/2 within the rest
    sewn = f.report["waist_len_mm"] + b.report["back_waist_mm"] - sum((8.0, 12.0))
    assert sewn == pytest.approx(m.waistband_mm / 2, abs=0.01)

    # the back piece outline is a simple closed polygon
    outline = b.outline()
    assert Polygon([(p.x, p.y) for p in outline]).is_simple
    assert distance(b.edges[-1][1][-1], b.edges[0][1][0]) < 1e-6

    # darts end exactly on the yoke line
    for d in b.darts:
        yo, yc = b.yoke_line
        cross = ((yc.x - yo.x) * (d.tip.y - yo.y) - (yc.y - yo.y) * (d.tip.x - yo.x))
        assert abs(cross) / distance(yo, yc) < 0.01

    # c.b. is perpendicular to the auxiliary slant line by construction;
    # waist meets c.b. near a right angle (the book accepts ~87 deg)
    assert b.report["waist_cb_angle_deg"] == pytest.approx(90.0, abs=5.0)
