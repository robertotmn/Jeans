"""SVG preview widget. Displays the assembled pattern as a scrollable SVG image
with zoom in / zoom out / fit-width controls."""
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import QByteArray, Qt


class PreviewWidget(QtWidgets.QWidget):
    """Wraps a QSvgWidget inside a QScrollArea so very wide patterns
    (e.g. 3.5m of jeans pieces side-by-side) remain navigable.
    Zoom: pulsanti +/- e Ctrl+rotella mouse."""

    MIN_ZOOM = 0.05
    MAX_ZOOM = 10.0
    ZOOM_STEP = 1.25

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # ----- toolbar with zoom controls --------------------------------
        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setContentsMargins(4, 2, 4, 2)
        btn_zoom_out = QtWidgets.QPushButton("−")   # minus
        btn_zoom_in = QtWidgets.QPushButton("+")
        btn_fit = QtWidgets.QPushButton("Adatta larghezza")
        btn_reset = QtWidgets.QPushButton("100%")
        for b in (btn_zoom_out, btn_zoom_in):
            b.setFixedWidth(32)
        self._zoom_label = QtWidgets.QLabel("100%")
        self._zoom_label.setMinimumWidth(48)
        toolbar.addWidget(btn_zoom_out)
        toolbar.addWidget(btn_zoom_in)
        toolbar.addWidget(self._zoom_label)
        toolbar.addWidget(btn_reset)
        toolbar.addWidget(btn_fit)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # ----- svg + scroll area -----------------------------------------
        self._svg = QSvgWidget()
        self._svg.setMinimumSize(100, 100)

        self._scroll = QtWidgets.QScrollArea()
        self._scroll.setWidget(self._svg)
        self._scroll.setWidgetResizable(False)
        self._scroll.viewport().installEventFilter(self)
        layout.addWidget(self._scroll)

        # ----- state -----------------------------------------------------
        self._zoom = 1.0
        self._natural_size = QtCore.QSize(0, 0)

        # ----- wiring ----------------------------------------------------
        btn_zoom_in.clicked.connect(lambda: self._set_zoom(self._zoom * self.ZOOM_STEP))
        btn_zoom_out.clicked.connect(lambda: self._set_zoom(self._zoom / self.ZOOM_STEP))
        btn_reset.clicked.connect(lambda: self._set_zoom(1.0))
        btn_fit.clicked.connect(self._fit_width)

    # ----- public API -----------------------------------------------------
    def update_svg(self, svg_bytes: bytes) -> None:
        self._svg.load(QByteArray(svg_bytes))
        size = self._svg.renderer().defaultSize()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self._natural_size = size
            self._apply_zoom()

    # ----- zoom helpers ---------------------------------------------------
    def _set_zoom(self, z: float) -> None:
        z = max(self.MIN_ZOOM, min(self.MAX_ZOOM, z))
        self._zoom = z
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        if self._natural_size.width() <= 0:
            return
        w = int(self._natural_size.width() * self._zoom)
        h = int(self._natural_size.height() * self._zoom)
        self._svg.setFixedSize(w, h)
        self._zoom_label.setText(f"{int(self._zoom * 100)}%")

    def _fit_width(self) -> None:
        if self._natural_size.width() <= 0:
            return
        viewport_w = self._scroll.viewport().width() - 4
        if viewport_w <= 0:
            return
        self._set_zoom(viewport_w / self._natural_size.width())

    # ----- mouse wheel zoom (Ctrl+wheel) ----------------------------------
    def eventFilter(self, obj, event):
        if obj is self._scroll.viewport() and event.type() == QtCore.QEvent.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self._set_zoom(self._zoom * self.ZOOM_STEP)
                elif delta < 0:
                    self._set_zoom(self._zoom / self.ZOOM_STEP)
                return True
        return super().eventFilter(obj, event)
