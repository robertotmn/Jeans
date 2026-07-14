import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from jeans_app.measurement_form import MeasurementForm  # noqa: E402
from jeans_pattern.measurements import Measurements  # noqa: E402


@pytest.fixture
def form(qtbot):
    f = MeasurementForm()
    qtbot.addWidget(f)
    return f


def test_form_default_unit_is_cm(form):
    assert form.unit() == "cm"


def test_form_defaults_are_size_50(form):
    m = form.to_measurements()
    assert isinstance(m, Measurements)
    assert m.waistband_mm == pytest.approx(900.0)
    assert m.hip_girth_mm == pytest.approx(1020.0)
    assert m.inseam_mm == pytest.approx(820.0)


def test_form_collects_measurements_in_cm(form):
    form.set_value("waistband", 96.0)
    form.set_value("hip_girth", 108.0)
    m = form.to_measurements()
    assert m.waistband_mm == pytest.approx(960.0)
    assert m.hip_girth_mm == pytest.approx(1080.0)


def test_form_emits_changed_signal(form, qtbot):
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.set_value("waistband", 91.0)


def test_form_unit_toggle_converts_values(form):
    form.set_value("waistband", 88.9)   # ~35"
    form.set_unit("inch")
    assert form.unit() == "inch"
    assert form._spinboxes["waistband"].value() == pytest.approx(35.0, abs=0.01)
    # and to_measurements converts back to mm correctly
    m = form.to_measurements()
    assert m.waistband_mm == pytest.approx(889.0, abs=0.5)


def test_form_unknown_key_raises(form):
    with pytest.raises(KeyError):
        form.set_value("waist", 90.0)
