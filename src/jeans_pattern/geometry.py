from dataclasses import dataclass
from math import hypot

@dataclass(frozen=True)
class Point:
    x: float
    y: float


def points_equal(a: Point, b: Point, tol: float = 1e-9) -> bool:
    """Tolerance comparison for points. Use this when comparing computed coords
    that may have float drift (e.g. from line_intersection or bezier_curve)."""
    return abs(a.x - b.x) < tol and abs(a.y - b.y) < tol


def distance(a: Point, b: Point) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def square_out(p: Point, length: float, direction: str) -> Point:
    """Coordinate convention: y cresce verso il basso (come SVG/PDF). 'up' diminuisce y."""
    if direction == "right":
        return Point(p.x + length, p.y)
    if direction == "left":
        return Point(p.x - length, p.y)
    if direction == "up":
        return Point(p.x, p.y - length)
    if direction == "down":
        return Point(p.x, p.y + length)
    raise ValueError(f"unknown direction {direction!r}")


def midpoint(a: Point, b: Point) -> Point:
    return Point((a.x + b.x) / 2, (a.y + b.y) / 2)


def line_intersection(p1: Point, p2: Point, p3: Point, p4: Point) -> Point:
    """Intersection of the infinite lines through (p1,p2) and (p3,p4).

    Does NOT clip to the segments - returns the intersection even if it lies
    outside both. Used to extend construction lines in the draft.
    Raises ValueError if lines are parallel (within 1e-12).
    """
    x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y
    x3, y3, x4, y4 = p3.x, p3.y, p4.x, p4.y
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        raise ValueError("lines are parallel")
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return Point(x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def bezier_curve(p0: Point, p1: Point, p2: Point, n: int = 32) -> list[Point]:
    """Quadratic Bezier sampled at n points (endpoints inclusive)."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        x = u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x
        y = u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y
        pts.append(Point(x, y))
    return pts


def cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, n: int = 24) -> list[Point]:
    """Cubic Bezier sampled at n points (endpoints inclusive)."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        x = u**3 * p0.x + 3 * u*u * t * p1.x + 3 * u * t*t * p2.x + t**3 * p3.x
        y = u**3 * p0.y + 3 * u*u * t * p1.y + 3 * u * t*t * p2.y + t**3 * p3.y
        pts.append(Point(x, y))
    return pts


def unit_vector(dx: float, dy: float) -> tuple[float, float]:
    """Normalize a 2D vector. Raises ValueError on near-zero input."""
    norm = (dx * dx + dy * dy) ** 0.5
    if norm < 1e-9:
        raise ValueError("zero-length vector")
    return dx / norm, dy / norm


def cubic_with_tangents(
    p_start: Point,
    p_end: Point,
    t_start: tuple[float, float],
    t_end: tuple[float, float],
    alpha: float | None = None,
    beta: float | None = None,
    n: int = 24,
) -> list[Point]:
    """Cubic Bezier from p_start to p_end with prescribed tangent directions.

    t_start: vector pointing OUT of p_start along the curve (does not need to be unit).
    t_end:   vector pointing INTO p_end (i.e. the direction the curve is traveling
             as it arrives at p_end). Does not need to be unit.

    The control points P1, P2 are placed along these tangents at distances
    alpha (from p_start) and beta (from p_end). When alpha=beta=chord/3 the
    curve has a moderate, natural-looking bow; larger values produce deeper
    curves. Defaults to chord_length / 3 if not given.
    """
    chord_len = ((p_end.x - p_start.x) ** 2 + (p_end.y - p_start.y) ** 2) ** 0.5
    if alpha is None:
        alpha = chord_len / 3.0
    if beta is None:
        beta = chord_len / 3.0
    ux_s, uy_s = unit_vector(*t_start)
    ux_e, uy_e = unit_vector(*t_end)
    p1 = Point(p_start.x + alpha * ux_s, p_start.y + alpha * uy_s)
    # t_end points INTO p_end, so P2 is reached by going BACKWARDS along it.
    p2 = Point(p_end.x - beta * ux_e, p_end.y - beta * uy_e)
    return cubic_bezier(p_start, p1, p2, p_end, n)


def horizontal_line_through(y: float, span: float = 10000) -> tuple[Point, Point]:
    """Return two points defining the infinite horizontal line at the given y.
    `line_intersection` only needs the line direction; `span` keeps the points
    clearly off-pattern. Used to find intersections with construction lines."""
    return Point(-span, y), Point(span, y)


def curve_segment(p_from: Point, p_to: Point, bow_mm: float, perp_x: float, perp_y: float, n: int = 16) -> list[Point]:
    """Quadratic Bezier curve from p_from to p_to, with control point at the chord midpoint
    offset along the unit vector (perp_x, perp_y) by bow_mm.

    Returns sampled points INCLUDING both endpoints.

    The caller chooses (perp_x, perp_y) explicitly to avoid ambiguity about
    'outward' vs 'inward' direction (which depends on polygon orientation).
    Pass the unit vector as you intend it: e.g. (1, 0) bows the curve in +x,
    (0, -1) bows in -y. Magnitude doesn't matter (vector is normalized).
    """
    norm = (perp_x ** 2 + perp_y ** 2) ** 0.5
    if norm < 1e-9:
        raise ValueError("perp vector must be non-zero")
    ux = perp_x / norm
    uy = perp_y / norm
    midx = (p_from.x + p_to.x) / 2
    midy = (p_from.y + p_to.y) / 2
    control = Point(midx + ux * bow_mm, midy + uy * bow_mm)
    return bezier_curve(p_from, control, p_to, n)


def curve_through(p_from: Point, control: Point, p_to: Point, n: int = 16) -> list[Point]:
    """Wrapper: explicit control point. Use when you have a meaningful waypoint
    (like F or AA in the jeans draft) you want the curve to bend toward."""
    return bezier_curve(p_from, control, p_to, n)


def curved_edge(p_from: Point, p_to: Point, bow_mm: float, side: str = "right", n: int = 20) -> list[Point]:
    """Sample a quadratic Bezier from p_from to p_to that bulges perpendicular
    to the chord by `bow_mm`. `side` selects the side of the chord:
    - "right": rotate the chord direction 90 degrees clockwise (in y-down coords,
      this is "to the geographic right of travel direction").
    - "left": rotate 90 degrees counter-clockwise.

    Returns n points INCLUDING both endpoints. Used to replace straight outline
    edges with smooth curves (hip curve, seat curve, fly, hollow inseam, etc.).
    """
    if bow_mm == 0:
        return [p_from, p_to]
    dx = p_to.x - p_from.x
    dy = p_to.y - p_from.y
    norm = (dx * dx + dy * dy) ** 0.5
    if norm < 1e-9:
        return [p_from, p_to]
    if side == "right":
        nx, ny = dy / norm, -dx / norm
    elif side == "left":
        nx, ny = -dy / norm, dx / norm
    else:
        raise ValueError(f"unknown side {side!r}; expected 'right' or 'left'")
    midx = (p_from.x + p_to.x) / 2
    midy = (p_from.y + p_to.y) / 2
    control = Point(midx + nx * bow_mm, midy + ny * bow_mm)
    return bezier_curve(p_from, control, p_to, n)
