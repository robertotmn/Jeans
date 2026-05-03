"""Measurement input form (Qt). Reproduces the input section of the Excel
calculator: 6 numeric inputs (waist, seat, rise, knee, bottom, length) plus
a unit toggle (cm/inch) and a draft-style toggle (basic/updated 501)."""
from PySide6 import QtWidgets, QtCore

from jeans_pattern.measurements import Measurements

FIELDS = [
    ("waist", "Waist (giro vita)"),
    ("seat", "Seat (giro fianchi)"),
    ("rise", "Rise (cavallo)"),
    ("knee", "Knee (giro ginocchio)"),
    ("bottom", "Bottom (giro fondo gamba)"),
    ("length", "Length (lunghezza interna)"),
]

DEFAULTS_CM = {
    "waist": 87.63,
    "seat": 111.76,
    "rise": 24.765,
    "knee": 26.35,
    "bottom": 24.765,
    "length": 86.36,
}

CM_PER_INCH = 2.54


class MeasurementForm(QtWidgets.QWidget):
    """Form widget. Emits `measurements_changed` whenever any input changes."""

    measurements_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "cm"

        layout = QtWidgets.QFormLayout(self)

        # Unit toggle
        self._unit_combo = QtWidgets.QComboBox()
        self._unit_combo.addItems(["cm", "inch"])
        self._unit_combo.currentTextChanged.connect(self._on_unit_changed)
        layout.addRow("Unita di misura", self._unit_combo)

        # Numeric inputs
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

        # Draft style toggle
        self._style_combo = QtWidgets.QComboBox()
        self._style_combo.addItems(["updated (501)", "basic (vintage)"])
        self._style_combo.currentTextChanged.connect(self._on_value_changed)
        layout.addRow("Stile draft", self._style_combo)

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
        vals = {k: sb.value() for k, sb in self._spinboxes.items()}
        if self._unit == "cm":
            return Measurements.from_cm(**vals)
        return Measurements.from_inches(**vals)

    def style(self) -> str:
        """Returns 'basic' or 'updated'."""
        return "updated" if "updated" in self._style_combo.currentText() else "basic"

    def set_style(self, style: str) -> None:
        if style == "updated":
            self._style_combo.setCurrentText("updated (501)")
        elif style == "basic":
            self._style_combo.setCurrentText("basic (vintage)")
        else:
            raise ValueError(f"unknown style {style!r}")

    # ----- Internal handlers ---------------------------------------------

    def _on_unit_changed(self, new_unit: str) -> None:
        if new_unit == self._unit:
            return
        # Convert all spinbox values
        if self._unit == "cm" and new_unit == "inch":
            factor = 1 / CM_PER_INCH
        elif self._unit == "inch" and new_unit == "cm":
            factor = CM_PER_INCH
        else:
            factor = 1.0
        for sb in self._spinboxes.values():
            sb.blockSignals(True)
            sb.setValue(sb.value() * factor)
            sb.blockSignals(False)
        self._unit = new_unit
        self.measurements_changed.emit()

    def _on_value_changed(self, *_) -> None:
        self.measurements_changed.emit()
