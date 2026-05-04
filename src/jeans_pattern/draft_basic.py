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
        """Outline of the basic front piece (CW traversal in y-down screen coords).

        PDF reference (pages 7-9, "Drafting front part"):
        - Step 8: I-H = waist/4 + 0.5", measured from I TOWARD the fly axis
          (in our mirrored layout the fly axis is at x=0, so H is to the LEFT of I).
        - Steps 11-12: B-L is the inseam (straight chord, creating O at the knee
          intersection), G-M is the outseam (straight chord, creating P at knee).
        - Step 13: "Finish fly G-F-I" — smooth curve from outseam-hip G through F
          up to outseam-waist I (the upper outseam curves into the waist).
        - Step 14: "Finish hip B-H" — smooth curve from fly-axis-crotch B up to
          fly-side-waist H (the front-crotch / J-curve).

        Polygon (CW from H, the fly-side waist corner):
        - H -> I        : waist (straight)
        - I -> G        : "fly" curve, via F (outseam-side curve from waist to hip)
        - G -> M        : outseam (straight, through P at knee)
        - M -> L        : hem (straight)
        - L -> B        : inseam (straight, through O at knee)
        - B -> H        : "hip" curve (front-crotch J-shape from hip to waist)
        """
        from .geometry import cubic_with_tangents

        # Fly curve I -> G via F. In the PDF the construction places F between G
        # and I horizontally, with F square-down from I and G one extension over.
        # Tangent at I is vertical (down) so it joins the waist with a sharp
        # corner; tangent at G is along the outseam G->M so the curve flows into
        # the straight outseam without a kink.
        outseam_dx = self.M.x - self.G.x
        outseam_dy = self.M.y - self.G.y
        fly_chord_len = ((self.G.x - self.I.x) ** 2 + (self.G.y - self.I.y) ** 2) ** 0.5
        fly_curve = cubic_with_tangents(
            self.I, self.G,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=fly_chord_len * 0.50,
            beta=fly_chord_len * 0.40,
            n=20,
        )

        # Hip curve B -> H (front-crotch J-shape). Tangent at B continues the
        # straight inseam L->B (so the crotch transitions smoothly from inseam
        # into the curve); tangent at H is vertical (up into the waist) so the
        # curve meets the waist with a sharp corner.
        inseam_dx = self.B.x - self.L.x
        inseam_dy = self.B.y - self.L.y
        hip_chord_len = ((self.H.x - self.B.x) ** 2 + (self.H.y - self.B.y) ** 2) ** 0.5
        hip_curve = cubic_with_tangents(
            self.B, self.H,
            t_start=(inseam_dx, inseam_dy),
            t_end=(0.0, -1.0),
            alpha=hip_chord_len * 0.50,
            beta=hip_chord_len * 0.55,
            n=24,
        )

        outline = []
        outline.append(self.H)
        outline.append(self.I)
        outline.extend(fly_curve[1:])     # I..G via curve, drop duplicate I
        outline.append(self.M)
        outline.append(self.L)
        outline.append(self.B)
        outline.extend(hip_curve[1:-1])   # B..H via curve, drop duplicates
        return outline

    def construction_lines(self) -> list[list[Point]]:
        """Drafting axes & helper lines that lead to each landmark. These are
        rendered as dashed green lines alongside the cut outline to make the
        geometric construction transparent on the printed pattern."""
        from .geometry import Point

        # Extend horizontals to span both fly side (x=0) and outseam side (G.x).
        left_edge = min(self.A.x, self.H.x) - 10
        right_edge = max(self.G.x, self.M.x) + 30
        return [
            # Vertical fly axis A-E (centro davanti)
            [self.A, self.E],
            # Waist horizontal (extends across the full draft)
            [Point(left_edge, self.A.y), Point(right_edge, self.A.y)],
            # Hip / crotch horizontal at y=B.y
            [Point(left_edge, self.B.y), Point(right_edge, self.B.y)],
            # Knee horizontal at y=D.y
            [Point(left_edge, self.D.y), Point(right_edge, self.D.y)],
            # Hem horizontal at y=E.y
            [Point(left_edge, self.E.y), Point(right_edge, self.E.y)],
            # F square-up: vertical from F to I (locates I on waist)
            [self.F, self.I],
            # I-A waist segment, showing H is between A and I
            [self.A, self.I],
            # B-G hip-line segment
            [self.B, self.G],
            # K square-down: vertical from K to N (centerline of leg)
            [self.K, self.N],
            # B-L straight chord (used to locate O on knee line)
            [self.B, self.L],
            # G-M straight chord (used to locate P on knee line)
            [self.G, self.M],
        ]

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
    # I-H = waist/4 + 0.5", measured TOWARD the fly axis (PDF page 7 step 8).
    # In our mirrored layout the fly axis is at x=0, so H is to the LEFT of I.
    H = square_out(I, m.waist_mm / 4 + 0.5 * INCH, "left")

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
        """Basic back outline (CW traversal in y-down screen coords).

        PDF reference (pages 10-13, "Drafting back part"):
        - Step 3: outseam W-U-R is one straight line, extended to create Y on the
          waist line. R, U, W (and Y) are collinear.
        - Step 4: inseam V-T-S is straight (V-T from hem to knee, T-S from knee
          to hip; the two segments may have slightly different slopes).
        - Step 6: waist line Y-Z is straight.
        - Step 8: "Shape seat seam S-Z" — the only curve in the basic back, going
          from inseam-hip S up to inseam-side waist Z.

        Polygon (CW from Y, the outseam-extension waist corner):
        - Y -> Z : waist (straight, going from outseam side to inseam side)
        - Z -> S : seat curve (the only curve)
        - S -> T -> V : inseam (straight, with corner at T)
        - V -> W : hem (straight)
        - W -> U -> R -> Y : outseam (straight, all colinear; R/U kept as
          construction landmarks even though the segments are colinear)
        """
        from .geometry import cubic_with_tangents

        # Seat curve Z -> S: at Z the curve departs PERPENDICULAR to the waist
        # (vertical, going down) — sharp corner with the waist line, matching the
        # corner convention used for the front hip curve. At S the tangent matches
        # the inseam direction S->T so seat-to-inseam blends smoothly.
        inseam_dx = self.T.x - self.S.x
        inseam_dy = self.T.y - self.S.y
        seat_chord_len = ((self.S.x - self.Z.x) ** 2 + (self.S.y - self.Z.y) ** 2) ** 0.5
        seat_curve = cubic_with_tangents(
            self.Z, self.S,
            t_start=(0.0, 1.0),
            t_end=(inseam_dx, inseam_dy),
            alpha=seat_chord_len * 0.55,
            beta=seat_chord_len * 0.35,
            n=20,
        )

        outline = []
        outline.append(self.Y)
        outline.append(self.Z)
        outline.extend(seat_curve[1:])      # Z..S via curve, drop duplicate Z
        outline.append(self.T)
        outline.append(self.V)
        outline.append(self.W)
        outline.append(self.U)
        outline.append(self.R)
        return outline

    def construction_lines(self) -> list[list[Point]]:
        """Construction axes for the basic back. Y/Z/S/extra-shift segments make
        the derivation from the front draft visible at a glance."""
        from .geometry import Point

        left_edge = min(self.Y.x, self.R.x, self.W.x) - 30
        right_edge = max(self.Z.x, self.S.x) + 30

        return [
            # Waist horizontal (extends past Y and Z so the corners are obvious)
            [Point(left_edge, self.Y.y), Point(right_edge, self.Y.y)],
            # Hip / crotch horizontal through B-G-S
            [Point(left_edge, self.B.y), Point(right_edge, self.B.y)],
            # Knee horizontal
            [Point(left_edge, self.O.y), Point(right_edge, self.O.y)],
            # Hem horizontal
            [Point(left_edge, self.L.y), Point(right_edge, self.L.y)],
            # Front fly axis (x=0) shown for reference
            [Point(0, self.Y.y), Point(0, self.L.y)],
            # B-R 1" outward shift on hip line
            [self.B, self.R],
            # G-S seat extension
            [self.G, self.S],
            # I-X (here X==I in basic; segment collapses but we still draw I)
            [self.I, self.X],
            # 1" shifts at knee and hem (front-to-back point pairs)
            [self.O, self.U],
            [self.P, self.T],
            [self.L, self.W],
            [self.M, self.V],
            # W-R extended outseam-side line that locates Y on the waist
            [self.W, self.Y],
            # Z-T inferred straight outseam reference
            [self.S, self.T],
        ]

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
