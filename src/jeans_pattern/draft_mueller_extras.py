"""Accessory pieces for the Mueller & Sohn Design 3069 jeans.

Dimensions per PDF pages 4-5. All in mm internally. The M&S system uses
metric throughout; we keep that convention.

Each builder takes a MuellerMeasurements instance and returns a PatternPiece
(or dict of pieces for fly and pocket which produce 2 pieces each).
"""
from .geometry import Point
from .pattern import PatternPiece
from .draft_mueller import MuellerMeasurements
from .constants import SA_3_8_IN_MM, SA_5_8_IN_MM

CM = 10.0    # cm to mm conversion


def _rect(x: float, y: float, w: float, h: float) -> list[Point]:
    return [Point(x, y), Point(x + w, y), Point(x + w, y + h), Point(x, y + h)]


def build_mueller_waistband(m: MuellerMeasurements) -> PatternPiece:
    """4 cm finished + SA on both sides; length = waist + 4 cm fly extension + closure overlap.
    M&S design uses zipper closure - overlap is shorter than button fly."""
    width = m.waistband_mm + 4.0 * CM + SA_3_8_IN_MM * 2
    height = 4.0 * CM + SA_3_8_IN_MM * 2
    return PatternPiece(
        name="waistband",
        outline=_rect(0, 0, width, height),
        labels=[(Point(width / 2, height / 2), "WAISTBAND x 1 (4cm)")],
    )


def build_mueller_belt_loop() -> PatternPiece:
    """5 belt loops finished 1.2 cm wide x 6 cm tall (pre-fold strip)."""
    width = 6.0 * CM
    height = 1.2 * CM * 4   # fold in 4 -> finished 1.2 cm wide
    return PatternPiece(
        name="belt_loop",
        outline=_rect(0, 0, width, height),
        labels=[(Point(width / 2, height / 2), "BELT LOOP x 5 (1.2cm finished)")],
    )


def build_mueller_zipper_fly(m: MuellerMeasurements) -> dict[str, PatternPiece]:
    """Two fly pieces for a 15 cm zipper closure: zipper shield (underlap) and
    topstitching panel."""
    fly_length = 15.0 * CM   # zipper length
    fly_width = 3.4 * CM     # topstitching width

    shield = PatternPiece(
        name="fly_shield",
        outline=_rect(0, 0, fly_width + 1.0 * CM, fly_length + 2.0 * CM),
        labels=[(Point((fly_width + CM) / 2, (fly_length + 2 * CM) / 2), "FLY SHIELD x 1")],
    )
    facing = PatternPiece(
        name="fly_facing",
        outline=_rect(0, 0, fly_width, fly_length + 1.0 * CM),
        labels=[(Point(fly_width / 2, (fly_length + CM) / 2), "FLY FACING x 1")],
    )
    return {"shield": shield, "facing": facing}


def build_mueller_front_pocket(m: MuellerMeasurements) -> dict[str, PatternPiece]:
    """Front pocket: bag (~24 cm deep) + facing (3 cm overlap on bag).
    Width derived from waist girth: half-front + room for hand."""
    bag_w = m.waistband_mm / 4 + 5.0 * CM
    bag_h = 24.0 * CM   # PDF page 5: "pocket length approx. 24"
    facing_h = 12.0 * CM   # half of bag

    bag = PatternPiece(
        name="pocket_bag",
        outline=_rect(0, 0, bag_w, bag_h),
        labels=[(Point(bag_w / 2, bag_h / 2), "POCKET BAG x 2 (mirror)")],
    )
    facing = PatternPiece(
        name="pocket_facing",
        outline=_rect(0, 0, bag_w, facing_h),
        labels=[(Point(bag_w / 2, facing_h / 2), "POCKET FACING x 2 (mirror)")],
    )
    return {"pocket_bag": bag, "pocket_facing": facing}


def build_mueller_back_pocket(m: MuellerMeasurements) -> PatternPiece:
    """Back patch pocket: ~17 cm wide top, tapering to ~13 cm bottom, ~17 cm tall.
    Standard 5-pocket jeans back pocket per PDF page 5."""
    top_w = 17.0 * CM
    bottom_w = 13.0 * CM
    height = 17.0 * CM
    margin = (top_w - bottom_w) / 2

    outline = [
        Point(0, 0),
        Point(top_w, 0),
        Point(top_w - margin, height),
        Point(margin, height),
    ]
    return PatternPiece(
        name="back_pocket",
        outline=outline,
        labels=[(Point(top_w / 2, height / 2), "BACK POCKET x 2 (mirror)")],
    )


def build_mueller_yoke(m: MuellerMeasurements) -> PatternPiece:
    """Back yoke: 4.5 cm at outseam tapering to 5 cm at centre back.
    Width = half of back waist (approx waistband / 4 + dart intake)."""
    width = m.waistband_mm / 4 + 3.0 * CM
    h_outseam = 4.5 * CM + SA_5_8_IN_MM * 2
    h_centre = 5.0 * CM + SA_5_8_IN_MM * 2

    outline = [
        Point(0, 0),
        Point(width, 0),
        Point(width, h_outseam),
        Point(0, h_centre),
    ]
    return PatternPiece(
        name="yoke",
        outline=outline,
        labels=[(Point(width / 2, max(h_outseam, h_centre) / 2), "YOKE x 2 (mirror, 5/8 SA)")],
        seam_allowance_mm=SA_5_8_IN_MM,
    )
