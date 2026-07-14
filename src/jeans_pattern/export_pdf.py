"""PDF export of an assembled Pattern at 1:1 scale.

Two modes:
- "single": one large page sized to fit the entire layout (for pattern projectors
  or plotters that handle arbitrary sheet sizes)
- "tiled_a4": pattern divided across multiple A4 pages with corner alignment
  markers; user prints, lines up the markers, and tapes the sheets together

Both modes optionally include a 10x10 cm calibration square in the header so
the user can verify the output is at correct scale before cutting fabric.
"""
import io

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4

from .pattern import Pattern, PatternPiece

A4_W_MM = 210.0
A4_H_MM = 297.0
MARGIN_MM = 10.0
GAP_MM = 30.0
CALIBRATION_SIZE_MM = 100.0


def _layout_pieces(pattern: Pattern):
    """Return (placed, total_w_mm, total_h_mm) where placed is a list of
    (piece, offset_x_mm, offset_y_mm)."""
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
        cursor_x += w + GAP_MM
        max_y = max(max_y, h)
    total_w = max(cursor_x, 50.0)
    total_h = max_y + 50.0   # extra for piece-name labels
    return placed, total_w, total_h


def _draw_polygon(c, pts, ox, oy, x_origin_mm, y_origin_mm):
    path = c.beginPath()
    first = True
    for p in pts:
        x = (p.x + ox + x_origin_mm) * mm
        y = (-(p.y + oy) + y_origin_mm) * mm    # flip y
        if first:
            path.moveTo(x, y)
            first = False
        else:
            path.lineTo(x, y)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def _draw_vector_piece(c, piece: PatternPiece, ox: float, oy: float, x_origin_mm: float, y_origin_mm: float) -> None:
    # cut line (solid, the one to trace/cut); net seam line dashed inside
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.3 * mm)
    if piece.cut_outline:
        _draw_polygon(c, piece.cut_outline, ox, oy, x_origin_mm, y_origin_mm)
        c.setDash(4, 2)
        c.setStrokeColorRGB(0.35, 0.35, 0.35)
        c.setLineWidth(0.2 * mm)
        _draw_polygon(c, piece.outline, ox, oy, x_origin_mm, y_origin_mm)
        c.setDash()
        c.setStrokeColorRGB(0, 0, 0)
    else:
        _draw_polygon(c, piece.outline, ox, oy, x_origin_mm, y_origin_mm)

    c.setDash(2, 2)
    c.setStrokeColorRGB(0, 0.5, 0)
    c.setLineWidth(0.2 * mm)
    for line in piece.construction_lines:
        for i in range(len(line) - 1):
            p1, p2 = line[i], line[i + 1]
            c.line(
                (p1.x + ox + x_origin_mm) * mm,
                (-(p1.y + oy) + y_origin_mm) * mm,
                (p2.x + ox + x_origin_mm) * mm,
                (-(p2.y + oy) + y_origin_mm) * mm,
            )
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)


def _draw_pieces(c, placed, x_origin_mm: float, y_origin_mm: float):
    """Draw all placed pieces onto the canvas, applying an additional
    (x_origin_mm, y_origin_mm) offset (for tile pagination or page margins).

    Note: ReportLab's coordinate origin is bottom-left of the page; our
    pattern coordinates are y-down. We flip y here at draw time."""
    for piece, ox, oy in placed:
        _draw_vector_piece(c, piece, ox, oy, x_origin_mm, y_origin_mm)

        # Piece-name label above the piece
        x0, y0, _, _ = piece.bbox()
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0, 0, 1)
        c.drawString(
            (x0 + ox + x_origin_mm) * mm,
            (-(y0 + oy) + y_origin_mm + 4) * mm,    # 4mm above the top of bbox
            piece.name,
        )
        c.setFillColorRGB(0, 0, 0)

        # Letter-style landmark labels (length <= 3): red dot + small text
        c.setFont("Helvetica", 6)
        for pt, text in piece.labels:
            if len(text) <= 3:
                px = (pt.x + ox + x_origin_mm) * mm
                py = (-(pt.y + oy) + y_origin_mm) * mm
                c.setFillColorRGB(1, 0, 0)
                c.circle(px, py, 0.8 * mm, stroke=0, fill=1)
                c.drawString(px + 1.5 * mm, py + 0.5 * mm, text)
                c.setFillColorRGB(0, 0, 0)
            else:
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", 8)
                c.drawString(
                    (pt.x + ox + x_origin_mm) * mm,
                    (-(pt.y + oy) + y_origin_mm) * mm,
                    text,
                )
                c.setFont("Helvetica", 6)


def _draw_calibration(c, x_mm: float, y_mm: float):
    """Draw a 100x100 mm calibration square with a label at (x_mm, y_mm)
    measured from bottom-left of the page (ReportLab convention)."""
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.5 * mm)
    c.rect(
        x_mm * mm,
        y_mm * mm,
        CALIBRATION_SIZE_MM * mm,
        CALIBRATION_SIZE_MM * mm,
        stroke=1,
        fill=0,
    )
    c.setFont("Helvetica", 9)
    c.drawString(
        (x_mm + 5) * mm,
        (y_mm + 5) * mm,
        f"{int(CALIBRATION_SIZE_MM/10)}cm x {int(CALIBRATION_SIZE_MM/10)}cm calibration square",
    )


def pattern_to_pdf(
    pattern: Pattern,
    mode: str = "single",
    calibration: bool = True,
) -> bytes:
    """Render a Pattern to PDF bytes at 1:1 scale.

    mode="single": one page sized to the layout bbox + margins, optionally
    prepended with a calibration square.

    mode="tiled_a4": one calibration page (if requested) followed by N pages
    of A4 each containing a tile of the layout. Corner alignment markers
    on every tile let the user line up adjacent sheets.
    """
    if mode not in {"single", "tiled_a4"}:
        raise ValueError(f"unknown mode {mode!r}; expected 'single' or 'tiled_a4'")

    placed, total_w, total_h = _layout_pieces(pattern)
    buf = io.BytesIO()

    if mode == "single":
        cal_band_h = (CALIBRATION_SIZE_MM + 20) if calibration else 0
        page_w = total_w + 2 * MARGIN_MM
        page_h = total_h + 2 * MARGIN_MM + cal_band_h
        c = canvas.Canvas(buf, pagesize=(page_w * mm, page_h * mm))

        if calibration:
            _draw_calibration(c, MARGIN_MM, page_h - MARGIN_MM - CALIBRATION_SIZE_MM)
            # Pieces below the calibration band, with a small gap
            piece_y_origin = page_h - MARGIN_MM - cal_band_h
            _draw_pieces(c, placed, MARGIN_MM, piece_y_origin)
        else:
            piece_y_origin = page_h - MARGIN_MM
            _draw_pieces(c, placed, MARGIN_MM, piece_y_origin)

        c.showPage()
        c.save()

    else:  # tiled_a4
        c = canvas.Canvas(buf, pagesize=A4)
        usable_w = A4_W_MM - 2 * MARGIN_MM
        usable_h = A4_H_MM - 2 * MARGIN_MM
        cols = max(1, int((total_w + usable_w - 1) // usable_w))
        rows = max(1, int((total_h + usable_h - 1) // usable_h))

        # First page: calibration + instructions
        if calibration:
            _draw_calibration(c, MARGIN_MM, A4_H_MM - MARGIN_MM - CALIBRATION_SIZE_MM)
            c.setFont("Helvetica", 10)
            c.drawString(
                MARGIN_MM * mm,
                MARGIN_MM * mm,
                f"Pattern tiled {cols}x{rows} A4 sheets. "
                f"Print at 100%, verify the 10x10cm square, then assemble using the corner markers.",
            )
            c.showPage()

        # Subsequent pages: one per tile
        for row in range(rows):
            for col in range(cols):
                # In ReportLab y grows up. Compute the tile's offset within the layout.
                # We want this tile to show the part of the layout starting at:
                #   layout_x_start = col * usable_w
                #   layout_y_start = row * usable_h   (in pattern y-down coords)
                # When drawing on the A4 page, place that tile with its top-left at
                # (MARGIN_MM, A4_H_MM - MARGIN_MM).

                # Use the same _draw_pieces machinery but with shifted origins.
                # x: pieces drawn at piece.x + ox + MARGIN_MM - col*usable_w
                #    so place x_origin_mm = MARGIN_MM - col * usable_w
                # y: page top is at A4_H_MM. Pieces drawn at -(piece.y + oy) + y_origin
                #    we want the layout's row*usable_h..((row+1)*usable_h) band visible.
                #    The pattern y starts at 0 at the top. On A4, top of usable region
                #    is at y=A4_H_MM-MARGIN_MM. So:
                #    y_origin_mm = (A4_H_MM - MARGIN_MM) + row * usable_h
                _draw_pieces(
                    c,
                    placed,
                    MARGIN_MM - col * usable_w,
                    (A4_H_MM - MARGIN_MM) + row * usable_h,
                )

                # Corner alignment markers (small + signs at each page corner)
                c.setStrokeColorRGB(0, 0, 0)
                c.setLineWidth(0.2 * mm)
                for cx, cy in [
                    (MARGIN_MM, MARGIN_MM),
                    (A4_W_MM - MARGIN_MM, MARGIN_MM),
                    (MARGIN_MM, A4_H_MM - MARGIN_MM),
                    (A4_W_MM - MARGIN_MM, A4_H_MM - MARGIN_MM),
                ]:
                    c.line((cx - 3) * mm, cy * mm, (cx + 3) * mm, cy * mm)
                    c.line(cx * mm, (cy - 3) * mm, cx * mm, (cy + 3) * mm)

                # Tile coordinates label
                c.setFont("Helvetica", 7)
                c.drawString(
                    MARGIN_MM * mm,
                    (A4_H_MM - 4) * mm,
                    f"Row {row + 1} / {rows}  Col {col + 1} / {cols}",
                )
                c.showPage()

        c.save()

    return buf.getvalue()
