import pytest

from jeans_pattern.export_pdf import pattern_to_pdf


def test_pdf_single_page_returns_bytes(mini_pattern):
    pdf = pattern_to_pdf(mini_pattern, mode="single")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_pdf_tiled_returns_bytes(mini_pattern):
    pdf = pattern_to_pdf(mini_pattern, mode="tiled_a4")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_pdf_calibration_changes_output(mini_pattern):
    a = pattern_to_pdf(mini_pattern, mode="single", calibration=True)
    b = pattern_to_pdf(mini_pattern, mode="single", calibration=False)
    assert a != b


def test_pdf_unknown_mode_raises(mini_pattern):
    with pytest.raises(ValueError):
        pattern_to_pdf(mini_pattern, mode="bogus")
