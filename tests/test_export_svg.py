from jeans_pattern.export_svg import pattern_to_svg
from jeans_pattern.pattern import SeamAllowances, build_jacket_pattern


def test_svg_is_valid_xml(mini_pattern):
    svg = pattern_to_svg(mini_pattern)
    assert svg.startswith(b"<?xml") or svg.startswith(b"<svg")
    assert b"</svg>" in svg


def test_svg_contains_all_pieces(mini_pattern):
    svg = pattern_to_svg(mini_pattern).decode()
    for piece in mini_pattern:
        assert piece.name in svg, f"piece {piece.name} not labelled in svg"


def test_svg_dimensions_in_mm(mini_pattern):
    """SVG width/height attributes use mm units (real-world scale)."""
    svg = pattern_to_svg(mini_pattern).decode()
    assert 'mm"' in svg, "SVG should declare width/height in mm"


# ---------------------------------------------------------------------------
# The real Design 4041 pattern: 17 pieces, fold edges at allowance 0, hundreds
# of construction lines and one label placed outside its own bounding box.
# ---------------------------------------------------------------------------

def test_svg_contains_every_jacket_piece(size50_jacket):
    jacket = build_jacket_pattern(size50_jacket)
    svg = pattern_to_svg(jacket).decode()
    assert len(jacket.pieces) == 17
    for piece in jacket:
        assert piece.name in svg, f"piece {piece.name} not labelled in svg"
    assert svg.count("</svg>") == 1


def test_svg_jacket_draws_cut_and_net_lines(size50_jacket):
    """One polygon per piece for the net line, a second for the cut line; with
    the allowances off only the net polygons are left."""
    with_sa = pattern_to_svg(build_jacket_pattern(size50_jacket)).decode()
    assert with_sa.count("<polygon") == 34

    net_only = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=0, hem_mm=0))
    assert all(p.cut_outline is None for p in net_only)
    assert pattern_to_svg(net_only).decode().count("<polygon") == 17
