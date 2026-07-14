"""Front draft vs the booklet's own size-50 scale drawing (the ground truth
extracted into tests/data/ms_reference_size50.json) plus parametric invariants
on other sizes."""
import pytest
from shapely.geometry import Polygon

from tests.conftest import max_deviation_to_polyline
from jeans_pattern.draft_ms import draft_front
from jeans_pattern.geometry import Point, arc_length, distance
from jeans_pattern.measurements import Measurements

LANDMARK_TOL_MM = 1.5
CURVE_TOL_MM = 2.0


@pytest.fixture(scope="module")
def front50():
    m = Measurements.from_cm(waistband=90, hip_girth=102, knee_girth=43,
                             hem_width=38, outseam=102, inseam=82)
    return draft_front(m)


# ---- landmarks vs the book drawing ----------------------------------------

@pytest.mark.parametrize("name", [
    "waist_out", "waist_cf", "crotch_pt", "knee_out", "knee_in",
    "hem_out", "hem_in", "halfd_pt",
])
def test_front_landmark_matches_book(front50, reference, name):
    ours = front50.landmarks[name]
    book = Point(*reference["front"]["landmarks"][name])
    assert distance(ours, book) < LANDMARK_TOL_MM, \
        f"{name}: ours ({ours.x:.1f},{ours.y:.1f}) vs book ({book.x:.1f},{book.y:.1f})"


# ---- curve shapes vs the book drawing --------------------------------------

def test_front_waist_curve_matches_book(front50, reference):
    dev = max_deviation_to_polyline(front50.edge("waist"), reference["front"]["edges"]["waist"])
    assert dev < CURVE_TOL_MM, f"waist deviates {dev:.2f} mm from the drawing"


def test_front_cf_crotch_curve_matches_book(front50, reference):
    dev = max_deviation_to_polyline(front50.edge("cf_crotch"),
                                    reference["front"]["edges"]["cf_crotch"])
    assert dev < CURVE_TOL_MM, f"cf/crotch deviates {dev:.2f} mm"


def test_front_inseam_curve_matches_book(front50, reference):
    ref = reference["front"]["edges"]["inseam_upper"] + reference["front"]["edges"]["inseam_lower"]
    dev = max_deviation_to_polyline(front50.edge("inseam"), ref)
    assert dev < CURVE_TOL_MM, f"inseam deviates {dev:.2f} mm"


def test_front_outseam_curve_matches_book(front50, reference):
    ref = reference["front"]["edges"]["outseam_lower"] + reference["front"]["edges"]["outseam_upper"]
    dev = max_deviation_to_polyline(front50.edge("outseam"), ref)
    assert dev < CURVE_TOL_MM, f"outseam deviates {dev:.2f} mm"


# ---- transfer lengths (used by the back draft) ------------------------------

def test_front_transfer_lengths_match_book(front50, reference):
    ref_out = arc_length([Point(*p) for p in reference["front"]["edges"]["outseam_upper"]])
    ref_in = arc_length([Point(*p) for p in reference["front"]["edges"]["inseam_upper"]])
    ref_waist = arc_length([Point(*p) for p in reference["front"]["edges"]["waist"]])
    assert front50.report["outseam_upper_len_mm"] == pytest.approx(ref_out, abs=2.5)
    assert front50.report["inseam_upper_len_mm"] == pytest.approx(ref_in, abs=2.5)
    assert front50.report["waist_len_mm"] == pytest.approx(ref_waist, abs=2.0)


def test_front_d_matches_book(front50, reference):
    assert front50.report["d_crotch_mm"] == pytest.approx(
        reference["front"]["meta"]["d_crotch_mm"], abs=1.0)


# ---- formula invariants across sizes ----------------------------------------

SIZES = {
    "44": dict(waistband=78, hip_girth=94, knee_girth=40, hem_width=35, outseam=100, inseam=80),
    "50": dict(waistband=90, hip_girth=102, knee_girth=43, hem_width=38, outseam=102, inseam=82),
    "60": dict(waistband=110, hip_girth=118, knee_girth=48, hem_width=42, outseam=106, inseam=84),
    "tall_slim": dict(waistband=80, hip_girth=96, knee_girth=41, hem_width=36, outseam=112, inseam=92),
}


@pytest.mark.parametrize("size", SIZES)
def test_front_invariants(size):
    m = Measurements.from_cm(**SIZES[size])
    f = draft_front(m)
    lm = f.landmarks

    # hem and knee widths: half garment widths minus 1 cm total
    assert distance(lm["hem_out"], lm["hem_in"]) == pytest.approx(m.hem_width_mm / 2 - 10)
    assert distance(lm["knee_out"], lm["knee_in"]) == pytest.approx(m.knee_girth_mm / 2 - 10)

    # crotch point: on the crotch line, on the knee->Fcw guideline
    crotch = lm["crotch_pt"]
    assert crotch.y == pytest.approx(m.body_rise_mm)
    knee_in, fcw = lm["knee_in"], lm["fcw_pt"]
    cross = ((fcw.x - knee_in.x) * (crotch.y - knee_in.y)
             - (fcw.y - knee_in.y) * (crotch.x - knee_in.x))
    assert abs(cross) / distance(knee_in, fcw) < 0.01

    # waist corners per the book rules
    assert lm["waist_out"] == Point(10.0, 0.0)
    assert lm["waist_cf"].x == pytest.approx(m.front_trouser_width_mm - 15.0)
    assert lm["waist_cf"].y == pytest.approx(10.0)

    # outline is a simple polygon and the edge chain closes
    outline = f.outline()
    assert Polygon([(p.x, p.y) for p in outline]).is_simple
    first_edge = f.edges[0][1]
    last_edge = f.edges[-1][1]
    assert distance(last_edge[-1], first_edge[0]) < 1e-6

    # report lengths are positive and sane
    assert 0 < f.report["inseam_upper_len_mm"] < m.inseam_mm
    assert f.report["outseam_upper_len_mm"] > m.outseam_mm - m.knee_length_mm - 20
    assert f.report["hip_width_a_mm"] == pytest.approx(m.front_trouser_width_mm, abs=6.0)
