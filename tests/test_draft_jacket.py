"""Jacket body block vs the booklet's own size-50 scale drawing (pages 11-12,
extracted into tests/data/ms_jacket_reference_size50.json) plus parametric
invariants on other sizes."""
import pytest
from shapely.geometry import Polygon

from tests.conftest import max_deviation_to_polyline
from jeans_pattern.draft_jacket import (
    BODY_GAP_MM, CF_HEM_ADD_MM, FRONT_SHOULDER_SUB_MM, HIP_EASE_MIN_MM,
    draft_jacket_back, draft_jacket_front,
)
from jeans_pattern.geometry import Point, arc_length, distance, unit_vector
from jeans_pattern.measurements_jacket import JacketMeasurements

LANDMARK_TOL_MM = 1.5
# The drawing prints the armhole-depth line about 1.1 mm below its own
# construction; every front landmark anchored to it inherits that offset.
SLOP_LANDMARK_TOL_MM = 2.5
SLOP_LANDMARKS = {"Cn", "S2", "C0", "HSP_f", "SP0_f", "SP_f"}
CURVE_TOL_MM = 2.0


@pytest.fixture(scope="module")
def blocks():
    m = JacketMeasurements.from_cm(body_height=179.0, chest_girth=100.0,
                                   waist_girth=90.0, hip_girth=102.0, sleeve_length=64.0)
    back = draft_jacket_back(m)
    return m, back, draft_jacket_front(m, back)


# ---- landmarks vs the book drawing ----------------------------------------

@pytest.mark.parametrize("name", [
    "N", "A2", "E", "HSP_b", "S1", "SP0", "SP_b", "G1", "U_b", "W_b", "H_b", "K",
])
def test_back_landmark_matches_book(blocks, jacket_reference, name):
    ours = blocks[1].landmarks[name]
    book = Point(*jacket_reference["body_block"]["back"]["landmarks"][name])
    assert distance(ours, book) < LANDMARK_TOL_MM, \
        f"{name}: ours ({ours.x:.1f},{ours.y:.1f}) vs book ({book.x:.1f},{book.y:.1f})"


@pytest.mark.parametrize("name", [
    "P_top", "Cn", "S2", "SP0_f", "SP_f", "HSP_f", "C0", "C1", "C2", "C3",
    "FAN", "quarter_Sd", "U_f", "W_f", "H_f",
])
def test_front_landmark_matches_book(blocks, jacket_reference, name):
    ours = blocks[2].landmarks[name]
    book = Point(*jacket_reference["body_block"]["front"]["landmarks"][name])
    tol = SLOP_LANDMARK_TOL_MM if name in SLOP_LANDMARKS else LANDMARK_TOL_MM
    assert distance(ours, book) < tol, \
        f"{name}: ours ({ours.x:.1f},{ours.y:.1f}) vs book ({book.x:.1f},{book.y:.1f})"


# ---- curve shapes vs the book drawing --------------------------------------

@pytest.mark.parametrize("side,edge", [
    ("back", "neck"), ("back", "shoulder"), ("back", "armhole"),
    ("back", "hem"), ("back", "cb"),
    ("front", "shoulder"), ("front", "armhole"), ("front", "hem"),
    ("front", "cf_upper"), ("front", "neck"),
])
def test_edge_matches_book(blocks, jacket_reference, side, edge):
    draft = blocks[1] if side == "back" else blocks[2]
    ref = jacket_reference["body_block"][side]["edges"][edge]
    dev = max_deviation_to_polyline(draft.edge(edge), ref)
    assert dev < CURVE_TOL_MM, f"{side} {edge} deviates {dev:.2f} mm from the drawing"


def test_back_armhole_hollow_sits_half_a_centimetre_past_the_back_width(blocks):
    """The booklet's back armhole scoops about 0.5 cm beyond the back width
    line before swinging out to the underarm."""
    _, back, _ = blocks
    hollow = min(back.edge("armhole"), key=lambda p: p.x)
    assert hollow.x - back.report["x_back_width_mm"] == pytest.approx(5.0, abs=1.5)


# ---- derived lengths -------------------------------------------------------

def test_shoulder_and_neckline_lengths_match_book(blocks):
    _, back, front = blocks
    assert back.report["shoulder_len_mm"] == pytest.approx(156.8, abs=1.5)
    assert front.report["shoulder_len_mm"] == pytest.approx(151.8, abs=1.5)
    assert back.report["neck_arc_mm"] == pytest.approx(105.0, abs=1.5)
    assert front.report["neck_arc_mm"] == pytest.approx(131.0, abs=1.5)


def test_side_seam_and_cf_lengths_match_book(blocks):
    _, back, front = blocks
    assert back.report["side_lower_len_mm"] == pytest.approx(180.8, abs=1.5)
    assert front.report["side_lower_len_mm"] == back.report["side_lower_len_mm"]
    assert front.report["cf_lower_len_mm"] == pytest.approx(185.9, abs=1.5)


def test_sleeve_transfers_match_book(blocks, jacket_reference):
    """Ah and Ac are measured on the block and handed to the sleeve draft."""
    _, back, front = blocks
    tr = jacket_reference["body_block"]["transfers"]
    ref_back_ah = arc_length([Point(*p) for p in tr["back_ah"]])
    ref_front_ah = arc_length([Point(*p) for p in tr["front_ah"]])
    ref_ac = sum(arc_length([Point(*p) for p in jacket_reference["body_block"][s]["edges"]["armhole"]])
                 for s in ("back", "front"))
    assert back.report["armhole_height_mm"] == pytest.approx(ref_back_ah, abs=2.5)
    assert front.report["armhole_height_mm"] == pytest.approx(ref_front_ah, abs=2.5)
    assert front.report["armhole_height_total_mm"] == pytest.approx(ref_back_ah + ref_front_ah, abs=2.5)
    assert front.report["armhole_circ_mm"] == pytest.approx(ref_ac, abs=2.5)


# ---- the book's own checks -------------------------------------------------

def test_total_chest_matches_the_measurement_chart(blocks):
    m, back, front = blocks
    assert front.report["total_chest_mm"] == pytest.approx(
        m.back_width_mm + m.scye_width_mm + m.chest_width_mm)
    assert front.report["chest_ease_mm"] == pytest.approx(75.0)   # chart: ease 7.5 cm


def test_hem_passes_the_hip_check_at_size_50(blocks):
    _, _, front = blocks
    assert front.report["total_hem_mm"] == pytest.approx(564.2, abs=2.0)
    assert front.report["hip_ease_mm"] > HIP_EASE_MIN_MM
    assert front.report["warnings"] == []


def test_hip_check_warns_when_hips_outgrow_the_chest():
    m = JacketMeasurements.from_cm(body_height=179.0, chest_girth=100.0,
                                   waist_girth=90.0, hip_girth=118.0, sleeve_length=64.0)
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    assert front.report["hip_ease_mm"] < HIP_EASE_MIN_MM
    assert any("Check Hg" in w for w in front.report["warnings"])


# ---- formula invariants across sizes ----------------------------------------

SIZES = {
    "44": dict(body_height=170.0, chest_girth=88.0, waist_girth=76.0, hip_girth=92.0, sleeve_length=61.0),
    "50": dict(body_height=179.0, chest_girth=100.0, waist_girth=90.0, hip_girth=102.0, sleeve_length=64.0),
    "56": dict(body_height=185.0, chest_girth=112.0, waist_girth=106.0, hip_girth=114.0, sleeve_length=66.0),
    "62": dict(body_height=188.0, chest_girth=124.0, waist_girth=124.0, hip_girth=126.0, sleeve_length=67.0),
}


@pytest.mark.parametrize("size", SIZES)
def test_body_block_invariants(size):
    m = JacketMeasurements.from_cm(**SIZES[size])
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    bl, fl = back.landmarks, front.landmarks

    # chest widths are exactly the chart split Bw + 1/2 Sw + 1.5 / 1/2 Sw - 1.5 + Cw
    assert front.report["total_chest_mm"] == pytest.approx(
        m.back_width_mm + m.scye_width_mm + m.chest_width_mm)
    assert fl["C2"].x - fl["quarter_Sd"].x == pytest.approx(m.abdomen_width_mm)

    # hem square to the centre back, side seam square to the hem
    cb = unit_vector(bl["K"].x - bl["N"].x, bl["K"].y - bl["N"].y)
    hem = unit_vector(bl["H_b"].x - bl["K"].x, bl["H_b"].y - bl["K"].y)
    side = unit_vector(bl["H_b"].x - bl["W_b"].x, bl["H_b"].y - bl["W_b"].y)
    assert cb[0] * hem[0] + cb[1] * hem[1] == pytest.approx(0.0, abs=1e-9)
    assert side[0] * hem[0] + side[1] * hem[1] == pytest.approx(0.0, abs=1e-9)

    # front side seam: same gap, same taper, same length as the back
    assert fl["U_f"].x - bl["U_b"].x == pytest.approx(BODY_GAP_MM)
    assert front.report["side_lower_len_mm"] == pytest.approx(back.report["side_lower_len_mm"])
    assert front.report["cf_lower_len_mm"] == pytest.approx(
        back.report["side_lower_len_mm"] + CF_HEM_ADD_MM)

    # finished front shoulder = finished back shoulder minus 0.5 cm
    assert back.report["shoulder_len_mm"] - front.report["shoulder_len_mm"] == pytest.approx(
        FRONT_SHOULDER_SUB_MM)

    # both outlines are simple closed polygons
    for draft in (back, front):
        assert Polygon([(p.x, p.y) for p in draft.outline()]).is_simple
        assert distance(draft.edges[-1][1][-1], draft.edges[0][1][0]) < 1e-6


def test_abdomen_width_falls_back_to_the_chest_width():
    """Chart rule: a waist narrower than the chest does not pull the c.f. in."""
    m = JacketMeasurements.from_cm(body_height=179.0, chest_girth=100.0,
                                   waist_girth=80.0, hip_girth=102.0, sleeve_length=64.0)
    front = draft_jacket_front(m, draft_jacket_back(m))
    assert m.abdomen_width_mm == m.chest_width_mm
    assert front.landmarks["C2"].x == pytest.approx(front.landmarks["C1"].x)


def test_edge_lookup_rejects_unknown_names(blocks):
    _, back, front = blocks
    with pytest.raises(KeyError):
        back.edge("inseam")
    with pytest.raises(KeyError):
        front.edge("cb")
