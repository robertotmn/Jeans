import numpy as np
import pytest

from jeans_pattern.warp import tps_solve, tps_apply


def test_identity_warp():
    """If source == target, the warp is identity."""
    pts = np.array([[0.0, 0.0], [10.0, 0.0], [5.0, 10.0], [10.0, 10.0]])
    W, A = tps_solve(pts, pts)
    test_pts = np.array([[1.0, 2.0], [3.0, 4.0], [7.0, 8.0]])
    out = tps_apply(test_pts, pts, W, A)
    np.testing.assert_allclose(out, test_pts, atol=1e-9)


def test_pure_translation():
    """Translating all control points produces identical translation on test points."""
    src = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0]])
    shift = np.array([3.0, -2.0])
    tgt = src + shift
    W, A = tps_solve(src, tgt)
    test_pts = np.array([[5.0, 5.0], [2.0, 8.0]])
    out = tps_apply(test_pts, src, W, A)
    np.testing.assert_allclose(out, test_pts + shift, atol=1e-9)


def test_uniform_scale():
    """Scaling all control points by 2x produces 2x scaling on internal points."""
    src = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0]])
    tgt = src * 2.0
    W, A = tps_solve(src, tgt)
    interior = np.array([[5.0, 5.0], [3.0, 7.0]])
    out = tps_apply(interior, src, W, A)
    np.testing.assert_allclose(out, interior * 2.0, atol=1e-6)


def test_anisotropic_scale():
    """Scaling x by 2 and y by 0.5 is reproduced on internal points."""
    src = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0]])
    M = np.array([[2.0, 0.0], [0.0, 0.5]])
    tgt = src @ M.T
    W, A = tps_solve(src, tgt)
    interior = np.array([[5.0, 5.0], [3.0, 7.0]])
    out = tps_apply(interior, src, W, A)
    np.testing.assert_allclose(out, interior @ M.T, atol=1e-6)


def test_non_uniform_warp_passes_through_anchors():
    """A non-affine warp still produces target values at the source anchor points."""
    src = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [10.0, 10.0], [5.0, 5.0]])
    tgt = np.array([[0.0, 0.0], [12.0, 0.0], [0.0, 8.0], [12.0, 8.0], [6.0, 3.0]])
    W, A = tps_solve(src, tgt)
    out = tps_apply(src, src, W, A)
    np.testing.assert_allclose(out, tgt, atol=1e-6)


def test_collinear_points_raise():
    """Three collinear points produce a singular TPS system."""
    src = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    tgt = np.array([[0.0, 0.0], [2.0, 0.0], [4.0, 0.0]])
    with pytest.raises(ValueError, match="singular|collinear"):
        tps_solve(src, tgt)


def test_too_few_points_raise():
    """Fewer than 3 control points is rejected."""
    with pytest.raises(ValueError, match="at least 3"):
        tps_solve(np.array([[0.0, 0.0], [1.0, 1.0]]),
                  np.array([[0.0, 0.0], [2.0, 2.0]]))


def test_shape_mismatch_raises():
    with pytest.raises(ValueError, match="shape mismatch"):
        tps_solve(np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]),
                  np.array([[0.0, 0.0], [1.0, 0.0]]))
