#!/usr/bin/env python3
"""Finite-difference self-test for the signed face-area barrier used by the ORIGINAL-v1 shoulder corrective."""
from __future__ import annotations
import numpy as np

def loss_grad(P, ref, area_min=0.20, weight=23000.0):
    A, B, C = P
    A0, B0, C0 = ref
    n0 = np.cross(B0 - A0, C0 - A0)
    den = max(float(n0 @ n0), 1e-18)
    n = np.cross(B - A, C - A)
    ratio = float(n @ n0) / den
    ex = max(area_min - ratio, 0.0)
    loss = weight * ex * ex
    g = np.zeros((3, 3), dtype=float)
    if ex > 0.0:
        gn = (-2.0 * weight * ex / den) * n0
        g[0] = np.cross(gn, C - B)
        g[1] = np.cross(gn, A - C)
        g[2] = np.cross(gn, B - A)
    return loss, g

def main():
    ref = np.array([[0.00, 0.00, 0.00], [0.03, 0.00, 0.00], [0.00, 0.04, 0.00]], dtype=float)
    P = np.array([[0.002, 0.001, 0.000], [0.012, 0.002, 0.002], [0.003, 0.008, -0.001]], dtype=float)
    loss, analytic = loss_grad(P, ref)
    if loss <= 0.0:
        raise SystemExit("test setup failed to activate area barrier")
    eps = 1e-7
    numeric = np.zeros_like(P)
    for i in range(3):
        for j in range(3):
            hi, lo = P.copy(), P.copy()
            hi[i, j] += eps
            lo[i, j] -= eps
            numeric[i, j] = (loss_grad(hi, ref)[0] - loss_grad(lo, ref)[0]) / (2.0 * eps)
    err = float(np.max(np.abs(analytic - numeric)))
    scale = max(1.0, float(np.max(np.abs(numeric))))
    rel = err / scale
    if rel > 2e-6:
        raise SystemExit(f"signed-area gradient check failed: abs={err:.6g} rel={rel:.6g}")
    print(f"SIGNED AREA GRADIENT VERIFIED abs={err:.3e} rel={rel:.3e}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
