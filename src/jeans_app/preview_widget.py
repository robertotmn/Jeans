"""SVG preview widget. Displays the assembled pattern as a scrollable SVG image."""
from PySide6 import QtWidgets, QtCore
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QByteArray


class PreviewWidget(QtWidgets.QWidget):
    """Wraps a QSvgWidget inside a QScrollArea so very wide patterns
    (e.g. 3.5m of jeans pieces side-by-side) remain navigable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._svg = QSvgWidget()
        self._svg.setMinimumSize(400, 600)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self._svg)
        scroll.setWidgetResizable(False)   # let svg keep natural size; allow scrolling
        layout.addWidget(scroll)

    def update_svg(self, svg_bytes: bytes) -> None:
        self._svg.load(QByteArray(svg_bytes))
        # Resize widget to its natural SVG dimensions so the scroll area
        # exposes the full content.
        size = self._svg.renderer().defaultSize()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self._svg.setFixedSize(size)
