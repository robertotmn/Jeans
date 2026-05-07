"""Thin-Plate Spline 2D warp utility (pure numpy).

Used by the Mueller2 template-based drafting system: maps a set of source
control points (the M&S diagram template's landmarks at their original
PDF coordinates) to target control points (where those landmarks should
sit for the user's body measurements). Then warps an entire polyline
through the same transformation.
"""
from __future__ import annotations

import numpy as np


def _u(r: np.ndarray) -> np.ndarray:
    """RBF kernel U(r) = r^2 * log(r), with U(0) = 0."""
    out = np.zeros_like(r)
    mask = r > 1e-12
    out[mask] = r[mask] ** 2 * np.log(r[mask])
    return out


def tps_solve(source_pts: np.ndarray, target_pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Solve TPS coefficients given N source/target control points.

    Args:
        source_pts: shape (N, 2)
        target_pts: shape (N, 2)

    Returns:
        (W, A) where:
            W is N x 2 (RBF weights, one column per output dim)
            A is 3 x 2 (affine part: [a0, a1, a2] rows for [x, y] cols)
    """
    source_pts = np.asarray(source_pts, dtype=float)
    target_pts = np.asarray(target_pts, dtype=float)
    if source_pts.shape != target_pts.shape:
        raise ValueError(f"shape mismatch: {source_pts.shape} vs {target_pts.shape}")
    if source_pts.ndim != 2 or source_pts.shape[1] != 2:
        raise ValueError(f"expected (N, 2) arrays, got {source_pts.shape}")
    N = source_pts.shape[0]
    if N < 3:
        raise ValueError(f"TPS needs at least 3 control points, got {N}")

    # Pairwise distances among source points
    diffs = source_pts[:, None, :] - source_pts[None, :, :]
    dist = np.sqrt((diffs ** 2).sum(axis=2))
    K = _u(dist)

    # P matrix: [1, x, y] for each source point
    P = np.hstack([np.ones((N, 1)), source_pts])

    # Build augmented system L = [[K, P], [P.T, 0]]
    L = np.zeros((N + 3, N + 3))
    L[:N, :N] = K
    L[:N, N:] = P
    L[N:, :N] = P.T

    # RHS: [target; 0] for each output dim
    rhs = np.zeros((N + 3, 2))
    rhs[:N] = target_pts

    try:
        sol = np.linalg.solve(L, rhs)
    except np.linalg.LinAlgError as e:
        raise ValueError(
            "TPS system is singular (control points likely collinear or duplicated)"
        ) from e

    W = sol[:N]    # (N, 2)
    A = sol[N:]    # (3, 2)
    return W, A


def tps_apply(coords: np.ndarray, source_pts: np.ndarray,
              W: np.ndarray, A: np.ndarray) -> np.ndarray:
    """Apply a TPS warp (solved via tps_solve) to a set of points.

    Args:
        coords: shape (M, 2) - points to warp
        source_pts: same as the source_pts passed to tps_solve, shape (N, 2)
        W: shape (N, 2) - RBF weights from tps_solve
        A: shape (3, 2) - affine part from tps_solve

    Returns:
        Warped points, shape (M, 2)
    """
    coords = np.asarray(coords, dtype=float)
    source_pts = np.asarray(source_pts, dtype=float)
    if coords.ndim != 2 or coords.shape[1] != 2:
        raise ValueError(f"expected (M, 2) coords, got {coords.shape}")

    # Distance from each query point to each source point
    diffs = coords[:, None, :] - source_pts[None, :, :]
    dist = np.sqrt((diffs ** 2).sum(axis=2))    # (M, N)
    U = _u(dist)                                 # (M, N)

    # Affine part: [1, x, y] @ A
    Q = np.hstack([np.ones((coords.shape[0], 1)), coords])    # (M, 3)

    return U @ W + Q @ A    # (M, 2)
