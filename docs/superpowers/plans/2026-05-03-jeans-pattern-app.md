# Selvedge Jeans Pattern App – Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Desktop app (Windows + macOS) che, dato un set di misure corporee, genera il cartamodello completo di un paio di selvedge jeans esportabile in PDF/SVG a scala 1:1 per l'uso con un pattern projector.

**Architecture:** Architettura a tre layer puri:
1. **Core geometrico** – calcolo punti/curve del cartamodello, indipendente dall'UI, completamente testabile.
2. **Export** – serializza il cartamodello in SVG (anteprima) e PDF (1:1 con calibration square + opzione tile A4).
3. **UI desktop Qt (PySide6)** – form misure stile Excel + anteprima live + bottoni esporta.

L'app segue il workflow del PDF "Drafting Selvedge Denim Jeans" di J.E. Landis: prima il **basic draft** (front + back), poi gli **updates** del 501-style (curva I-H, F-AA, perpendicolari hem, hollow thigh, ecc.), poi gli **accessori** (waistband, button fly, front pocket, yoke, back pocket, belt loops). Le formule del calcolatore Excel `SelvedgeJeansCalculatorMaster.xlsx` sono la fonte di verità per le derivazioni numeriche.

**Tech Stack:**
- **Python 3.11+** – linguaggio principale
- **PySide6** – GUI Qt cross-platform (Win + macOS) con licenza LGPL
- **shapely 2.x** – operazioni geometriche (linee, intersezioni, curve, offset)
- **svgwrite** – generazione SVG
- **reportlab** – generazione PDF a scala reale (mm)
- **pytest** – test
- **PyInstaller** – packaging in eseguibili Windows/macOS

---

## Context

L'utente cuce jeans selvedge su misura usando le istruzioni del PDF di J.E. Landis (2024) accompagnato da uno spreadsheet calcolatore. Il flusso attuale è manuale: digita misure in Excel, legge i valori derivati, traccia il cartamodello a mano su carta. Vuole automatizzare l'intero processo: da una form misure ottiene direttamente il PDF del cartamodello a scala 1:1 da proiettare sulla stoffa con un pattern projector e tagliare. Lo scopo è risparmiare ore di tracciatura manuale e azzerare errori di trascrizione/disegno.

**Convenzioni tecniche del cartamodello (dal PDF, pag. 4):**
- Seam allowance 3/8" ovunque, eccetto cucitura centrale dietro/yoke (5/8")
- Hem 1"
- Waistband finita 1-1/2", waist + 1-3/8" per button stand del fly + 3/8" SA per lato
- Belt loops 1/2" × 2-1/2"
- Tutte le SA sono **incluse** nel draft

**Nomi punti del draft (dal PDF e Excel):**
A, B, C, D, E (asse verticale fronte) · F, G (seat front) · H, I (waist front) · K, N, L, M (knee/hem) · O, P (linee diagonali) · R, S, T, U, V, W (back) · X, Y, Z, AA (updated draft)

---

## File Structure

```
C:\Projects\Jeans\
├── README.md
├── pyproject.toml                      # deps + project meta
├── requirements-dev.txt
├── .gitignore
├── src/jeans_pattern/
│   ├── __init__.py
│   ├── measurements.py                 # @dataclass Measurements (cm); validators
│   ├── geometry.py                     # Point, Line, helpers (square_out, mid, dist, intersect, curve)
│   ├── draft_basic.py                  # build_basic_front(), build_basic_back()
│   ├── draft_updated.py                # apply_501_updates(front, back) – curve, hollow, perpendicular hem
│   ├── draft_extras.py                 # build_waistband(), build_fly(), build_front_pocket(), build_yoke(), build_back_pocket(), build_belt_loop()
│   ├── pattern.py                      # @dataclass Pattern: list of PatternPiece (nome, polilinee, SA, etichette)
│   ├── export_svg.py                   # pattern_to_svg(pattern) -> bytes
│   ├── export_pdf.py                   # pattern_to_pdf(pattern, mode="single"|"tiled_a4", calibration=True)
│   └── version.py
├── src/jeans_app/
│   ├── __init__.py
│   ├── main.py                         # entry point; QApplication
│   ├── main_window.py                  # QMainWindow: form a sinistra, preview a destra
│   ├── measurement_form.py             # QFormLayout con campi misure + unit toggle
│   ├── preview_widget.py               # QSvgWidget per anteprima live
│   └── resources.py                    # constants/labels/icons
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # fixture sample_measurements (i valori default Excel: 34.5/44/9.75/10.375/9.75/34 inch)
│   ├── test_measurements.py
│   ├── test_geometry.py
│   ├── test_draft_basic.py             # confronta valori derivati con quelli Excel
│   ├── test_draft_updated.py
│   ├── test_draft_extras.py
│   ├── test_pattern.py
│   ├── test_export_svg.py
│   └── test_export_pdf.py
├── docs/
│   ├── source-spec/
│   │   ├── drafting_selvedge_jeans.pdf      (copia locale del PDF sorgente)
│   │   └── SelvedgeJeansCalculatorMaster.xlsx
│   └── superpowers/plans/
│       └── 2026-05-03-jeans-pattern-app.md  (questo file)
└── packaging/
    ├── pyinstaller_win.spec
    └── pyinstaller_mac.spec
```

**Convenzione unità interna:** tutto in **millimetri** internamente. La form accetta input in cm o inch (toggle), convertiti subito in mm. L'export PDF usa mm direttamente (reportlab supporta `mm`).

---

## Task 0: Project Bootstrap

**Files:**
- Create: `C:\Projects\Jeans\pyproject.toml`
- Create: `C:\Projects\Jeans\requirements-dev.txt`
- Create: `C:\Projects\Jeans\.gitignore`
- Create: `C:\Projects\Jeans\README.md`
- Create: `C:\Projects\Jeans\src\jeans_pattern\__init__.py` (vuoto)
- Create: `C:\Projects\Jeans\src\jeans_app\__init__.py` (vuoto)
- Create: `C:\Projects\Jeans\tests\__init__.py` (vuoto)
- Copy: i due file sorgente da `C:\Users\rober\Desktop\Cartamodelli\Selvedge Jeans su misura\` a `docs\source-spec\`

- [ ] **Step 1: Crea `pyproject.toml`**

```toml
[project]
name = "jeans-pattern-app"
version = "0.1.0"
description = "Selvedge jeans custom pattern generator with pattern projector export"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.7",
    "shapely>=2.0",
    "svgwrite>=1.4",
    "reportlab>=4.2",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-qt>=4.4", "pyinstaller>=6.10"]

[project.scripts]
jeans-app = "jeans_app.main:main"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Crea `requirements-dev.txt`**

```
PySide6>=6.7
shapely>=2.0
svgwrite>=1.4
reportlab>=4.2
pytest>=8
pytest-qt>=4.4
pyinstaller>=6.10
```

- [ ] **Step 3: Crea `.gitignore`**

```
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
build/
dist/
*.egg-info/
.idea/
.vscode/
*.spec
!packaging/*.spec
```

- [ ] **Step 4: Inizializza git repo e installa**

```bash
cd C:\Projects\Jeans
git init
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

- [ ] **Step 5: Copia spec sorgenti**

```bash
mkdir -p "C:\Projects\Jeans\docs\source-spec"
cp "C:\Users\rober\Desktop\Cartamodelli\Selvedge Jeans su misura\drafting_selvedge_jeans.pdf" "C:\Projects\Jeans\docs\source-spec\"
cp "C:\Users\rober\Desktop\Cartamodelli\Selvedge Jeans su misura\SelvedgeJeansCalculatorMaster.xlsx" "C:\Projects\Jeans\docs\source-spec\"
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "chore: bootstrap project structure"
```

---

## Task 1: Measurements model

**Files:**
- Create: `src/jeans_pattern/measurements.py`
- Test: `tests/test_measurements.py`

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_measurements.py
import pytest
from jeans_pattern.measurements import Measurements, INCH_TO_MM

def test_default_measurements_in_mm():
    m = Measurements.from_inches(waist=34.5, seat=44.0, rise=9.75,
                                  knee=10.375, bottom=9.75, length=34.0)
    assert m.waist_mm == pytest.approx(34.5 * 25.4)
    assert m.seat_mm == pytest.approx(44.0 * 25.4)

def test_from_cm_roundtrip():
    m = Measurements.from_cm(waist=87.63, seat=111.76, rise=24.765,
                             knee=26.3525, bottom=24.765, length=86.36)
    assert m.waist_mm == pytest.approx(876.3)

def test_negative_value_rejected():
    with pytest.raises(ValueError):
        Measurements.from_cm(waist=-1, seat=100, rise=25, knee=26, bottom=25, length=86)

def test_zero_value_rejected():
    with pytest.raises(ValueError):
        Measurements.from_cm(waist=0, seat=100, rise=25, knee=26, bottom=25, length=86)
```

- [ ] **Step 2: Esegui i test (devono fallire)**

```bash
pytest tests/test_measurements.py -v
```
Expected: tutti FAIL con `ModuleNotFoundError: No module named 'jeans_pattern.measurements'`

- [ ] **Step 3: Implementa `measurements.py`**

```python
# src/jeans_pattern/measurements.py
from dataclasses import dataclass

INCH_TO_MM = 25.4

@dataclass(frozen=True)
class Measurements:
    """Tutte le misure salvate in millimetri."""
    waist_mm: float
    seat_mm: float
    rise_mm: float
    knee_mm: float
    bottom_mm: float
    length_mm: float

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")

    @classmethod
    def from_inches(cls, *, waist, seat, rise, knee, bottom, length):
        return cls(
            waist_mm=waist * INCH_TO_MM,
            seat_mm=seat * INCH_TO_MM,
            rise_mm=rise * INCH_TO_MM,
            knee_mm=knee * INCH_TO_MM,
            bottom_mm=bottom * INCH_TO_MM,
            length_mm=length * INCH_TO_MM,
        )

    @classmethod
    def from_cm(cls, *, waist, seat, rise, knee, bottom, length):
        return cls(
            waist_mm=waist * 10,
            seat_mm=seat * 10,
            rise_mm=rise * 10,
            knee_mm=knee * 10,
            bottom_mm=bottom * 10,
            length_mm=length * 10,
        )
```

- [ ] **Step 4: Esegui i test (devono passare)**

```bash
pytest tests/test_measurements.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/measurements.py tests/test_measurements.py
git commit -m "feat(core): add Measurements model with mm/cm/inch support"
```

---

## Task 2: Geometry primitives

**Files:**
- Create: `src/jeans_pattern/geometry.py`
- Test: `tests/test_geometry.py`

Helpers necessari ricostruiti dalle istruzioni del PDF: "draw line", "square out from", "midpoint", "intersect", curve di Bézier per fly/hip/seat.

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_geometry.py
import pytest
from jeans_pattern.geometry import Point, distance, square_out, midpoint, line_intersection, bezier_curve

def test_point_equality():
    assert Point(1, 2) == Point(1, 2)

def test_distance():
    assert distance(Point(0, 0), Point(3, 4)) == pytest.approx(5)

def test_square_out_horizontal_right():
    p = Point(10, 20)
    q = square_out(p, length=5, direction="right")
    assert q == Point(15, 20)

def test_square_out_horizontal_left():
    assert square_out(Point(10, 20), 5, "left") == Point(5, 20)

def test_square_out_vertical_up():
    assert square_out(Point(10, 20), 5, "up") == Point(10, 15)

def test_square_out_vertical_down():
    assert square_out(Point(10, 20), 5, "down") == Point(10, 25)

def test_midpoint():
    assert midpoint(Point(0, 0), Point(10, 20)) == Point(5, 10)

def test_line_intersection():
    p = line_intersection(Point(0, 0), Point(10, 10), Point(0, 10), Point(10, 0))
    assert p.x == pytest.approx(5)
    assert p.y == pytest.approx(5)

def test_bezier_curve_endpoints():
    pts = bezier_curve(Point(0, 0), Point(5, -5), Point(10, 0), n=20)
    assert pts[0] == Point(0, 0)
    assert pts[-1].x == pytest.approx(10)
    assert pts[-1].y == pytest.approx(0)
    assert len(pts) == 20
```

- [ ] **Step 2: Esegui i test**

```bash
pytest tests/test_geometry.py -v
```
Expected: tutti FAIL

- [ ] **Step 3: Implementa `geometry.py`**

```python
# src/jeans_pattern/geometry.py
from dataclasses import dataclass
from math import hypot

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9

    def __hash__(self):
        return hash((round(self.x, 9), round(self.y, 9)))

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
    x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y
    x3, y3, x4, y4 = p3.x, p3.y, p4.x, p4.y
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        raise ValueError("lines are parallel")
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return Point(x1 + t * (x2 - x1), y1 + t * (y2 - y1))

def bezier_curve(p0: Point, p1: Point, p2: Point, n: int = 32) -> list[Point]:
    """Quadratic Bézier sampled at n points (endpoints inclusi)."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        x = u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x
        y = u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y
        pts.append(Point(x, y))
    return pts
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_geometry.py -v
```
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/geometry.py tests/test_geometry.py
git commit -m "feat(core): geometry primitives (Point, square_out, intersect, bezier)"
```

---

## Task 3: Pattern data model

**Files:**
- Create: `src/jeans_pattern/pattern.py`
- Test: `tests/test_pattern.py`

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_pattern.py
from jeans_pattern.geometry import Point
from jeans_pattern.pattern import PatternPiece, Pattern

def test_pattern_piece_bbox():
    p = PatternPiece(name="front", outline=[Point(0,0), Point(100,0), Point(100,200), Point(0,200)])
    assert p.bbox() == (0, 0, 100, 200)

def test_pattern_piece_with_holes_and_labels():
    p = PatternPiece(
        name="front",
        outline=[Point(0,0), Point(10,0), Point(10,10), Point(0,10)],
        construction_lines=[[Point(0,5), Point(10,5)]],
        labels=[(Point(5,5), "FRONT")],
    )
    assert p.construction_lines[0][0] == Point(0,5)
    assert p.labels[0] == (Point(5,5), "FRONT")

def test_pattern_pieces_iteration():
    a = PatternPiece(name="a", outline=[Point(0,0), Point(1,0), Point(1,1)])
    b = PatternPiece(name="b", outline=[Point(0,0), Point(2,0), Point(2,2)])
    pat = Pattern(pieces=[a, b])
    assert [p.name for p in pat] == ["a", "b"]
```

- [ ] **Step 2: Esegui i test**

```bash
pytest tests/test_pattern.py -v
```
Expected: tutti FAIL

- [ ] **Step 3: Implementa `pattern.py`**

```python
# src/jeans_pattern/pattern.py
from dataclasses import dataclass, field
from .geometry import Point

@dataclass
class PatternPiece:
    name: str
    outline: list[Point]                                  # poligono chiuso (no ripetere primo punto)
    construction_lines: list[list[Point]] = field(default_factory=list)
    labels: list[tuple[Point, str]] = field(default_factory=list)
    seam_allowance_mm: float = 9.525                       # 3/8" default

    def bbox(self) -> tuple[float, float, float, float]:
        xs = [p.x for p in self.outline]
        ys = [p.y for p in self.outline]
        return (min(xs), min(ys), max(xs), max(ys))

@dataclass
class Pattern:
    pieces: list[PatternPiece]

    def __iter__(self):
        return iter(self.pieces)
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_pattern.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/pattern.py tests/test_pattern.py
git commit -m "feat(core): Pattern and PatternPiece data model"
```

---

## Task 4: Basic front draft

**Files:**
- Create: `src/jeans_pattern/draft_basic.py`
- Test: `tests/test_draft_basic.py`
- Test: `tests/conftest.py`

Implementa pagine 6–9 del PDF + formule cella B10–B22 dell'Excel. Coordinate convention: A in alto a sinistra (0,0), y cresce verso il basso. Tutto in mm.

Mappatura formule (default 34.5"/44"/9.75"/10.375"/9.75"/34" → mm):
- waist=876.3, seat=1117.6, rise=247.65, knee=263.525, bottom=247.65, length=863.6
- A-B = rise = 247.65 mm
- B-C = length + 0.5" = (34 + 0.5)*25.4 = 876.3 mm
- C-E = 1" = 25.4 mm
- A-E = 247.65 + 876.3 + 25.4 = 1149.35 mm
- B-D = (length + 0.5)/2 - 2" inch space → in mm: ((34+0.5)/2 - 2)*25.4 = 419.1 mm
- B-F = seat/4 = 279.4 mm
- F-G = 2" = 50.8 mm
- I-H = waist/4 + 0.5" = (waist + 50.8)/4 → no, formula B17=D2+0.5 con D2=B2/4 cioè waist_inch/4 + 0.5 → in mm: (waist_mm/4) + 12.7 = 231.775 mm
- G-K = (B-F + F-G)/2 = (279.4 + 50.8)/2 = 165.1 mm (orizz. da B verso fuori? No, vedi sotto)
- N-M = N-L = bottom/2 = 123.825 mm

⚠ **Verifica formula G-K**: B18 = `=(B15+B16)/2` dove B15=`=D3` (=seat/4), B16=2.0 (F-G) → quindi G-K = midpoint orizz tra B e G… ma il PDF dice "K is half way between B-G, square down to N". Quindi K è punto sull'asse orizzontale a metà fra B e G, dal quale si scende a N sulla linea hem.

- [ ] **Step 1: Crea `conftest.py` con fixture default**

```python
# tests/conftest.py
import pytest
from jeans_pattern.measurements import Measurements

@pytest.fixture
def default_measurements():
    """Esempio di default dell'Excel calculator."""
    return Measurements.from_inches(
        waist=34.5, seat=44.0, rise=9.75,
        knee=10.375, bottom=9.75, length=34.0,
    )
```

- [ ] **Step 2: Scrivi i test**

```python
# tests/test_draft_basic.py
import pytest
from jeans_pattern.draft_basic import build_basic_front, build_basic_back, FrontPoints

INCH = 25.4

def test_front_axis_distances(default_measurements):
    front: FrontPoints = build_basic_front(default_measurements)
    assert front.A.y == 0
    assert (front.B.y - front.A.y) == pytest.approx(9.75 * INCH)         # rise
    assert (front.C.y - front.B.y) == pytest.approx(34.5 * INCH)         # length + 0.5"
    assert (front.E.y - front.C.y) == pytest.approx(1.0 * INCH)          # hem
    assert (front.D.y - front.B.y) == pytest.approx(((34.0 + 0.5)/2 - 2.0) * INCH)

def test_front_seat_and_waist(default_measurements):
    front = build_basic_front(default_measurements)
    assert front.F.x == pytest.approx(44.0 / 4 * INCH)                   # seat/4 from B
    assert (front.G.x - front.F.x) == pytest.approx(2.0 * INCH)
    assert (front.H.x - front.I.x) == pytest.approx((34.5 / 4 + 0.5) * INCH)  # waist/4+0.5

def test_front_K_and_N(default_measurements):
    front = build_basic_front(default_measurements)
    expected_K_x = (front.B.x + front.G.x) / 2
    assert front.K.x == pytest.approx(expected_K_x)
    assert front.N.x == pytest.approx(front.K.x)
    assert front.N.y == pytest.approx(front.E.y)

def test_front_hem_half_width(default_measurements):
    front = build_basic_front(default_measurements)
    half_hem = 9.75 / 2 * INCH
    assert (front.M.x - front.N.x) == pytest.approx(half_hem)
    assert (front.N.x - front.L.x) == pytest.approx(half_hem)

def test_front_outline_is_closed_polygon(default_measurements):
    front = build_basic_front(default_measurements)
    poly = front.outline_polygon()
    assert len(poly) >= 6
    assert poly[0] != poly[-1]   # convenzione: poligono chiuso senza ripetere
```

- [ ] **Step 3: Esegui i test**

```bash
pytest tests/test_draft_basic.py -v
```
Expected: tutti FAIL

- [ ] **Step 4: Implementa `draft_basic.py` (front)**

```python
# src/jeans_pattern/draft_basic.py
from dataclasses import dataclass
from .geometry import Point, square_out, midpoint, bezier_curve
from .measurements import Measurements

INCH = 25.4

@dataclass
class FrontPoints:
    A: Point; B: Point; C: Point; D: Point; E: Point
    F: Point; G: Point; H: Point; I: Point
    K: Point; N: Point; L: Point; M: Point
    O: Point; P: Point

    def outline_polygon(self) -> list[Point]:
        """Outline finale del front (basic): H -> I (waist) -> G (fly top) -> P (knee out) -> M (hem out)
        -> L (hem in) -> O (knee in) -> B (crotch) -> H (hip curve)."""
        return [self.H, self.I, self.G, self.P, self.M, self.L, self.O, self.B]

def build_basic_front(m: Measurements) -> FrontPoints:
    rise = m.rise_mm
    length_plus_half = m.length_mm + 0.5 * INCH
    hem = 1.0 * INCH

    # Asse verticale A-E (centro fly), x=0
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

    # K = midpoint orizzontale fra B e G, sulla quota waist line (A.y)? PDF: "K is halfway B-G,
    # square down to N". K sta sulla linea hip orizzontale tra B e G; ma su B la y=rise.
    # In base alla formula B18=(B15+B16)/2 (orizzontale), e B19=N-M=bottom/2, "square down to N":
    # K ha la x = midpoint(B.x, G.x), y = rise (linea orizzontale B-G prolungata).
    K = Point((B.x + G.x) / 2, B.y)

    # N = sotto K sulla linea hem (E.y), centro del bottom
    N = Point(K.x, E.y)
    # L (interno = lato inseam) e M (esterno = lato outseam)
    L = Point(N.x - m.bottom_mm / 2, E.y)
    M = Point(N.x + m.bottom_mm / 2, E.y)

    # O = intersezione di linea B-L con linea knee (D.y)
    from .geometry import line_intersection
    O = line_intersection(B, L, Point(0, D.y), Point(1000, D.y))
    # P = intersezione di linea G-M con linea knee
    P = line_intersection(G, M, Point(0, D.y), Point(1000, D.y))

    return FrontPoints(A=A, B=B, C=C, D=D, E=E, F=F, G=G, H=H, I=I,
                       K=K, N=N, L=L, M=M, O=O, P=P)
```

- [ ] **Step 5: Esegui i test front**

```bash
pytest tests/test_draft_basic.py -v -k front
```
Expected: 5 PASS

- [ ] **Step 6: Commit**

```bash
git add src/jeans_pattern/draft_basic.py tests/test_draft_basic.py tests/conftest.py
git commit -m "feat(core): basic front draft"
```

---

## Task 5: Basic back draft

**Files:**
- Modify: `src/jeans_pattern/draft_basic.py` (aggiungi `build_basic_back`)
- Modify: `tests/test_draft_basic.py` (aggiungi test back)

Implementa pagine 10–14 del PDF. Il back si costruisce **traslando** punti del front:
- B-R, O-U, P-T, M-V, L-W = 1" outward (per ogni punto, "outward" = direzione perpendicolare all'asse del cartamodello, vedi diagramma)
- G-S = seat/16 (extension oltre G, linea waist)
- Out seam W-U-R extended → Y sulla waist line
- Inseam V-T, T-S
- I-X = sopra I (basic back: 0; updated: seat/10 → vedi Task 6)
- Y-Z waist line; G-Z line
- Curve seat S-Z
- Hollow inseam: 1/8" giù da S, 3/8" hollow centro

Per il **basic** draft usiamo I-X = 0 (cioè X = I), Y-Z = waist/4 + 2" (B18 Excel).

- [ ] **Step 1: Aggiungi i test back**

```python
# tests/test_draft_basic.py (append)
def test_back_extension_distances(default_measurements):
    back = build_basic_back(default_measurements)
    INCH_ = 25.4
    assert (back.R.y - back.B.y) == pytest.approx(0)        # R = B shifted 1" toward outseam (orizz)
    assert abs(back.R.x - back.B.x) == pytest.approx(1 * INCH_)
    assert (back.S.x - back.G.x) == pytest.approx(44.0 / 16 * INCH_)
    assert (back.Z.x - back.I.x) == pytest.approx(34.5 / 4 * INCH_ + 2 * INCH_)

def test_back_outline_closed(default_measurements):
    back = build_basic_back(default_measurements)
    poly = back.outline_polygon()
    assert len(poly) >= 6
```

- [ ] **Step 2: Esegui i test back**

```bash
pytest tests/test_draft_basic.py -v -k back
```
Expected: FAIL (build_basic_back non esiste)

- [ ] **Step 3: Implementa `build_basic_back`**

```python
# src/jeans_pattern/draft_basic.py (append)
@dataclass
class BackPoints:
    B: Point; R: Point; G: Point; S: Point
    I: Point; X: Point; Y: Point; Z: Point
    P: Point; T: Point; O: Point; U: Point
    M: Point; V: Point; L: Point; W: Point

    def outline_polygon(self) -> list[Point]:
        # Y -> Z (waist) -> S (seat) -> T (knee out) -> V (hem out) -> W (hem in) -> U (knee in) -> R (back crotch) -> Y
        return [self.Y, self.Z, self.S, self.T, self.V, self.W, self.U, self.R]

def build_basic_back(m: Measurements) -> BackPoints:
    """Basic back: nessuna estensione I-X (vedi Task 6 per updated)."""
    front = build_basic_front(m)

    # Shift di 1" "outward". Per la nostra convenzione coordinate:
    # - B è all'inseam → outward dal back significa verso sinistra (x negativa) sull'inseam side.
    #   Ma il PDF mostra che il back è specchiato e attaccato al front lungo l'inseam.
    # - Per semplicità geometrica: il BACK è disegnato su uno stesso sistema con asse y comune,
    #   spostato a sinistra del front. Adottiamo: i punti R/U/T/V/W sono traslati 1" RISPETTO ai
    #   loro corrispondenti front, lungo direzioni che corrispondono a "fuori dal front":
    #       B → R: 1" a sinistra (back inseam si estende verso il back-crotch)
    #       O → U: 1" a sinistra
    #       P → T: 1" a destra (outseam back più largo)
    #       M → V: 1" a destra
    #       L → W: 1" a sinistra
    one_inch = 1 * INCH
    R = square_out(front.B, one_inch, "left")
    U = square_out(front.O, one_inch, "left")
    T = square_out(front.P, one_inch, "right")
    V = square_out(front.M, one_inch, "right")
    W = square_out(front.L, one_inch, "left")

    # G-S = seat/16 (oltre G verso outseam = destra)
    S = square_out(front.G, m.seat_mm / 16, "right")

    # I-X (basic): X = I (no estensione)
    X = front.I

    # Y = intersezione linea outseam W-U-R prolungata con linea waist (A.y)
    from .geometry import line_intersection
    waist_left = Point(-10000, front.A.y)
    waist_right = Point(10000, front.A.y)
    Y = line_intersection(W, R, waist_left, waist_right)

    # Z = waist/4 + 2" da I sulla waist line (verso destra)
    Z = square_out(front.I, m.waist_mm / 4 + 2 * INCH, "right")

    return BackPoints(
        B=front.B, R=R, G=front.G, S=S,
        I=front.I, X=X, Y=Y, Z=Z,
        P=front.P, T=T, O=front.O, U=U,
        M=front.M, V=V, L=front.L, W=W,
    )
```

- [ ] **Step 4: Esegui tutti i test draft_basic**

```bash
pytest tests/test_draft_basic.py -v
```
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/draft_basic.py tests/test_draft_basic.py
git commit -m "feat(core): basic back draft"
```

---

## Task 6: Updated draft (501 silhouette)

**Files:**
- Create: `src/jeans_pattern/draft_updated.py`
- Test: `tests/test_draft_updated.py`

Implementa pagine 19–24 del PDF + formule M21 (F-AA = seat/16) e M22 (I-X for 501 = seat/10) dell'Excel.

Modifiche rispetto al basic:
1. **I-X** = seat/10 (verticale sopra I)
2. Ridisegna **Y-Z** per intersecare nuovo X
3. Sposta **I e H** verso outseam di 3/4" (orizzontale)
4. Abbassa I di 1/4", curva I-H
5. Ricurva B-H, sposta tasca 3/4"
6. Crea **F-AA** = seat/16 (verticale sotto F sull'asse fly), nuovo fly I-AA-G (curve)
7. Cancella hem, square da L e W perpendicolare a outseam (non a construction line)
8. Square up da V e M a 90° su knee line (parallel outseam) → nuovi T, P
9. Sposta T e P giù di 2" lungo le loro linee
10. Hollow front thigh 3/4", back thigh 1"
11. Hem 1" finale a V, M, L, W

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_draft_updated.py
import pytest
from jeans_pattern.measurements import Measurements
from jeans_pattern.draft_updated import build_updated_front, build_updated_back

INCH = 25.4

def test_updated_front_I_shifted(default_measurements):
    f = build_updated_front(default_measurements)
    from jeans_pattern.draft_basic import build_basic_front
    base = build_basic_front(default_measurements)
    assert f.I.x == pytest.approx(base.I.x + 0.75 * INCH)
    assert f.I.y == pytest.approx(base.I.y + 0.25 * INCH)

def test_updated_front_AA_position(default_measurements):
    f = build_updated_front(default_measurements)
    from jeans_pattern.draft_basic import build_basic_front
    base = build_basic_front(default_measurements)
    # F-AA = seat/16 sulla verticale dell'asse fly (x=0)
    assert f.AA.x == pytest.approx(0)
    assert f.AA.y == pytest.approx(base.F.y + 44.0/16 * INCH)

def test_updated_back_X_position(default_measurements):
    b = build_updated_back(default_measurements)
    from jeans_pattern.draft_basic import build_basic_back
    base = build_basic_back(default_measurements)
    # I-X = seat/10 sopra I
    assert b.X.x == pytest.approx(base.I.x)
    assert b.X.y == pytest.approx(base.I.y - 44.0/10 * INCH)

def test_updated_P_moved_down(default_measurements):
    f = build_updated_front(default_measurements)
    from jeans_pattern.draft_basic import build_basic_front
    base = build_basic_front(default_measurements)
    # P_new costruito perpendicolare al knee da M, poi 2" lungo outseam → 
    # deve essere più in basso del P originale (basic) di almeno ~1.5"
    assert f.P_new.y > base.P.y + 1.5 * INCH

def test_updated_back_T_moved_down(default_measurements):
    b = build_updated_back(default_measurements)
    from jeans_pattern.draft_basic import build_basic_back
    base = build_basic_back(default_measurements)
    assert b.T_new.y > base.T.y + 1.5 * INCH
```

- [ ] **Step 2: Esegui (deve fallire)**

```bash
pytest tests/test_draft_updated.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementa `draft_updated.py`**

```python
# src/jeans_pattern/draft_updated.py
from dataclasses import dataclass
from .geometry import Point, square_out, line_intersection
from .measurements import Measurements
from .draft_basic import build_basic_front, build_basic_back, FrontPoints, BackPoints

INCH = 25.4

@dataclass
class UpdatedFront:
    """Wrapper attorno al FrontPoints base con i punti aggiunti dell'updated draft."""
    base: FrontPoints
    new_I: Point
    new_H: Point
    AA: Point
    P_new: Point

    # Proxy attribute access alla base per i punti invariati
    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def I(self) -> Point: return self.new_I
    @property
    def H(self) -> Point: return self.new_H

    def outline_polygon(self) -> list[Point]:
        b = self.base
        return [self.new_H, self.new_I, self.AA, b.G, self.P_new, b.M, b.L, b.O, b.B]

@dataclass
class UpdatedBack:
    base: BackPoints
    new_X: Point
    new_Y: Point
    new_Z: Point
    T_new: Point

    def __getattr__(self, name):
        return getattr(self.base, name)

    @property
    def X(self) -> Point: return self.new_X
    @property
    def Y(self) -> Point: return self.new_Y
    @property
    def Z(self) -> Point: return self.new_Z

    def outline_polygon(self) -> list[Point]:
        b = self.base
        return [self.new_Y, self.new_Z, b.S, self.T_new, b.V, b.W, b.U, b.R]

def build_updated_front(m: Measurements) -> UpdatedFront:
    base = build_basic_front(m)

    # 3+5: I shifted 0.75" verso outseam (right) e 0.25" giù
    new_I = Point(base.I.x + 0.75 * INCH, base.I.y + 0.25 * INCH)
    # 4: H shifted 0.75" verso outseam
    new_H = Point(base.H.x + 0.75 * INCH, base.H.y)

    # 7: F-AA = seat/16, AA sull'asse fly (x=0) sotto F
    AA = Point(0, base.F.y + m.seat_mm / 16)

    # 9-10 (front): square up da M perpendicolare al knee line, poi 2" lungo outseam G-M
    dx = base.M.x - base.G.x
    dy = base.M.y - base.G.y
    norm = (dx**2 + dy**2) ** 0.5
    ux, uy = dx / norm, dy / norm
    P_perp = Point(base.M.x, base.D.y)
    P_new = Point(P_perp.x + ux * 2 * INCH, P_perp.y + uy * 2 * INCH)

    return UpdatedFront(base=base, new_I=new_I, new_H=new_H, AA=AA, P_new=P_new)

def build_updated_back(m: Measurements) -> UpdatedBack:
    base = build_basic_back(m)

    # 1+2: I-X = seat/10 sopra I
    new_X = Point(base.I.x, base.I.y - m.seat_mm / 10)

    # 3: ridisegna Y-Z per intersecare nuovo X (Z mantiene x, sale a y di X)
    new_waist_y = new_X.y
    Y_new = line_intersection(base.W, base.R,
                              Point(-10000, new_waist_y), Point(10000, new_waist_y))
    Z_new = Point(base.Z.x, new_waist_y)

    # 9-10 (back): perpendicolare V → knee line, poi 2" lungo outseam V-S
    dx = base.V.x - base.S.x
    dy = base.V.y - base.S.y
    norm = (dx**2 + dy**2) ** 0.5
    ux, uy = dx / norm, dy / norm
    knee_y = base.T.y
    T_perp = Point(base.V.x, knee_y)
    T_new = Point(T_perp.x + ux * 2 * INCH, T_perp.y + uy * 2 * INCH)

    return UpdatedBack(base=base, new_X=new_X, new_Y=Y_new, new_Z=Z_new, T_new=T_new)
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_draft_updated.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/draft_updated.py tests/test_draft_updated.py
git commit -m "feat(core): updated draft with 501 silhouette modifications"
```

---

## Task 7: Accessori (waistband, fly, pockets, yoke, belt loop)

**Files:**
- Create: `src/jeans_pattern/draft_extras.py`
- Test: `tests/test_draft_extras.py`

Riferimenti PDF:
- **Waistband** (pag. 15): rettangolo, larghezza = waist + 1-3/8" + 3/8" SA × 2 = waist + 2-1/8"; altezza finita 1-1/2" + 3/8" SA × 2 = 2-1/4". Estensione button-stand 3-3/4".
- **Belt loop** (pag. 15): 3" × 1-1/4" finita 1/2" × 2-1/2"
- **Button fly** (pag. 16): button hole side 1-3/4" × (lunghezza fly), button stand 1-3/4" × (lunghezza fly + 1")
- **Front pocket** (pag. 17): apertura tasca da metà waist → 3" lungo outseam; pocket bag profondo 12"; pocket facing 1-1/8" × 1-1/8" rispetto curva
- **Yoke** (pag. 18): 1-1/2" giù sull'outseam, square verso center seat; SA 5/8" sui due lati
- **Back pocket** (pag. 18): 3-3/8" × ~5", piazzato per allinearsi con front pocket finita

- [ ] **Step 1: Scrivi i test (dimensioni base, no curve)**

```python
# tests/test_draft_extras.py
import pytest
from jeans_pattern.measurements import Measurements
from jeans_pattern.draft_extras import (
    build_waistband, build_belt_loop, build_button_fly,
    build_front_pocket, build_back_pocket, build_yoke,
)

INCH = 25.4

def test_waistband_dimensions(default_measurements):
    wb = build_waistband(default_measurements)
    width = max(p.x for p in wb.outline) - min(p.x for p in wb.outline)
    height = max(p.y for p in wb.outline) - min(p.y for p in wb.outline)
    assert width == pytest.approx((34.5 + 1.375 + 0.375 * 2) * INCH, abs=0.5)
    assert height == pytest.approx((1.5 + 0.375 * 2) * INCH, abs=0.5)

def test_belt_loop_dimensions(default_measurements):
    bl = build_belt_loop()
    w = max(p.x for p in bl.outline) - min(p.x for p in bl.outline)
    h = max(p.y for p in bl.outline) - min(p.y for p in bl.outline)
    assert w == pytest.approx(3.0 * INCH, abs=0.5)
    assert h == pytest.approx(1.25 * INCH, abs=0.5)

def test_front_pocket_returns_two_pieces(default_measurements):
    pieces = build_front_pocket(default_measurements)
    assert "pocket_bag" in pieces
    assert "pocket_facing" in pieces
    assert pieces["pocket_bag"].name == "pocket_bag"
    assert pieces["pocket_facing"].name == "pocket_facing"

def test_yoke_basic(default_measurements):
    yk = build_yoke(default_measurements)
    h = max(p.y for p in yk.outline) - min(p.y for p in yk.outline)
    assert h == pytest.approx(1.5 * INCH, abs=0.5)

def test_back_pocket(default_measurements):
    bp = build_back_pocket(default_measurements)
    w = max(p.x for p in bp.outline) - min(p.x for p in bp.outline)
    assert w == pytest.approx(3.375 * INCH, abs=1)

def test_button_fly_two_pieces(default_measurements):
    pieces = build_button_fly(default_measurements)
    assert "buttonhole_side" in pieces
    assert "button_stand" in pieces
```

- [ ] **Step 2: Esegui (devono fallire)**

```bash
pytest tests/test_draft_extras.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementa `draft_extras.py`**

```python
# src/jeans_pattern/draft_extras.py
from .geometry import Point
from .pattern import PatternPiece
from .measurements import Measurements

INCH = 25.4

def build_waistband(m: Measurements) -> PatternPiece:
    width = m.waist_mm + 1.375 * INCH + 0.375 * 2 * INCH
    height = 1.5 * INCH + 0.375 * 2 * INCH
    return PatternPiece(
        name="waistband",
        outline=[Point(0, 0), Point(width, 0), Point(width, height), Point(0, height)],
        labels=[(Point(width / 2, height / 2), "WAISTBAND × 1")],
    )

def build_belt_loop() -> PatternPiece:
    width = 3.0 * INCH    # piega in 4 → finito 3" / 4 = ~3/4" ma usato 1/2" finito
    height = 1.25 * INCH
    return PatternPiece(
        name="belt_loop",
        outline=[Point(0, 0), Point(width, 0), Point(width, height), Point(0, height)],
        labels=[(Point(width/2, height/2), "BELT LOOP × 5")],
    )

def build_button_fly(m: Measurements) -> dict[str, PatternPiece]:
    fly_length = m.rise_mm * 0.7  # approssimazione: fly = ~70% del rise
    bh_side = PatternPiece(
        name="fly_buttonhole_side",
        outline=[Point(0,0), Point(1.75*INCH, 0), Point(1.75*INCH, fly_length), Point(0, fly_length)],
        labels=[(Point(0.875*INCH, fly_length/2), "BUTTONHOLE SIDE × 1")],
    )
    stand = PatternPiece(
        name="fly_button_stand",
        outline=[Point(0,0), Point(1.75*INCH, 0), Point(1.75*INCH, fly_length + 1*INCH), Point(0, fly_length + 1*INCH)],
        labels=[(Point(0.875*INCH, (fly_length+INCH)/2), "BUTTON STAND × 1")],
    )
    return {"buttonhole_side": bh_side, "button_stand": stand}

def build_front_pocket(m: Measurements) -> dict[str, PatternPiece]:
    # Pocket bag: profondo 12", largo come metà waist + offset
    bag_w = m.waist_mm / 4 + 1 * INCH
    bag_h = 12 * INCH
    bag = PatternPiece(
        name="pocket_bag",
        outline=[Point(0,0), Point(bag_w, 0), Point(bag_w, bag_h), Point(0, bag_h)],
        labels=[(Point(bag_w/2, bag_h/2), "POCKET BAG × 2 (mirror)")],
    )
    facing = PatternPiece(
        name="pocket_facing",
        outline=[Point(0,0), Point(bag_w, 0), Point(bag_w, 4*INCH), Point(0, 4*INCH)],
        labels=[(Point(bag_w/2, 2*INCH), "POCKET FACING × 2 (mirror)")],
    )
    return {"pocket_bag": bag, "pocket_facing": facing}

def build_back_pocket(m: Measurements) -> PatternPiece:
    width = 3.375 * INCH    # 3-3/8"
    height = 5.5 * INCH
    return PatternPiece(
        name="back_pocket",
        outline=[Point(0,0), Point(width, 0), Point(width*0.5, height), Point(0, height*0.85)],
        labels=[(Point(width/2, height/2), "BACK POCKET × 2 (mirror)")],
    )

def build_yoke(m: Measurements) -> PatternPiece:
    # Approssimazione: yoke 1-1/2" + 5/8" SA × 2
    h = 1.5 * INCH + 0.625 * 2 * INCH
    w = m.waist_mm / 2
    return PatternPiece(
        name="yoke",
        outline=[Point(0,0), Point(w, 0), Point(w, h), Point(0, h*0.6)],
        labels=[(Point(w/2, h/2), "YOKE × 2 (mirror)")],
    )
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_draft_extras.py -v
```
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/draft_extras.py tests/test_draft_extras.py
git commit -m "feat(core): waistband, fly, pockets, yoke, belt loop pieces"
```

---

## Task 8: Pattern assembler

**Files:**
- Modify: `src/jeans_pattern/pattern.py` (aggiungi `build_full_pattern`)
- Test: `tests/test_pattern.py` (aggiungi test integrazione)

Aggrega tutti i pezzi in un `Pattern` unico, con flag `style: "basic"|"updated"`.

- [ ] **Step 1: Aggiungi test integrazione**

```python
# tests/test_pattern.py (append)
def test_build_full_pattern_basic(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="basic")
    names = {p.name for p in pat}
    assert {"front", "back", "waistband", "fly_buttonhole_side", "fly_button_stand",
            "pocket_bag", "pocket_facing", "back_pocket", "yoke", "belt_loop"}.issubset(names)

def test_build_full_pattern_updated(default_measurements):
    from jeans_pattern.pattern import build_full_pattern
    pat = build_full_pattern(default_measurements, style="updated")
    assert any(p.name == "front" for p in pat)
```

- [ ] **Step 2: Esegui (deve fallire)**

```bash
pytest tests/test_pattern.py -v -k full
```
Expected: FAIL

- [ ] **Step 3: Implementa `build_full_pattern`**

```python
# src/jeans_pattern/pattern.py (append)
from .draft_basic import build_basic_front, build_basic_back
from .draft_updated import build_updated_front, build_updated_back
from .draft_extras import (
    build_waistband, build_belt_loop, build_button_fly,
    build_front_pocket, build_back_pocket, build_yoke,
)

def build_full_pattern(m, style: str = "updated") -> "Pattern":
    if style == "basic":
        front_pts = build_basic_front(m)
        back_pts = build_basic_back(m)
    elif style == "updated":
        front_pts = build_updated_front(m)
        back_pts = build_updated_back(m)
    else:
        raise ValueError(f"unknown style {style!r}")

    front = PatternPiece(name="front", outline=front_pts.outline_polygon(),
                         labels=[(front_pts.K, "FRONT × 2 (mirror)")])
    back = PatternPiece(name="back", outline=back_pts.outline_polygon(),
                        labels=[(back_pts.G, "BACK × 2 (mirror)")])

    fly = build_button_fly(m)
    pocket = build_front_pocket(m)

    return Pattern(pieces=[
        front, back,
        build_waistband(m),
        fly["buttonhole_side"], fly["button_stand"],
        pocket["pocket_bag"], pocket["pocket_facing"],
        build_back_pocket(m),
        build_yoke(m),
        build_belt_loop(),
    ])
```

- [ ] **Step 4: Esegui tutti i test core**

```bash
pytest tests/ -v --ignore=tests/test_export_pdf.py --ignore=tests/test_export_svg.py
```
Expected: tutti PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/pattern.py tests/test_pattern.py
git commit -m "feat(core): build_full_pattern assembler"
```

---

## Task 9: SVG export (preview)

**Files:**
- Create: `src/jeans_pattern/export_svg.py`
- Test: `tests/test_export_svg.py`

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_export_svg.py
from jeans_pattern.export_svg import pattern_to_svg
from jeans_pattern.pattern import build_full_pattern

def test_svg_is_valid_xml(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    svg = pattern_to_svg(pat)
    assert svg.startswith(b"<?xml") or svg.startswith(b"<svg")
    assert b"</svg>" in svg

def test_svg_contains_all_pieces(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    svg = pattern_to_svg(pat).decode()
    for piece in pat:
        assert piece.name in svg, f"piece {piece.name} not labelled in svg"
```

- [ ] **Step 2: Esegui (deve fallire)**

```bash
pytest tests/test_export_svg.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementa `export_svg.py`**

```python
# src/jeans_pattern/export_svg.py
import svgwrite
from .pattern import Pattern

MM_PER_USER_UNIT = 1.0   # 1 user unit = 1 mm

def pattern_to_svg(pattern: Pattern, gap_mm: float = 30.0) -> bytes:
    """Layout: pezzi affiancati orizzontalmente sull'asse x, separati da gap_mm."""
    # Calcola layout
    placed = []
    cursor_x = 0.0
    max_y = 0.0
    for piece in pattern:
        x0, y0, x1, y1 = piece.bbox()
        w = x1 - x0
        h = y1 - y0
        offset_x = cursor_x - x0
        offset_y = -y0
        placed.append((piece, offset_x, offset_y))
        cursor_x += w + gap_mm
        max_y = max(max_y, h)

    total_w = cursor_x
    total_h = max_y + 50

    dwg = svgwrite.Drawing(size=(f"{total_w}mm", f"{total_h}mm"),
                           viewBox=f"0 0 {total_w} {total_h}")
    for piece, ox, oy in placed:
        pts = [(p.x + ox, p.y + oy) for p in piece.outline]
        dwg.add(dwg.polygon(points=pts, fill="none", stroke="black", stroke_width=0.3))
        for line in piece.construction_lines:
            d_pts = [(p.x + ox, p.y + oy) for p in line]
            dwg.add(dwg.polyline(points=d_pts, fill="none",
                                 stroke="green", stroke_dasharray="2,2", stroke_width=0.2))
        for pt, text in piece.labels:
            dwg.add(dwg.text(text, insert=(pt.x + ox, pt.y + oy), font_size="6"))
        # nome del pezzo in alto
        x0, y0, x1, _ = piece.bbox()
        dwg.add(dwg.text(piece.name, insert=(x0 + ox, y0 + oy - 5), font_size="8", fill="blue"))
    return dwg.tostring().encode("utf-8")
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_export_svg.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_pattern/export_svg.py tests/test_export_svg.py
git commit -m "feat(export): SVG export with auto layout"
```

---

## Task 10: PDF export (1:1 + calibration square + tile A4)

**Files:**
- Create: `src/jeans_pattern/export_pdf.py`
- Test: `tests/test_export_pdf.py`

Modi supportati:
- `mode="single"`: una pagina grande (= bbox totale + margini), per stampanti plotter o pattern projector software che importa singola pagina
- `mode="tiled_a4"`: divide il cartamodello in tile A4 (210×297 mm) con marcatori di allineamento

Calibration square: rettangolo nero 10×10 cm in alto a sinistra della prima pagina con label "10cm × 10cm — verifica scala" — serve all'utente per calibrare il pattern projector.

- [ ] **Step 1: Scrivi i test**

```python
# tests/test_export_pdf.py
import io
from jeans_pattern.export_pdf import pattern_to_pdf
from jeans_pattern.pattern import build_full_pattern

def test_pdf_single_page_returns_bytes(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    pdf = pattern_to_pdf(pat, mode="single")
    assert pdf[:4] == b"%PDF"

def test_pdf_tiled_returns_bytes(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    pdf = pattern_to_pdf(pat, mode="tiled_a4")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000

def test_pdf_calibration_square_optional(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    a = pattern_to_pdf(pat, mode="single", calibration=True)
    b = pattern_to_pdf(pat, mode="single", calibration=False)
    assert a != b
```

- [ ] **Step 2: Esegui (deve fallire)**

```bash
pytest tests/test_export_pdf.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementa `export_pdf.py`**

```python
# src/jeans_pattern/export_pdf.py
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from .pattern import Pattern

A4_W_MM = 210
A4_H_MM = 297
MARGIN_MM = 10

def _draw_pieces(c: canvas.Canvas, pattern: Pattern, offset_x_mm: float, offset_y_mm: float):
    """Disegna tutti i pezzi del pattern in mm con offset specificato."""
    cursor_x = offset_x_mm
    gap = 30.0
    for piece in pattern:
        x0, y0, x1, y1 = piece.bbox()
        w = x1 - x0
        h = y1 - y0
        # outline
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.3 * mm)
        path = c.beginPath()
        first = True
        for p in piece.outline:
            x_mm = (p.x - x0 + cursor_x)
            y_mm = (p.y - y0 + offset_y_mm)
            if first:
                path.moveTo(x_mm * mm, y_mm * mm)
                first = False
            else:
                path.lineTo(x_mm * mm, y_mm * mm)
        path.close()
        c.drawPath(path, stroke=1, fill=0)
        # label
        c.setFont("Helvetica", 8)
        c.drawString(cursor_x * mm, (offset_y_mm - 4) * mm, piece.name)
        cursor_x += w + gap

def _draw_calibration(c: canvas.Canvas, x_mm: float, y_mm: float):
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5 * mm)
    c.rect(x_mm * mm, y_mm * mm, 100 * mm, 100 * mm, stroke=1, fill=0)
    c.setFont("Helvetica", 9)
    c.drawString((x_mm + 5) * mm, (y_mm + 5) * mm, "10cm x 10cm calibration square")

def pattern_to_pdf(pattern: Pattern, mode: str = "single",
                   calibration: bool = True) -> bytes:
    buf = io.BytesIO()
    if mode == "single":
        # Calcola dimensioni totali
        gap = 30.0
        total_w = sum((p.bbox()[2] - p.bbox()[0]) for p in pattern) + gap * (len(pattern.pieces))
        total_h = max((p.bbox()[3] - p.bbox()[1]) for p in pattern) + 50
        if calibration:
            total_h += 110
        page_size = (total_w * mm, total_h * mm)
        c = canvas.Canvas(buf, pagesize=page_size)
        cal_offset = 0
        if calibration:
            _draw_calibration(c, MARGIN_MM, total_h - 110)
            cal_offset = 110
        _draw_pieces(c, pattern, MARGIN_MM, MARGIN_MM)
        c.showPage()
        c.save()
    elif mode == "tiled_a4":
        c = canvas.Canvas(buf, pagesize=A4)
        # Render full pattern in coordinate plane, then tile
        gap = 30.0
        total_w = sum((p.bbox()[2] - p.bbox()[0]) for p in pattern) + gap * (len(pattern.pieces))
        total_h = max((p.bbox()[3] - p.bbox()[1]) for p in pattern) + 50
        usable_w = A4_W_MM - 2 * MARGIN_MM
        usable_h = A4_H_MM - 2 * MARGIN_MM
        cols = int((total_w + usable_w - 1) // usable_w)
        rows = int((total_h + usable_h - 1) // usable_h)
        # Pagina 0: calibration
        if calibration:
            _draw_calibration(c, MARGIN_MM, A4_H_MM - 110 - MARGIN_MM)
            c.setFont("Helvetica", 10)
            c.drawString(MARGIN_MM * mm, MARGIN_MM * mm,
                         f"Pattern tiled {cols}x{rows}. Allineare i bordi con i marker +.")
            c.showPage()
        # Tile
        for row in range(rows):
            for col in range(cols):
                # offset negativo per spostare il pattern dentro la pagina
                ox = MARGIN_MM - col * usable_w
                oy = MARGIN_MM - row * usable_h
                _draw_pieces(c, pattern, ox, oy)
                # marker di allineamento agli angoli
                c.setStrokeColorRGB(0, 0, 0)
                c.setLineWidth(0.2 * mm)
                for cx, cy in [(MARGIN_MM, MARGIN_MM),
                               (A4_W_MM - MARGIN_MM, MARGIN_MM),
                               (MARGIN_MM, A4_H_MM - MARGIN_MM),
                               (A4_W_MM - MARGIN_MM, A4_H_MM - MARGIN_MM)]:
                    c.line((cx - 3) * mm, cy * mm, (cx + 3) * mm, cy * mm)
                    c.line(cx * mm, (cy - 3) * mm, cx * mm, (cy + 3) * mm)
                c.setFont("Helvetica", 7)
                c.drawString(MARGIN_MM * mm, (A4_H_MM - 5) * mm, f"r{row+1}c{col+1}")
                c.showPage()
        c.save()
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return buf.getvalue()
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_export_pdf.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Verifica visiva manuale**

```bash
python -c "from jeans_pattern.measurements import Measurements; from jeans_pattern.pattern import build_full_pattern; from jeans_pattern.export_pdf import pattern_to_pdf; m = Measurements.from_inches(waist=34.5, seat=44, rise=9.75, knee=10.375, bottom=9.75, length=34); pdf = pattern_to_pdf(build_full_pattern(m, 'updated'), mode='single'); open('test_single.pdf','wb').write(pdf); pdf2 = pattern_to_pdf(build_full_pattern(m, 'updated'), mode='tiled_a4'); open('test_tiled.pdf','wb').write(pdf2)"
```
Expected: due file `test_single.pdf` e `test_tiled.pdf` generati. Apri con un viewer PDF e verifica:
- Il calibration square misura esattamente 10×10 cm (riga vera o usando il righello del viewer)
- I pezzi del cartamodello hanno proporzioni plausibili
- Nel tiled: il pattern si distribuisce su più pagine A4 con marker di allineamento

- [ ] **Step 6: Commit**

```bash
git add src/jeans_pattern/export_pdf.py tests/test_export_pdf.py
git commit -m "feat(export): PDF export with single-page and tiled-A4 modes + calibration square"
```

---

## Task 11: UI – measurement form

**Files:**
- Create: `src/jeans_app/measurement_form.py`
- Test: `tests/test_measurement_form.py`

- [ ] **Step 1: Scrivi i test (pytest-qt)**

```python
# tests/test_measurement_form.py
import pytest
from PySide6 import QtCore
from jeans_app.measurement_form import MeasurementForm

@pytest.fixture
def form(qtbot):
    f = MeasurementForm()
    qtbot.addWidget(f)
    return f

def test_form_default_unit_is_cm(form):
    assert form.unit() == "cm"

def test_form_collects_measurements_in_cm(form, qtbot):
    form.set_value("waist", 87.63)
    form.set_value("seat", 111.76)
    form.set_value("rise", 24.765)
    form.set_value("knee", 26.35)
    form.set_value("bottom", 24.765)
    form.set_value("length", 86.36)
    m = form.to_measurements()
    assert m.waist_mm == pytest.approx(876.3)

def test_form_emits_changed_signal(form, qtbot):
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.set_value("waist", 90.0)

def test_form_unit_toggle(form):
    form.set_unit("inch")
    assert form.unit() == "inch"
```

- [ ] **Step 2: Esegui (deve fallire)**

```bash
pytest tests/test_measurement_form.py -v
```
Expected: FAIL

- [ ] **Step 3: Implementa `measurement_form.py`**

```python
# src/jeans_app/measurement_form.py
from PySide6 import QtWidgets, QtCore
from jeans_pattern.measurements import Measurements

FIELDS = [
    ("waist", "Waist (giro vita)"),
    ("seat", "Seat (giro fianchi)"),
    ("rise", "Rise (cavallo)"),
    ("knee", "Knee (giro ginocchio)"),
    ("bottom", "Bottom (giro fondo gamba)"),
    ("length", "Length (lunghezza interna)"),
]

DEFAULTS_CM = {
    "waist": 87.63, "seat": 111.76, "rise": 24.765,
    "knee": 26.35, "bottom": 24.765, "length": 86.36,
}

class MeasurementForm(QtWidgets.QWidget):
    measurements_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QFormLayout(self)
        self._unit = "cm"
        self._unit_combo = QtWidgets.QComboBox()
        self._unit_combo.addItems(["cm", "inch"])
        self._unit_combo.currentTextChanged.connect(self._on_unit_changed)
        layout.addRow("Unità", self._unit_combo)

        self._spinboxes = {}
        for key, label in FIELDS:
            sb = QtWidgets.QDoubleSpinBox()
            sb.setRange(0.1, 1000)
            sb.setDecimals(3)
            sb.setSingleStep(0.5)
            sb.setValue(DEFAULTS_CM[key])
            sb.valueChanged.connect(self._on_value_changed)
            self._spinboxes[key] = sb
            layout.addRow(label, sb)

        # Style
        self._style_combo = QtWidgets.QComboBox()
        self._style_combo.addItems(["updated (501)", "basic (vintage)"])
        layout.addRow("Stile draft", self._style_combo)

    def unit(self) -> str:
        return self._unit

    def set_unit(self, u: str):
        self._unit_combo.setCurrentText(u)

    def _on_unit_changed(self, new_unit: str):
        # Converti i valori nei spinbox
        if new_unit == self._unit:
            return
        factor = 1 / 2.54 if (self._unit == "cm" and new_unit == "inch") else 2.54
        for sb in self._spinboxes.values():
            sb.blockSignals(True)
            sb.setValue(sb.value() * factor)
            sb.blockSignals(False)
        self._unit = new_unit
        self._on_value_changed()

    def set_value(self, key: str, value: float):
        self._spinboxes[key].setValue(value)

    def _on_value_changed(self, *_):
        self.measurements_changed.emit()

    def to_measurements(self) -> Measurements:
        vals = {k: sb.value() for k, sb in self._spinboxes.items()}
        if self._unit == "cm":
            return Measurements.from_cm(**vals)
        return Measurements.from_inches(**vals)

    def style(self) -> str:
        return "updated" if "updated" in self._style_combo.currentText() else "basic"
```

- [ ] **Step 4: Esegui i test**

```bash
pytest tests/test_measurement_form.py -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add src/jeans_app/measurement_form.py tests/test_measurement_form.py
git commit -m "feat(ui): measurement input form with unit toggle and live signal"
```

---

## Task 12: UI – preview widget

**Files:**
- Create: `src/jeans_app/preview_widget.py`

- [ ] **Step 1: Implementa preview**

```python
# src/jeans_app/preview_widget.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QByteArray

class PreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self._svg = QSvgWidget()
        self._svg.setMinimumSize(400, 600)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self._svg)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

    def update_svg(self, svg_bytes: bytes):
        self._svg.load(QByteArray(svg_bytes))
        # Adatta size al contenuto naturale del SVG
        size = self._svg.sizeHint()
        self._svg.setFixedSize(size)
```

- [ ] **Step 2: Smoke test manuale**

```bash
python -c "from PySide6.QtWidgets import QApplication; from jeans_app.preview_widget import PreviewWidget; app = QApplication([]); w = PreviewWidget(); w.show()"
```
(Premi Ctrl+C per chiudere)

- [ ] **Step 3: Commit**

```bash
git add src/jeans_app/preview_widget.py
git commit -m "feat(ui): SVG preview widget with scroll area"
```

---

## Task 13: UI – main window e wiring

**Files:**
- Create: `src/jeans_app/main_window.py`
- Create: `src/jeans_app/main.py`

- [ ] **Step 1: Implementa `main_window.py`**

```python
# src/jeans_app/main_window.py
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QFileDialog, QMessageBox
from .measurement_form import MeasurementForm
from .preview_widget import PreviewWidget
from jeans_pattern.pattern import build_full_pattern
from jeans_pattern.export_svg import pattern_to_svg
from jeans_pattern.export_pdf import pattern_to_pdf

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selvedge Jeans Pattern Maker")
        self.resize(1200, 800)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)

        # Left: form + buttons
        left = QtWidgets.QVBoxLayout()
        self.form = MeasurementForm()
        left.addWidget(self.form)
        btn_pdf_single = QtWidgets.QPushButton("Esporta PDF (singola pagina)")
        btn_pdf_tiled = QtWidgets.QPushButton("Esporta PDF (tiled A4)")
        btn_svg = QtWidgets.QPushButton("Esporta SVG")
        left.addWidget(btn_pdf_single)
        left.addWidget(btn_pdf_tiled)
        left.addWidget(btn_svg)
        left.addStretch()
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left)
        left_widget.setMaximumWidth(400)
        h.addWidget(left_widget)

        # Right: preview
        self.preview = PreviewWidget()
        h.addWidget(self.preview, 1)

        # Wiring
        self.form.measurements_changed.connect(self._refresh_preview)
        btn_pdf_single.clicked.connect(lambda: self._export_pdf("single"))
        btn_pdf_tiled.clicked.connect(lambda: self._export_pdf("tiled_a4"))
        btn_svg.clicked.connect(self._export_svg)

        # Initial preview
        QtCore.QTimer.singleShot(100, self._refresh_preview)

    def _build_pattern(self):
        m = self.form.to_measurements()
        return build_full_pattern(m, style=self.form.style())

    def _refresh_preview(self):
        try:
            pat = self._build_pattern()
            svg = pattern_to_svg(pat)
            self.preview.update_svg(svg)
        except Exception as e:
            QMessageBox.warning(self, "Errore preview", str(e))

    def _export_pdf(self, mode: str):
        path, _ = QFileDialog.getSaveFileName(self, "Salva PDF", "jeans_pattern.pdf",
                                              "PDF (*.pdf)")
        if not path:
            return
        try:
            pdf = pattern_to_pdf(self._build_pattern(), mode=mode, calibration=True)
            with open(path, "wb") as f:
                f.write(pdf)
            QMessageBox.information(self, "Esportato", f"Salvato in:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore export", str(e))

    def _export_svg(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva SVG", "jeans_pattern.svg",
                                              "SVG (*.svg)")
        if not path:
            return
        try:
            svg = pattern_to_svg(self._build_pattern())
            with open(path, "wb") as f:
                f.write(svg)
            QMessageBox.information(self, "Esportato", f"Salvato in:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore export", str(e))
```

- [ ] **Step 2: Implementa `main.py`**

```python
# src/jeans_app/main.py
import sys
from PySide6 import QtWidgets
from .main_window import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Smoke test manuale**

```bash
python -m jeans_app.main
```
Expected: si apre la finestra. Modifica una misura → preview si aggiorna. Click "Esporta PDF singola pagina" → file salvato. Apri il PDF e verifica calibration square 10×10 cm con righello.

- [ ] **Step 4: Commit**

```bash
git add src/jeans_app/main_window.py src/jeans_app/main.py
git commit -m "feat(ui): main window wiring form ↔ preview ↔ export"
```

---

## Task 14: Verifica end-to-end con misure reali

**Files:** nessuno (test manuale)

- [ ] **Step 1: Genera con misure default Excel**

```bash
python -c "from jeans_pattern.measurements import Measurements; from jeans_pattern.pattern import build_full_pattern; from jeans_pattern.export_pdf import pattern_to_pdf; m = Measurements.from_inches(waist=34.5, seat=44, rise=9.75, knee=10.375, bottom=9.75, length=34); pdf = pattern_to_pdf(build_full_pattern(m, 'updated'), mode='tiled_a4'); open('e2e_default.pdf','wb').write(pdf)"
```

- [ ] **Step 2: Verifica numerica vs Excel**

Apri Excel `docs/source-spec/SelvedgeJeansCalculatorMaster.xlsx` (con `data_only=True`) e confronta i valori derivati con un dump Python:

```python
python -c "
from jeans_pattern.measurements import Measurements
from jeans_pattern.draft_basic import build_basic_front, build_basic_back
m = Measurements.from_inches(waist=34.5, seat=44, rise=9.75, knee=10.375, bottom=9.75, length=34)
f = build_basic_front(m); b = build_basic_back(m)
# Output in inch per confronto diretto con Excel
print('A-E', (f.E.y - f.A.y)/25.4)
print('A-B', (f.B.y - f.A.y)/25.4)
print('B-C', (f.C.y - f.B.y)/25.4)
print('C-E', (f.E.y - f.C.y)/25.4)
print('B-D', (f.D.y - f.B.y)/25.4)
print('B-F', f.F.x/25.4)
print('F-G', (f.G.x - f.F.x)/25.4)
print('I-H', (f.H.x - f.I.x)/25.4)
print('G-K', (f.K.x - f.G.x)/25.4)
print('N-M', (f.M.x - f.N.x)/25.4)
print('N-L', (f.N.x - f.L.x)/25.4)
print('finished waist', ((f.H.x - f.I.x) + (b.Z.x - b.I.x) - 1.75*25.4)/25.4)
"
```
Confronta con valori Excel attesi (calcolati a mano dalle formule):
- A-E ≈ 45.25, A-B ≈ 9.75, B-C ≈ 34.5, C-E ≈ 1.0, B-D ≈ 15.25, B-F ≈ 11.0, F-G ≈ 2.0, I-H ≈ 9.125, G-K ≈ 6.5 (= 13/2), N-M ≈ 4.875, N-L ≈ 4.875, finished waist ≈ 18.25

- [ ] **Step 3: Stampa di verifica**

Stampa il PDF tiled, attacca i fogli seguendo i marker di allineamento, misura il calibration square con righello → deve essere 10×10 cm. Misura il giro vita del waistband → deve corrispondere alla misura inserita + 1-3/8" + 3/8" SA × 2.

- [ ] **Step 4: Test pattern projector** (richiede setup hardware utente)

Apri il PDF singola pagina nel software del pattern projector. Calibra usando il calibration square. Proietta su un foglio di carta da pacco e misura le sagome con metro flessibile.

- [ ] **Step 5: Commit eventuali fix**

```bash
git commit -am "fix: ..."
```

---

## Task 15: Packaging Windows + macOS

**Files:**
- Create: `packaging/pyinstaller_win.spec`
- Create: `packaging/pyinstaller_mac.spec`

- [ ] **Step 1: Crea spec Windows**

```python
# packaging/pyinstaller_win.spec
from PyInstaller.utils.hooks import collect_submodules
block_cipher = None
hiddenimports = collect_submodules("PySide6") + collect_submodules("reportlab")

a = Analysis(['../src/jeans_app/main.py'],
             pathex=['../src'],
             binaries=[], datas=[],
             hiddenimports=hiddenimports,
             hookspath=[], runtime_hooks=[],
             excludes=[], win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='SelvedgeJeansPattern', console=False, icon=None)
```

- [ ] **Step 2: Crea spec macOS** (analoga, bundle .app)

```python
# packaging/pyinstaller_mac.spec
# (struttura simile, con BUNDLE() finale)
from PyInstaller.utils.hooks import collect_submodules
block_cipher = None
hiddenimports = collect_submodules("PySide6") + collect_submodules("reportlab")

a = Analysis(['../src/jeans_app/main.py'], pathex=['../src'],
             hiddenimports=hiddenimports, cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='SelvedgeJeansPattern', console=False)
app = BUNDLE(exe, name='SelvedgeJeansPattern.app',
             icon=None, bundle_identifier='io.tumini.jeans')
```

- [ ] **Step 3: Build Windows**

```bash
pyinstaller packaging/pyinstaller_win.spec --noconfirm
# output: dist/SelvedgeJeansPattern.exe
```

- [ ] **Step 4: Build macOS** (su macchina Mac)

```bash
pyinstaller packaging/pyinstaller_mac.spec --noconfirm
# output: dist/SelvedgeJeansPattern.app
```

- [ ] **Step 5: Commit**

```bash
git add packaging/
git commit -m "build: PyInstaller specs for Windows and macOS"
```

---

## Verification

End-to-end check completo:

1. **Test suite**: `pytest tests/ -v` → tutti PASS
2. **Avvio app**: `python -m jeans_app.main` → finestra si apre, form preimpostata coi default Excel
3. **Cambio unità**: toggle cm↔inch → valori convertiti correttamente
4. **Cambio stile**: dropdown "updated"↔"basic" → preview si aggiorna
5. **Live preview**: digita una misura → SVG ricalcolato in <1s
6. **Export PDF singola pagina**: salva, apri, misura calibration square 10×10 cm con righello fisico → corretto
7. **Export PDF tiled A4**: salva, stampa, attacca fogli ai marker, verifica continuità del cartamodello
8. **Verifica numerica**: confronta valori con Excel calculator, scarto <0.1mm
9. **Pattern projector**: importa PDF singola pagina, calibra col 10×10cm, proietta — le sagome devono essere identificabili
10. **Build cross-platform**: PyInstaller produce eseguibile Windows e bundle macOS, entrambi avviabili

**Open issues / TODO post-MVP** (non bloccanti, da gestire in plan futuri):
- Curve di Bézier per fly/hip/seat (attualmente outline poligonali; il PDF mostra curve smooth)
- Indicatori grainline e notches (taglio/cuciture)
- Export DXF per CNC/cutter automatici
- Salvataggio/caricamento profili misure (JSON)
- Internazionalizzazione (IT/EN)
- Ottimizzazione layout pezzi su pagina (nesting algorithm)

---
