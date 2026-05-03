import pytest
from jeans_pattern.measurements import Measurements, INCH_TO_MM

def test_default_measurements_in_mm():
    m = Measurements.from_inches(waist=34.5, seat=44.0, rise=9.75,
                                  knee=10.375, bottom=9.75, length=34.0)
    assert m.waist_mm == pytest.approx(34.5 * 25.4)
    assert m.seat_mm == pytest.approx(44.0 * 25.4)

def test_from_cm_roundtrip():
    m = Measurements.from_cm(waist=87.63, seat=111.76, rise=24.765,
                             knee=26.3525, bottom=24.765, length=86.36)
    assert m.waist_mm == pytest.approx(876.3)

def test_negative_value_rejected():
    with pytest.raises(ValueError):
        Measurements.from_cm(waist=-1, seat=100, rise=25, knee=26, bottom=25, length=86)

def test_zero_value_rejected():
    with pytest.raises(ValueError):
        Measurements.from_cm(waist=0, seat=100, rise=25, knee=26, bottom=25, length=86)
