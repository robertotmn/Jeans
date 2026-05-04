import pytest
from jeans_pattern.measurements import Measurements
from jeans_pattern.draft_basic import build_basic_front, build_basic_back
from jeans_pattern.draft_updated import build_updated_front, build_updated_back

INCH = 25.4

def test_updated_front_I_shifted(default_measurements):
    f = build_updated_front(default_measurements)
    base = build_basic_front(default_measurements)
    # I shifted 0.75" toward outseam (right) and 0.25" down
    assert f.I.x == pytest.approx(base.I.x + 0.75 * INCH)
    assert f.I.y == pytest.approx(base.I.y + 0.25 * INCH)

def test_updated_front_AA_position(default_measurements):
    f = build_updated_front(default_measurements)
    base = build_basic_front(default_measurements)
    # PDF page 21 step 7: F-AA = seat/16, AA directly below F by seat/16.
    assert f.AA.x == pytest.approx(base.F.x)
    assert f.AA.y == pytest.approx(base.F.y + 44.0/16 * INCH)

def test_updated_back_X_position(default_measurements):
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    # I-X = seat/10 sopra I (y diminuisce)
    assert b.X.x == pytest.approx(base.I.x)
    assert b.X.y == pytest.approx(base.I.y - 44.0/10 * INCH)

def test_updated_P_moved_down(default_measurements):
    f = build_updated_front(default_measurements)
    base = build_basic_front(default_measurements)
    # P_new = perpendicular from M to knee line, then 2" along outseam G->M.
    # Should land below the basic P by at least ~1.5"
    assert f.P_new.y > base.P.y + 1.5 * INCH

def test_updated_back_T_moved_down(default_measurements):
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    assert b.T_new.y > base.T.y + 1.5 * INCH

def test_updated_back_Y_at_new_waist_height(default_measurements):
    """Y_new is on the W-R outseam at the new (raised) waist line."""
    b = build_updated_back(default_measurements)
    assert b.Y.y == pytest.approx(b.X.y)

def test_updated_back_Z_at_new_waist_height(default_measurements):
    """Z_new keeps its x position but follows the raised waist line up to X.y."""
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    assert b.Z.x == pytest.approx(base.Z.x)
    assert b.Z.y == pytest.approx(b.X.y)
