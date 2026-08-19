"""Design 4041 pieces vs the booklet's own size-50 scale drawings (pages 14-15,
extracted into tests/data/ms_jacket_reference_size50.json) plus parametric
invariants on other sizes."""
import pytest
from shapely.geometry import Polygon

from tests.conftest import max_deviation_to_polyline
from tests.test_draft_jacket import SIZES
from jeans_pattern.draft_jacket import (
    draft_jacket_back, draft_jacket_front, draft_jacket_sleeve)
from jeans_pattern.draft_jacket_design import (
    BACK_PANEL_AT_HEM_MM, BACK_PANEL_FROM_ARMHOLE_MM, BACK_YOKE_DOWN_MM,
    BUTTONHOLE_BELOW_NECK_MM, COLLAR_TOL_MM, CUFF_HEIGHT_MM, FLAP_POINT_MM,
    FLAP_SIDE_MM, FLAP_WIDTH_MM, FRONT_YOKE_ABOVE_BH2_MM, NECK_LOWER_CB_MM,
    NECK_LOWER_SHOULDER_MM, OVERLAP_MM, PINTUCK_SPREAD_MM,
    POCKET_BAG_POINT_MM, POCKET_BAG_SIDE_MM, POCKET_OPENING_WIDTH_MM,
    POCKET_WELT_MM, SIDE_POCKET_LEN_MM, SIDE_POCKET_WELT_MM, SLEEVE_VENT_MM,
    TAB_BUTTONS_MM, TAB_HEIGHT_MM, TAB_LEN_MM, WAISTBAND_HEIGHT_MM,
    build_back_centre, build_back_side_panel, build_back_yoke,
    build_chest_pocket_bag, build_chest_pocket_flap, build_collar, build_cuff,
    build_front_centre, build_front_chest_panel, build_front_side_panel,
    build_front_yoke, build_jacket_waistband, build_side_pocket_bag,
    build_side_pocket_welt, build_tab, design_body, front_jacket_marks,
    split_sleeve,
)
from jeans_pattern.geometry import Point, arc_length, distance
from jeans_pattern.measurements_jacket import JacketMeasurements

PIECE_NAMES = [
    "carre_davanti", "davanti", "pannello_petto", "fianchetto_davanti",
    "carre_dietro", "dietro", "fianchetto_dietro", "sopramanica", "sottomanica",
    "polsino", "colletto", "cinturino", "patta_taschino", "sacchetto_taschino",
    "listino_tasca_laterale", "sacchetto_tasca_laterale", "linguetta",
]
LANDMARK_TOL_MM = 2.5
CURVE_TOL_MM = 2.0


def build(size: str):
    m = JacketMeasurements.from_cm(**SIZES[size])
    back = draft_jacket_back(m)
    front = draft_jacket_front(m, back)
    sleeve = draft_jacket_sleeve(m, back, front)
    db = design_body(back, front)
    marks = front_jacket_marks(db)
    top, under = split_sleeve(sleeve)
    pieces = [build_front_yoke(db, marks), build_front_centre(db, marks),
              build_front_chest_panel(db, marks), build_front_side_panel(db, marks),
              build_back_yoke(db), build_back_centre(db), build_back_side_panel(db),
              top, under, build_cuff(top, under), build_collar(db),
              build_jacket_waistband(db), build_chest_pocket_flap(),
              build_chest_pocket_bag(), build_side_pocket_welt(),
              build_side_pocket_bag(), build_tab()]
    return m, back, front, sleeve, db, {p.name: p for p in pieces}


@pytest.fixture(scope="module")
def design():
    return build("50")


@pytest.fixture(scope="module")
def to_body(design):
    """The page-14 front frame (x on the pitch line, y on the chest line) sits
    on the block frame by a plain translation."""
    m, _back, front, _sleeve, _db, _pieces = design
    x_pitch, sd = front.landmarks["P_top"].x, m.scye_depth_mm
    return lambda p: Point(p[0] + x_pitch, p[1] + sd)


# ---- the seventeen pieces --------------------------------------------------

def test_every_piece_is_a_simple_closed_polygon(design):
    pieces = design[5]
    assert sorted(pieces) == sorted(PIECE_NAMES)
    for name, piece in pieces.items():
        outline = piece.outline()
        assert Polygon([(p.x, p.y) for p in outline]).is_simple, f"{name} self-intersects"
        assert distance(piece.edges[-1][1][-1], piece.edges[0][1][0]) < 1e-6, \
            f"{name} edge chain does not close"


def test_folded_edges_are_named_for_the_allowance_rule(design):
    """D27: fold edges start with `fold_`, and no jacket edge is called `hem`."""
    pieces = design[5]
    for name in ("carre_dietro", "dietro", "carre_davanti", "davanti",
                 "colletto", "cinturino", "polsino"):
        assert any(e.startswith("fold_") for e, _pts in pieces[name].edges), name
    for name, piece in pieces.items():
        assert "hem" not in [e for e, _pts in piece.edges], name


# ---- design landmarks vs the drawing ---------------------------------------

@pytest.mark.parametrize("ours,book", [
    ("neck_cb", "neck_cb"), ("neck_shoulder_b", "neck_shoulder"),
    ("hem_cb", "hem_cb"), ("side_hem_b", "side_hem"), ("BAN", "BAN"),
])
def test_back_design_landmark_matches_book(design, jacket_reference, ours, book):
    ref = Point(*jacket_reference["design_body"]["back"]["landmarks"][book])
    assert distance(design[4].landmarks[ours], ref) < LANDMARK_TOL_MM


@pytest.mark.parametrize("ours,book", [
    ("neck_cf", "neck_cf"), ("edge_top", "edge_top"),
    ("neck_shoulder_f", "neck_shoulder"), ("hem_cf", "hem_cf"),
    ("edge_hem", "hem_edge"), ("side_hem_f", "side_hem"),
])
def test_front_design_landmark_matches_book(design, jacket_reference, to_body, ours, book):
    ref = to_body(jacket_reference["design_body"]["front"]["landmarks"][book])
    assert distance(design[4].landmarks[ours], ref) < LANDMARK_TOL_MM


@pytest.mark.parametrize("side,edge,book", [
    ("back", "neck", "neck"), ("back", "armhole", "armhole"),
    ("back", "side", "side"), ("back", "waistband_seam", "hem"),
    ("front", "neck", "neck"), ("front", "armhole", "armhole"),
    ("front", "side", "side"), ("front", "waistband_seam", "hem"),
])
def test_design_outline_matches_book(design, jacket_reference, to_body, side, edge, book):
    ref = jacket_reference["design_body"][side]["edges"][book]
    if side == "front":
        ref = [[to_body(p).x, to_body(p).y] for p in ref]
    dev = max_deviation_to_polyline(design[4].edge(side, edge), ref)
    assert dev < CURVE_TOL_MM, f"{side} {edge} deviates {dev:.2f} mm from the drawing"


def test_buttonholes_sit_where_the_book_puts_them(design, jacket_reference, to_body):
    lm = design[4].landmarks
    ref = jacket_reference["design_body"]["front"]["landmarks"]["buttonholes"]
    for i, p in enumerate(ref, start=1):
        assert distance(lm[f"button{i}"], to_body(p)) < 6.0
        # the drawn slot centre sits ~0.55 cm inside the c.f.; the y placement
        # is the part the booklet actually prescribes
        assert abs(lm[f"button{i}"].y - to_body(p).y) < LANDMARK_TOL_MM


# ---- the rules the booklet states ------------------------------------------

def test_yoke_and_panel_seams_follow_the_book(design):
    db = design[4]
    lm, r = db.landmarks, db.report
    assert distance(lm["neck_cb"], lm["yoke_cb"]) == pytest.approx(BACK_YOKE_DOWN_MM)
    assert distance(lm["yoke_ah_b"], lm["panel_top_b"]) == pytest.approx(
        BACK_PANEL_FROM_ARMHOLE_MM)
    # the hem splits 1/2 - 2 cm on the side seam, 1/2 + 2 cm at the c.b.
    assert distance(lm["side_hem_b"], lm["panel_hem_b"]) == pytest.approx(
        r["back_hem_mm"] / 2 - BACK_PANEL_AT_HEM_MM)
    assert distance(lm["panel_hem_b"], lm["hem_cb"]) == pytest.approx(
        r["back_hem_mm"] / 2 + BACK_PANEL_AT_HEM_MM)
    assert r["back_yoke_mm"] == pytest.approx(221.9, abs=1.5)
    assert r["back_panel_mm"] == pytest.approx(461.1, abs=1.5)


def test_neckline_is_lowered_by_the_quoted_amounts(design):
    _m, back, front, _sleeve, db, _pieces = design
    lm = db.landmarks
    assert distance(back.landmarks["N"], lm["neck_cb"]) == pytest.approx(NECK_LOWER_CB_MM)
    assert distance(back.landmarks["HSP_b"], lm["neck_shoulder_b"]) == pytest.approx(
        NECK_LOWER_SHOULDER_MM)
    assert distance(front.landmarks["HSP_f"], lm["neck_shoulder_f"]) == pytest.approx(
        NECK_LOWER_SHOULDER_MM)
    assert db.report["shoulder_back_mm"] == pytest.approx(146.6, abs=1.5)
    assert db.report["shoulder_front_mm"] == pytest.approx(141.8, abs=1.5)


def test_front_yoke_and_buttonholes_are_evenly_distributed(design):
    db = design[4]
    lm = db.landmarks
    assert distance(lm["neck_cf"], lm["button1"]) == pytest.approx(BUTTONHOLE_BELOW_NECK_MM)
    assert distance(lm["hem_cf"], lm["button5"]) == pytest.approx(WAISTBAND_HEIGHT_MM / 2)
    steps = [distance(lm[f"button{i}"], lm[f"button{i + 1}"]) for i in range(1, 5)]
    assert max(steps) - min(steps) < 1e-6
    assert db.report["buttonhole_pitch_mm"] == pytest.approx(131.0, abs=1.5)
    assert lm["yoke_edge_f"].y == pytest.approx(lm["button2"].y - FRONT_YOKE_ABOVE_BH2_MM)
    assert db.report["front_yoke_mm"] == pytest.approx(224.8, abs=1.5)


def test_front_edge_is_the_two_centimetre_overlap(design):
    db = design[4]
    lm = db.landmarks
    assert distance(lm["neck_cf"], lm["edge_top"]) == pytest.approx(OVERLAP_MM)
    assert distance(lm["hem_cf"], lm["edge_hem"]) == pytest.approx(OVERLAP_MM)
    cf = db.lines["cf"]
    assert max_deviation_to_polyline(db.lines["fold_edge"],
                                     [[cf[0].x + OVERLAP_MM, cf[0].y],
                                      [cf[1].x + OVERLAP_MM, cf[1].y]]) < 0.5


# ---- collar ----------------------------------------------------------------

def test_collar_seam_matches_the_lowered_neckline(design):
    db, collar = design[4], design[5]["colletto"]
    r = collar.report
    assert r["baseline_mm"] == pytest.approx(db.report["neckline_mm"])
    assert abs(r["neck_seam_mm"] - db.report["neckline_mm"]) < COLLAR_TOL_MM
    assert r["correction_mm"] == pytest.approx(db.report["neckline_mm"] - r["neck_seam_mm"])
    assert r["warnings"] == []


def test_collar_heights_match_the_book(design, jacket_reference):
    collar = design[5]["colletto"]
    ref = jacket_reference["design_body"]["collar"]["landmarks"]
    seam = dict(collar.edges)["neck_seam"]
    fold = dict(collar.edges)["fold_cb"]
    assert seam[0].y == pytest.approx(ref["cf_seam"][1], abs=0.5)          # 1 cm at the c.f.
    assert fold[0].y == pytest.approx(ref["cb_seam"][1], abs=0.5)          # 1.5 at the c.b.
    assert fold[1].y == pytest.approx(ref["cb_top"][1], abs=0.5)           # 9.5 at the c.b.
    point = dict(collar.edges)["front"][0]
    assert point.x == pytest.approx(ref["point"][0], abs=0.5)              # 2.5 past the c.f.
    assert point.y == pytest.approx(ref["point"][1], abs=0.5)              # 7.5 at the c.f.
    touch = min(seam, key=lambda p: p.y)
    assert touch.x == pytest.approx(collar.report["baseline_mm"] / 3, abs=1.0)
    assert touch.y == pytest.approx(0.0, abs=0.1)


def test_collar_curves_match_the_drawing(design, jacket_reference):
    collar = design[5]["colletto"]
    ref = jacket_reference["design_body"]["collar"]["outline"]
    for name in ("neck_seam", "outer"):
        dev = max_deviation_to_polyline(dict(collar.edges)[name], ref)
        assert dev < CURVE_TOL_MM, f"collar {name} deviates {dev:.2f} mm"
    roll = jacket_reference["design_body"]["collar"]["lines"]["roll"]
    assert max_deviation_to_polyline(collar.construction_lines[0], roll) < CURVE_TOL_MM


# ---- waistband, tab, cuff --------------------------------------------------

def test_waistband_matches_the_hem_it_is_sewn_to(design, jacket_reference):
    db, band = design[4], design[5]["cinturino"]
    ref = jacket_reference["design_body"]["waistband"]
    r = band.report
    assert r["length_mm"] == pytest.approx(db.report["front_hem_mm"] + db.report["back_hem_mm"])
    assert r["height_mm"] == pytest.approx(WAISTBAND_HEIGHT_MM)
    assert r["length_mm"] == pytest.approx(ref["length_mm"], abs=LANDMARK_TOL_MM)
    assert r["cf_from_edge_mm"] == pytest.approx(ref["cf_from_edge_mm"])
    assert r["side_notch_mm"] == pytest.approx(ref["notches_from_edge_mm"][0], abs=LANDMARK_TOL_MM)
    assert r["panel_notch_mm"] == pytest.approx(ref["notches_from_edge_mm"][1], abs=LANDMARK_TOL_MM)


def test_tab_and_its_buttons_match_the_drawing(design, jacket_reference):
    ref = jacket_reference["design_body"]["waistband"]
    band, tab = design[5]["cinturino"], design[5]["linguetta"]
    assert tab.report["length_mm"] == pytest.approx(TAB_LEN_MM)
    assert tab.report["height_mm"] == pytest.approx(TAB_HEIGHT_MM)
    assert ref["tab_from_edge_mm"][1] - ref["tab_from_edge_mm"][0] == pytest.approx(
        TAB_LEN_MM, abs=1.0)
    assert ref["tab_height_mm"] == pytest.approx(TAB_HEIGHT_MM, abs=0.5)
    drawn = [b[0] - ref["tab_from_edge_mm"][0] for b in ref["buttons_mm"]]
    for ours, book in zip(TAB_BUTTONS_MM, drawn):
        assert ours == pytest.approx(book, abs=1.0)
    assert band.report["side_notch_mm"] == pytest.approx(
        ref["tab_from_edge_mm"][0], abs=LANDMARK_TOL_MM)


def test_cuff_matches_the_shortened_sleeve_hem(design, jacket_reference):
    pieces = design[5]
    cuff = pieces["polsino"]
    assert cuff.report["height_mm"] == pytest.approx(CUFF_HEIGHT_MM)
    assert cuff.report["length_mm"] == pytest.approx(
        pieces["sopramanica"].report["hem_len_mm"]
        + pieces["sottomanica"].report["hem_len_mm"])
    assert cuff.report["length_mm"] == pytest.approx(
        jacket_reference["design_sleeve"]["cuff"]["length_mm"], abs=1.5)


# ---- sleeve ----------------------------------------------------------------

def test_sleeve_is_shortened_by_the_cuff_width(design, jacket_reference):
    sleeve, pieces = design[3], design[5]
    for name, part in (("sopramanica", "upper"), ("sottomanica", "under")):
        ref = jacket_reference["design_sleeve"][part]["landmarks"]["hem_back"]
        hem = dict(pieces[name].edges)["cuff_seam"]
        assert distance(hem[0], Point(*ref)) < LANDMARK_TOL_MM
        assert distance(hem[0], sleeve.landmarks["B_hem"]) == pytest.approx(CUFF_HEIGHT_MM)


def test_front_sleeve_seam_is_blended(design, jacket_reference):
    """The kinked elbow of the block becomes one smooth curve, same ends."""
    pieces = design[5]
    ref = jacket_reference["design_sleeve"]["under"]["edges"]["front_seam"]
    seam = dict(pieces["sottomanica"].edges)["front_seam"]
    assert max_deviation_to_polyline(seam, ref) < CURVE_TOL_MM
    elbow = min(seam, key=lambda p: abs(p.y - design[3].landmarks["elbow_front"].y))
    assert distance(elbow, design[3].landmarks["elbow_front"]) < 1.0


@pytest.mark.parametrize("name,part", [("sopramanica", "upper"), ("sottomanica", "under")])
def test_sleeve_back_seam_and_vent_match_the_drawing(design, jacket_reference, name, part):
    ref_edges = jacket_reference["design_sleeve"][part]["edges"]
    ref = ref_edges["back_seam"] + ref_edges["back_fold"][1:]
    piece = design[5][name]
    assert max_deviation_to_polyline(dict(piece.edges)["back_seam"], ref) < CURVE_TOL_MM
    assert piece.report["vent_mm"] == pytest.approx(SLEEVE_VENT_MM)


def test_cap_ease_is_taken_out_by_the_slash(design):
    sleeve, pieces = design[3], design[5]
    caps = (pieces["sopramanica"].report["cap_len_mm"]
            + pieces["sottomanica"].report["cap_len_mm"])
    assert sleeve.report["cap_ease_mm"] > 15.0        # the block carries 1.8 cm
    assert abs(caps - sleeve.report["armhole_circ_mm"]) < 1.0
    assert pieces["sopramanica"].report["warnings"] == []
    # only the upper sleeve turns; the under one keeps the block's cap
    assert pieces["sottomanica"].report["pivot_deg"] == pytest.approx(
        pieces["sopramanica"].report["pivot_deg"])
    assert 0.0 < pieces["sopramanica"].report["pivot_deg"] < 3.0


def test_cap_ease_warns_when_the_slash_is_clamped():
    """Big sizes carry more block ease than a 2.5 cm slash can absorb."""
    _m, _b, _f, sleeve, _db, pieces = build("62")
    assert pieces["sopramanica"].report["cap_ease_mm"] > 1.0
    assert any("agio testa" in w for w in pieces["sopramanica"].report["warnings"])


# ---- pockets, pintuck and the marks ----------------------------------------

def test_chest_pocket_quotes_match_the_book(design):
    db, pieces = design[4], design[5]
    flap = db.lines["pocket_flap"]
    assert distance(flap[0], flap[-1]) == pytest.approx(FLAP_WIDTH_MM)
    assert distance(flap[0], flap[1]) == pytest.approx(FLAP_SIDE_MM)
    assert flap[2].y - flap[0].y == pytest.approx(FLAP_POINT_MM)
    entry = db.lines["pocket_opening"]
    assert distance(entry[0], entry[1]) == pytest.approx(POCKET_OPENING_WIDTH_MM)
    assert distance(entry[1], entry[2]) == pytest.approx(POCKET_WELT_MM)
    assert entry[0].y - flap[0].y == pytest.approx(10.0)         # 1 cm below the yoke
    bag = db.lines["pocket_bag"]
    assert bag[1].y - entry[0].y == pytest.approx(POCKET_BAG_SIDE_MM)
    assert bag[2].y - entry[0].y == pytest.approx(POCKET_BAG_POINT_MM)
    assert pieces["patta_taschino"].report["width_mm"] == pytest.approx(FLAP_WIDTH_MM)
    assert pieces["sacchetto_taschino"].report["width_mm"] == pytest.approx(
        POCKET_OPENING_WIDTH_MM)


def test_chest_pocket_marks_match_the_drawing(design, jacket_reference, to_body):
    db = design[4]
    for ours, book in (("pocket_flap", "pocket_flap"), ("pocket_bag", "pocket_bag"),
                       ("pocket_axis", "pocket_axis")):
        ref = [[to_body(p).x, to_body(p).y]
               for p in jacket_reference["design_body"]["front"]["lines"][book]]
        assert max_deviation_to_polyline(db.lines[ours], ref) < LANDMARK_TOL_MM, ours


def test_side_pocket_is_a_slanted_sixteen_centimetre_welt(design, jacket_reference, to_body):
    db, pieces = design[4], design[5]
    lo, hi = db.landmarks["welt_lo"], db.landmarks["welt_hi"]
    assert distance(lo, hi) == pytest.approx(SIDE_POCKET_LEN_MM)
    assert hi.x - lo.x == pytest.approx(15.0)          # 1.5 cm short of the pitch line
    ref = [[to_body(p).x, to_body(p).y]
           for p in jacket_reference["design_body"]["front"]["lines"]["side_pocket_welt"]]
    assert max_deviation_to_polyline(db.lines["side_pocket_welt"], ref) < LANDMARK_TOL_MM
    assert pieces["listino_tasca_laterale"].report["length_mm"] == pytest.approx(
        SIDE_POCKET_LEN_MM)
    assert pieces["listino_tasca_laterale"].report["welt_mm"] == pytest.approx(
        SIDE_POCKET_WELT_MM)


def test_pintuck_slashes_the_centre_front_panel_open(design):
    db, front_panel = design[4], design[5]["davanti"]
    lm = db.landmarks
    yoke = dict(front_panel.edges)["yoke_seam"]
    assert arc_length(yoke) == pytest.approx(
        distance(lm["yoke_edge_f"], lm["panel_cf_top"]) + PINTUCK_SPREAD_MM, abs=0.01)
    assert front_panel.report["pintuck_spread_mm"] == pytest.approx(PINTUCK_SPREAD_MM)


def test_marks_are_clipped_panel_by_panel(design):
    """D20: the 12 cm pocket entry straddles both front panel seams, so each of
    the three panels below the yoke carries its own share of it."""
    db, pieces = design[4], design[5]
    entry_y = db.lines["pocket_opening"][0].y

    def share(piece) -> float:
        return sum(distance(p, q) for line in piece.construction_lines
                   for p, q in zip(line, line[1:])
                   if abs(p.y - entry_y) < 0.5 and abs(q.y - entry_y) < 0.5)

    shares = [share(pieces[n]) for n in
              ("davanti", "pannello_petto", "fianchetto_davanti")]
    assert all(s > 1.0 for s in shares), shares
    assert sum(shares) == pytest.approx(POCKET_OPENING_WIDTH_MM, abs=1.0)


# ---- invariants across sizes -----------------------------------------------

@pytest.mark.parametrize("size", SIZES)
def test_design_invariants(size):
    _m, back, front, sleeve, db, pieces = build(size)
    lm, r = db.landmarks, db.report

    assert sorted(pieces) == sorted(PIECE_NAMES)
    for name, piece in pieces.items():
        assert Polygon([(p.x, p.y) for p in piece.outline()]).is_simple, name
        assert distance(piece.edges[-1][1][-1], piece.edges[0][1][0]) < 1e-6, name

    # the design body is the block minus the waistband height and the lowering
    assert distance(back.landmarks["H_b"], lm["side_hem_b"]) == pytest.approx(
        WAISTBAND_HEIGHT_MM)
    assert distance(front.landmarks["C3"], lm["hem_cf"]) == pytest.approx(WAISTBAND_HEIGHT_MM)
    assert r["shoulder_back_mm"] - r["shoulder_front_mm"] == pytest.approx(5.0)

    # the bands are exactly as long as what they are sewn to
    assert pieces["cinturino"].report["length_mm"] == pytest.approx(
        r["front_hem_mm"] + r["back_hem_mm"])
    assert pieces["polsino"].report["length_mm"] == pytest.approx(
        pieces["sopramanica"].report["hem_len_mm"]
        + pieces["sottomanica"].report["hem_len_mm"])
    assert abs(pieces["colletto"].report["neck_seam_mm"] - r["neckline_mm"]) < COLLAR_TOL_MM

    # the cap never comes out longer than the block's, and never below the armhole
    caps = (pieces["sopramanica"].report["cap_len_mm"]
            + pieces["sottomanica"].report["cap_len_mm"])
    assert r["armhole_circ_mm"] <= caps < sleeve.report["cap_len_mm"]

    # the pieces cut out of the body add back up to it
    assert (pieces["carre_dietro"].report["yoke_seam_mm"]
            == pytest.approx(r["back_yoke_mm"]))
    assert (distance(lm["side_hem_b"], lm["panel_hem_b"])
            + distance(lm["panel_hem_b"], lm["hem_cb"])) == pytest.approx(r["back_hem_mm"])


def test_design_body_edge_lookup_rejects_unknown_names(design):
    db = design[4]
    with pytest.raises(KeyError):
        db.edge("back", "cf")
    with pytest.raises(KeyError):
        db.edge("sleeve", "cap")
