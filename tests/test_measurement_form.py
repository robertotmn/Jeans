import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from jeans_app.measurement_form import (  # noqa: E402
    MODEL_JACKET,
    MODEL_JEANS,
    MeasurementForm,
)
from jeans_pattern.measurements import Measurements  # noqa: E402
from jeans_pattern.measurements_jacket import JacketMeasurements  # noqa: E402


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


def test_form_seam_allowance_defaults(form):
    sa = form.seam_allowances()
    assert sa.seam_mm == pytest.approx(15.0)
    assert sa.hem_mm == pytest.approx(30.0)


def test_form_seam_allowance_converts_with_unit(form):
    form.set_unit("inch")
    sa = form.seam_allowances()
    # 1.5 cm -> 0.5906 inch shown; converted back = 15 mm
    assert sa.seam_mm == pytest.approx(15.0, abs=0.05)
    assert sa.hem_mm == pytest.approx(30.0, abs=0.05)


def test_form_zero_allowances_disable_cut_line(form):
    form.set_value("sa_seam", 0.0)
    form.set_value("sa_hem", 0.0)
    assert not form.seam_allowances().enabled


def test_form_reset_restores_defaults(form, qtbot):
    form.set_value("waistband", 104.0)
    form.set_value("sa_hem", 0.0)
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.reset_to_defaults()
    m = form.to_measurements()
    assert m.waistband_mm == pytest.approx(900.0)
    assert form.seam_allowances().hem_mm == pytest.approx(30.0)


def test_form_reset_respects_current_unit(form):
    form.set_unit("inch")
    form.set_value("waistband", 40.0)
    form.reset_to_defaults()
    # spinbox shows inches, converted measurement is back to 90 cm
    assert form._spinboxes["waistband"].value() == pytest.approx(90.0 / 2.54, abs=0.01)
    assert form.to_measurements().waistband_mm == pytest.approx(900.0, abs=0.5)


# ----- model selection (Basic Jeans / Classic Denim Jacket) -----------------


def test_form_default_model_is_jeans(form):
    assert form.model() == MODEL_JEANS
    assert form._model_combo.currentText() == "Basic Jeans"


def test_form_jacket_model_hides_jeans_rows(form):
    form.set_model(MODEL_JACKET)
    assert form.model() == MODEL_JACKET
    for key in ("knee_girth", "hem_width", "outseam", "inseam"):
        assert form._spinboxes[key].isHidden()
    for key in ("body_height", "chest_girth", "sleeve_length"):
        assert not form._spinboxes[key].isHidden()
    # shared measurements and the allowances stay visible in both models
    for key in ("waistband", "hip_girth", "sa_seam", "sa_hem"):
        assert not form._spinboxes[key].isHidden()


def test_form_switching_back_shows_jeans_rows(form):
    form.set_model(MODEL_JACKET)
    form.set_model(MODEL_JEANS)
    assert not form._spinboxes["inseam"].isHidden()
    assert form._spinboxes["body_height"].isHidden()


def test_form_model_change_emits_signals(form, qtbot):
    with qtbot.waitSignal(form.model_changed, timeout=1000) as blocker:
        with qtbot.waitSignal(form.measurements_changed, timeout=1000):
            form.set_model(MODEL_JACKET)
    assert blocker.args == [MODEL_JACKET]


def test_form_unknown_model_raises(form):
    with pytest.raises(ValueError):
        form.set_model("Trucker Jacket")


def test_form_jacket_defaults_are_size_50(form):
    m = form.to_jacket_measurements()
    assert isinstance(m, JacketMeasurements)
    assert m.body_height_mm == pytest.approx(1790.0)
    assert m.chest_girth_mm == pytest.approx(1000.0)
    assert m.sleeve_length_mm == pytest.approx(640.0)
    # Wg and Hg come from the shared jeans fields
    assert m.waist_girth_mm == pytest.approx(900.0)
    assert m.hip_girth_mm == pytest.approx(1020.0)


def test_form_collects_jacket_measurements_in_cm(form):
    form.set_value("chest_girth", 104.0)
    form.set_value("waistband", 96.0)
    m = form.to_jacket_measurements()
    assert m.chest_girth_mm == pytest.approx(1040.0)
    assert m.waist_girth_mm == pytest.approx(960.0)


def test_form_collects_jacket_measurements_in_inch(form):
    form.set_unit("inch")
    assert form._spinboxes["chest_girth"].value() == pytest.approx(100.0 / 2.54, abs=0.01)
    m = form.to_jacket_measurements()
    assert m.chest_girth_mm == pytest.approx(1000.0, abs=0.5)
    assert m.sleeve_length_mm == pytest.approx(640.0, abs=0.5)


def test_form_reset_with_jacket_model(form):
    form.set_model(MODEL_JACKET)
    form.set_value("chest_girth", 112.0)
    form.set_value("sleeve_length", 70.0)
    form.reset_to_defaults()
    m = form.to_jacket_measurements()
    assert m.chest_girth_mm == pytest.approx(1000.0)
    assert m.sleeve_length_mm == pytest.approx(640.0)
    # the reset does not change the selected model
    assert form.model() == MODEL_JACKET
