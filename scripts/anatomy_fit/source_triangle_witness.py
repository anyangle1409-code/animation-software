"""Unsigned point-to-closed-triangle witness in unverified source units.

Not a mesh-mesh minimum, signed penetration, cartilage gap or joint centre.
No source geometry repair, registration, anatomical approval or scaling.
"""
import math


def _vector(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError('Expected three source coordinates')
    if any(type(x) not in (int, float) or not math.isfinite(x) or
           abs(x) > 1_000_000 for x in value):
        raise ValueError('Nonfinite, nonnumeric or out-of-bound source coordinate')
    return tuple(float(x) for x in value)


def _sub(a, b):
    return tuple(x-y for x,y in zip(a,b))


def _dot(a, b):
    return math.fsum(x*y for x,y in zip(a,b))


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def closest_point(point, triangle):
    """Project onto the face interior or nearest of three closed edges.

    Reject zero/underflowed triangle area rather than silently treating a line
    or point as a source surface. Bound coordinates to keep arithmetic finite.
    Winding changes barycentric order only, never unsigned distance semantics.
    """
    p = _vector(point)
    if not isinstance(triangle, (tuple, list)) or len(triangle) != 3:
        raise ValueError('Expected three triangle vertices')
    a,b,c = [_vector(v) for v in triangle]
    ab, ac = _sub(b,a), _sub(c,a)
    n = _cross(ab,ac)
    n2 = _dot(n,n)
    if n2 == 0:
        raise ValueError('Degenerate or numerically underflowed source triangle')
    ap = _sub(p,a)
    h = _dot(ap,n)/n2
    projected = tuple(p[j]-h*n[j] for j in range(3))
    aq = _sub(projected,a)
    v = _dot(_cross(aq,ac),n)/n2
    w = _dot(_cross(ab,aq),n)/n2
    u = 1-v-w
    candidates = []
    if min(u,v,w) >= 0:
        candidates.append((projected, [u,v,w]))
    for i,j in [(0,1),(1,2),(2,0)]:
        start,end = (a,b,c)[i], (a,b,c)[j]
        edge = _sub(end,start)
        length2 = _dot(edge,edge)
        if length2 == 0:
            raise ValueError('Numerically underflowed source edge')
        t = min(1., max(0., _dot(_sub(p,start),edge)/length2))
        q = tuple(start[k]+t*edge[k] for k in range(3))
        bary = [0.,0.,0.]
        bary[i],bary[j] = 1-t,t
        candidates.append((q,bary))
    q,bary = min(candidates, key=lambda item: _dot(_sub(p,item[0]),_sub(p,item[0])))
    distance = math.sqrt(_dot(_sub(p,q),_sub(p,q)))
    return {'point_source_units': list(q), 'distance_source_units': distance,
            'barycentric': bary, 'physical_units_verified': False,
            'anatomical_contact_accepted': False,
            'whole_surface_clearance_verified': False}
