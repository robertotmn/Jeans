"""Main application window: form on the left, preview on the right, export buttons."""
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QFileDialog, QMessageBox

from jeans_pattern.pattern import build_full_pattern, build_jacket_pattern
from jeans_pattern.export_svg import pattern_to_svg
from jeans_pattern.export_pdf import pattern_to_pdf

from .measurement_form import MODEL_JACKET, MeasurementForm
from .preview_widget import PreviewWidget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selvedge Jeans Pattern Maker")
        self.resize(1200, 800)

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)

        # ----- Left column: form + report + buttons ------------------------
        left = QtWidgets.QVBoxLayout()
        self.form = MeasurementForm()
        left.addWidget(self.form)

        self.info_label = QtWidgets.QLabel("")
        self.info_label.setWordWrap(True)
        left.addWidget(self.info_label)

        btn_pdf_single = QtWidgets.QPushButton("Esporta PDF (singola pagina)")
        btn_pdf_tiled = QtWidgets.QPushButton("Esporta PDF (tile A4)")
        btn_svg = QtWidgets.QPushButton("Esporta SVG")
        left.addWidget(btn_pdf_single)
        left.addWidget(btn_pdf_tiled)
        left.addWidget(btn_svg)
        left.addStretch()

        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left)
        left_widget.setMaximumWidth(400)
        h.addWidget(left_widget)

        # ----- Right column: SVG preview ----------------------------------
        self.preview = PreviewWidget()
        h.addWidget(self.preview, stretch=1)

        # ----- Wiring ----------------------------------------------------
        self.form.measurements_changed.connect(self._refresh_preview)
        btn_pdf_single.clicked.connect(lambda: self._export_pdf("single"))
        btn_pdf_tiled.clicked.connect(lambda: self._export_pdf("tiled_a4"))
        btn_svg.clicked.connect(self._export_svg)

        # Initial preview after the event loop starts
        QtCore.QTimer.singleShot(100, self._refresh_preview)

    # ----- Internal helpers ----------------------------------------------

    def _build_pattern(self):
        if self.form.model() == MODEL_JACKET:
            return build_jacket_pattern(
                self.form.to_jacket_measurements(), self.form.seam_allowances()
            )
        return build_full_pattern(self.form.to_measurements(), self.form.seam_allowances())

    def _export_name(self, ext: str) -> str:
        stem = "jacket_pattern" if self.form.model() == MODEL_JACKET else "jeans_pattern"
        return f"{stem}.{ext}"

    def _refresh_preview(self) -> None:
        try:
            pat = self._build_pattern()
            svg = pattern_to_svg(pat)
            self.preview.update_svg(svg)
            self._show_report(pat.report)
        except Exception as e:
            QMessageBox.warning(self, "Errore preview", str(e))

    def _show_report(self, r: dict) -> None:
        if r.get("model") == "jacket":
            text = (
                f"Prof. giro Sd: {r['scye_depth_mm'] / 10:.1f} cm  ·  "
                f"Lunghezza Lg: {r['length_mm'] / 10:.1f} cm\n"
                f"Agio petto: {r['chest_ease_mm'] / 10:.1f} cm  ·  "
                f"Check fianchi Hg: {r['hip_ease_mm'] / 10:.1f} cm\n"
                f"Giro manica Ac: {r['armhole_circ_mm'] / 10:.1f} cm  ·  "
                f"Agio testa: {r['sleeve_cap_ease_mm'] / 10:.1f} cm"
            )
        else:
            text = (
                f"Cavallo Br: {r['body_rise_mm'] / 10:.1f} cm  ·  "
                f"Alt. ginocchio Kl: {r['knee_length_mm'] / 10:.1f} cm\n"
                f"Agio fianchi: {r['hip_ease_mm'] / 10:.1f} cm  ·  "
                f"Resto vita dietro: {r['waist_rest_mm'] / 10:.1f} cm"
            )
        if r["warnings"]:
            text += "\n⚠ " + "\n⚠ ".join(r["warnings"])
            self.info_label.setStyleSheet("color: #b00;")
        else:
            self.info_label.setStyleSheet("")
        self.info_label.setText(text)

    def _export_pdf(self, mode: str) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva PDF", self._export_name("pdf"), "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            pdf = pattern_to_pdf(self._build_pattern(), mode=mode, calibration=True)
            with open(path, "wb") as f:
                f.write(pdf)
            QMessageBox.information(self, "Esportato", f"Salvato:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore export", str(e))

    def _export_svg(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva SVG", self._export_name("svg"), "SVG (*.svg)"
        )
        if not path:
            return
        try:
            svg = pattern_to_svg(self._build_pattern())
            with open(path, "wb") as f:
                f.write(svg)
            QMessageBox.information(self, "Esportato", f"Salvato:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore export", str(e))
