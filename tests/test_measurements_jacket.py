import pytest

from jeans_pattern.measurements_jacket import JacketMeasurements


@pytest.fixture
def size50_jacket():
    """M&S chart sample, size 50 (booklet page 12). The pages 11-13 drawings of
    this size are the ground truth for the jacket block."""
    return JacketMeasurements.from_cm(
        body_height=179.0, chest_girth=100.0, waist_girth=90.0,
        hip_girth=102.0, sleeve_length=64.0,
    )


def test_size50_chart_derived_values(size50_jacket):
    """Every derived value must match the printed chart (page 12, size 50)."""
    m = size50_jacket
    assert m.neck_width_mm == pytest.approx(80.0)          # Nw = 8.0 cm (chart 8.5: typo)
    assert m.scye_depth_mm == pytest.approx(250.0)         # Sd = 25.0 cm
    assert m.back_waist_length_mm == pytest.approx(447.5)  # Bwl = 44.75 cm
    assert m.jacket_length_mm == pytest.approx(640.0)      # Lg = 64.0 cm
    assert m.armhole_depth_mm == pytest.approx(275.0)      # Ad = 27.5 cm
    assert m.back_width_mm == pytest.approx(212.0)         # Bw = 21.2 cm
    assert m.scye_width_mm == pytest.approx(155.0)         # Sw = 15.5 cm
    assert m.chest_width_mm == pytest.approx(208.0)        # Cw = 20.8 cm
    assert m.abdomen_width_mm == pytest.approx(212.0)      # Aw = 21.2 cm


def test_total_chest_width_matches_chart(size50_jacket):
    """Bw + Sw + Cw = 1/2 Cg + 7.5 cm of ease (chart: 57.5 cm)."""
    m = size50_jacket
    total = m.back_width_mm + m.scye_width_mm + m.chest_width_mm
    assert total == pytest.approx(575.0)
    assert total - m.chest_girth_mm / 2 == pytest.approx(75.0)


def test_back_width_switch_is_continuous_at_cg_100():
    below = JacketMeasurements.from_cm(body_height=179, chest_girth=99.9, waist_girth=90,
                                       hip_girth=102, sleeve_length=64)
    at = JacketMeasurements.from_cm(body_height=179, chest_girth=100.0, waist_girth=90,
                                    hip_girth=102, sleeve_length=64)
    above = JacketMeasurements.from_cm(body_height=179, chest_girth=100.1, waist_girth=90,
                                       hip_girth=102, sleeve_length=64)
    assert below.back_width_mm == pytest.approx(211.8)   # 2/10 Cg + 1.2
    assert at.back_width_mm == pytest.approx(212.0)
    assert above.back_width_mm == pytest.approx(212.1)   # 1/10 Cg + 11.2
    assert above.back_width_mm - at.back_width_mm == pytest.approx(0.1, abs=1e-6)


def test_back_width_large_size_uses_second_formula():
    m = JacketMeasurements.from_cm(body_height=179, chest_girth=110, waist_girth=100,
                                   hip_girth=112, sleeve_length=64)
    assert m.back_width_mm == pytest.approx(222.0)  # 11.0 + 11.2 = 22.2 cm


def test_abdomen_width_floors_at_chest_width():
    m = JacketMeasurements.from_cm(body_height=179, chest_girth=100, waist_girth=80,
                                   hip_girth=102, sleeve_length=64)
    assert m.waist_girth_mm / 4 - 13.0 < m.chest_width_mm
    assert m.abdomen_width_mm == pytest.approx(m.chest_width_mm)


def test_from_cm_stores_mm(size50_jacket):
    assert size50_jacket.body_height_mm == pytest.approx(1790.0)
    assert size50_jacket.chest_girth_mm == pytest.approx(1000.0)
    assert size50_jacket.sleeve_length_mm == pytest.approx(640.0)


def test_from_inches_converts():
    m = JacketMeasurements.from_inches(body_height=70.0, chest_girth=39.0, waist_girth=35.0,
                                       hip_girth=40.0, sleeve_length=25.0)
    assert m.body_height_mm == pytest.approx(70.0 * 25.4)
    assert m.sleeve_length_mm == pytest.approx(25.0 * 25.4)


def test_nonpositive_rejected():
    with pytest.raises(ValueError):
        JacketMeasurements.from_cm(body_height=179, chest_girth=0, waist_girth=90,
                                   hip_girth=102, sleeve_length=64)


def test_sleeve_length_must_be_below_body_height():
    with pytest.raises(ValueError):
        JacketMeasurements.from_cm(body_height=64, chest_girth=100, waist_girth=90,
                                   hip_girth=102, sleeve_length=64)


def test_jacket_length_must_exceed_armhole_depth():
    with pytest.raises(ValueError):
        JacketMeasurements.from_cm(body_height=10, chest_girth=100, waist_girth=90,
                                   hip_girth=102, sleeve_length=5)
