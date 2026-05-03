from dataclasses import dataclass
from .geometry import Point, square_out, line_intersection
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
        -> L (hem in) -> O (knee in) -> B (crotch) -> H (hip curve via close)
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
