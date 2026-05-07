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
        """Updated 501 front outline (CW traversal in y-down screen coords).

        Same structural sequence as the basic front (PDF pages 7-9) plus the
        updated 501 refinements (PDF pages 19-23):
        - I and H shifted 3/4" toward the outseam (step 4); I lowered 1/4" (step 5).
        - Slight downward curve on the I-H waist segment (step 5).
        - Reshaped hip curve B-H (step 6).
        - Fly curve I-AA-G via the AA waypoint (step 7).
        - Front thigh hollow 3/4" on the L-B inseam (step 12, page 23).
        - Hem perpendicular to outseam: P_new replaces P (steps 8-10, page 22).

        Polygon (CW from new_H, the fly-side waist corner):
        - new_H -> new_I : waist (slight downward curve, PDF p.21 step 5)
        - new_I -> G     : "fly" curve via AA waypoint (PDF p.21 step 7)
        - G -> P_new -> M: outseam (straight, with hem-perpendicular construction)
        - M -> L         : hem (straight)
        - L -> B         : front thigh hollow on the inseam (3/4")
        - B -> new_H     : "hip" / front-crotch curve (PDF p.21 step 6)
        """
        from .geometry import cubic_with_tangents, curve_segment
        b = self.base

        # Slight waist curve new_H -> new_I: shallow quadratic, bow downward
        # (into polygon) by ~3mm. Tangents at the endpoints are essentially
        # horizontal anyway, so a quadratic perp bow is indistinguishable from
        # a cubic in the rendered output.
        waist_curve = curve_segment(
            self.new_H, self.new_I,
            bow_mm=3.0, perp_x=0, perp_y=1, n=12,
        )

        # Fly curve new_I -> G. Tangenti analoghe al basic per evitare di
        # gonfiare la cucitura outseam: verticale a new_I, lungo G->M a G.
        # AA (seat/16 sotto F) resta come construction landmark ma NON viene
        # usata come control point del Bezier: usarla come control come prima
        # tirava la curva ~32 mm sotto la linea hip, allungando l'outseam front
        # rispetto al back e rendendo i due lati non cucibili.
        outseam_dx = b.M.x - b.G.x
        outseam_dy = b.M.y - b.G.y
        fly_chord_len = ((b.G.x - self.new_I.x) ** 2 + (b.G.y - self.new_I.y) ** 2) ** 0.5
        fly_curve = cubic_with_tangents(
            self.new_I, b.G,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=fly_chord_len * 0.50,
            beta=fly_chord_len * 0.40,
            n=20,
        )

        # Front thigh hollow L -> B (3/4" = ~19mm, PDF p.23 step 12). Tangent
        # at L matches the hem (straight horizontal at L going right doesn't
        # carry into the inseam, so use the chord direction L->B); tangent at B
        # continues into the hip curve via a shared tangent at B (same as basic).
        chord_x = b.B.x - b.L.x
        chord_y = b.B.y - b.L.y
        # Tangent shared with the hip curve at B: along O -> new_H (gives the
        # crotch a smooth front-crotch profile blending into the J).
        tangent_B_dx = self.new_H.x - b.O.x
        tangent_B_dy = self.new_H.y - b.O.y
        thigh_hollow = cubic_with_tangents(
            b.L, b.B,
            t_start=(chord_x, chord_y),
            t_end=(tangent_B_dx, tangent_B_dy),
            alpha=((chord_x ** 2 + chord_y ** 2) ** 0.5) * 0.40,
            beta=((chord_x ** 2 + chord_y ** 2) ** 0.5) * 0.35,
            n=18,
        )

        # Hip / front-crotch curve B -> new_H. Tangent at B is the shared
        # tangent (G1 with the thigh hollow); tangent at new_H is vertical
        # (up into the curve) for a sharp corner with the slight waist curve.
        hip_chord_len = ((self.new_H.x - b.B.x) ** 2 + (self.new_H.y - b.B.y) ** 2) ** 0.5
        hip_curve = cubic_with_tangents(
            b.B, self.new_H,
            t_start=(tangent_B_dx, tangent_B_dy),
            t_end=(0.0, -1.0),
            alpha=hip_chord_len * 0.50,
            beta=hip_chord_len * 0.55,
            n=24,
        )

        outline = []
        outline.append(self.new_H)
        outline.extend(waist_curve[1:])         # new_H..new_I via slight curve
        outline.extend(fly_curve[1:])           # new_I..G via quadratic via AA, drop new_I
        outline.append(self.P_new)
        outline.append(b.M)
        outline.append(b.L)
        outline.extend(thigh_hollow[1:])        # L..B via hollow, drop L
        outline.extend(hip_curve[1:-1])         # B..new_H via curve, drop both ends
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
        """Updated 501 back BODY outline (CW traversal in y-down screen coords).

        Same structural sequence as the basic back (PDF pages 10-13) plus the
        updated 501 refinements (PDF pages 19-23):
        - I-X = seat/10 e' il riferimento del yoke; il yoke (build_yoke) e' un
          pezzo separato sopra la vita base. Il back body resta sulla vita base
          (y=0) per cucibilita' con il front.
        - Back thigh hollow 1" on the V-T-S inseam (step 12, page 23).
        - Hem perpendicular to outseam: T_new replaces T (steps 8-10, page 22).

        Polygon (CW from new_Y, the outseam-extension waist corner):
        - new_Y -> new_Z : waist (straight, raised through new_X)
        - new_Z -> S     : seat curve (only top curve, PDF p.13 step 8)
        - S -> T_new     : back thigh hollow (1") on the inseam upper segment
        - T_new -> V     : inseam knee-to-hem (straight)
        - V -> W         : hem (straight)
        - W -> U -> R -> new_Y : outseam (straight, all colinear; R/U kept as
          construction landmarks)
        """
        from .geometry import cubic_with_tangents
        b = self.base

        # Seat curve new_Z -> S: vertical at Z (sharp corner with waist), tangent
        # along the inseam direction S->T_new at S so seat-to-inseam blends smoothly.
        inseam_dx = self.T_new.x - b.S.x
        inseam_dy = self.T_new.y - b.S.y
        seat_chord_len = ((b.S.x - self.new_Z.x) ** 2 + (b.S.y - self.new_Z.y) ** 2) ** 0.5
        seat_curve = cubic_with_tangents(
            self.new_Z, b.S,
            t_start=(0.0, 1.0),
            t_end=(inseam_dx, inseam_dy),
            alpha=seat_chord_len * 0.55,
            beta=seat_chord_len * 0.35,
            n=20,
        )

        # Back thigh hollow S -> T_new (1" = ~25.4mm, PDF p.23 step 12). The
        # hollow bows the chord INWARD (toward the leg interior). Tangent at S
        # is the shared tangent with the seat curve (along S->T_new direction);
        # tangent at T_new continues the straight V-T_new inseam below.
        chord_x = self.T_new.x - b.S.x
        chord_y = self.T_new.y - b.S.y
        below_dx = b.V.x - self.T_new.x
        below_dy = b.V.y - self.T_new.y
        hollow_inseam = cubic_with_tangents(
            b.S, self.T_new,
            t_start=(chord_x, chord_y),
            t_end=(below_dx, below_dy),
            alpha=((chord_x ** 2 + chord_y ** 2) ** 0.5) * 0.40,
            beta=((chord_x ** 2 + chord_y ** 2) ** 0.5) * 0.35,
            n=18,
        )

        outline = []
        outline.append(self.new_Y)
        outline.append(self.new_Z)
        outline.extend(seat_curve[1:])              # new_Z..S via curve, drop new_Z
        outline.extend(hollow_inseam[1:])           # S..T_new via hollow curve, drop S
        outline.append(b.V)
        outline.append(b.W)
        outline.append(b.U)
        outline.append(b.R)
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

    # F-AA = seat/16, AA directly BELOW F by seat/16 (PDF page 21 step 7).
    # AA is the waypoint that the updated fly curve I-AA-G passes through.
    AA = Point(base.F.x, base.F.y + m.seat_mm / 16)

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

    # I-X = seat/10, sopra I (y decreases). X e' il punto di costruzione
    # del YOKE (cucitura yoke posteriore), NON il bordo superiore del back body.
    # Il back body si ferma sulla vita base (y=0): il yoke e' un pezzo separato
    # gestito da build_yoke. Senza questa distinzione il back outline includerebbe
    # la regione yoke (raise di seat/10 = ~98mm) e la cucitura outseam back
    # risulterebbe ~98mm piu' lunga del front, rendendo il pattern non cucibile.
    new_X = Point(base.I.x, base.I.y - m.seat_mm / 10)

    # Y e Z restano sulla vita base (y=base.A.y=0): il back body sews al yoke
    # lungo la vita base. new_X e' tracciato come construction line per indicare
    # dove arriverebbe il yoke se assemblato.
    Y_new = base.Y
    Z_new = base.Z

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
