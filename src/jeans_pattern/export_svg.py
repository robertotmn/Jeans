"""SVG export of an assembled Pattern. Output unit is mm (1 SVG user unit = 1 mm),
so the rendered SVG is at 1:1 scale when imported into a viewer that respects
declared dimensions."""
import svgwrite

from .pattern import Pattern


def pattern_to_svg(pattern: Pattern, gap_mm: float = 30.0) -> bytes:
    """Render a Pattern as SVG bytes.

    Layout: pieces are placed side-by-side along the x axis with a `gap_mm`
    spacing. Each piece keeps its native coordinates, translated to start at
    (cursor_x, 0). The bounding box of each piece is computed via PatternPiece.bbox().
    """
    TOP_MARGIN_MM = 60.0      # spazio sopra: nome pezzo + lettura bordi
    BOTTOM_MARGIN_MM = 60.0   # spazio sotto: lettura bordi inferiori
    SIDE_MARGIN_MM = 50.0     # spazio laterale ai due estremi del foglio

    # Compute placement: cursor_x advances by piece width + gap
    placed = []
    cursor_x = SIDE_MARGIN_MM
    max_y_used = 0.0

    for piece in pattern:
        x0, y0, x1, y1 = piece.bbox()
        offset_x = cursor_x - x0
        offset_y = -y0 + TOP_MARGIN_MM   # leave room above for piece-name labels
        placed.append((piece, offset_x, offset_y))
        cursor_x += (x1 - x0) + gap_mm
        max_y_used = max(max_y_used, y1 - y0)

    # rimuovi l'ultimo gap aggiunto e includi il margine laterale destro
    total_w = max(cursor_x - gap_mm + SIDE_MARGIN_MM, 100.0)
    total_h = TOP_MARGIN_MM + max_y_used + BOTTOM_MARGIN_MM

    dwg = svgwrite.Drawing(
        size=(f"{total_w}mm", f"{total_h}mm"),
        viewBox=f"0 0 {total_w} {total_h}",
    )

    for piece, ox, oy in placed:
        pts = [(p.x + ox, p.y + oy) for p in piece.outline]
        dwg.add(dwg.polygon(
            points=pts,
            fill="none",
            stroke="black",
            stroke_width=0.3,
        ))

        for line in piece.construction_lines:
            d_pts = [(p.x + ox, p.y + oy) for p in line]
            dwg.add(dwg.polyline(
                points=d_pts,
                fill="none",
                stroke="green",
                stroke_dasharray="2,2",
                stroke_width=0.2,
            ))

        # Labels (text annotations on the piece)
        for pt, text in piece.labels:
            x = pt.x + ox
            y = pt.y + oy
            # Short letter-style labels get a marker dot
            if len(text) <= 3:
                dwg.add(dwg.circle(center=(x, y), r=4.0, fill="red", stroke="none"))
                # Offset the text proportionally so it doesn't overlap the dot
                dwg.add(dwg.text(
                    text,
                    insert=(x + 8, y - 8),
                    font_size="24",
                    fill="red",
                ))
            else:
                # Long descriptive labels (e.g. "FRONT x 2 (mirror)") rendered as before
                dwg.add(dwg.text(
                    text,
                    insert=(x, y),
                    font_size="6",
                ))

        # Piece name as a label at the top of the bounding box
        x0, y0, x1, _y1 = piece.bbox()
        dwg.add(dwg.text(
            piece.name,
            insert=(x0 + ox, y0 + oy - 5),
            font_size="8",
            fill="blue",
        ))

    return dwg.tostring().encode("utf-8")
