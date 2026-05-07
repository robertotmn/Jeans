import pytest
from jeans_app.measurement_form import MeasurementForm


@pytest.fixture
def form(qtbot):
    f = MeasurementForm()
    qtbot.addWidget(f)
    return f


def test_form_default_unit_is_cm(form):
    assert form.unit() == "cm"


def test_form_default_style_is_updated(form):
    assert form.style() == "updated"


def test_form_collects_measurements_in_cm(form, qtbot):
    form.set_value("waist", 87.63)
    form.set_value("seat", 111.76)
    form.set_value("rise", 24.765)
    form.set_value("knee", 26.35)
    form.set_value("bottom", 24.765)
    form.set_value("length", 86.36)
    m = form.to_measurements()
    assert m.waist_mm == pytest.approx(876.3)
    assert m.seat_mm == pytest.approx(1117.6)


def test_form_emits_changed_signal(form, qtbot):
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.set_value("waist", 90.0)


def test_form_unit_toggle_converts_values(form):
    form.set_value("waist", 88.9)   # ~35"
    form.set_unit("inch")
    assert form.unit() == "inch"
    # 88.9 cm = 35.0 inch
    assert form._spinboxes["waist"].value() == pytest.approx(35.0, abs=0.01)


def test_form_style_toggle(form):
    form.set_style("basic")
    assert form.style() == "basic"


def test_form_default_system_is_landis(form):
    assert form.system() == "landis"


def test_form_system_toggle_to_mueller(form, qtbot):
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.set_system("mueller")
    assert form.system() == "mueller"
    assert form.style() == "mueller"


def test_form_mueller_to_measurements(form):
    form.set_system("mueller")
    form.set_value("waistband", 90.0)
    form.set_value("hip_girth", 102.0)
    form.set_value("knee_girth", 43.0)
    form.set_value("hem_width", 38.0)
    form.set_value("outseam", 102.0)
    form.set_value("inseam", 82.0)
    m = form.to_measurements()
    from jeans_pattern.draft_mueller import MuellerMeasurements
    assert isinstance(m, MuellerMeasurements)
    assert m.waistband_mm == pytest.approx(900.0)
    assert m.hip_girth_mm == pytest.approx(1020.0)


def test_form_landis_to_measurements_after_toggle(form):
    """Switching to Mueller and back to Landis still produces Measurements."""
    form.set_system("mueller")
    form.set_system("landis")
    m = form.to_measurements()
    from jeans_pattern.measurements import Measurements
    assert isinstance(m, Measurements)


def test_form_system_toggle_to_mueller2(form, qtbot):
    with qtbot.waitSignal(form.measurements_changed, timeout=1000):
        form.set_system("mueller2")
    assert form.system() == "mueller2"
    assert form.style() == "mueller2"


def test_form_mueller2_to_measurements(form):
    form.set_system("mueller2")
    form.set_value("waistband", 90.0)
    form.set_value("hip_girth", 102.0)
    form.set_value("knee_girth", 43.0)
    form.set_value("hem_width", 38.0)
    form.set_value("outseam", 102.0)
    form.set_value("inseam", 82.0)
    m = form.to_measurements()
    from jeans_pattern.draft_mueller import MuellerMeasurements
    assert isinstance(m, MuellerMeasurements)
    assert m.waistband_mm == pytest.approx(900.0)
