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
from .constants import INCH, SA_3_8_IN_MM, SA_5_8_IN_MM


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

    Pocket bag (PDF page 17): 12" deep, "one piece and folded down the center".
    Shape: U-shape with a CONCAVE cutout at the top-left for the pocket opening
    (matches the pocket-mouth curve on the front piece), a square top-right
    corner, and a rounded bottom. A vertical dashed construction line down the
    middle marks the fold.

    Width: waist/4 + 1" (slightly wider than the front piece's pocket-opening
    span so the bag clears the fly).
    Concave cutout: 1-1/8" wide x 1-1/8" tall (PDF page 17, "1-1/8 inch over
    and 1-1/8 inch down from the pocket curve").
    """
    from .geometry import bezier_curve

    width = m.waist_mm / 4 + 1 * INCH
    height = 12 * INCH
    cut_w = 1.125 * INCH         # pocket-opening cutout, horizontal extent
    cut_h = 1.125 * INCH         # pocket-opening cutout, vertical extent
    side_h = height * 0.55       # vertical straight portion of the side seams
    bottom_radius = width * 0.45 # rounding of the bottom corners

    # Outline (CW from top of pocket-opening cutout):
    #   (cut_w, 0) -> (width, 0)                top edge (right of cutout)
    #   (width, 0) -> (width, side_h)           right side straight
    #   convex bottom-right corner -> (width - bottom_radius, height)
    #   bottom edge -> (bottom_radius, height)
    #   convex bottom-left corner -> (0, side_h)
    #   left side straight -> (0, cut_h)
    #   concave cutout -> (cut_w, 0)
    outline: list[Point] = []
    outline.append(Point(cut_w, 0))
    outline.append(Point(width, 0))
    outline.append(Point(width, side_h))

    # Bottom-right convex corner: quadratic Bezier with control at the
    # would-be sharp corner (width, height).
    br = bezier_curve(
        Point(width, side_h),
        Point(width, height),
        Point(width - bottom_radius, height),
        n=12,
    )
    outline.extend(br[1:])

    outline.append(Point(bottom_radius, height))

    # Bottom-left convex corner.
    bl = bezier_curve(
        Point(bottom_radius, height),
        Point(0, height),
        Point(0, side_h),
        n=12,
    )
    outline.extend(bl[1:])

    outline.append(Point(0, cut_h))

    # Concave cutout at top-left: quadratic Bezier with control at the corner
    # (0, 0) — bows the curve into the missing-corner region so the polygon
    # excludes the corner just like a real pocket opening.
    cut = bezier_curve(
        Point(0, cut_h),
        Point(0, 0),
        Point(cut_w, 0),
        n=12,
    )
    outline.extend(cut[1:-1])

    # Construction line: vertical fold down the centre.
    fold_line = [Point(width / 2, 0), Point(width / 2, height)]

    bag = PatternPiece(
        name="pocket_bag",
        outline=outline,
        construction_lines=[fold_line],
        labels=[(Point(width / 2, height / 2), "POCKET BAG x 2 (fold on dashed)")],
    )

    # Pocket facing: same overall outline but only 4" deep — faces the outside
    # of the bag where it shows through the pocket opening.
    facing_h = 4 * INCH
    facing_outline: list[Point] = []
    facing_outline.append(Point(cut_w, 0))
    facing_outline.append(Point(width, 0))
    facing_outline.append(Point(width, facing_h))
    facing_outline.append(Point(0, facing_h))
    facing_outline.append(Point(0, cut_h))
    facing_cut = bezier_curve(
        Point(0, cut_h),
        Point(0, 0),
        Point(cut_w, 0),
        n=12,
    )
    facing_outline.extend(facing_cut[1:-1])

    facing = PatternPiece(
        name="pocket_facing",
        outline=facing_outline,
        labels=[(Point(width / 2, facing_h / 2), "POCKET FACING x 2 (mirror)")],
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
