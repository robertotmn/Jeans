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
        """Outline of the basic front piece (CW traversal), with smooth cubic
        Bezier curves at the hip and the fly. Tangent directions are chosen
        to match the adjacent straight edges so curves blend without kinks.

        Edges (clockwise from waist near fly):
        - I -> H : waist (straight, horizontal)
        - H -> G : hip curve, tangent down at H, tangent along outseam at G
        - G -> P : outseam, hip to knee (straight)
        - P -> M : outseam, knee to hem (straight)
        - M -> L : hem (straight)
        - L -> O : inseam, hem to knee (straight)
        - O -> B : inseam, knee to crotch (straight)
        - B -> I : fly J-curve, tangent along inseam at B, vertical-up at I
        """
        from .geometry import cubic_with_tangents

        # Hip curve H -> G: at H tangent is vertical (down) so it blends with the
        # waist endpoint smoothly perpendicular; at G tangent matches outseam G->P.
        outseam_dx = self.P.x - self.G.x
        outseam_dy = self.P.y - self.G.y
        hip_curve = cubic_with_tangents(
            self.H, self.G,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=(self.G.y - self.H.y) * 0.55,
            beta=(self.G.y - self.H.y) * 0.35,
            n=20,
        )

        # Fly J-curve B -> I: at B tangent matches inseam direction O->B (so the
        # crotch transitions smoothly from inseam to fly); at I tangent is vertical
        # (down into the curve), making the fly meet the waist near-perpendicular.
        inseam_dx = self.B.x - self.O.x
        inseam_dy = self.B.y - self.O.y
        chord_len = ((self.I.x - self.B.x) ** 2 + (self.I.y - self.B.y) ** 2) ** 0.5
        fly_curve = cubic_with_tangents(
            self.B, self.I,
            t_start=(inseam_dx, inseam_dy),
            t_end=(0.0, -1.0),
            alpha=chord_len * 0.45,
            beta=chord_len * 0.55,
            n=24,
        )

        outline = []
        outline.append(self.I)
        outline.append(self.H)
        outline.extend(hip_curve[1:])     # H..G via curve, drop duplicate H
        outline.append(self.P)
        outline.append(self.M)
        outline.append(self.L)
        outline.append(self.O)
        outline.append(self.B)
        outline.extend(fly_curve[1:-1])   # B..I via curve, drop duplicates
        return outline

    def construction_lines(self) -> list[list[Point]]:
        """Drafting axes & helper lines that lead to each landmark. These are
        rendered as dashed green lines alongside the cut outline to make the
        geometric construction transparent on the printed pattern."""
        from .geometry import Point

        right_edge = self.H.x + 30  # extend horizontals past the outseam side
        return [
            # Vertical fly axis A-E (centro davanti)
            [self.A, self.E],
            # Waist horizontal A-H
            [Point(self.A.x, self.A.y), Point(right_edge, self.A.y)],
            # Hip / crotch horizontal at y=B.y
            [Point(self.A.x, self.B.y), Point(right_edge, self.B.y)],
            # Knee horizontal at y=D.y
            [Point(self.A.x, self.D.y), Point(right_edge, self.D.y)],
            # Hem horizontal at y=E.y
            [Point(self.A.x, self.E.y), Point(right_edge, self.E.y)],
            # F square-up: vertical from F to I (locates I on waist)
            [self.F, self.I],
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
        """Basic back outline (CW), curves with C1-tangent matching to adjacent
        edges so the seat, hollow inseam and back-crotch flow without kinks.

        - Y -> Z : waist (straight)
        - Z -> S : seat curve, tangent along waist at Z, along outseam at S
        - S -> T : outseam seat-to-knee (straight)
        - T -> V : outseam knee-to-hem (straight)
        - V -> W : hem (straight)
        - W -> U : inseam hem-to-knee (straight)
        - U -> R : hollow inseam, blends with W->U at U and with R->Y at R
        - R -> Y : back-crotch J-curve, tangent shared with hollow inseam at R,
                   vertical at Y to seat smoothly into waist
        """
        from .geometry import cubic_with_tangents

        # Seat curve Z -> S: at Z the curve departs PERPENDICULAR to the waist
        # (vertical, going down), creating an intentional sharp corner with the
        # waist line — same convention as the front hip curve at H. At S the
        # tangent matches outseam S->T so seat-to-outseam transition is smooth.
        outseam_dx = self.T.x - self.S.x
        outseam_dy = self.T.y - self.S.y
        seat_chord_len = ((self.S.x - self.Z.x) ** 2 + (self.S.y - self.Z.y) ** 2) ** 0.5
        seat_curve = cubic_with_tangents(
            self.Z, self.S,
            t_start=(0.0, 1.0),
            t_end=(outseam_dx, outseam_dy),
            alpha=seat_chord_len * 0.55,
            beta=seat_chord_len * 0.35,
            n=20,
        )

        # The hollow inseam and back-crotch share a common tangent at R (G1)
        # so the inseam-to-crotch transition is smooth. Build the shared tangent
        # from the line R -> midpoint(U, Y), reversed so it points outward at R.
        # Equivalently: tangent at R points away from R, roughly along the average
        # of the incoming hollow-inseam direction and outgoing crotch direction.
        # Simple and stable: tangent at R lies along (Y - U) direction.
        tangent_R_dx = self.Y.x - self.U.x
        tangent_R_dy = self.Y.y - self.U.y

        # Hollow inseam U -> R: tangent at U continues from straight inseam W->U
        # (so knee transition is smooth); tangent into R matches the shared tangent.
        inseam_dx = self.U.x - self.W.x
        inseam_dy = self.U.y - self.W.y
        hollow_chord_len = ((self.R.x - self.U.x) ** 2 + (self.R.y - self.U.y) ** 2) ** 0.5
        hollow_inseam = cubic_with_tangents(
            self.U, self.R,
            t_start=(inseam_dx, inseam_dy),
            t_end=(tangent_R_dx, tangent_R_dy),
            alpha=hollow_chord_len * 0.30,
            beta=hollow_chord_len * 0.30,
            n=18,
        )

        # Back-crotch R -> Y: tangent at R continues the shared tangent (G1 with
        # hollow inseam); tangent at Y is vertical (down into the curve) so the
        # crotch meets the waist near-perpendicular.
        crotch_chord_len = ((self.Y.x - self.R.x) ** 2 + (self.Y.y - self.R.y) ** 2) ** 0.5
        crotch_curve = cubic_with_tangents(
            self.R, self.Y,
            t_start=(tangent_R_dx, tangent_R_dy),
            t_end=(0.0, -1.0),
            alpha=crotch_chord_len * 0.55,
            beta=crotch_chord_len * 0.45,
            n=24,
        )

        outline = []
        outline.append(self.Y)
        outline.append(self.Z)
        outline.extend(seat_curve[1:])
        outline.append(self.T)
        outline.append(self.V)
        outline.append(self.W)
        outline.append(self.U)
        outline.extend(hollow_inseam[1:])
        outline.extend(crotch_curve[1:-1])
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
