import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_preview_widget_instantiates(qtbot):
    from jeans_app.preview_widget import PreviewWidget
    w = PreviewWidget()
    qtbot.addWidget(w)
    assert w is not None


def test_preview_widget_loads_svg(qtbot, mini_pattern):
    """update_svg accepts SVG bytes without error."""
    from jeans_app.preview_widget import PreviewWidget
    from jeans_pattern.export_svg import pattern_to_svg

    w = PreviewWidget()
    qtbot.addWidget(w)
    w.update_svg(pattern_to_svg(mini_pattern))


def test_preview_widget_loads_jacket_svg(qtbot, size50_jacket):
    """The real Design 4041 pattern (17 pieces laid out over ~4 m) renders and
    sizes the canvas to the sheet: far wider than it is tall."""
    from jeans_app.preview_widget import PreviewWidget
    from jeans_pattern.export_svg import pattern_to_svg
    from jeans_pattern.pattern import build_jacket_pattern

    w = PreviewWidget()
    qtbot.addWidget(w)
    w.update_svg(pattern_to_svg(build_jacket_pattern(size50_jacket)))
    assert w._svg.renderer().isValid()
    assert w._svg.width() > 4 * w._svg.height() > 0


def test_preview_widget_loads_jacket_svg_without_allowances(qtbot, size50_jacket):
    """Net lines only (no cut outline) still make a valid drawing."""
    from jeans_app.preview_widget import PreviewWidget
    from jeans_pattern.export_svg import pattern_to_svg
    from jeans_pattern.pattern import SeamAllowances, build_jacket_pattern

    net_only = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=0, hem_mm=0))
    assert all(p.cut_outline is None for p in net_only)
    w = PreviewWidget()
    qtbot.addWidget(w)
    w.update_svg(pattern_to_svg(net_only))
    assert w._svg.renderer().isValid()
