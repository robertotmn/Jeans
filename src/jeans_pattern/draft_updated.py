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
        """Updated front outline (simple polygon, 8 vertices).

        Same vertex count as basic — AA is intentionally excluded from the
        polygon because as a fly-axis waypoint (x=0, below F) it would create
        a self-intersection with the closing chord B->new_H. AA is preserved
        as a field so post-MVP Bezier rendering can sample I->AA->G as a
        smooth curve replacing the straight I->G segment.
        """
        b = self.base
        return [self.new_H, self.new_I, b.G, self.P_new, b.M, b.L, b.O, b.B]


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
        b = self.base
        # Y -> Z (waist) -> S (seat extension) -> T_new (knee out) ->
        # V (hem out) -> W (hem in) -> U (knee in) -> R (back crotch).
        return [self.new_Y, self.new_Z, b.S, self.T_new, b.V, b.W, b.U, b.R]


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
