"""Measurement input form for the M. Mueller & Sohn drafts.

Six body measurements for the jeans (chart page 2) or five for the denim jacket
(chart page 12), plus the two seam-allowance values, entered in cm or inch.
Values are converted in place when the unit changes; the rows that do not
belong to the selected model are hidden.
"""
from PySide6 import QtWidgets, QtCore

from jeans_pattern.measurements import Measurements
from jeans_pattern.measurements_jacket import JacketMeasurements
from jeans_pattern.pattern import SeamAllowances

MODEL_JEANS = "Basic Jeans"
MODEL_JACKET = "Classic Denim Jacket"

FIELDS = [
    ("waistband", "Waistband W (giro vita)"),
    ("hip_girth", "Hip girth Hg (giro fianchi)"),
    ("knee_girth", "Knee girth Kg (giro ginocchio)"),
    ("hem_width", "Hem width Hw (giro fondo gamba)"),
    ("outseam", "Outseam Os (lunghezza esterna)"),
    ("inseam", "Inseam Is (lunghezza interna)"),
]

DEFAULTS_CM = {
    "waistband": 90.0, "hip_girth": 102.0, "knee_girth": 43.0, "hem_width": 38.0,
    "outseam": 102.0, "inseam": 82.0,
}

JACKET_FIELDS = [
    ("body_height", "Body height Bh (statura)"),
    ("chest_girth", "Chest girth Cg (giro petto)"),
    ("sleeve_length", "Sleeve length Sl (lunghezza manica)"),
]

JACKET_DEFAULTS_CM = {"body_height": 179.0, "chest_girth": 100.0, "sleeve_length": 64.0}

# waistband (= Wg) and hip_girth (= Hg) are shared, the rest belongs to one model
JEANS_ONLY_KEYS = ["knee_girth", "hem_width", "outseam", "inseam"]
JACKET_ONLY_KEYS = [key for key, _label in JACKET_FIELDS]

SA_FIELDS = [
    ("sa_seam", "Margine cuciture"),
    ("sa_hem", "Margine orlo"),
]

SA_DEFAULTS_CM = {"sa_seam": 1.5, "sa_hem": 3.0}

CM_PER_INCH = 2.54


class MeasurementForm(QtWidgets.QWidget):
    """Form widget. Emits `measurements_changed` whenever any input changes."""

    measurements_changed = QtCore.Signal()
    model_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "cm"
        self._model = MODEL_JEANS

        layout = self._layout = QtWidgets.QFormLayout(self)

        self._model_combo = QtWidgets.QComboBox()
        self._model_combo.addItems([MODEL_JEANS, MODEL_JACKET])
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addRow("Modello", self._model_combo)

        self._unit_combo = QtWidgets.QComboBox()
        self._unit_combo.addItems(["cm", "inch"])
        self._unit_combo.currentTextChanged.connect(self._on_unit_changed)
        layout.addRow("Unita di misura", self._unit_combo)

        self._spinboxes: dict[str, QtWidgets.QDoubleSpinBox] = {}
        for key, label in FIELDS:
            sb = QtWidgets.QDoubleSpinBox()
            sb.setRange(0.1, 1000.0)
            sb.setDecimals(3)
            sb.setSingleStep(0.5)
            sb.setValue(DEFAULTS_CM[key])
            sb.valueChanged.connect(self._on_value_changed)
            self._spinboxes[key] = sb
            layout.addRow(label, sb)

        for key, label in JACKET_FIELDS:
            sb = QtWidgets.QDoubleSpinBox()
            sb.setRange(0.1, 1000.0)
            sb.setDecimals(3)
            sb.setSingleStep(0.5)
            sb.setValue(JACKET_DEFAULTS_CM[key])
            sb.valueChanged.connect(self._on_value_changed)
            self._spinboxes[key] = sb
            layout.addRow(label, sb)

        # Seam allowances (0 = net pattern only); converted with the unit too
        for key, label in SA_FIELDS:
            sb = QtWidgets.QDoubleSpinBox()
            sb.setRange(0.0, 100.0)
            sb.setDecimals(3)
            sb.setSingleStep(0.5)
            sb.setValue(SA_DEFAULTS_CM[key])
            sb.valueChanged.connect(self._on_value_changed)
            self._spinboxes[key] = sb
            layout.addRow(label, sb)

        btn_reset = QtWidgets.QPushButton("Ripristina misure predefinite (taglia 50)")
        btn_reset.clicked.connect(self.reset_to_defaults)
        layout.addRow(btn_reset)

        self._apply_model_visibility()

    # ----- Public API ----------------------------------------------------

    def model(self) -> str:
        return self._model

    def set_model(self, name: str) -> None:
        if name not in (MODEL_JEANS, MODEL_JACKET):
            raise ValueError(f"unknown model {name!r}")
        self._model_combo.setCurrentText(name)

    def unit(self) -> str:
        return self._unit

    def set_unit(self, new_unit: str) -> None:
        """Switch unit and convert all current spinbox values to the new unit."""
        self._unit_combo.setCurrentText(new_unit)

    def set_value(self, key: str, value: float) -> None:
        if key not in self._spinboxes:
            raise KeyError(f"unknown measurement key {key!r}")
        self._spinboxes[key].setValue(value)

    def to_measurements(self) -> Measurements:
        vals = {key: self._spinboxes[key].value() for key, _label in FIELDS}
        if self._unit == "inch":
            return Measurements.from_inches(**vals)
        return Measurements.from_cm(**vals)

    def to_jacket_measurements(self) -> JacketMeasurements:
        vals = {key: self._spinboxes[key].value() for key, _label in JACKET_FIELDS}
        vals["waist_girth"] = self._spinboxes["waistband"].value()
        vals["hip_girth"] = self._spinboxes["hip_girth"].value()
        if self._unit == "inch":
            return JacketMeasurements.from_inches(**vals)
        return JacketMeasurements.from_cm(**vals)

    def seam_allowances(self) -> SeamAllowances:
        factor = 25.4 if self._unit == "inch" else 10.0
        return SeamAllowances(
            seam_mm=self._spinboxes["sa_seam"].value() * factor,
            hem_mm=self._spinboxes["sa_hem"].value() * factor,
        )

    def reset_to_defaults(self) -> None:
        """Restore every field (measurements + allowances) to the defaults,
        expressed in the current unit. Emits measurements_changed once."""
        factor = 1 / CM_PER_INCH if self._unit == "inch" else 1.0
        defaults = {**DEFAULTS_CM, **JACKET_DEFAULTS_CM, **SA_DEFAULTS_CM}
        for key, sb in self._spinboxes.items():
            sb.blockSignals(True)
            sb.setValue(defaults[key] * factor)
            sb.blockSignals(False)
        self.measurements_changed.emit()

    # ----- Internal handlers ---------------------------------------------

    def _apply_model_visibility(self) -> None:
        jacket = self._model == MODEL_JACKET
        for key in JEANS_ONLY_KEYS:
            self._layout.setRowVisible(self._spinboxes[key], not jacket)
        for key in JACKET_ONLY_KEYS:
            self._layout.setRowVisible(self._spinboxes[key], jacket)

    def _on_model_changed(self, name: str) -> None:
        if name == self._model:
            return
        self._model = name
        self._apply_model_visibility()
        self.model_changed.emit(name)
        self.measurements_changed.emit()

    def _on_unit_changed(self, new_unit: str) -> None:
        if new_unit == self._unit:
            return
        factor = 1 / CM_PER_INCH if new_unit == "inch" else CM_PER_INCH
        for sb in self._spinboxes.values():
            sb.blockSignals(True)
            sb.setValue(sb.value() * factor)
            sb.blockSignals(False)
        self._unit = new_unit
        self.measurements_changed.emit()

    def _on_value_changed(self, *_) -> None:
        self.measurements_changed.emit()
