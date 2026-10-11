"""Exact closed-triangle predicate, not anatomical or whole-mesh clearance.

Rational arithmetic is exact for the supplied finite Python int/float values,
not for the unknowable continuous anatomy underlying sampled source surfaces.
Bounded two-triangle API only; not intended as an all-pairs mesh scan.
"""
from fractions import Fraction
import math


def _triangle(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('Expected three source triangle vertices')
    result = []
    for vertex in value:
        if not isinstance(vertex, (list, tuple)) or len(vertex) != 3:
            raise ValueError('Expected three source coordinates')
        for x in vertex:
            if type(x) not in (int, float) or abs(x) > 1_000_000 or not math.isfinite(x):
                raise ValueError('Invalid or out-of-bound source coordinate')
        result.append(tuple(Fraction(x) for x in vertex))
    return result


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def intersection(triangle_a, triangle_b):
    """Return whether two nondegenerate closed triangles share any point.

    Separating-axis test uses face normals and all edge cross products.
    In-plane edge normals additionally cover coplanar disjoint triangles,
    whose edge cross products alone cannot separate them. No normalized axes,
    tolerances, repair or floating-point predicates. Equality means touching.
    Invalid/degenerate triangles raise; they are never reported as clear.
    """
    a, b = _triangle(triangle_a), _triangle(triangle_b)
    ea = [_sub(a[(i+1) % 3], a[i]) for i in range(3)]
    eb = [_sub(b[(i+1) % 3], b[i]) for i in range(3)]
    na, nb = _cross(ea[0], ea[1]), _cross(eb[0], eb[1])
    if not any(na) or not any(nb):
        raise ValueError('Degenerate source triangle is not a surface')
    axes = [na, nb]
    axes.extend(_cross(x, y) for x in ea for y in eb)
    axes.extend(_cross(na, x) for x in ea)
    axes.extend(_cross(nb, x) for x in eb)
    intersects = True
    for axis in axes:
        if not any(axis):
            continue
        pa, pb = [_dot(v, axis) for v in a], [_dot(v, axis) for v in b]
        if max(pa) < min(pb) or max(pb) < min(pa):
            intersects = False
            break
    return {'closed_triangles_intersect': intersects,
            'anatomical_contact_accepted': False,
            'physical_units_verified': False,
            'whole_surface_clearance_verified': False}
