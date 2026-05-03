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
