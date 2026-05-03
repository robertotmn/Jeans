import pytest
from jeans_pattern.export_pdf import pattern_to_pdf
from jeans_pattern.pattern import build_full_pattern


def test_pdf_single_page_returns_bytes(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    pdf = pattern_to_pdf(pat, mode="single")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_pdf_tiled_returns_bytes(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    pdf = pattern_to_pdf(pat, mode="tiled_a4")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_pdf_calibration_changes_output(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    a = pattern_to_pdf(pat, mode="single", calibration=True)
    b = pattern_to_pdf(pat, mode="single", calibration=False)
    assert a != b


def test_pdf_unknown_mode_raises(default_measurements):
    pat = build_full_pattern(default_measurements, style="updated")
    with pytest.raises(ValueError):
        pattern_to_pdf(pat, mode="bogus")
