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


def test_build_full_pattern_is_transitional_stub(size50):
    """Until draft_ms lands (plan phases 3-6), the assembler returns an empty pattern."""
    pat = build_full_pattern(size50)
    assert list(pat) == []
