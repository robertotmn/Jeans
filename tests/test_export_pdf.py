import pytest

from jeans_pattern.export_pdf import pattern_to_pdf
from jeans_pattern.pattern import SeamAllowances, build_jacket_pattern


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


# ---------------------------------------------------------------------------
# The real Design 4041 pattern: 17 pieces, fold edges at allowance 0, hundreds
# of construction lines and one label placed outside its own bounding box.
# ---------------------------------------------------------------------------

def test_pdf_jacket_both_modes(size50_jacket):
    jacket = build_jacket_pattern(size50_jacket)
    assert len(jacket.pieces) == 17
    single = pattern_to_pdf(jacket, mode="single")
    tiled = pattern_to_pdf(jacket, mode="tiled_a4")
    assert single[:4] == b"%PDF" and tiled[:4] == b"%PDF"
    # the layout is ~4 m wide, so the tiled version repeats it over many sheets
    assert len(tiled) > len(single) > 10000


def test_pdf_jacket_without_allowances(size50_jacket):
    """With the allowances off every piece drops its cut line, so the page
    carries strictly less ink than the one with the margins."""
    net_only = build_jacket_pattern(size50_jacket, SeamAllowances(seam_mm=0, hem_mm=0))
    assert all(p.cut_outline is None for p in net_only)
    pdf = pattern_to_pdf(net_only, mode="single")
    assert pdf[:4] == b"%PDF"
    assert len(pdf) < len(pattern_to_pdf(build_jacket_pattern(size50_jacket), mode="single"))
