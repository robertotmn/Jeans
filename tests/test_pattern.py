from jeans_pattern.geometry import Point
from jeans_pattern.pattern import PatternPiece, Pattern

def test_pattern_piece_bbox():
    p = PatternPiece(name="front", outline=[Point(0,0), Point(100,0), Point(100,200), Point(0,200)])
    assert p.bbox() == (0, 0, 100, 200)

def test_pattern_piece_with_holes_and_labels():
    p = PatternPiece(
        name="front",
        outline=[Point(0,0), Point(10,0), Point(10,10), Point(0,10)],
        construction_lines=[[Point(0,5), Point(10,5)]],
        labels=[(Point(5,5), "FRONT")],
    )
    assert p.construction_lines[0][0] == Point(0,5)
    assert p.labels[0] == (Point(5,5), "FRONT")

def test_pattern_pieces_iteration():
    a = PatternPiece(name="a", outline=[Point(0,0), Point(1,0), Point(1,1)])
    b = PatternPiece(name="b", outline=[Point(0,0), Point(2,0), Point(2,2)])
    pat = Pattern(pieces=[a, b])
    assert [p.name for p in pat] == ["a", "b"]


def test_build_full_pattern_basic(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="basic")
    names = {p.name for p in pat}
    assert {"front", "back", "waistband", "fly_buttonhole_side", "fly_button_stand",
            "pocket_bag", "pocket_facing", "back_pocket", "yoke", "belt_loop"}.issubset(names)


def test_build_full_pattern_updated(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    assert any(p.name == "front" for p in pat)
    assert any(p.name == "back" for p in pat)


def test_build_full_pattern_unknown_style_raises(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    import pytest
    with pytest.raises(ValueError):
        build_full_pattern(default_measurements, style="bogus")


def test_build_full_pattern_pieces_have_valid_outlines(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    for piece in pat:
        assert len(piece.outline) >= 3, f"piece {piece.name} has degenerate outline"
        # bbox sanity: width and height both positive (in mm)
        x0, y0, x1, y1 = piece.bbox()
        assert x1 > x0, f"piece {piece.name} has zero width"
        assert y1 > y0, f"piece {piece.name} has zero height"


def _descriptive_label(piece):
    """Find the multi-word descriptive label (e.g. 'FRONT x 2 (mirror)') among
    a piece's labels. Letter-style landmarks are short identifiers (A, B, P_new,
    T_new, etc.); the descriptive label is the multi-word one with spaces and
    is positioned inside the outline."""
    return next((pt, txt) for pt, txt in piece.labels if " " in txt)


def test_front_label_inside_outline_basic(default_measurements):
    """The 'FRONT' label is positioned at K. Verify K falls inside the front outline."""
    from shapely.geometry import Polygon, Point as ShapelyPoint
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="basic")
    front = next(p for p in pat if p.name == "front")
    poly = Polygon([(p.x, p.y) for p in front.outline])
    label_point, _label_text = _descriptive_label(front)
    assert poly.contains(ShapelyPoint(label_point.x, label_point.y)), \
        f"front label at {label_point} falls outside the outline"


def test_front_label_inside_outline_updated(default_measurements):
    from shapely.geometry import Polygon, Point as ShapelyPoint
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    front = next(p for p in pat if p.name == "front")
    poly = Polygon([(p.x, p.y) for p in front.outline])
    label_point, _ = _descriptive_label(front)
    assert poly.contains(ShapelyPoint(label_point.x, label_point.y)), \
        f"updated front label at {label_point} falls outside the outline"


def test_back_label_inside_outline_updated(default_measurements):
    from shapely.geometry import Polygon, Point as ShapelyPoint
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    back = next(p for p in pat if p.name == "back")
    poly = Polygon([(p.x, p.y) for p in back.outline])
    label_point, _ = _descriptive_label(back)
    assert poly.contains(ShapelyPoint(label_point.x, label_point.y)), \
        f"updated back label at {label_point} falls outside the outline"


def test_all_pieces_are_simple_polygons_basic(default_measurements):
    """Every pattern piece must have a simple (non-self-intersecting) outline.
    Catches vertex-ordering bugs in draft modules."""
    from shapely.geometry import Polygon
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="basic")
    for piece in pat:
        poly = Polygon([(p.x, p.y) for p in piece.outline])
        assert poly.is_simple, f"piece {piece.name!r} has self-intersecting outline"


def test_all_pieces_are_simple_polygons_updated(default_measurements):
    from shapely.geometry import Polygon
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    for piece in pat:
        poly = Polygon([(p.x, p.y) for p in piece.outline])
        assert poly.is_simple, f"piece {piece.name!r} has self-intersecting outline"


def test_build_full_pattern_mueller_size50():
    from jeans_pattern.draft_mueller import MuellerMeasurements
    from jeans_pattern.pattern import build_full_pattern
    m = MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )
    pat = build_full_pattern(m, style="mueller")
    names = [p.name for p in pat]
    assert "front" in names and "back" in names


def test_build_full_pattern_mueller_includes_accessories():
    from jeans_pattern.draft_mueller import MuellerMeasurements
    from jeans_pattern.pattern import build_full_pattern
    m = MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )
    pat = build_full_pattern(m, style="mueller")
    names = {p.name for p in pat}
    assert names == {
        "front", "back", "waistband", "fly_shield", "fly_facing",
        "pocket_bag", "pocket_facing", "back_pocket", "yoke", "belt_loop",
    }


def test_build_full_pattern_mueller_rejects_landis_measurements(default_measurements):
    import pytest
    from jeans_pattern.pattern import build_full_pattern
    with pytest.raises(TypeError):
        build_full_pattern(default_measurements, style="mueller")


def test_build_full_pattern_mueller2_includes_accessories():
    from jeans_pattern.draft_mueller import MuellerMeasurements
    from jeans_pattern.pattern import build_full_pattern
    m = MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )
    pat = build_full_pattern(m, style="mueller2")
    names = {p.name for p in pat}
    assert names == {
        "front", "back", "waistband", "fly_shield", "fly_facing",
        "pocket_bag", "pocket_facing", "back_pocket", "yoke", "belt_loop",
    }


def test_build_full_pattern_mueller2_rejects_landis_measurements(default_measurements):
    import pytest
    from jeans_pattern.pattern import build_full_pattern
    with pytest.raises(TypeError):
        build_full_pattern(default_measurements, style="mueller2")
