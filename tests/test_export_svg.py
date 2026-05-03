from jeans_pattern.export_svg import pattern_to_svg
from jeans_pattern.pattern import build_full_pattern


def test_svg_is_valid_xml(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    svg = pattern_to_svg(pat)
    # SVG bytes should start with <?xml or <svg
    assert svg.startswith(b"<?xml") or svg.startswith(b"<svg")
    assert b"</svg>" in svg


def test_svg_contains_all_pieces(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    svg = pattern_to_svg(pat).decode()
    for piece in pat:
        assert piece.name in svg, f"piece {piece.name} not labelled in svg"


def test_svg_basic_style(default_measurements):
    pat = build_full_pattern(default_measurements, style="basic")
    svg = pattern_to_svg(pat).decode()
    # All 10 pieces should be present
    for piece in pat:
        assert piece.name in svg


def test_svg_dimensions_in_mm(default_measurements):
    """SVG width/height attributes use mm units (real-world scale)."""
    pat = build_full_pattern(default_measurements, style="updated")
    svg = pattern_to_svg(pat).decode()
    assert 'mm"' in svg, "SVG should declare width/height in mm"
