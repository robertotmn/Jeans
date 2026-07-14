"""Design 3069 accessory pieces: book checks and shape sanity."""
import pytest
from shapely.geometry import Polygon

from jeans_pattern.draft_ms import draft_back, draft_front
from jeans_pattern.draft_ms_extras import (
    build_back_pocket,
    build_belt_loop_strip,
    build_coin_pocket,
    build_fly_facing,
    build_fly_shield,
    build_front_pocket_bag,
    build_front_pocket_facing,
    build_waistband,
    build_yoke,
    front_design_marks,
    pocket_opening_curve,
)
from jeans_pattern.geometry import Point, arc_length, distance, point_at_arc_length
from jeans_pattern.measurements import Measurements


@pytest.fixture(scope="module")
def m50():
    return Measurements.from_cm(waistband=90, hip_girth=102, knee_girth=43,
                                hem_width=38, outseam=102, inseam=82)


@pytest.fixture(scope="module")
def drafts(m50):
    f = draft_front(m50)
    return f, draft_back(m50, f)


@pytest.fixture(scope="module")
def all_pieces(m50, drafts):
    f, b = drafts
    return [
        build_yoke(b),
        build_waistband(m50, f),
        build_back_pocket(b),
        build_front_pocket_bag(m50, f),
        build_front_pocket_facing(m50, f),
        build_fly_facing(),
        build_fly_shield(),
        build_coin_pocket(),
        build_belt_loop_strip(),
    ]


def test_all_pieces_simple_and_closed(all_pieces):
    for piece in all_pieces:
        outline = piece.outline()
        assert len(outline) >= 3, piece.name
        assert Polygon([(p.x, p.y) for p in outline]).is_simple, piece.name
        first = piece.edges[0][1][0]
        last = piece.edges[-1][1][-1]
        assert distance(first, last) < 1e-6, f"{piece.name}: edge chain not closed"


# ---- yoke: the booklet's own seam-length check ------------------------------

def test_yoke_seam_matches_back(drafts):
    _f, b = drafts
    yoke = build_yoke(b)
    assert yoke.report["kinked_len_mm"] == pytest.approx(yoke.report["back_yoke_len_mm"], abs=0.01)
    assert yoke.report["yoke_seam_len_mm"] == pytest.approx(yoke.report["back_yoke_len_mm"], abs=2.5)


def test_yoke_waist_equals_sewn_back_waist(drafts):
    """Closing the darts removes exactly the 2 cm of intakes."""
    _f, b = drafts
    yoke = build_yoke(b)
    top = next(pts for n, pts in yoke.edges if n == "waist")
    expected = b.report["back_waist_mm"] - 20.0
    assert arc_length(top) == pytest.approx(expected, abs=3.0)


def test_yoke_cb_and_outseam_depths(drafts):
    _f, b = drafts
    yoke = build_yoke(b)
    cb = next(pts for n, pts in yoke.edges if n == "cb")
    outseam = next(pts for n, pts in yoke.edges if n == "outseam")
    assert distance(cb[0], cb[-1]) == pytest.approx(70.0, abs=0.01)
    assert arc_length(outseam) == pytest.approx(35.0, abs=0.1)


# ---- waistband ---------------------------------------------------------------

def test_waistband_dimensions(m50, drafts):
    f, _b = drafts
    band = build_waistband(m50, f)
    x0, y0, x1, y1 = _bbox(band.outline())
    assert x1 - x0 == pytest.approx(m50.waistband_mm / 2 + 40.0)
    assert y1 - y0 == pytest.approx(40.0)
    assert band.report["ss_notch_mm"] == pytest.approx(f.report["waist_len_mm"])
    assert band.report["pocket_notch_mm"] == pytest.approx(f.report["waist_len_mm"] - 130.0)


def test_waistband_notches_match_book(m50, drafts, reference):
    f, _b = drafts
    band = build_waistband(m50, f)
    wb = reference["design"]["waistband"]
    assert band.report["ss_notch_mm"] == pytest.approx(wb["ss_notch_from_cf_mm"], abs=2.0)
    assert band.report["pocket_notch_mm"] == pytest.approx(wb["pocket_notch_from_cf_mm"], abs=2.0)
    assert wb["length_mm"] == pytest.approx(m50.waistband_mm / 2, abs=1.0)


# ---- back pocket ---------------------------------------------------------------

def test_back_pocket_book_dimensions(drafts):
    _f, b = drafts
    pocket = build_back_pocket(b)
    assert pocket.report["top_mm"] == pytest.approx(170.0, abs=1.0)
    assert pocket.report["centre_len_mm"] == pytest.approx(180.0, abs=1.0)


def test_back_pocket_placement_matches_book(drafts, reference):
    """Corners within a few mm of the measured page-5 placement."""
    _f, b = drafts
    pocket = build_back_pocket(b)
    hem = next(pts for n, pts in pocket.edges if n == "hem")
    book = reference["design"]["back_pocket"]["corners_app"]
    assert distance(hem[0], Point(*book["top_left"])) < 8.0
    assert distance(hem[-1], Point(*book["top_right"])) < 8.0


def test_back_pocket_sits_on_back_piece(drafts):
    _f, b = drafts
    pocket = build_back_pocket(b)
    back_poly = Polygon([(p.x, p.y) for p in b.outline()])
    pocket_poly = Polygon([(p.x, p.y) for p in pocket.outline()])
    assert back_poly.contains(pocket_poly)


# ---- front pocket pieces -------------------------------------------------------

def test_opening_curve_endpoints(drafts):
    f, _b = drafts
    curve = pocket_opening_curve(f)
    waist = f.edge("waist")
    assert distance(curve[0], point_at_arc_length(waist, 130.0)) < 0.01
    from_top = f.edge("outseam")[::-1]
    e0 = point_at_arc_length(from_top, 80.0)
    assert distance(curve[-1], e0) == pytest.approx(6.0, abs=0.1)


def test_bag_depth(m50, drafts):
    f, _b = drafts
    bag = build_front_pocket_bag(m50, f)
    assert bag.report["depth_mm"] == pytest.approx(240.0, abs=0.5)


def test_front_design_marks(drafts):
    f, _b = drafts
    marks = front_design_marks(f)
    assert len(marks) == 2
    opening, stitch = marks
    assert arc_length(opening) > 150.0
    # the topstitch runs parallel to the c.f. 34 mm inside
    cf = f.edge("cf_crotch")
    assert distance(stitch[0], cf[0]) == pytest.approx(34.0, abs=0.5)


# ---- helpers -------------------------------------------------------------------

def _bbox(pts):
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return min(xs), min(ys), max(xs), max(ys)
