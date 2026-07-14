import json
import math
import pathlib

import pytest

from jeans_pattern.geometry import Point
from jeans_pattern.measurements import Measurements
from jeans_pattern.pattern import Pattern, PatternPiece

REFERENCE_PATH = pathlib.Path(__file__).parent / "data" / "ms_reference_size50.json"


@pytest.fixture(scope="session")
def reference():
    """Size-50 ground truth measured from the booklet's scale drawing."""
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def max_deviation_to_polyline(gen: list[Point], ref_pts: list[list[float]]) -> float:
    """Max over generated points of the distance to the reference polyline."""
    ref = [Point(*p) for p in ref_pts]

    def d_pt(p: Point) -> float:
        best = float("inf")
        for a, b in zip(ref, ref[1:]):
            vx, vy = b.x - a.x, b.y - a.y
            L2 = vx * vx + vy * vy
            if L2 < 1e-12:
                continue
            t = max(0.0, min(1.0, ((p.x - a.x) * vx + (p.y - a.y) * vy) / L2))
            best = min(best, math.hypot(p.x - a.x - t * vx, p.y - a.y - t * vy))
        return best

    return max(d_pt(p) for p in gen)


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
