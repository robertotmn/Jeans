"""M. Mueller & Sohn 'Metric Pattern Techniques: Jeans-Basics' drafting system.

Reference: docs/source-spec/Metric-pattern-techniques_Jeans-Basics.pdf (Design 3069).
Native unit: cm. Internal app unit: mm. All formulas use mm.

Coordinate convention (matching the rest of the app):
- y=0 at waist line
- y grows DOWN toward hem
- x grows RIGHT toward outseam (front piece)

This module implements the Basic Jeans front + back. Dungarees, denim jacket,
and trucker jacket designs (PDF pages 6-18) are out of scope for this task.
"""
from dataclasses import dataclass

from .geometry import Point


CM_TO_MM = 10.0


@dataclass(frozen=True)
class MuellerMeasurements:
    """8 body measurements per the M&S Jeans-Basics chart (page 2).

    All values stored in mm internally. Use from_cm() factory for input.
    Auxiliary measurements (Ftw, Fcw, Bcw, Btw, hip_depth, knee_length) are
    DERIVED from these via formulas in property methods.
    """
    waistband_mm: float       # W
    hip_girth_mm: float        # Hg
    knee_girth_mm: float       # Kg
    hem_width_mm: float        # Hw (leg-opening circumference)
    outseam_mm: float          # Os
    inseam_mm: float           # Is
    body_rise_mm: float        # Br = Os - Is
    knee_length_mm: float      # Kl

    def __post_init__(self):
        for f, val in [("waistband", self.waistband_mm), ("hip_girth", self.hip_girth_mm),
                       ("knee_girth", self.knee_girth_mm), ("hem_width", self.hem_width_mm),
                       ("outseam", self.outseam_mm), ("inseam", self.inseam_mm),
                       ("body_rise", self.body_rise_mm), ("knee_length", self.knee_length_mm)]:
            if val <= 0:
                raise ValueError(f"{f} must be > 0, got {val}")

    @classmethod
    def from_cm(cls, *, waistband, hip_girth, knee_girth, hem_width,
                outseam, inseam, body_rise=None, knee_length=None):
        if body_rise is None:
            body_rise = outseam - inseam
        if knee_length is None:
            knee_length = inseam / 2 + inseam / 10 - 2
        return cls(
            waistband_mm=waistband * CM_TO_MM,
            hip_girth_mm=hip_girth * CM_TO_MM,
            knee_girth_mm=knee_girth * CM_TO_MM,
            hem_width_mm=hem_width * CM_TO_MM,
            outseam_mm=outseam * CM_TO_MM,
            inseam_mm=inseam * CM_TO_MM,
            body_rise_mm=body_rise * CM_TO_MM,
            knee_length_mm=knee_length * CM_TO_MM,
        )

    # Auxiliary derived measurements (in mm)
    @property
    def front_trouser_width_mm(self) -> float:
        """Ftw = 1/4 Hg"""
        return self.hip_girth_mm / 4

    @property
    def front_crotch_width_mm(self) -> float:
        """Fcw = 1/10 of 1/2 Hg = Hg/20"""
        return self.hip_girth_mm / 20

    @property
    def back_crotch_width_mm(self) -> float:
        """Bcw = 1/10 Hg + 2.0 cm (mid-range adjustment)"""
        return self.hip_girth_mm / 10 + 2.0 * CM_TO_MM

    @property
    def back_trouser_width_mm(self) -> float:
        """Btw = 1/4 Hg + 2.5 cm (mid-range adjustment)"""
        return self.hip_girth_mm / 4 + 2.5 * CM_TO_MM

    @property
    def hip_depth_mm(self) -> float:
        """1/10 of 1/2 Hg + 3 cm = Hg/20 + 30"""
        return self.hip_girth_mm / 20 + 3.0 * CM_TO_MM


@dataclass(frozen=True)
class MuellerFrontPoints:
    """Front pattern landmark points. M&S doesn't use Landis's letter convention;
    we use descriptive names for clarity."""
    waist_cf: Point             # Centre Front at waist (lowered 1cm)
    waist_cf_inset: Point       # 1.5cm right of waist_cf (after taper)
    waist_outseam: Point        # Top of outseam (1cm tapered from F1's vertical projection)
    F1: Point                   # Front trouser width corner at hip (Ftw, hip_y)
    F2: Point                   # Front crotch corner at hip (Ftw+Fcw, hip_y)
    crotch_inseam_top: Point    # (0, crotch_y) - top of inseam
    knee_left: Point            # Inseam at knee
    knee_right: Point           # Outseam at knee
    hem_left: Point             # Inseam at hem
    hem_right: Point            # Outseam at hem
    creaseline_x: float         # x of the creaseline (vertical grain)

    def labeled_points(self) -> dict[str, Point]:
        return {
            "Wcf": self.waist_cf,
            "Wcfi": self.waist_cf_inset,
            "Wos": self.waist_outseam,
            "F1": self.F1,
            "F2": self.F2,
            "Cr": self.crotch_inseam_top,
            "Kl": self.knee_left,
            "Kr": self.knee_right,
            "Hl": self.hem_left,
            "Hr": self.hem_right,
        }

    def outline_polygon(self) -> list[Point]:
        """Front piece outline, clockwise from waist near fly.

        Topology mirrors the Landis basic front: waist (fly side -> outseam),
        outseam down through hip corner (F2) and knee (knee_right) to hem,
        hem across, inseam back up through knee_left to crotch corner.

        Two M&S curves are sampled into the polygon:
        - waist_outseam -> F2: slight outward hip curve (~8 mm bow)
        - crotch_inseam_top -> waist_cf_inset (closing fly chord): J-curve
          bowing inward toward upper-left (concave fly seam, ~12 mm bow)
        """
        from .geometry import curve_segment

        # Outward hip curve waist_outseam -> F2 (bow OUTWARD, +x).
        # In y-down coords, perpendicular (+x outward) for a chord going
        # roughly down-right is (chord_y, -chord_x).
        chord_x = self.F2.x - self.waist_outseam.x
        chord_y = self.F2.y - self.waist_outseam.y
        outseam_hip_curve = curve_segment(
            self.waist_outseam, self.F2,
            bow_mm=8.0, perp_x=chord_y, perp_y=-chord_x, n=14,
        )

        # Closing fly chord crotch_inseam_top -> waist_cf_inset, J-curve.
        # The fly is the "front centre" closing seam; bow it concavely toward
        # the centre line so the polygon belly bulges INWARD (toward CF).
        chord_x = self.waist_cf_inset.x - self.crotch_inseam_top.x
        chord_y = self.waist_cf_inset.y - self.crotch_inseam_top.y
        fly_curve = curve_segment(
            self.crotch_inseam_top, self.waist_cf_inset,
            bow_mm=12.0, perp_x=-chord_y, perp_y=chord_x, n=20,
        )

        outline: list[Point] = [self.waist_cf_inset, self.waist_outseam]
        # waist_outseam -> F2: hip curve (drop endpoint duplicate)
        outline.extend(outseam_hip_curve[1:])
        # F2 -> knee_right -> hem_right -> hem_left -> knee_left -> crotch_inseam_top: straight
        outline.append(self.knee_right)
        outline.append(self.hem_right)
        outline.append(self.hem_left)
        outline.append(self.knee_left)
        outline.append(self.crotch_inseam_top)
        # Closing chord: crotch_inseam_top -> waist_cf_inset (drop both endpoints
        # since both are already present at start/end of polygon list).
        outline.extend(fly_curve[1:-1])
        return outline


@dataclass(frozen=True)
class MuellerBackPoints:
    """Back pattern landmark points for M&S Design 3069.

    The back has a distinctive WEDGE shape per the M&S diagram (PDF page 3):
    - Slanted waistline (outseam waist lower, centre back waist higher by ~3.5 cm)
    - J-shaped back-crotch curve from centre back down to inseam top
    - Inseam offset 1 cm parallel from front pattern's outseam

    Self-contained coordinate system: back's local origin at outseam waist
    (top-left). Positioned in the layout via export.
    """
    outseam_waist: Point          # top-left
    centre_back_waist: Point      # top-right (raised)
    crotch_corner: Point          # right side at hip line
    crotch_inseam_top: Point      # deep crotch point at crotch line
    knee_inseam: Point            # back's inseam at knee
    knee_outseam: Point           # back's outseam at knee
    hem_inseam: Point             # back's inseam at hem
    hem_outseam: Point            # back's outseam at hem

    def labeled_points(self) -> dict[str, Point]:
        return {
            "BWos": self.outseam_waist,
            "BWcb": self.centre_back_waist,
            "BCr": self.crotch_corner,
            "BCit": self.crotch_inseam_top,
            "BKi": self.knee_inseam,
            "BKo": self.knee_outseam,
            "BHi": self.hem_inseam,
            "BHo": self.hem_outseam,
        }

    def outline_polygon(self) -> list[Point]:
        """Back piece outline with M&S wedge shape and J-curve back-crotch."""
        from .geometry import curve_segment

        # Back-crotch J-curve: crotch_corner -> crotch_inseam_top
        # Polygon goes clockwise; interior is to the LEFT of motion. We want
        # the curve to bow OUT of the polygon interior (away from interior),
        # which for clockwise motion is to the RIGHT of the chord direction.
        # Right-of-motion in y-down: (chord_y, -chord_x).
        chord_x = self.crotch_inseam_top.x - self.crotch_corner.x
        chord_y = self.crotch_inseam_top.y - self.crotch_corner.y
        crotch_curve = curve_segment(
            self.crotch_corner, self.crotch_inseam_top,
            bow_mm=20.0,
            perp_x=chord_y, perp_y=-chord_x,
            n=24,
        )

        outline: list[Point] = []
        outline.append(self.outseam_waist)
        # Slanted waist top: straight line outseam_waist -> centre_back_waist
        outline.append(self.centre_back_waist)
        # Centre back vertical: straight line centre_back_waist -> crotch_corner
        outline.append(self.crotch_corner)
        # Back-crotch J-curve: crotch_corner -> crotch_inseam_top (drop first endpoint)
        outline.extend(crotch_curve[1:])
        # Inseam: straight from crotch_inseam_top -> knee_inseam -> hem_inseam
        outline.append(self.knee_inseam)
        outline.append(self.hem_inseam)
        # Hem: straight hem_inseam -> hem_outseam
        outline.append(self.hem_outseam)
        # Outseam: straight hem_outseam -> knee_outseam -> outseam_waist (close)
        outline.append(self.knee_outseam)
        return outline


def build_mueller_front(m: MuellerMeasurements) -> MuellerFrontPoints:
    """Construct M&S Design 3069 Basic Jeans FRONT landmark points.

    See module docstring and the M&S PDF page 2 for the source formulas.
    """
    Os = m.outseam_mm
    Is = m.inseam_mm
    hip_depth = m.hip_depth_mm
    Kl = m.knee_length_mm
    Ftw = m.front_trouser_width_mm
    Fcw = m.front_crotch_width_mm
    Hw = m.hem_width_mm
    Kg = m.knee_girth_mm

    # In app coords (y down, y=0 at waist):
    hip_y = Os - (Is + hip_depth)       # converts M&S y-up to app y-down
    crotch_y = Os - Is
    knee_y = Os - Kl
    hem_y = Os

    # Construction line at x=0. Build the hipline to the right.
    F1 = Point(Ftw, hip_y)
    F2 = Point(Ftw + Fcw, hip_y)

    # Creaseline x: midway between construction line and F2 ((Ftw+Fcw)/2),
    # shifted 2 cm toward the construction line.
    x_crease = (Ftw + Fcw) / 2 - 2.0 * CM_TO_MM

    # Hem and knee, distributed equally around the creaseline.
    # Half-piece width at hem = 1/2 Hw - 0.5 cm; each side gets 1/4 Hw - 0.25 cm.
    hem_half_each = (Hw / 2 - 0.5 * CM_TO_MM) / 2
    knee_half_each = (Kg / 2 - 0.5 * CM_TO_MM) / 2

    hem_left = Point(x_crease - hem_half_each, hem_y)
    hem_right = Point(x_crease + hem_half_each, hem_y)
    knee_left = Point(x_crease - knee_half_each, knee_y)
    knee_right = Point(x_crease + knee_half_each, knee_y)

    # Waist construction:
    # - Lower waist 1 cm at centre front (the construction-line top)
    waist_cf = Point(0, 1.0 * CM_TO_MM)
    # - Taper 1.5 cm at centre front (move 1.5 cm RIGHT from waist_cf)
    waist_cf_inset = Point(1.5 * CM_TO_MM, 1.0 * CM_TO_MM)
    # - Outseam waist: square up from F1 to waist line, then taper 1 cm inward
    waist_outseam = Point(F1.x - 1.0 * CM_TO_MM, 0.0)

    # Crotch inseam top: at construction line at crotch level
    crotch_inseam_top = Point(0.0, crotch_y)

    return MuellerFrontPoints(
        waist_cf=waist_cf,
        waist_cf_inset=waist_cf_inset,
        waist_outseam=waist_outseam,
        F1=F1, F2=F2,
        crotch_inseam_top=crotch_inseam_top,
        knee_left=knee_left, knee_right=knee_right,
        hem_left=hem_left, hem_right=hem_right,
        creaseline_x=x_crease,
    )


def build_mueller_back(m: MuellerMeasurements,
                       front: MuellerFrontPoints | None = None) -> MuellerBackPoints:
    """Build back pattern with M&S wedge shape per PDF page 3 illustration.

    The back is self-contained in its own coordinate system:
    - Local origin at outseam_waist (top-left).
    - y grows DOWN toward hem (matches app convention).
    - x grows RIGHT toward centre back.
    - Centre back at waist is RAISED 3.5 cm above outseam waist (negative y).

    The optional `front` parameter is accepted for API compatibility but the
    back is no longer derived from front coordinates — it stands alone.
    """
    Os = m.outseam_mm
    Is = m.inseam_mm
    hip_depth = m.hip_depth_mm
    Kl = m.knee_length_mm
    Btw = m.back_trouser_width_mm
    Bcw = m.back_crotch_width_mm
    Hw = m.hem_width_mm
    Kg = m.knee_girth_mm

    # Y levels (back's local frame: outseam waist at y=0, going down)
    waist_y_outseam = 0.0
    # Centre back raised 3.5 cm above outseam waist (PDF: "3 to 4 cm extra";
    # pick 3.5 cm as midpoint).
    waist_y_cb = -3.5 * CM_TO_MM
    hip_y = Os - Is - hip_depth
    crotch_y = Os - Is
    knee_y = Os - Kl
    hem_y = Os

    # Back hem and knee widths: 2 cm wider than front (1 cm extra each side
    # per the PDF, since back is paired with front around the leg).
    back_hem_width = (Hw / 2 - 0.5 * CM_TO_MM) + 2.0 * CM_TO_MM
    back_knee_width = (Kg / 2 - 0.5 * CM_TO_MM) + 2.0 * CM_TO_MM

    # Total back hip width = Btw + Bcw (full extent at hip line, x=0 at outseam)
    back_hip_width = Btw + Bcw

    # Key points (back local x: 0 at outseam_waist, positive toward centre back)
    outseam_waist = Point(0.0, waist_y_outseam)
    centre_back_waist = Point(back_hip_width, waist_y_cb)
    crotch_corner = Point(back_hip_width, hip_y)
    # crotch_inseam_top: x = back_hip_width - Bcw = Btw
    crotch_inseam_top = Point(Btw, crotch_y)
    # Inseam (right edge of back as drawn): straight DOWN from crotch_inseam_top
    knee_inseam = Point(Btw, knee_y)
    hem_inseam = Point(Btw, hem_y)
    # Outseam (left edge of back as drawn): hem and knee offset LEFT by back widths
    hem_outseam = Point(Btw - back_hem_width, hem_y)
    knee_outseam = Point(Btw - back_knee_width, knee_y)

    return MuellerBackPoints(
        outseam_waist=outseam_waist,
        centre_back_waist=centre_back_waist,
        crotch_corner=crotch_corner,
        crotch_inseam_top=crotch_inseam_top,
        knee_inseam=knee_inseam,
        knee_outseam=knee_outseam,
        hem_inseam=hem_inseam,
        hem_outseam=hem_outseam,
    )
