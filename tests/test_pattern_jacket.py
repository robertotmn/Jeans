"""Design 4041 assembly: the 17 pieces, their cut lines and the report, plus
the regression test that the fold rule added to `SeamAllowances.for_edges`
leaves the jeans pieces exactly as they were."""
import pytest
from shapely.geometry import Polygon

from tests.test_draft_jacket import SIZES
from jeans_pattern.measurements_jacket import JacketMeasurements
from jeans_pattern.pattern import SeamAllowances, build_jacket_pattern

EXPECTED_JACKET_PIECES = {
    "carre_davanti", "davanti", "pannello_petto", "fianchetto_davanti",
    "carre_dietro", "dietro", "fianchetto_dietro", "sopramanica", "sottomanica",
    "polsino", "colletto", "cinturino", "patta_taschino", "sacchetto_taschino",
    "listino_tasca_laterale", "sacchetto_tasca_laterale", "linguetta",
}


def bbox(pts):
    return (min(p.x for p in pts), min(p.y for p in pts),
            max(p.x for p in pts), max(p.y for p in pts))


def test_build_jacket_pattern_piece_set(size50_jacket):
    pat = build_jacket_pattern(size50_jacket)
    assert {p.name for p in pat} == EXPECTED_JACKET_PIECES
    assert len(pat.pieces) == 17


def test_jacket_outlines_simple_with_allowances(size50_jacket):
    pat = build_jacket_pattern(size50_jacket)
    for piece in pat:
        net = Polygon([(p.x, p.y) for p in piece.outline])
        assert net.is_simple, piece.name
        assert piece.cut_outline is not None, piece.name
        cut = Polygon([(p.x, p.y) for p in piece.cut_outline])
        assert cut.is_simple, piece.name
        assert cut.contains(net.buffer(-0.05)), f"{piece.name}: cut line inside the net line"


def test_jacket_outlines_simple_without_allowances(size50_jacket):
    pat = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=0, hem_mm=0))
    for piece in pat:
        assert Polygon([(p.x, p.y) for p in piece.outline]).is_simple, piece.name


def test_allowances_disabled(size50_jacket):
    pat = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=0, hem_mm=0))
    assert all(p.cut_outline is None for p in pat)


def test_fold_edges_get_no_allowance(size50_jacket):
    """The waistband's c.b. fold (x max) and the cuff's long fold (y max) stay
    on the net line; every other side of those rectangles is out by seam_mm."""
    pat = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=15.0, hem_mm=30.0))
    band = next(p for p in pat if p.name == "cinturino")
    x0, y0, x1, y1 = bbox(band.outline)
    cx0, cy0, cx1, cy1 = bbox(band.cut_outline)
    assert (cx0, cy0, cy1) == pytest.approx((x0 - 15.0, y0 - 15.0, y1 + 15.0), abs=0.01)
    assert cx1 == pytest.approx(x1, abs=0.01)          # fold_cb

    cuff = next(p for p in pat if p.name == "polsino")
    x0, y0, x1, y1 = bbox(cuff.outline)
    cx0, cy0, cx1, cy1 = bbox(cuff.cut_outline)
    assert (cx0, cy0, cx1) == pytest.approx((x0 - 15.0, y0 - 15.0, x1 + 15.0), abs=0.01)
    assert cy1 == pytest.approx(y1, abs=0.01)          # fold_edge


def test_jacket_report(size50_jacket):
    """Size-50 report against the values the block and the design produce
    (plan, "Valori generati alla 50")."""
    r = build_jacket_pattern(size50_jacket).report
    assert r["model"] == "jacket"
    assert r["scye_depth_mm"] == pytest.approx(250.0)
    assert r["length_mm"] == pytest.approx(640.0)
    assert r["chest_ease_mm"] == pytest.approx(75.0)          # Bw+Sw+Cw - 1/2 Cg
    assert r["hip_ease_mm"] == pytest.approx(54.1, abs=0.5)   # > 1/2 Hg + 5: no warning
    assert r["armhole_circ_mm"] == pytest.approx(531.15, abs=0.5)
    assert r["sleeve_cap_height_mm"] == pytest.approx(161.0, abs=0.5)
    assert abs(r["sleeve_cap_ease_mm"]) < 1.0                 # normalised by the slash
    assert r["neckline_mm"] == pytest.approx(258.27, abs=0.5)
    assert abs(r["collar_correction_mm"]) < 2.5
    assert r["waistband_len_mm"] == pytest.approx(582.31, abs=0.5)
    assert r["cuff_len_mm"] == pytest.approx(313.07, abs=0.5)   # drawn 314.0
    assert r["warnings"] == []


@pytest.mark.parametrize("size", SIZES)
def test_jacket_pattern_other_sizes(size):
    pat = build_jacket_pattern(JacketMeasurements.from_cm(**SIZES[size]))
    assert {p.name for p in pat} == EXPECTED_JACKET_PIECES
    for piece in pat:
        assert Polygon([(p.x, p.y) for p in piece.cut_outline]).is_simple, piece.name
    # the matched seams close on every size: the only warnings left are the two
    # the block already declares (hip ease at 44, clamped cap ease at 56/62)
    for w in pat.report["warnings"]:
        assert w.startswith("Check Hg") or w.startswith("agio testa"), w


# ---------------------------------------------------------------------------
# Jeans regression: the fold rule must be inert on Design 3069
# ---------------------------------------------------------------------------

def jeans_drafts(m):
    from jeans_pattern.draft_ms import draft_back, draft_front
    from jeans_pattern.draft_ms_extras import (
        build_back_pocket, build_belt_loop_strip, build_coin_pocket,
        build_fly_facing, build_fly_shield, build_front_pocket_bag,
        build_front_pocket_facing, build_waistband, build_yoke)
    front = draft_front(m)
    back = draft_back(m, front)
    return [front, back, build_yoke(back), build_waistband(m, front),
            build_back_pocket(back), build_front_pocket_bag(m, front),
            build_front_pocket_facing(m, front), build_fly_facing(),
            build_fly_shield(), build_coin_pocket(), build_belt_loop_strip()]


def test_jeans_edges_keep_the_old_allowance_map(size50):
    """No jeans edge is named fold*, so for_edges still returns hem_mm on the
    hem and seam_mm everywhere else - the mapping of before the jacket."""
    sa = SeamAllowances(seam_mm=12.0, hem_mm=30.0)
    hems = 0
    for draft in jeans_drafts(size50):
        names = [name for name, _pts in draft.edges]
        assert not any(name.startswith("fold") for name in names), names
        assert sa.for_edges(draft.edges) == {n: (30.0 if n == "hem" else 12.0)
                                             for n in names}
        hems += names.count("hem")
    assert hems > 0            # the mapping above is not vacuous
