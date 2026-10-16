import numpy as np

def section_profile(points, faces, gh, view, side, levels=None):
    direction = np.array((0., 1., .02) if view == "back" else (.7, .7, .05))
    direction /= np.linalg.norm(direction)
    right = np.cross(-direction, np.array((0., 0., 1.)))
    right /= np.linalg.norm(right)
    up = np.cross(right, -direction)
    sign = 1 if gh @ right > 0 else -1
    if levels is None:
        levels = np.arange(-.12, .151, .002)
    a = faces[:, [0, 1, 2]].reshape(-1)
    b = faces[:, [1, 2, 0]].reshape(-1)
    p, q = points[a], points[b]
    heights_a, heights_b = (p-gh) @ up, (q-gh) @ up
    result = []
    for level in levels:
        crosses = ((heights_a <= level) & (heights_b > level)) | ((heights_b <= level) & (heights_a > level))
        aa, bb = p[crosses], q[crosses]
        da, db = heights_a[crosses], heights_b[crosses]
        intersections = aa + ((level-da)/(db-da))[:, None]*(bb-aa)
        keep = ((np.linalg.norm(intersections-gh, axis=1) < .22)
                & (intersections[:, 0] * (1 if side=="r" else -1) > 0))
        intersections = intersections[keep]
        result.append(float(((intersections-gh) @ right * sign).max()) if len(intersections) else float("nan"))
    return np.asarray(levels), np.asarray(result)


def corner_degrees(levels, outline):
    angle=np.degrees(np.arctan2(outline[5:]-outline[:-5],levels[5:]-levels[:-5]))
    change=np.abs(angle[5:]-angle[:-5])
    y=levels[5:-5]
    selected=change[(y>-.08)&(y<-.015)]
    if not np.isfinite(selected).all():
        raise ValueError('Missing contour intersections')
    return float(selected.max())

