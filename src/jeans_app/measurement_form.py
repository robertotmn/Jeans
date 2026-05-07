"""Measurement input form. Supports two drafting systems:
- Landis: 6 measurements (waist, seat, rise, knee, bottom, length) in cm or inch
- Mueller & Sohn: 6 measurements (waistband, hip_girth, knee_girth, hem_width,
  outseam, inseam) in cm only (M&S is metric-native; inch input is converted).
"""
from PySide6 import QtWidgets, QtCore

from jeans_pattern.measurements import Measurements
from jeans_pattern.draft_mueller import MuellerMeasurements

LANDIS_FIELDS = [
    ("waist", "Waist (giro vita)"),
    ("seat", "Seat (giro fianchi)"),
    ("rise", "Rise (cavallo)"),
    ("knee", "Knee (giro ginocchio)"),
    ("bottom", "Bottom (giro fondo gamba)"),
    ("length", "Length (lunghezza interna)"),
]

LANDIS_DEFAULTS_CM = {
    "waist": 87.63, "seat": 111.76, "rise": 24.765,
    "knee": 26.35, "bottom": 24.765, "length": 86.36,
}

MUELLER_FIELDS = [
    ("waistband", "Waistband W (giro vita)"),
    ("hip_girth", "Hip girth Hg (giro fianchi)"),
    ("knee_girth", "Knee girth Kg (giro ginocchio)"),
    ("hem_width", "Hem width Hw (giro fondo gamba)"),
    ("outseam", "Outseam Os (lunghezza esterna)"),
    ("inseam", "Inseam Is (lunghezza interna)"),
]

MUELLER_DEFAULTS_CM = {
    "waistband": 90.0, "hip_girth": 102.0, "knee_girth": 43.0, "hem_width": 38.0,
    "outseam": 102.0, "inseam": 82.0,
}

CM_PER_INCH = 2.54

# Backwards-compat aliases used by older tests
FIELDS = LANDIS_FIELDS
DEFAULTS_CM = LANDIS_DEFAULTS_CM


class MeasurementForm(QtWidgets.QWidget):
    """Form widget. Emits `measurements_changed` whenever any input changes."""

    measurements_changed = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unit = "cm"
        self._system = "landis"

        layout = QtWidgets.QFormLayout(self)

        # System toggle (drafting system)
        self._system_combo = QtWidgets.QComboBox()
        self._system_combo.addItems([
            "Landis (basic / 501)",
            "Mueller & Sohn 1 (formule)",
            "Mueller & Sohn 2 (template)",
            "Mueller & Sohn 3 (raster)",
        ])
        self._system_combo.currentTextChanged.connect(self._on_system_changed)
        layout.addRow("Sistema", self._system_combo)

        # Unit toggle
        self._unit_combo = QtWidgets.QComboBox()
        self._unit_combo.addItems(["cm", "inch"])
        self._unit_combo.currentTextChanged.connect(self._on_unit_changed)
        layout.addRow("Unita di misura", self._unit_combo)

        # Spinboxes for both systems - show/hide based on system
        self._spinboxes: dict[str, QtWidgets.QDoubleSpinBox] = {}
        self._field_rows: dict[str, tuple[QtWidgets.QLabel, QtWidgets.QDoubleSpinBox]] = {}

        # Build all spinboxes (Landis + Mueller union; keys are disjoint).
        all_fields = {**dict(LANDIS_FIELDS), **dict(MUELLER_FIELDS)}
        all_defaults = {**LANDIS_DEFAULTS_CM, **MUELLER_DEFAULTS_CM}
        for key, label in all_fields.items():
            sb = QtWidgets.QDoubleSpinBox()
            sb.setRange(0.1, 1000.0)
            sb.setDecimals(3)
            sb.setSingleStep(0.5)
            sb.setValue(all_defaults[key])
            sb.valueChanged.connect(self._on_value_changed)
            self._spinboxes[key] = sb
            label_widget = QtWidgets.QLabel(label)
            layout.addRow(label_widget, sb)
            self._field_rows[key] = (label_widget, sb)

        # Style combo (only for Landis)
        self._style_combo = QtWidgets.QComboBox()
        self._style_combo.addItems(["updated (501)", "basic (vintage)"])
        self._style_combo.currentTextChanged.connect(self._on_value_changed)
        self._style_label = QtWidgets.QLabel("Stile draft (Landis only)")
        layout.addRow(self._style_label, self._style_combo)

        # Initial visibility: show Landis fields, hide Mueller fields
        self._apply_system_visibility()

    # ----- Public API ----------------------------------------------------

    def system(self) -> str:
        """Returns 'landis', 'mueller', 'mueller2', or 'mueller3'."""
        return self._system

    def set_system(self, system: str) -> None:
        if system == "landis":
            self._system_combo.setCurrentIndex(0)
        elif system == "mueller":
            self._system_combo.setCurrentIndex(1)
        elif system == "mueller2":
            self._system_combo.setCurrentIndex(2)
        elif system == "mueller3":
            self._system_combo.setCurrentIndex(3)
        else:
            raise ValueError(f"unknown system {system!r}")

    def unit(self) -> str:
        return self._unit

    def set_unit(self, new_unit: str) -> None:
        """Switch unit and convert all current spinbox values to the new unit."""
        self._unit_combo.setCurrentText(new_unit)

    def set_value(self, key: str, value: float) -> None:
        if key not in self._spinboxes:
            raise KeyError(f"unknown measurement key {key!r}")
        self._spinboxes[key].setValue(value)

    def to_measurements(self):
        """Returns Measurements (Landis) or MuellerMeasurements based on current system."""
        if self._system == "landis":
            keys = [k for k, _ in LANDIS_FIELDS]
            vals = {k: self._spinboxes[k].value() for k in keys}
            if self._unit == "cm":
                return Measurements.from_cm(**vals)
            return Measurements.from_inches(**vals)
        # mueller, mueller2, or mueller3 (all produce MuellerMeasurements)
        keys = [k for k, _ in MUELLER_FIELDS]
        vals = {k: self._spinboxes[k].value() for k in keys}
        if self._unit == "inch":
            # M&S is metric-native. Convert inch input to cm before constructing.
            vals = {k: v * CM_PER_INCH for k, v in vals.items()}
        return MuellerMeasurements.from_cm(**vals)

    def style(self) -> str:
        """Returns 'mueller3', 'mueller2', 'mueller', or 'basic'/'updated' for Landis."""
        if self._system == "mueller3":
            return "mueller3"
        if self._system == "mueller2":
            return "mueller2"
        if self._system == "mueller":
            return "mueller"
        return "updated" if "updated" in self._style_combo.currentText() else "basic"

    def set_style(self, style: str) -> None:
        if style == "mueller3":
            self.set_system("mueller3")
        elif style == "mueller2":
            self.set_system("mueller2")
        elif style == "mueller":
            self.set_system("mueller")
        elif style == "updated":
            self.set_system("landis")
            self._style_combo.setCurrentText("updated (501)")
        elif style == "basic":
            self.set_system("landis")
            self._style_combo.setCurrentText("basic (vintage)")
        else:
            raise ValueError(f"unknown style {style!r}")

    # ----- Internal handlers ---------------------------------------------

    def _on_system_changed(self, new_text: str) -> None:
        if "Mueller" in new_text and "3" in new_text:
            new_system = "mueller3"
        elif "Mueller" in new_text and "2" in new_text:
            new_system = "mueller2"
        elif "Mueller" in new_text:
            new_system = "mueller"
        else:
            new_system = "landis"
        if new_system == self._system:
            return
        self._system = new_system
        self._apply_system_visibility()
        self.measurements_changed.emit()

    def _apply_system_visibility(self) -> None:
        landis_keys = {k for k, _ in LANDIS_FIELDS}
        mueller_keys = {k for k, _ in MUELLER_FIELDS}
        for key, (label, sb) in self._field_rows.items():
            if self._system == "landis":
                visible = key in landis_keys
            else:   # mueller or mueller2
                visible = key in mueller_keys
            label.setVisible(visible)
            sb.setVisible(visible)
        # Style combo only relevant for Landis
        self._style_label.setVisible(self._system == "landis")
        self._style_combo.setVisible(self._system == "landis")

    def _on_unit_changed(self, new_unit: str) -> None:
        if new_unit == self._unit:
            return
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
