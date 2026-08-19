"""Jacket sleeve block vs the booklet's own size-50 scale drawing (pages 12-13,
extracted into tests/data/ms_jacket_reference_size50.json) plus parametric
invariants on other sizes."""
import pytest
from shapely.geometry import Polygon

from tests.conftest import max_deviation_to_polyline
from tests.test_draft_jacket import SIZES
from jeans_pattern.draft_jacket import (
    BACK_FOLD_ADD_MM, BACK_MERGE_BELOW_ELBOW_MM, FRONT_SEAM_OFFSET_MM,
    SLEEVE_HEM_MM, SP_ADD_MM,
    draft_jacket_back, draft_jacket_front, draft_jacket_sleeve,
)
from jeans_pattern.geometry import Point, distance
from jeans_pattern.measurements_jacket import JacketMeasurements

LANDMARK_TOL_MM = 1.5
CURVE_TOL_MM = 2.0
# D13: the hem corner is placed with the chart's sleeve hem (31.0 cm) while the
# drawing follows its own printed "1/2 sleeve hem 15", 4.6 mm further in. Every
# straight edge that ends at B_hem inherits that gap.
B_HEM_TOL_MM = 5.0


@pytest.fixture(scope="module")
def sleeve():
    m = JacketMeasurements.from_cm(body_height=179.0, chest_girth=100.0,
                                   waist_girth=90.0, hip_girth=102.0, sleeve_length=64.0)
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    return m, draft_jacket_sleeve(m, back, front)


@pytest.fixture(scope="module")
def book(jacket_reference):
    ref = jacket_reference["sleeve_block"]
    return {**ref["under"]["landmarks"], **ref["upper"]["landmarks"]}


# ---- the sleeve measurement chart (page 13) --------------------------------

def test_sleeve_measurements_match_the_chart(sleeve):
    """Ah and Ac are measured on the generated block, so they fall ~0.5 % short
    of the chart's own numbers; the two calibration constants put Sch and Scw
    back on the chart (D12)."""
    _, s = sleeve
    assert s.report["armhole_height_mm"] == pytest.approx(442.0, abs=3.0)
    assert s.report["armhole_circ_mm"] == pytest.approx(534.0, abs=3.0)
    assert s.report["sleeve_cap_height_mm"] == pytest.approx(161.0, abs=1.0)
    assert s.report["sleeve_cap_width_mm"] == pytest.approx(242.0, abs=1.0)


# ---- landmarks vs the book drawing -----------------------------------------

@pytest.mark.parametrize("name", [
    "E", "Sp", "M1", "M2", "FAN", "Q", "T", "U2", "U22", "FST", "UST",
    "fold_elbow", "fold_elbow_front", "elbow_front", "fold_hem", "hem_front",
    "F_b", "merge_back",
])
def test_landmark_matches_book(sleeve, book, name):
    ours = sleeve[1].landmarks[name]
    ref = Point(*book[name])
    assert distance(ours, ref) < LANDMARK_TOL_MM, \
        f"{name}: ours ({ours.x:.1f},{ours.y:.1f}) vs book ({ref.x:.1f},{ref.y:.1f})"


def test_hem_corner_follows_the_chart_not_the_drawing(sleeve, book):
    """D13: 1/2 Sh measured diagonally from the front to the back sleeve length.
    The drawing places it 4.6 mm short, following its own "1/2 sleeve hem 15"
    label instead of the 31.0 the chart states."""
    _, s = sleeve
    b_hem = s.landmarks["B_hem"]
    front_hem = Point(0.0, s.report["levels_y_mm"]["front_hem"])
    assert distance(front_hem, b_hem) == pytest.approx(SLEEVE_HEM_MM / 2)
    assert distance(b_hem, Point(*book["B_hem"])) == pytest.approx(4.6, abs=0.5)


# ---- curve shapes vs the book drawing --------------------------------------

@pytest.mark.parametrize("part,edge", [
    ("upper", "cap_front"), ("upper", "cap"), ("upper", "back_seam"),
    ("upper", "front_seam"), ("under", "cap"), ("under", "back_seam"),
    ("under", "front_seam"),
])
def test_edge_matches_book(sleeve, jacket_reference, part, edge):
    ref = jacket_reference["sleeve_block"][part]["edges"][edge]
    dev = max_deviation_to_polyline(sleeve[1].edge(part, edge), ref)
    assert dev < CURVE_TOL_MM, f"{part} {edge} deviates {dev:.2f} mm from the drawing"


@pytest.mark.parametrize("part,edge", [
    ("upper", "back_fold"), ("upper", "hem"), ("under", "hem"),
])
def test_edge_anchored_on_the_hem_corner_matches_within_the_d13_gap(
        sleeve, jacket_reference, part, edge):
    ref = jacket_reference["sleeve_block"][part]["edges"][edge]
    dev = max_deviation_to_polyline(sleeve[1].edge(part, edge), ref)
    assert dev < B_HEM_TOL_MM, f"{part} {edge} deviates {dev:.2f} mm from the drawing"


def test_back_seam_bellies_match_the_drawing(sleeve, jacket_reference):
    ref = jacket_reference["sleeve_block"]
    for part in ("upper", "under"):
        widest = max(p.x for p in sleeve[1].edge(part, "back_seam"))
        assert widest == pytest.approx(ref[part]["landmarks"]["belly_back"][0], abs=1.5)


# ---- derived lengths -------------------------------------------------------

def test_cap_length_and_ease_match_the_drawing(sleeve):
    """Drawn cap seam 54.90 cm against an armhole of 53.30: the booklet's own
    size-50 sleeve carries under 3 % ease, below the 4 - 6 % it asks for (D17)."""
    _, s = sleeve
    assert s.report["cap_len_mm"] == pytest.approx(549.0, abs=2.0)
    assert s.report["cap_ease_mm"] == pytest.approx(
        s.report["cap_len_mm"] - s.report["armhole_circ_mm"])
    assert 2.0 < s.report["cap_ease_pct"] < 4.0


def test_back_seams_are_almost_equal(sleeve):
    """Upper and under sleeve are sewn together down the back: 60.92 vs 60.83
    on the drawing."""
    _, s = sleeve
    assert abs(s.report["back_seam_upper_mm"] - s.report["back_seam_under_mm"]) < 2.0
    assert s.report["back_seam_upper_mm"] == pytest.approx(609.2, abs=1.5)
    assert s.report["back_seam_under_mm"] == pytest.approx(608.4, abs=1.5)


def test_hem_width_matches_the_chart_sleeve_hem(sleeve):
    _, s = sleeve
    assert s.report["hem_len_mm"] == pytest.approx(SLEEVE_HEM_MM, abs=1.0)


def test_notches_sit_on_the_upper_sleeve_cap(sleeve):
    _, s = sleeve
    cap_front, cap = s.edge("upper", "cap_front"), s.edge("upper", "cap")
    assert s.notches["FAN"] == s.landmarks["FAN"]
    assert s.notches["Sp"] == s.landmarks["Sp"]
    assert distance(cap_front[-1], s.notches["FAN"]) < 1e-9
    assert distance(cap[0], s.notches["FAN"]) < 1e-9
    assert min(distance(p, s.notches["Sp"]) for p in cap) < 1e-9


# ---- formula invariants across sizes ---------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_sleeve_block_invariants(size):
    m = JacketMeasurements.from_cm(**SIZES[size])
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    s = draft_jacket_sleeve(m, back, front)
    lm, r = s.landmarks, s.report

    # the cap width is the diagonal FAN -> E, the cap height the biceps level
    assert distance(lm["FAN"], lm["E"]) == pytest.approx(r["sleeve_cap_width_mm"])
    assert r["levels_y_mm"]["biceps"] == pytest.approx(r["sleeve_cap_height_mm"])
    assert lm["FAN"].y == pytest.approx(
        r["sleeve_cap_height_mm"] - (m.scye_width_mm / 4 - 10.0))
    assert lm["Sp"].x == pytest.approx(lm["E"].x / 2 + SP_ADD_MM)

    # the front seams are the fold's two parallels, the hem the chart's Sh
    assert distance(lm["FST"], lm["UST"]) == pytest.approx(2 * FRONT_SEAM_OFFSET_MM)
    assert distance(lm["fold_hem"], lm["hem_front"]) == pytest.approx(2 * FRONT_SEAM_OFFSET_MM)
    assert distance(Point(0.0, r["levels_y_mm"]["front_hem"]), lm["B_hem"]) == pytest.approx(
        SLEEVE_HEM_MM / 2)
    assert lm["F_b"].x - lm["fold_elbow"].x == pytest.approx(SLEEVE_HEM_MM / 2 + BACK_FOLD_ADD_MM)

    # the under sleeve rejoins the back fold 9 cm below the elbow
    assert lm["merge_back"].y - lm["fold_elbow"].y == pytest.approx(BACK_MERGE_BELOW_ELBOW_MM)
    assert (distance(lm["F_b"], lm["merge_back"]) + distance(lm["merge_back"], lm["B_hem"])
            == pytest.approx(distance(lm["F_b"], lm["B_hem"])))

    # the cap is always longer than the armhole it is set into; the two back
    # seams stay close (they drift apart on big sizes because Sh is fixed, D13)
    assert r["cap_ease_mm"] > 0
    assert abs(r["back_seam_upper_mm"] - r["back_seam_under_mm"]) < 3.0

    # both pieces are simple closed polygons
    for part, edges in (("upper", s.upper), ("under", s.under)):
        assert Polygon([(p.x, p.y) for p in s.outline(part)]).is_simple
        assert distance(edges[-1][1][-1], edges[0][1][0]) < 1e-6


def test_part_and_edge_lookup_reject_unknown_names(sleeve):
    _, s = sleeve
    with pytest.raises(KeyError):
        s.edge("upper", "inseam")
    with pytest.raises(KeyError):
        s.edge("sleeve", "cap")
    with pytest.raises(KeyError):
        s.outline("sleeve")
