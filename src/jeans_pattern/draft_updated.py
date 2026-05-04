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
        """Updated 501 front outline (CW), drawn with C1-tangent cubic Bezier
        curves so adjacent edges blend without visible kinks.

        - new_I -> new_H : slight downward waist curve (~3mm)  -- PDF p.21 step 5
        - new_H -> G    : enhanced hip curve, vertical at H, along outseam at G
        - G -> P_new    : outseam (straight)
        - P_new -> M    : outseam knee-to-hem (straight)
        - M -> L        : hem (straight)
        - L -> O        : inseam hem-to-knee (straight)
        - O -> B        : front thigh hollow (3/4"), tangent-blended at O and B
        - B -> new_I    : fly J-curve, tangent shared with thigh-hollow at B,
                          tangent vertical at new_I to meet waist near-perpendicular
        """
        from .geometry import cubic_with_tangents, curve_segment
        b = self.base

        # Slight waist curve new_I -> new_H: kept as a shallow quadratic perp bow
        # (tangents at the endpoints are essentially horizontal anyway, and 3mm
        # of bow is small enough that a quadratic looks indistinguishable from a cubic).
        waist_curve = curve_segment(
            self.new_I, self.new_H,
            bow_mm=3.0, perp_x=0, perp_y=1, n=12,
        )

        # Hip curve new_H -> G: tangent vertical at H (perpendicular to waist),
        # tangent along outseam G->P_new at G (so hip-to-outseam transition is smooth).
        outseam_dx = self.P_new.x - b.G.x
        outseam_dy = self.P_new.y - b.G.y
        hip_chord_len = ((b.G.x - self.new_H.x) ** 2 + (b.G.y - self.new_H.y) ** 2) ** 0.5
        hip_curve = cubic_with_tangents(
            self.new_H, b.G,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=hip_chord_len * 0.55,
            beta=hip_chord_len * 0.30,
            n=20,
        )

        # The thigh hollow (O -> B) and the fly (B -> new_I) share a common
        # tangent at B (G1), keeping the front-crotch transition smooth.
        # Tangent at B points up-and-slightly-right (along the line O -> new_I).
        tangent_B_dx = self.new_I.x - b.O.x
        tangent_B_dy = self.new_I.y - b.O.y

        # Thigh hollow O -> B: tangent at O continues the straight inseam L->O;
        # tangent at B is the shared tangent above.
        inseam_dx = b.O.x - b.L.x
        inseam_dy = b.O.y - b.L.y
        thigh_chord_len = ((b.B.x - b.O.x) ** 2 + (b.B.y - b.O.y) ** 2) ** 0.5
        thigh_hollow = cubic_with_tangents(
            b.O, b.B,
            t_start=(inseam_dx, inseam_dy),
            t_end=(tangent_B_dx, tangent_B_dy),
            alpha=thigh_chord_len * 0.30,
            beta=thigh_chord_len * 0.30,
            n=18,
        )

        # Fly J-curve B -> new_I: tangent at B continues the shared tangent;
        # tangent at new_I is vertical (down into the curve) so the fly meets
        # the waist near-perpendicular, like a real jeans front-crotch seam.
        fly_chord_len = ((self.new_I.x - b.B.x) ** 2 + (self.new_I.y - b.B.y) ** 2) ** 0.5
        fly_curve = cubic_with_tangents(
            b.B, self.new_I,
            t_start=(tangent_B_dx, tangent_B_dy),
            t_end=(0.0, -1.0),
            alpha=fly_chord_len * 0.50,
            beta=fly_chord_len * 0.55,
            n=24,
        )

        outline = []
        outline.append(self.new_I)
        outline.extend(waist_curve[1:])
        outline.extend(hip_curve[1:])
        outline.append(self.P_new)
        outline.append(b.M)
        outline.append(b.L)
        outline.append(b.O)
        outline.extend(thigh_hollow[1:])
        outline.extend(fly_curve[1:-1])
        return outline

    def construction_lines(self) -> list[list[Point]]:
        """Updated front construction lines: same skeleton as the basic front
        plus the AA waypoint and the M-perpendicular that locates P_new."""
        from .geometry import Point

        b = self.base
        right_edge = max(self.new_H.x, b.G.x, b.M.x) + 30
        return [
            # Vertical fly axis A-E
            [b.A, b.E],
            # Waist horizontal
            [Point(b.A.x, b.A.y), Point(right_edge, b.A.y)],
            # Hip / crotch horizontal at y=B.y
            [Point(b.A.x, b.B.y), Point(right_edge, b.B.y)],
            # Knee horizontal
            [Point(b.A.x, b.D.y), Point(right_edge, b.D.y)],
            # Hem horizontal
            [Point(b.A.x, b.E.y), Point(right_edge, b.E.y)],
            # F square-up (locates the basic I above F)
            [b.F, b.I],
            # F-AA fly waypoint (seat/16 below F on fly axis)
            [b.F, self.AA],
            # B-G hip-line segment
            [b.B, b.G],
            # K square-down (centerline of leg)
            [b.K, b.N],
            # B-L straight chord (locates O at knee)
            [b.B, b.L],
            # G-M straight chord (locates basic P at knee)
            [b.G, b.M],
            # I shift: original-I to new_I (visualises the 3/4" outseam-ward shift)
            [b.I, self.new_I],
            # H shift: original-H to new_H
            [b.H, self.new_H],
            # M-perpendicular up to knee line, then 2" along outseam to P_new
            [b.M, Point(b.M.x, b.D.y)],
            [Point(b.M.x, b.D.y), self.P_new],
        ]

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
        """Updated 501 back outline (CW), with C1-tangent cubic Bezier curves
        on the seat, hollow inseam, and back-crotch.

        - new_Y -> new_Z : waist (straight, raised through new_X)
        - new_Z -> S     : seat curve, tangent along waist at Z, along outseam at S
        - S -> T_new     : outseam (straight)
        - T_new -> V     : outseam knee-to-hem (straight)
        - V -> W         : hem (straight)
        - W -> U         : inseam hem-to-knee (straight)
        - U -> R         : hollow inseam (1"), C1 with W->U at U and shared tangent at R
        - R -> new_Y     : back-crotch J-curve, tangent shared with hollow inseam at R,
                           vertical at Y to meet the waist near-perpendicular
        """
        from .geometry import cubic_with_tangents
        b = self.base

        # Seat curve new_Z -> S: tangent vertical at Z (sharp corner with waist),
        # tangent along outseam S->T_new at S (smooth blend with outseam).
        outseam_dx = self.T_new.x - b.S.x
        outseam_dy = self.T_new.y - b.S.y
        seat_chord_len = ((b.S.x - self.new_Z.x) ** 2 + (b.S.y - self.new_Z.y) ** 2) ** 0.5
        seat_curve = cubic_with_tangents(
            self.new_Z, b.S,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=seat_chord_len * 0.55,
            beta=seat_chord_len * 0.35,
            n=20,
        )

        # Shared tangent at R (G1) between hollow inseam and back-crotch curve.
        # Direction: from U toward new_Y; it bisects the two segments visually.
        tangent_R_dx = self.new_Y.x - b.U.x
        tangent_R_dy = self.new_Y.y - b.U.y

        # Hollow inseam U -> R: tangent at U continues straight inseam W->U; tangent
        # at R is the shared tangent.
        inseam_dx = b.U.x - b.W.x
        inseam_dy = b.U.y - b.W.y
        hollow_chord_len = ((b.R.x - b.U.x) ** 2 + (b.R.y - b.U.y) ** 2) ** 0.5
        hollow_inseam = cubic_with_tangents(
            b.U, b.R,
            t_start=(inseam_dx, inseam_dy),
            t_end=(tangent_R_dx, tangent_R_dy),
            alpha=hollow_chord_len * 0.30,
            beta=hollow_chord_len * 0.30,
            n=18,
        )

        # Back-crotch R -> new_Y: tangent at R is the shared tangent; tangent
        # at new_Y is vertical (down into the curve), so the crotch meets the
        # waist near-perpendicular for a natural top-of-yoke shape.
        crotch_chord_len = ((self.new_Y.x - b.R.x) ** 2 + (self.new_Y.y - b.R.y) ** 2) ** 0.5
        crotch_curve = cubic_with_tangents(
            b.R, self.new_Y,
            t_start=(tangent_R_dx, tangent_R_dy),
            t_end=(0.0, -1.0),
            alpha=crotch_chord_len * 0.55,
            beta=crotch_chord_len * 0.45,
            n=24,
        )

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

    def construction_lines(self) -> list[list[Point]]:
        """Updated back construction lines: shows the raised waist line through
        new_X and the V-perpendicular construction that locates T_new."""
        from .geometry import Point

        b = self.base
        left_edge = min(self.new_Y.x, b.R.x, b.W.x) - 30
        right_edge = max(self.new_Z.x, b.S.x, b.V.x) + 30
        top_y = self.new_X.y
        return [
            # Original (basic) waist horizontal at y=A.y
            [Point(left_edge, b.B.y - b.B.y), Point(right_edge, b.B.y - b.B.y)],
            # Raised waist horizontal through new_X
            [Point(left_edge, top_y), Point(right_edge, top_y)],
            # Hip / crotch horizontal through B-G-S
            [Point(left_edge, b.B.y), Point(right_edge, b.B.y)],
            # Knee horizontal
            [Point(left_edge, b.O.y), Point(right_edge, b.O.y)],
            # Hem horizontal
            [Point(left_edge, b.L.y), Point(right_edge, b.L.y)],
            # Front fly axis (x=0) for reference
            [Point(0, top_y), Point(0, b.L.y)],
            # I-X raise (seat/10) – the 501 yoke addition
            [b.I, self.new_X],
            # 1" outward shifts shown as horizontal segments on hip/knee/hem
            [b.B, b.R],
            [b.G, b.S],
            [b.O, b.U],
            [b.P, b.T],
            [b.L, b.W],
            [b.M, b.V],
            # W-R extended outseam-side reference (locates new_Y on the new waist)
            [b.W, self.new_Y],
            # Original Z position (on basic waist) -> new_Z (on raised waist)
            [b.Z, self.new_Z],
            # V-perpendicular up to knee, then 2" along outseam to T_new
            [b.V, Point(b.V.x, b.O.y)],
            [Point(b.V.x, b.O.y), self.T_new],
        ]

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
