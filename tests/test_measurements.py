import pytest

from jeans_pattern.measurements import Measurements


def test_size50_chart_derived_values(size50):
    """Every derived value must match the printed chart (page 2, size 50)."""
    m = size50
    assert m.body_rise_mm == pytest.approx(200.0)              # Br = Os - Is = 20.0 cm
    assert m.knee_length_mm == pytest.approx(472.0)            # Kl = 47.2 cm
    assert m.front_trouser_width_mm == pytest.approx(255.0)    # Ftw = 25.5 cm
    assert m.front_crotch_width_mm == pytest.approx(51.0)      # Fcw = 5.1 cm
    assert m.back_crotch_width_mm == pytest.approx(122.0)      # Bcw = 12.2 cm
    assert m.back_trouser_width_mm == pytest.approx(280.0)     # Btw = 28.0 cm
    assert m.hip_depth_above_crotch_mm == pytest.approx(81.0)  # 1/10 (Hg/2) + 3 = 8.1 cm


def test_from_cm_stores_mm(size50):
    assert size50.waistband_mm == pytest.approx(900.0)
    assert size50.hip_girth_mm == pytest.approx(1020.0)
    assert size50.inseam_mm == pytest.approx(820.0)


def test_from_inches_converts():
    m = Measurements.from_inches(
        waistband=35.0, hip_girth=40.0, knee_girth=17.0, hem_width=15.0,
        outseam=40.0, inseam=32.0,
    )
    assert m.waistband_mm == pytest.approx(35.0 * 25.4)
    assert m.inseam_mm == pytest.approx(32.0 * 25.4)


def test_nonpositive_rejected():
    with pytest.raises(ValueError):
        Measurements.from_cm(waistband=0, hip_girth=102, knee_girth=43,
                             hem_width=38, outseam=102, inseam=82)


def test_outseam_must_exceed_inseam():
    with pytest.raises(ValueError):
        Measurements.from_cm(waistband=90, hip_girth=102, knee_girth=43,
                             hem_width=38, outseam=82, inseam=82)
