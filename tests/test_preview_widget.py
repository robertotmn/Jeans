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
