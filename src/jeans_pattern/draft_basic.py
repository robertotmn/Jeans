from dataclasses import dataclass
from .geometry import Point, square_out, line_intersection, horizontal_line_through
from .measurements import Measurements

INCH = 25.4

@dataclass
class FrontPoints:
    A: Point; B: Point; C: Point; D: Point; E: Point
    F: Point; G: Point; H: Point; I: Point
    K: Point; N: Point; L: Point; M: Point
    O: Point; P: Point

    def outline_polygon(self) -> list[Point]:
        """Outline of the basic front piece, sampled with curves where the
        J.E. Landis PDF prescribes them.

        Edges (clockwise from waist near fly):
        - I -> H : waist (straight)
        - H -> G : hip curve (outward bow ~12mm to the right)  -- PDF p.9 step 14
        - G -> P : outseam, hip to knee (straight)
        - P -> M : outseam, knee to hem (straight)
        - M -> L : hem (straight)
        - L -> O : inseam, hem to knee (straight)
        - O -> B : inseam, knee to crotch (straight)
        - B -> I : fly closing curve (J-shape, control point near F)  -- PDF p.9 step 13
        """
        from .geometry import curve_segment, curve_through, Point

        # Hip curve H -> G: bow toward +x (away from polygon center which is to the left)
        # H is at (waist_outseam_x, 0); G is at (~330, 247). Chord direction: down-left.
        # Outward (rightward) perpendicular: rotate chord (G-H) 90 deg CW = (G.y-H.y, -(G.x-H.x)).
        # Pre-compute:
        chord_x = self.G.x - self.H.x
        chord_y = self.G.y - self.H.y
        # Outward perpendicular for outline going H -> G clockwise: rotate chord 90 deg CCW = (-chord_y, chord_x)
        # In y-down screen coords with the polygon on the LEFT of clockwise traversal,
        # outward is on the RIGHT of motion. For motion (chord_x, chord_y), right is (chord_y, -chord_x).
        hip_curve = curve_segment(self.H, self.G, bow_mm=15.0,
                                  perp_x=chord_y, perp_y=-chord_x, n=16)

        # Fly closing B -> I: control point near F (between B and I). The fly bows
        # OUTWARD = into the polygon's right (since outline goes B -> I clockwise from
        # bottom-left to top-near-fly, and the polygon is on the right of this direction
        # going up). Use F itself as a reasonable control: F is at (seat/4, rise),
        # halfway between I (at top, x=seat/4) and B (at bottom, x=0). Pulling the
        # control toward F creates a J-shape that hugs the natural fly curve.
        fly_curve = curve_through(self.B, self.F, self.I, n=20)

        # Assemble the outline: include each segment's endpoints, then drop duplicates
        # at segment boundaries.
        outline = []
        # I -> H (straight): just I, then go through to H added by next segment's start
        outline.append(self.I)
        outline.append(self.H)
        # H -> G (curve): drop the first point (it's H, already added)
        outline.extend(hip_curve[1:])
        # G is at the end of hip_curve; continue to P, M, L, O, B straight
        outline.append(self.P)
        outline.append(self.M)
        outline.append(self.L)
        outline.append(self.O)
        outline.append(self.B)
        # B -> I (curve): drop first (B is already there) AND last (I is the polygon close)
        outline.extend(fly_curve[1:-1])
        return outline

    def labeled_points(self) -> dict[str, Point]:
        """Map of letter labels to their coordinates, matching the J.E. Landis PDF naming."""
        return {
            "A": self.A, "B": self.B, "C": self.C, "D": self.D, "E": self.E,
            "F": self.F, "G": self.G, "H": self.H, "I": self.I,
            "K": self.K, "L": self.L, "M": self.M, "N": self.N,
            "O": self.O, "P": self.P,
        }


def build_basic_front(m: Measurements) -> FrontPoints:
    rise = m.rise_mm
    length_plus_half = m.length_mm + 0.5 * INCH
    hem = 1.0 * INCH

    # Asse verticale A-E (centro fly), x=0. y cresce verso il basso.
    A = Point(0, 0)
    B = Point(0, rise)
    C = Point(0, rise + length_plus_half)
    E = Point(0, rise + length_plus_half + hem)

    # Knee line: B-D = (length+0.5)/2 - 2"
    knee_y = rise + (length_plus_half / 2 - 2 * INCH)
    D = Point(0, knee_y)

    # B-F = seat/4 (orizzontale verso destra = outseam side per il front)
    F = square_out(B, m.seat_mm / 4, "right")
    G = square_out(F, 2 * INCH, "right")

    # I = direttamente sopra F sulla linea waist (square up from F to I)
    I = Point(F.x, A.y)
    # I-H = waist/4 + 0.5"
    H = square_out(I, m.waist_mm / 4 + 0.5 * INCH, "right")

    # K = midpoint orizzontale fra B e G, sulla linea hip (y=B.y)
    # PDF dice "K is halfway between B-G, square down to N"
    K = Point((B.x + G.x) / 2, B.y)

    # N = sotto K sulla linea hem (E.y), centro del bottom
    N = Point(K.x, E.y)
    # L (interno = lato inseam) e M (esterno = lato outseam)
    L = Point(N.x - m.bottom_mm / 2, E.y)
    M = Point(N.x + m.bottom_mm / 2, E.y)

    # O = intersezione di linea B-L con linea knee (orizzontale a y=D.y)
    O = line_intersection(B, L, Point(0, D.y), Point(1000, D.y))
    # P = intersezione di linea G-M con linea knee
    P = line_intersection(G, M, Point(0, D.y), Point(1000, D.y))

    return FrontPoints(A=A, B=B, C=C, D=D, E=E, F=F, G=G, H=H, I=I,
                       K=K, N=N, L=L, M=M, O=O, P=P)


@dataclass
class BackPoints:
    """Back draft points. Field order is pair-wise: each (front-anchor, back-derived)
    pair groups the front point that's reused with the back-side point that extends it.
    Pairs: B-R, G-S, I-X, Y-Z, P-T, O-U, M-V, L-W."""
    B: Point; R: Point; G: Point; S: Point
    I: Point; X: Point; Y: Point; Z: Point
    P: Point; T: Point; O: Point; U: Point
    M: Point; V: Point; L: Point; W: Point

    def outline_polygon(self) -> list[Point]:
        """Basic back outline with PDF-prescribed curves:
        - Y -> Z : waist (straight)
        - Z -> S : seat curve (outward bow ~15mm)  -- PDF p.14 step 8
        - S -> T : outseam seat-to-knee (straight)
        - T -> V : outseam knee-to-hem (straight)
        - V -> W : hem (straight)
        - W -> U : inseam hem-to-knee (straight)
        - U -> R : inseam knee-to-crotch with hollow ~9.5mm (3/8")  -- PDF p.14 step 11
        - R -> Y : back-crotch closing curve (J-shape, ~25mm bow)
        """
        from .geometry import curve_segment, Point

        # Seat curve Z -> S: outward = +x direction (rightward, away from polygon center)
        chord_x = self.S.x - self.Z.x
        chord_y = self.S.y - self.Z.y
        seat_curve = curve_segment(self.Z, self.S, bow_mm=15.0,
                                   perp_x=chord_y, perp_y=-chord_x, n=16)

        # Inseam hollow U -> R: bow INWARD (into the polygon, away from leg axis).
        # For back outline going clockwise, going from U (knee inseam) UP to R (crotch),
        # the polygon is on the right (outseam side). "Hollow" means the curve bows
        # AWAY from the polygon = to the LEFT of motion direction.
        chord_x = self.R.x - self.U.x
        chord_y = self.R.y - self.U.y
        # Left of motion (chord_x, chord_y) = (-chord_y, chord_x)
        hollow_inseam = curve_segment(self.U, self.R, bow_mm=9.525,  # 3/8"
                                       perp_x=-chord_y, perp_y=chord_x, n=16)

        # Back crotch R -> Y: J-shape concave. Closing chord direction: R is at (R.x, rise),
        # Y is at (Y.x, 0) (waist line). R -> Y goes UP and slightly RIGHT or LEFT (depends).
        # Bow LEFTWARD (into polygon would be... let's bow outward = away from polygon center).
        # Polygon center is roughly at the back's middle; R is at the LEFT EDGE of the back
        # (back-crotch). The curve should bulge LEFTWARD (-x) to give the back-crotch
        # its J-shape. Using the convention "right of motion" for outward bow:
        chord_x = self.Y.x - self.R.x
        chord_y = self.Y.y - self.R.y
        # Bow LEFTWARD = -x. For motion direction (chord_x, chord_y), the leftward
        # perpendicular is (-chord_y, chord_x).
        crotch_curve = curve_segment(self.R, self.Y, bow_mm=20.0,
                                      perp_x=-chord_y, perp_y=chord_x, n=20)

        outline = []
        outline.append(self.Y)
        # Y -> Z straight (waist)
        outline.append(self.Z)
        # Z -> S curve
        outline.extend(seat_curve[1:])
        # S -> T -> V -> W straight
        outline.append(self.T)
        outline.append(self.V)
        outline.append(self.W)
        # W -> U straight
        outline.append(self.U)
        # U -> R curve (hollow inseam)
        outline.extend(hollow_inseam[1:])
        # R -> Y curve (back-crotch), drop first and last
        outline.extend(crotch_curve[1:-1])
        return outline

    def labeled_points(self) -> dict[str, Point]:
        return {
            "B": self.B, "R": self.R, "G": self.G, "S": self.S,
            "I": self.I, "X": self.X, "Y": self.Y, "Z": self.Z,
            "P": self.P, "T": self.T, "O": self.O, "U": self.U,
            "M": self.M, "V": self.V, "L": self.L, "W": self.W,
        }


def build_basic_back(m: Measurements, front: FrontPoints | None = None) -> BackPoints:
    """Basic back draft (PDF pp. 10-14). Derived from the front via 1" outward
    shifts plus G-S = seat/16 extension. Updated 501 silhouette adds I-X
    extension; here X = I (no extension)."""
    if front is None:
        front = build_basic_front(m)
    one_inch = 1 * INCH

    # 1" outward shifts. Convention: the back lives in the same coordinate
    # plane as the front (mirrored conceptually). The 1" shifts move points
    # OFF the front along directions that grow the back's outline:
    #   B -> R: 1" left  (back-crotch point sticks out past the front fly axis)
    #   O -> U: 1" left  (knee inseam)
    #   P -> T: 1" right (knee outseam)
    #   M -> V: 1" right (hem outseam)
    #   L -> W: 1" left  (hem inseam)
    R = square_out(front.B, one_inch, "left")
    U = square_out(front.O, one_inch, "left")
    T = square_out(front.P, one_inch, "right")
    V = square_out(front.M, one_inch, "right")
    W = square_out(front.L, one_inch, "left")

    # G-S = seat/16, extension oltre G sulla linea hip (verso outseam = right)
    S = square_out(front.G, m.seat_mm / 16, "right")

    # I-X (basic): X = I (no extension; updated 501 sets I-X = seat/10)
    X = front.I

    # Y = intersezione della linea outseam estesa W-R con la waist line (y = A.y)
    waist_p1, waist_p2 = horizontal_line_through(front.A.y)
    Y = line_intersection(W, R, waist_p1, waist_p2)

    # Z = waist/4 + 2" da I sulla waist line (verso destra = outseam side)
    Z = square_out(front.I, m.waist_mm / 4 + 2 * INCH, "right")

    return BackPoints(
        B=front.B, R=R, G=front.G, S=S,
        I=front.I, X=X, Y=Y, Z=Z,
        P=front.P, T=T, O=front.O, U=U,
        M=front.M, V=V, L=front.L, W=W,
    )
