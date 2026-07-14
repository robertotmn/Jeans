import pytest

from jeans_pattern.geometry import Point
from jeans_pattern.pattern import Pattern, PatternPiece, build_full_pattern


def test_pattern_piece_bbox():
    p = PatternPiece(name="front", outline=[Point(0, 0), Point(100, 0), Point(100, 200), Point(0, 200)])
    assert p.bbox() == (0, 0, 100, 200)


def test_bbox_includes_construction_lines():
    p = PatternPiece(
        name="front",
        outline=[Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)],
        construction_lines=[[Point(-5, 5), Point(15, 5)]],
    )
    assert p.bbox() == (-5, 0, 15, 10)


def test_pattern_pieces_iteration():
    a = PatternPiece(name="a", outline=[Point(0, 0), Point(1, 0), Point(1, 1)])
    b = PatternPiece(name="b", outline=[Point(0, 0), Point(2, 0), Point(2, 2)])
    pat = Pattern(pieces=[a, b])
    assert [p.name for p in pat] == ["a", "b"]


def test_degenerate_outline_rejected():
    with pytest.raises(ValueError):
        PatternPiece(name="bad", outline=[Point(0, 0), Point(1, 1)])


def test_self_intersecting_outline_rejected():
    # bow-tie polygon
    with pytest.raises(ValueError):
        PatternPiece(name="bowtie", outline=[Point(0, 0), Point(10, 10), Point(10, 0), Point(0, 10)])


EXPECTED_PIECES = {
    "davanti", "dietro", "carre", "cinturino", "tasca_posteriore",
    "sacchetto_tasca", "paramontura_tasca", "paramontura_patta",
    "scudo_patta", "taschino", "passanti",
}


def test_build_full_pattern_piece_set(size50):
    pat = build_full_pattern(size50)
    assert {p.name for p in pat} == EXPECTED_PIECES


def test_build_full_pattern_outlines_simple_with_allowances(size50):
    from shapely.geometry import Polygon
    pat = build_full_pattern(size50)
    for piece in pat:
        assert Polygon([(p.x, p.y) for p in piece.outline]).is_simple, piece.name
        assert piece.cut_outline is not None, piece.name
        cut = Polygon([(p.x, p.y) for p in piece.cut_outline])
        assert cut.is_simple, piece.name
        net = Polygon([(p.x, p.y) for p in piece.outline])
        assert cut.contains(net.buffer(-0.05)), f"{piece.name}: cut line does not contain the net line"


def test_allowance_distances(size50):
    """Hem edge offset 30, seam edges 10 (sampled on the front piece)."""
    from shapely.geometry import LineString, Point as ShPoint
    from jeans_pattern.pattern import SeamAllowances
    pat = build_full_pattern(size50, SeamAllowances(seam_mm=10, hem_mm=30))
    front = next(p for p in pat if p.name == "davanti")
    cut = LineString([(p.x, p.y) for p in front.cut_outline] + [(front.cut_outline[0].x, front.cut_outline[0].y)])
    hem_mid = ShPoint(133.0, 1020.0)         # centre of the hem edge
    assert cut.distance(hem_mid) == pytest.approx(30.0, abs=0.5)
    seam_pt = ShPoint(228.0, 400.0)          # inside the leg, nearest edge = inseam
    net = LineString([(p.x, p.y) for p in front.outline])
    d_net = net.distance(seam_pt)
    d_cut = cut.distance(seam_pt)
    assert d_cut - d_net == pytest.approx(10.0, abs=1.0)


def test_allowances_disabled(size50):
    from jeans_pattern.pattern import SeamAllowances
    pat = build_full_pattern(size50, SeamAllowances(seam_mm=0, hem_mm=0))
    assert all(p.cut_outline is None for p in pat)


def test_report_contents(size50):
    pat = build_full_pattern(size50)
    r = pat.report
    assert r["body_rise_mm"] == pytest.approx(200.0)
    assert r["knee_length_mm"] == pytest.approx(472.0)
    assert 15.0 < r["hip_ease_mm"] < 30.0
    assert r["warnings"] == []


def test_build_full_pattern_other_sizes():
    from jeans_pattern.measurements import Measurements
    from shapely.geometry import Polygon
    for kwargs in (
        dict(waistband=78, hip_girth=94, knee_girth=40, hem_width=35, outseam=100, inseam=80),
        dict(waistband=110, hip_girth=118, knee_girth=48, hem_width=42, outseam=106, inseam=84),
    ):
        pat = build_full_pattern(Measurements.from_cm(**kwargs))
        assert {p.name for p in pat} == EXPECTED_PIECES
        for piece in pat:
            assert Polygon([(p.x, p.y) for p in piece.cut_outline]).is_simple, piece.name
