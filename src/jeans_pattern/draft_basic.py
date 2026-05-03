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
        """Outline finale del front (basic):
        H -> I (waist) -> G (fly top) -> P (knee out) -> M (hem out)
        -> L (hem in) -> O (knee in) -> B (crotch).
        Closes B->H as a straight chord (the hip curve will be added in the updated 501 draft).
        """
        return [self.H, self.I, self.G, self.P, self.M, self.L, self.O, self.B]

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
        """Outline finale del back (basic):
        Y -> Z (waist) -> S (seat) -> T (knee out) -> V (hem out)
        -> W (hem in) -> U (knee in) -> R (back crotch).
        Both Z->S and R->Y are straight chords here; the updated draft (Task 6)
        replaces Z->S with the seat curve and inseam V->T->S with curve geometry.
        """
        return [self.Y, self.Z, self.S, self.T, self.V, self.W, self.U, self.R]


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
