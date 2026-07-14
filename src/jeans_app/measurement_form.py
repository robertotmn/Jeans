"""Measurement input form for the M. Mueller & Sohn jeans draft.

Six body measurements (chart page 2), entered in cm or inch. Values are
converted in place when the unit changes.
"""
from PySide6 import QtWidgets, QtCore

from jeans_pattern.measurements import Measurements

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

CM_PER_INCH = 2.54


class MeasurementForm(QtWidgets.QWidget):
    """Form widget. Emits `measurements_changed` whenever any input changes."""

    measurements_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "cm"

        layout = QtWidgets.QFormLayout(self)

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

    # ----- Public API ----------------------------------------------------

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

    # ----- Internal handlers ---------------------------------------------

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
