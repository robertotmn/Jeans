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
