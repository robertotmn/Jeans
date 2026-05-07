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


def test_pdf_mueller3_single_returns_bytes():
    from jeans_pattern.draft_mueller import MuellerMeasurements
    m = MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )
    pat = build_full_pattern(m, style="mueller3")
    pdf = pattern_to_pdf(pat, mode="single")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000   # raster embed adds bulk vs vector


def test_pdf_mueller3_tiled_returns_bytes():
    from jeans_pattern.draft_mueller import MuellerMeasurements
    m = MuellerMeasurements.from_cm(
        waistband=90, hip_girth=102, knee_girth=43, hem_width=38,
        outseam=102, inseam=82,
    )
    pat = build_full_pattern(m, style="mueller3")
    pdf = pattern_to_pdf(pat, mode="tiled_a4")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000
