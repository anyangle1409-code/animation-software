"""Exact planar sections of a closed triangle mesh, split into connected loops.

Pure numpy; used by the character fitting tools outside Blender. A section loop is the
polyline of triangle/plane intersection segments chained through shared mesh edges.
"""
import numpy as np


def plane_section(V, T, origin, normal):
    """Return a list of loops (arrays of points) for the plane through origin with normal."""
    n = np.asarray(normal, float); n = n / np.linalg.norm(n)
    d = (V - np.asarray(origin, float)) @ n
    d = np.where(np.abs(d) < 1e-12, 1e-12, d)  # no vertex exactly on the plane
    s = np.sign(d)[T]
    hit = ~((s[:, 0] == s[:, 1]) & (s[:, 1] == s[:, 2]))
    edges_of = {}
    points = {}
    segs = []
    for t in np.nonzero(hit)[0]:
        tri = T[t]
        crossing = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if np.sign(d[a]) != np.sign(d[b]):
                key = (min(a, b), max(a, b))
                if key not in points:
                    w = d[a] / (d[a] - d[b])
                    points[key] = V[a] + w * (V[b] - V[a])
                crossing.append(key)
        if len(crossing) == 2:
            segs.append(crossing)
            for k in crossing:
                edges_of.setdefault(k, []).append(len(segs) - 1)
    used = np.zeros(len(segs), bool)
    loops = []
    for start in range(len(segs)):
        if used[start]:
            continue
        used[start] = True
        chain = [segs[start][0], segs[start][1]]
        while True:
            nxt = [s for s in edges_of[chain[-1]] if not used[s]]
            if not nxt:
                break
            used[nxt[0]] = True
            a, b = segs[nxt[0]]
            chain.append(b if a == chain[-1] else a)
        loops.append(np.array([points[k] for k in chain]))
    return loops


def loop_metrics(loop, normal):
    """Perimeter, area-weighted centroid and in-plane area of a closed loop."""
    n = np.asarray(normal, float); n = n / np.linalg.norm(n)
    p = loop
    q = np.roll(p, -1, axis=0)
    perimeter = float(np.linalg.norm(q - p, axis=1).sum())
    c0 = p.mean(0)
    cr = np.cross(p - c0, q - c0) @ n
    area = 0.5 * cr.sum()
    if abs(area) < 1e-15:
        return perimeter, c0, 0.0
    cent = c0 + ((p - c0 + q - c0) * cr[:, None]).sum(0) / (6 * area)
    return perimeter, cent, abs(float(area))
