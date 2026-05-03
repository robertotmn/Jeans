import os
import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_preview_widget_instantiates(qtbot):
    from jeans_app.preview_widget import PreviewWidget
    w = PreviewWidget()
    qtbot.addWidget(w)
    assert w is not None


def test_preview_widget_loads_svg(qtbot):
    """update_svg accepts SVG bytes without error."""
    from jeans_app.preview_widget import PreviewWidget
    from jeans_pattern.measurements import Measurements
    from jeans_pattern.pattern import build_full_pattern
    from jeans_pattern.export_svg import pattern_to_svg

    w = PreviewWidget()
    qtbot.addWidget(w)
    m = Measurements.from_inches(waist=34.5, seat=44, rise=9.75, knee=10.375, bottom=9.75, length=34)
    svg = pattern_to_svg(build_full_pattern(m, "updated"))
    w.update_svg(svg)
