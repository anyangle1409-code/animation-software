"""Experimental authoring geometry, SI units. Not a force or tissue simulator.

Authored via points are evaluated, never invented. Clearance reports reject a
bad path; they do not silently solve wrapping or establish anatomical validity.
"""
import math


def scalar(value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Expected finite number')
    if low is not None and value < low or high is not None and value > high:
        raise ValueError('Number outside permitted range')
    return float(value)


def vec(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('Expected three coordinates')
    return tuple(scalar(x) for x in value)


def resolve_path(anchors, transforms):
    """Bone-local metres -> world metres, using evaluated affine bone matrices."""
    if len(anchors) < 2:
        raise ValueError('Path requires origin and insertion')
    result=[]
    for anchor in anchors:
        bone=anchor.get('bone')
        if bone not in transforms:
            raise ValueError(f'Missing actual bone transform: {bone}')
        p=vec(anchor.get('local_m'))
        m=transforms[bone]
        if len(m)!=4 or any(len(row)!=4 for row in m):
            raise ValueError('Expected 4x4 matrix')
        m=tuple(tuple(scalar(x) for x in row) for row in m)
        if m[3]!=(0.,0.,0.,1.):
            raise ValueError('Expected affine matrix')
        result.append(vec(tuple(sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3))))
    path_length(result)
    return result


def path_length(points):
    if len(points)<2:
        raise ValueError('Path requires two points')
    points=[vec(p) for p in points]
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:])]
    if any(x<=1e-12 or not math.isfinite(x) for x in lengths):
        raise ValueError('Degenerate path segment')
    return scalar(sum(lengths),1e-12)


def sphere_clearance(points, center, radius):
    """Minimum signed segment clearance from an authored spherical obstacle.

    This is centreline clearance only. Subtract local muscle radius separately;
    not a triangle-intersection/contact classifier or complete wrap solver.
    """
    path_length(points)
    center=vec(center)
    radius=scalar(radius,1e-12)
    distances=[]
    for a,b in zip(points,points[1:]):
        a,b=vec(a),vec(b)
        d=tuple(y-x for x,y in zip(a,b))
        length=scalar(math.hypot(*d),1e-12)
        unit=tuple(v/length for v in d)
        along=scalar(sum(scalar(c-x)*v for c,x,v in zip(center,a,unit)))
        t=max(0.,min(1.,along/length))
        distances.append(math.dist(center,tuple(x+t*v for x,v in zip(a,d)))-radius)
    return min(distances)


def belly_axes(volume_m3, belly_length_m, activation, visual_gain=0):
    """Equal-volume elliptic cylinder proxy, NOT an anatomical muscle surface.

    Shortening widens both axes. Independent activation redistributes axes at
    fixed volume/length; gain is an authored appearance setting, not physiology.
    Tendon length must be excluded by caller; no tendon force/equilibrium solve.
    """
    volume_m3=scalar(volume_m3,1e-12)
    belly_length_m=scalar(belly_length_m,1e-12)
    activation=scalar(activation,0,1)
    visual_gain=scalar(visual_gain,0,1)
    r=math.sqrt(volume_m3/(math.pi*belly_length_m))
    ratio=1+activation*visual_gain
    return scalar(r*ratio,1e-12),scalar(r/ratio,1e-12)


def skin_delta(influences, region_mask, max_displacement_m):
    """Blend caller-approved *rest-relative* deltas; no cumulative frame drift.

    Deep tissue must receive zero direct weight unless an explicit reviewed
    transfer cage exists. Mask and maximum are authored engineering bounds.
    """
    mask=scalar(region_mask,0,1)
    cap=scalar(max_displacement_m,0)
    parsed=[(scalar(w,0,1),vec(d)) for w,d in influences]
    total=sum(w for w,_ in parsed)
    delta=tuple(mask*sum(w*d[i] for w,d in parsed)/max(1.,total) for i in range(3))
    length=scalar(math.hypot(*delta),0)
    factor=min(1.,cap/length) if length else 1.
    return vec(tuple(x*factor for x in delta))
