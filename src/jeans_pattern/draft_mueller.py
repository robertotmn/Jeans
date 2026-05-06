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
        """
        return [
            self.waist_cf_inset,
            self.waist_outseam,
            self.F2,
            self.knee_right,
            self.hem_right,
            self.hem_left,
            self.knee_left,
            self.crotch_inseam_top,
        ]


@dataclass(frozen=True)
class MuellerBackPoints:
    """Back pattern landmark points (M&S Design 3069, simplified).

    The M&S back is constructed by overlaying the front; we keep the same
    horizontal levels and shift outseam/inseam outward by 1 cm at hem and
    knee (parallel offset), then extend the hipline rightward by 2 cm + Btw
    + Bcw to define the back-crotch corner.
    """
    front: MuellerFrontPoints   # original front, used as reference
    back_waist_outseam: Point
    back_waist_cb: Point        # centre back at waist
    back_crotch_corner: Point   # back-crotch outermost corner at hip level
    back_knee_left: Point
    back_knee_right: Point
    back_hem_left: Point
    back_hem_right: Point
    back_crotch_inseam_top: Point

    def labeled_points(self) -> dict[str, Point]:
        return {
            "BWos": self.back_waist_outseam,
            "BWcb": self.back_waist_cb,
            "BCr": self.back_crotch_corner,
            "BKl": self.back_knee_left,
            "BKr": self.back_knee_right,
            "BHl": self.back_hem_left,
            "BHr": self.back_hem_right,
            "BCit": self.back_crotch_inseam_top,
        }

    def outline_polygon(self) -> list[Point]:
        return [
            self.back_waist_outseam,
            self.back_waist_cb,
            self.back_crotch_corner,
            self.back_knee_right,
            self.back_hem_right,
            self.back_hem_left,
            self.back_knee_left,
            self.back_crotch_inseam_top,
        ]


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
    """Construct M&S Design 3069 Basic Jeans BACK landmark points.

    Simplified interpretation of PDF pages 2-3:
    - Hem and knee 1 cm parallel-offset from front (outward on both sides).
    - Hipline extended rightward: +2cm beyond F1 = back outseam at hip,
      then +Btw, then +Bcw -> back crotch corner.
    - Back outseam waist squared up from back hip outseam.
    - Centre-back at waist squared up from back crotch corner. (The PDF's
      "+3-4 cm to centre back, chosen for right-angle" refinement is left
      to a future curve-fitting pass.)
    - Crotch inseam top is shared with the front (at the construction line).
    """
    if front is None:
        front = build_mueller_front(m)

    Btw = m.back_trouser_width_mm
    Bcw = m.back_crotch_width_mm

    one_cm = 1.0 * CM_TO_MM
    two_cm = 2.0 * CM_TO_MM

    # Hem and knee 1 cm parallel offset
    back_hem_left = Point(front.hem_left.x - one_cm, front.hem_left.y)
    back_hem_right = Point(front.hem_right.x + one_cm, front.hem_right.y)
    back_knee_left = Point(front.knee_left.x - one_cm, front.knee_left.y)
    back_knee_right = Point(front.knee_right.x + one_cm, front.knee_right.y)

    # Hipline extension: 2cm right of F1 is the back outseam-at-hip
    back_hip_outseam = Point(front.F1.x + two_cm, front.F1.y)
    # Then Btw to the right: back trouser width corner at hip
    back_hip_trouser = Point(back_hip_outseam.x + Btw, front.F1.y)
    # Then Bcw further right: back crotch corner at hip
    back_crotch_corner = Point(back_hip_trouser.x + Bcw, front.F1.y)

    # Back outseam waist: square up from back_hip_outseam to waist line
    back_waist_outseam = Point(back_hip_outseam.x, 0.0)
    # Back centre-back waist: square up from back_crotch_corner to waist line
    back_waist_cb = Point(back_crotch_corner.x, 0.0)

    # Back crotch inseam top: shared with front (at crotch level on construction line)
    back_crotch_inseam_top = front.crotch_inseam_top

    return MuellerBackPoints(
        front=front,
        back_waist_outseam=back_waist_outseam,
        back_waist_cb=back_waist_cb,
        back_crotch_corner=back_crotch_corner,
        back_knee_left=back_knee_left,
        back_knee_right=back_knee_right,
        back_hem_left=back_hem_left,
        back_hem_right=back_hem_right,
        back_crotch_inseam_top=back_crotch_inseam_top,
    )
