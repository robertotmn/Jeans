# Selvedge Jeans Pattern App

Desktop application (Windows + macOS) that generates a custom selvedge denim jeans pattern from body measurements and exports it to PDF/SVG at 1:1 scale for use with a pattern projector.

## Status

Under development. See `docs/superpowers/plans/2026-05-03-jeans-pattern-app.md` for the full implementation plan.

## Sources

The drafting rules are based on:
- `docs/source-spec/drafting_selvedge_jeans.pdf` — instructions by J.E. Landis (2024)
- `docs/source-spec/SelvedgeJeansCalculatorMaster.xlsx` — formula calculator

## Development

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows bash; on macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m jeans_app.main          # GUI
```

## Packaging

PyInstaller specs are provided in `packaging/`. Build natively on each target:

```bash
# On Windows:
pyinstaller packaging/pyinstaller_win.spec --noconfirm
# Output: dist/SelvedgeJeansPattern.exe

# On macOS:
pyinstaller packaging/pyinstaller_mac.spec --noconfirm
# Output: dist/SelvedgeJeansPattern.app
```

## Pattern Projector Workflow

To use the generated cartamodello with a pattern projector:

1. Click **Esporta PDF (singola pagina)** — produces a single large PDF (~3.5m x 1.6m for default measurements) at 1:1 scale with a 10x10 cm calibration square in the top-left corner.
2. Open the PDF in your projector software (Pattern Projector web app, Sherline Patternizer, etc.).
3. Calibrate using the 10x10 cm square: project it onto fabric and measure with a ruler. The measured square must be exactly 10x10 cm.
4. Once calibrated, project the pieces onto your fabric and trace each outline.

**Note:** Do NOT print the single-page PDF on standard letter/A4 paper — most viewers (Adobe Acrobat, Apple Preview) will silently scale it to fit the page, breaking the 1:1 calibration. Either:
- Use the **tiled A4** export to print across multiple A4 sheets and assemble (corner alignment markers are provided), OR
- Send the single-page PDF to a plotter/large-format printer that respects native dimensions, OR
- Use the single-page PDF with a calibrated pattern projector (verify the 10x10 cm square first).

## Limitations (MVP scope)

This is an MVP. Some refinements from the J.E. Landis drafting PDF are intentionally deferred:

- **Curves rendered as straight chords**: the fly curve I-AA-G, the hip curve B-H, and the back seat curve S-Z are currently drawn as straight line segments. The control points are tracked internally (e.g. AA, the fly curve waypoint at seat/16 below F) so a future version can sample smooth Bezier paths.
- **Hem is horizontal, not perpendicular to outseam**: the updated 501 draft prescribes a hem perpendicular to the (now-slanted) outseam; current output uses the basic horizontal hem.
- **Thigh is not hollowed**: the updated draft hollows the front thigh by 3/4" and the back thigh by 1" for a tapered fit. Currently the thigh edge is straight from G/S to P/T.
- **Pocket placement is approximate**: front pocket bag, pocket facing, and back pocket are emitted as standalone rectangles. Precise placement on the front/back pieces (per PDF pages 17-18) is the user's responsibility when sewing.
- **No notches or grainline indicators**: the cut outlines are clean polygons without sewing notches or fabric-grain marks. Add these manually on the printed pattern.
- **All seam allowances are included** in the cut outlines (3/8" everywhere except 5/8" on yoke and center back seat seam — per PDF page 4).
- **Outseam length tolerance front-vs-back ~6 mm (~1/4")**: Landis's basic draft (PDF pp. 10-13 step 3) prescribes the back outseam as a single straight line through W-U-R-Y, while the front outseam has the 2" hip extension at G plus the I→G fly curve. This produces an inherent ~6 mm front-longer-than-back mismatch that falls within standard ~1/4" sewing ease — eased in during outseam construction. Not a bug in the implementation: it reflects the source draft.

For now this means a competent sewist may need to fair the curves by eye on the printed pattern. None of these limitations prevent the cartamodello from being usable for cutting and sewing a wearable pair of jeans.
