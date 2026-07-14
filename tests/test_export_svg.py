from jeans_pattern.export_svg import pattern_to_svg


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
