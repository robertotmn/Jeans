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

def test_updated_back_Y_on_basic_waist(default_measurements):
    """Il back body si ferma sulla vita base (y=0); il yoke e' un pezzo separato.
    Y resta sulla intersezione W-R con la vita base, non sulla vita rialzata."""
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    assert b.Y.x == pytest.approx(base.Y.x)
    assert b.Y.y == pytest.approx(base.Y.y)

def test_updated_back_Z_on_basic_waist(default_measurements):
    """Z resta sulla vita base (y=0); la regione yoke sopra la vita e' separata."""
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    assert b.Z.x == pytest.approx(base.Z.x)
    assert b.Z.y == pytest.approx(base.Z.y)

def test_updated_back_X_remains_construction_point(default_measurements):
    """new_X resta sopra I di seat/10 come riferimento yoke, anche se il back
    body non si estende fino a quella altezza."""
    b = build_updated_back(default_measurements)
    base = build_basic_back(default_measurements)
    assert b.X.y == pytest.approx(base.I.y - 44.0/10 * INCH)
