"""Accessory pieces: waistband, button fly, front pocket, back pocket, yoke, belt loop.

Dimensions per PDF pages 15-18:
- Waistband (p.15): waist + 1-3/8" fly stand + 3/8" SA x 2; height 1-1/2" + 3/8" SA x 2
- Belt loop (p.15): 1/2" x 2-1/2" finished. Pre-fold strip 1-1/4" x 3"
- Button fly (p.16): buttonhole side 1-3/4" wide x fly length;
                    button stand 1-3/4" x (fly length + 1")
- Front pocket (p.17): pocket bag 12" deep, pocket facing 4" deep
- Back pocket (p.18): 3-3/8" wide x ~5" tall
- Yoke (p.18): 1-1/2" finished + 5/8" SA x 2

Seam allowances per PDF p.4: 3/8" everywhere except center back / yoke seam (5/8").
"""
from .geometry import Point
from .pattern import PatternPiece
from .measurements import Measurements

INCH = 25.4
SA_3_8_IN_MM = 0.375 * INCH    # 9.525 mm
SA_5_8_IN_MM = 0.625 * INCH    # 15.875 mm


def _rect(x: float, y: float, w: float, h: float) -> list[Point]:
    """Return a closed-polygon-convention rectangle (no repeated first vertex)."""
    return [Point(x, y), Point(x + w, y), Point(x + w, y + h), Point(x, y + h)]


def build_waistband(m: Measurements) -> PatternPiece:
    width = m.waist_mm + 1.375 * INCH + SA_3_8_IN_MM * 2
    height = 1.5 * INCH + SA_3_8_IN_MM * 2
    return PatternPiece(
        name="waistband",
        outline=_rect(0, 0, width, height),
        labels=[(Point(width / 2, height / 2), "WAISTBAND x 1")],
    )


def build_belt_loop() -> PatternPiece:
    """Pre-fold strip: 3" long x 1-1/4" wide. Cut 5 of these."""
    width = 3.0 * INCH
    height = 1.25 * INCH
    return PatternPiece(
        name="belt_loop",
        outline=_rect(0, 0, width, height),
        labels=[(Point(width / 2, height / 2), "BELT LOOP x 5")],
    )


def build_button_fly(m: Measurements) -> dict[str, PatternPiece]:
    """Approximation: fly length ~ 70% of rise (covers from waist to crotch curve start)."""
    fly_length = m.rise_mm * 0.7
    fly_width = 1.75 * INCH

    bh_side = PatternPiece(
        name="fly_buttonhole_side",
        outline=_rect(0, 0, fly_width, fly_length),
        labels=[(Point(fly_width / 2, fly_length / 2), "BUTTONHOLE SIDE x 1")],
    )
    stand = PatternPiece(
        name="fly_button_stand",
        outline=_rect(0, 0, fly_width, fly_length + 1.0 * INCH),
        labels=[(Point(fly_width / 2, (fly_length + INCH) / 2), "BUTTON STAND x 1")],
    )
    return {"buttonhole_side": bh_side, "button_stand": stand}


def build_front_pocket(m: Measurements) -> dict[str, PatternPiece]:
    """Front pocket bag (12" deep) + pocket facing (4" deep).
    Width approximates half-waist + offset to clear the fly."""
    bag_w = m.waist_mm / 4 + 1 * INCH
    bag_h = 12 * INCH
    bag = PatternPiece(
        name="pocket_bag",
        outline=_rect(0, 0, bag_w, bag_h),
        labels=[(Point(bag_w / 2, bag_h / 2), "POCKET BAG x 2 (mirror)")],
    )
    facing = PatternPiece(
        name="pocket_facing",
        outline=_rect(0, 0, bag_w, 4 * INCH),
        labels=[(Point(bag_w / 2, 2 * INCH), "POCKET FACING x 2 (mirror)")],
    )
    return {"pocket_bag": bag, "pocket_facing": facing}


def build_back_pocket(m: Measurements) -> PatternPiece:
    """Back pocket 3-3/8" wide x ~5-1/2" tall, tapered toward the bottom."""
    width = 3.375 * INCH
    height = 5.5 * INCH
    # Tapered shape: top corners square, bottom narrows by ~25% to a point/short edge
    outline = [
        Point(0, 0),
        Point(width, 0),
        Point(width * 0.75, height),
        Point(width * 0.25, height),
    ]
    return PatternPiece(
        name="back_pocket",
        outline=outline,
        labels=[(Point(width / 2, height / 2), "BACK POCKET x 2 (mirror)")],
    )


def build_yoke(m: Measurements) -> PatternPiece:
    """Yoke: 1-1/2" finished height + 5/8" SA x 2 = ~2-3/4". Width = half waist."""
    h = 1.5 * INCH + SA_5_8_IN_MM * 2
    w = m.waist_mm / 2
    return PatternPiece(
        name="yoke",
        outline=_rect(0, 0, w, h),
        labels=[(Point(w / 2, h / 2), "YOKE x 2 (mirror)")],
        seam_allowance_mm=SA_5_8_IN_MM,
    )
