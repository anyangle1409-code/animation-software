#!/usr/bin/env python3
"""Dependency-free finite-difference self-test for the ORIGINAL-v1 signed face-area barrier."""
from __future__ import annotations


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def scale(s, a):
    return [s * x for x in a]


def loss_grad(points, reference, area_min=0.20, weight=23000.0):
    A, B, C = points
    A0, B0, C0 = reference
    n0 = cross(sub(B0, A0), sub(C0, A0))
    den = max(dot(n0, n0), 1e-18)
    n = cross(sub(B, A), sub(C, A))
    ratio = dot(n, n0) / den
    ex = max(area_min - ratio, 0.0)
    loss = weight * ex * ex
    grad = [[0.0, 0.0, 0.0] for _ in range(3)]
    if ex > 0.0:
        gn = scale(-2.0 * weight * ex / den, n0)
        grad[0] = cross(gn, sub(C, B))
        grad[1] = cross(gn, sub(A, C))
        grad[2] = cross(gn, sub(B, A))
    return loss, grad


def clone(points):
    return [list(row) for row in points]


def main():
    reference = [[0.00, 0.00, 0.00], [0.03, 0.00, 0.00], [0.00, 0.04, 0.00]]
    points = [[0.002, 0.001, 0.000], [0.012, 0.002, 0.002], [0.003, 0.008, -0.001]]
    loss, analytic = loss_grad(points, reference)
    if loss <= 0.0:
        raise SystemExit("test setup failed to activate area barrier")

    eps = 1e-7
    numeric = [[0.0, 0.0, 0.0] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            hi, lo = clone(points), clone(points)
            hi[i][j] += eps
            lo[i][j] -= eps
            numeric[i][j] = (loss_grad(hi, reference)[0] - loss_grad(lo, reference)[0]) / (2.0 * eps)

    err = max(abs(analytic[i][j] - numeric[i][j]) for i in range(3) for j in range(3))
    scale0 = max(1.0, max(abs(numeric[i][j]) for i in range(3) for j in range(3)))
    rel = err / scale0
    if rel > 2e-6:
        raise SystemExit(f"signed-area gradient check failed: abs={err:.6g} rel={rel:.6g}")
    print(f"SIGNED AREA GRADIENT VERIFIED abs={err:.3e} rel={rel:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
