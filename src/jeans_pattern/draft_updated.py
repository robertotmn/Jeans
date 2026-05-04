"""Updated 501-style draft. Builds on the basic draft (Task 4-5) with:

Implemented in outline polygon (cut shape):
- I shifted 3/4" toward outseam, lowered 1/4"
- I-X (back) = seat/10 (raised back-yoke point)
- Y-Z redrawn through new X
- T,P moved down 2" (new perpendicular construction at hem)

Tracked as fields, deferred to post-MVP curve rendering:
- AA (F-AA = seat/16 fly axis waypoint) — used as Bezier control point
  to replace the straight I->G segment with a smooth fly curve.

Deferred to MVP post-processing (visual refinements not in outline polygon):
- Curve I-H (slight curve replacing straight chord)
- Recurve B-H (hip curve, currently straight chord)
- Hem perpendicular to outseam (currently inherited from basic horizontal hem)
- Hollow thigh (front 3/4", back 1")
- Seat curve S-Z (back, currently straight chord)

PDF reference: pages 19-24 of drafting_selvedge_jeans.pdf.
Excel formulas: cells M21 (F-AA = seat/16) and M22 (I-X for 501 = seat/10).
"""
from dataclasses import dataclass
from .geometry import Point, line_intersection, horizontal_line_through
from .measurements import Measurements
from .draft_basic import (
    build_basic_front, build_basic_back, FrontPoints, BackPoints,
)

INCH = 25.4


@dataclass(frozen=True)
class UpdatedFront:
    """Wrapper around the basic FrontPoints with the updated-draft additions.
    Attribute access on this object falls back to the underlying FrontPoints
    via __getattr__, so callers can use updated_front.E, updated_front.G, etc.,
    and only the modified points (I, H, AA, P_new) are explicitly overridden.
    """
    base: FrontPoints
    new_I: Point
    new_H: Point
    AA: Point
    P_new: Point

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def I(self) -> Point:
        return self.new_I

    @property
    def H(self) -> Point:
        return self.new_H

    def outline_polygon(self) -> list[Point]:
        """Updated 501 front outline with curves:
        - new_I -> new_H : slight downward curve on waist (~3mm)  -- PDF p.21 step 5
        - new_H -> G : enhanced hip curve (~18mm bow)  -- PDF p.21 step 6
        - G -> P_new : outseam (straight; perpendicular hem geometry handled by P_new shift)
        - P_new -> M : outseam (straight)
        - M -> L : hem (straight)
        - L -> O : inseam, hem to knee (straight)
        - O -> B : front thigh hollow (~19mm = 3/4")  -- PDF p.23 step 12
        - B -> new_I : fly curve via AA  -- PDF p.21 step 7
        """
        from .geometry import curve_segment, curve_through, Point
        b = self.base

        # Slight waist curve: new_I -> new_H, slight downward bow into polygon
        # Direction: rightward (waist is horizontal). Down = +y. Polygon is below (high y).
        # Bow into polygon = +y. Perpendicular direction (0, 1).
        waist_curve = curve_segment(self.new_I, self.new_H, bow_mm=3.0,
                                     perp_x=0, perp_y=1, n=12)

        # Enhanced hip curve new_H -> G: outward bow rightward (+x perpendicular for clockwise outline)
        chord_x = b.G.x - self.new_H.x
        chord_y = b.G.y - self.new_H.y
        hip_curve = curve_segment(self.new_H, b.G, bow_mm=18.0,
                                   perp_x=chord_y, perp_y=-chord_x, n=16)

        # Front thigh hollow on inseam O -> B: bow INWARD (into polygon, +x).
        # O is at (~18, 635), B is at (0, ~248). Going O -> B is up-and-left.
        # Polygon is to the right of this direction (the leg body). Hollow = away from polygon = left.
        # Wait: hollow is concave on the inseam, meaning the inseam curves INWARD toward the leg axis.
        # The leg axis is to the right (positive x) of the inseam. So hollow bows the inseam to the
        # right (+x), into the polygon. For motion O -> B (chord_x = -O.x, chord_y = B.y - O.y < 0),
        # right of motion = (chord_y, -chord_x). chord_y < 0, -chord_x > 0, so right = (negative, positive)? Hmm.
        # Let me just use +x explicitly:
        thigh_hollow = curve_segment(self.O, b.B, bow_mm=19.05,  # 3/4"
                                      perp_x=1, perp_y=0, n=16)

        # Fly curve B -> new_I: bows LEFTWARD (toward fly axis x=0) to give the
        # natural J-shape. AA is preserved as a draft waypoint but is NOT used
        # as the Bezier control point: AA sits BELOW B on the fly axis (y=AA.y
        # > B.y), so a quadratic Bezier through it would dip below B and cross
        # the thigh hollow near the crotch (self-intersection). Instead, bow
        # perpendicular to the chord B -> new_I, on the polygon-outward side.
        chord_x = self.new_I.x - b.B.x
        chord_y = self.new_I.y - b.B.y
        # Left-of-motion in y-down screen coords is (-chord_y, chord_x); for
        # this CW outline going B -> new_I (up-right), that direction bows the
        # curve up-and-right of the chord, hugging the J-shape outward.
        fly_curve = curve_segment(b.B, self.new_I, bow_mm=15.0,
                                   perp_x=-chord_y, perp_y=chord_x, n=24)

        outline = []
        outline.append(self.new_I)
        # new_I -> new_H curve (waist)
        outline.extend(waist_curve[1:])
        # new_H -> G curve (hip)
        outline.extend(hip_curve[1:])
        # G -> P_new -> M -> L straight
        outline.append(self.P_new)
        outline.append(b.M)
        outline.append(b.L)
        # L -> O straight
        outline.append(b.O)
        # O -> B curve (thigh hollow)
        outline.extend(thigh_hollow[1:])
        # B -> new_I curve via AA, drop first and last
        outline.extend(fly_curve[1:-1])
        return outline

    def labeled_points(self) -> dict[str, Point]:
        labels = self.base.labeled_points()
        labels["I"] = self.new_I
        labels["H"] = self.new_H
        labels["AA"] = self.AA
        labels["P_new"] = self.P_new
        return labels


@dataclass(frozen=True)
class UpdatedBack:
    """Wrapper around the basic BackPoints with updated-draft additions."""
    base: BackPoints
    new_X: Point
    new_Y: Point
    new_Z: Point
    T_new: Point

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def X(self) -> Point:
        return self.new_X

    @property
    def Y(self) -> Point:
        return self.new_Y

    @property
    def Z(self) -> Point:
        return self.new_Z

    def outline_polygon(self) -> list[Point]:
        """Updated 501 back outline:
        - new_Y -> new_Z : waist (straight)
        - new_Z -> S : seat curve (~18mm outward bow)
        - S -> T_new : outseam (straight)
        - T_new -> V : outseam knee-to-hem (straight)
        - V -> W : hem (straight)
        - W -> U : inseam hem-to-knee (straight)
        - U -> R : inseam thigh hollow ~25.4mm (1")  -- PDF p.23 step 12
        - R -> new_Y : back-crotch curve (~22mm)
        """
        from .geometry import curve_segment, Point
        b = self.base

        chord_x = b.S.x - self.new_Z.x
        chord_y = b.S.y - self.new_Z.y
        seat_curve = curve_segment(self.new_Z, b.S, bow_mm=18.0,
                                    perp_x=chord_y, perp_y=-chord_x, n=16)

        # Inseam hollow U -> R: 1" = 25.4mm, bow LEFT of motion direction (away from polygon)
        chord_x = b.R.x - b.U.x
        chord_y = b.R.y - b.U.y
        hollow_inseam = curve_segment(b.U, b.R, bow_mm=25.4,
                                       perp_x=-chord_y, perp_y=chord_x, n=16)

        chord_x = self.new_Y.x - b.R.x
        chord_y = self.new_Y.y - b.R.y
        crotch_curve = curve_segment(b.R, self.new_Y, bow_mm=22.0,
                                      perp_x=-chord_y, perp_y=chord_x, n=20)

        outline = []
        outline.append(self.new_Y)
        outline.append(self.new_Z)
        outline.extend(seat_curve[1:])
        outline.append(self.T_new)
        outline.append(b.V)
        outline.append(b.W)
        outline.append(b.U)
        outline.extend(hollow_inseam[1:])
        outline.extend(crotch_curve[1:-1])
        return outline

    def labeled_points(self) -> dict[str, Point]:
        labels = self.base.labeled_points()
        labels["X"] = self.new_X
        labels["Y"] = self.new_Y
        labels["Z"] = self.new_Z
        labels["T_new"] = self.T_new
        return labels


def build_updated_front(m: Measurements) -> UpdatedFront:
    base = build_basic_front(m)

    # I shifted 0.75" toward outseam (right), lowered 0.25"
    new_I = Point(base.I.x + 0.75 * INCH, base.I.y + 0.25 * INCH)
    # H shifted 0.75" toward outseam (waist endpoint follows)
    new_H = Point(base.H.x + 0.75 * INCH, base.H.y)

    # F-AA = seat/16, AA on the fly axis (x=0), below F (y increases)
    AA = Point(0, base.F.y + m.seat_mm / 16)

    # P_new: perpendicular from M to knee line, then 2" along outseam G->M
    # NOTE: PDF page 22 instruction is ambiguous between "2 inches along the
    # *new* perpendicular line (straight down)" vs. "2 inches along the
    # *original* outseam G->M direction". We use the latter interpretation
    # (along original outseam unit vector). Visual check pending in Task 14.
    dx = base.M.x - base.G.x
    dy = base.M.y - base.G.y
    norm = (dx ** 2 + dy ** 2) ** 0.5
    ux, uy = dx / norm, dy / norm
    # The plan says: square up from M perpendicular to knee line (y=D.y),
    # producing a point at (M.x, D.y), then move 2" down along outseam direction
    P_perp = Point(base.M.x, base.D.y)
    P_new = Point(P_perp.x + ux * 2 * INCH, P_perp.y + uy * 2 * INCH)

    return UpdatedFront(base=base, new_I=new_I, new_H=new_H, AA=AA, P_new=P_new)


def build_updated_back(m: Measurements,
                       front: FrontPoints | None = None) -> UpdatedBack:
    base = build_basic_back(m, front=front)

    # I-X = seat/10, sopra I (y decreases)
    new_X = Point(base.I.x, base.I.y - m.seat_mm / 10)

    # Y-Z redrawn through the new X. Z keeps its x but moves up to X's y.
    new_waist_y = new_X.y
    waist_p1, waist_p2 = horizontal_line_through(new_waist_y)
    Y_new = line_intersection(base.W, base.R, waist_p1, waist_p2)
    Z_new = Point(base.Z.x, new_waist_y)

    # T_new: perpendicular from V to knee line, then 2" along outseam V->S
    # (V is the hem-outseam back point; S is the seat extension; outseam V->S goes upward toward S)
    # The construction is symmetric to front P_new but with V and S as the line endpoints.
    # NOTE: PDF page 22 instruction is ambiguous between "2 inches along the
    # *new* perpendicular line (straight down)" vs. "2 inches along the
    # *original* outseam V->S direction". We use the latter interpretation
    # (along original outseam unit vector). Visual check pending in Task 14.
    knee_y = base.T.y     # original T sits on the knee line
    T_perp = Point(base.V.x, knee_y)
    dx = base.V.x - base.S.x
    dy = base.V.y - base.S.y
    norm = (dx ** 2 + dy ** 2) ** 0.5
    ux, uy = dx / norm, dy / norm
    T_new = Point(T_perp.x + ux * 2 * INCH, T_perp.y + uy * 2 * INCH)

    return UpdatedBack(base=base, new_X=new_X, new_Y=Y_new, new_Z=Z_new, T_new=T_new)
