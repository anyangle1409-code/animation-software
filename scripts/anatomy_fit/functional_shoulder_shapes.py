"""Project-authored PROVISIONAL shape guides, never a clinical bone surface.

Joint anchors are supplied by the caller; curvature/thickness are explicit
artist assumptions, not inferred from Fontana's two projected circle radii.
Frame: metres, +X anatomical left, +Y posterior, +Z superior.
"""
import math


def point(p):
    if not isinstance(p, (list, tuple)) or len(p) != 3:
        raise ValueError('expected a finite three-coordinate point')
    if any(type(x) not in (int, float) or abs(x) > 10 or not math.isfinite(x) for x in p):
        raise ValueError('invalid metre coordinate')
    return tuple(p)


def clavicle_points(sc, ac):
    sc, ac = point(sc), point(ac)
    if math.dist(sc, ac) < .01:
        raise ValueError('collapsed clavicle anchors')
    out = []
    for i in range(41):
        t = i / 40
        # Smooth separated anterior medial / posterior lateral bows. Endpoints
        # unchanged; amplitudes are authored review hypotheses, not measurements.
        bow = (-.012 * math.sin(math.pi * t / .65) ** 2 if t <= .65 else
               .007 * math.sin(math.pi * (t - .65) / .35) ** 2)
        out.append(tuple(sc[k] + t * (ac[k] - sc[k]) + (bow if k == 1 else 0) for k in range(3)))
    out[0], out[-1] = sc, ac
    return out


def blade_mesh(perimeter):
    """Closed thin fan around source-informed outline; NOT reconstructed scan."""
    if not isinstance(perimeter, (list, tuple)) or not 3 <= len(perimeter) <= 32:
        raise ValueError('bounded blade outline required')
    p = [point(x) for x in perimeter]
    a = tuple(p[1][k] - p[0][k] for k in range(3))
    b = tuple(p[2][k] - p[0][k] for k in range(3))
    n = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    length = math.hypot(*n)
    if length <= 1e-12:
        raise ValueError('collapsed blade outline')
    n = tuple(x / length for x in n)
    centre = tuple(sum(x[k] for x in p) / len(p) for k in range(3))
    for i, q in enumerate(p):
        r = p[(i + 1) % len(p)]
        u = tuple(q[k] - centre[k] for k in range(3))
        v = tuple(r[k] - centre[k] for k in range(3))
        area = math.hypot(u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        if area <= 1e-12:
            raise ValueError('unsupported outline: degenerate fan triangle')
    layer = p + [centre]
    vertices = [tuple(x[k] + sign * .002 * n[k] for k in range(3)) for sign in (1, -1) for x in layer]
    size, c = len(layer), len(p)
    faces = []
    for i in range(c):
        j = (i + 1) % c
        faces.extend([(c, i, j), (c + size, j + size, i + size), (i, i + size, j + size, j)])
    return vertices, faces


def scapula_bowl_mesh(perimeter, depth):
    """Authored shallow costal concavity; retained outline, NOT thorax contact.

    Four radial rings, parabolic posterior recession,4mm normal thickness.
    Depth is a caller-declared artistic hypothesis, not a specimen measurement.
    """
    if type(depth) not in (int, float) or not 0 <= depth <= .02:
        raise ValueError('bounded finite authored depth0..20mm required')
    base, _ = blade_mesh(perimeter)  # Existing bounded outline/fan validation.
    count = len(perimeter)
    size = count + 1
    n = tuple((base[0][k] - base[size][k]) / .004 for k in range(3))
    if abs(n[1]) < .1:
        raise ValueError('costal posterior orientation is ambiguous')
    if n[1] < 0:
        n = tuple(-x for x in n)
    p = [point(x) for x in perimeter]
    c = tuple(sum(x[k] for x in p) / count for k in range(3))
    middle = [tuple(c[k] + depth * n[k] for k in range(3))]
    for ring in range(1, 5):
        r = ring / 4
        for q in p:
            middle.append(tuple(c[k] + r * (q[k] - c[k]) + depth * (1-r*r) * n[k] for k in range(3)))
    size = len(middle)
    vertices = [tuple(q[k] + sign * .002 * n[k] for k in range(3))
                for sign in (1, -1) for q in middle]
    surface = []
    for i in range(count):
        j = (i+1) % count
        surface.append((0, 1+i, 1+j))
        for ring in range(3):
            inner, outer = 1+ring*count, 1+(ring+1)*count
            surface.append((inner+i, outer+i, outer+j, inner+j))
    # Original ordering may reverse under an X mirror; keep outside winding.
    original_n_y = (base[0][1] - base[count+1][1]) / .004
    if original_n_y < 0:
        surface = [tuple(reversed(f)) for f in surface]
    faces = surface + [tuple(i+size for i in reversed(f)) for f in surface]
    outer = size-count
    for i in range(count):
        a, b = outer+i, outer+(i+1)%count
        rim = (a,b,b+size,a+size)
        faces.append(tuple(reversed(rim)) if original_n_y > 0 else rim)
    return vertices, faces
