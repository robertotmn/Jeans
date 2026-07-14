import pytest

from jeans_pattern.geometry import Point
from jeans_pattern.measurements import Measurements
from jeans_pattern.pattern import Pattern, PatternPiece


@pytest.fixture
def size50():
    """M&S chart sample, size 50 (booklet page 2). The page-3 drawing of this
    size is the ground truth in tests/data/ms_reference_size50.json."""
    return Measurements.from_cm(
        waistband=90.0, hip_girth=102.0, knee_girth=43.0, hem_width=38.0,
        outseam=102.0, inseam=82.0,
    )


@pytest.fixture
def mini_pattern():
    """Small hand-made pattern for exporter tests (no draft involved)."""
    front = PatternPiece(
        name="front",
        outline=[Point(0, 0), Point(300, 0), Point(250, 1000), Point(20, 1000)],
        construction_lines=[[Point(0, 500), Point(300, 500)]],
        labels=[(Point(150, 500), "FRONT x 2"), (Point(0, 0), "A")],
    )
    pocket = PatternPiece(
        name="pocket",
        outline=[Point(0, 0), Point(170, 0), Point(170, 180), Point(85, 210), Point(0, 180)],
    )
    return Pattern(pieces=[front, pocket])
