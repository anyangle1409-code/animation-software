"""Authored context guides only; not registered rib surfaces or contact evidence."""
import math
from functional_shoulder_shapes import point

def rib_points(head, tail, side, bow):
    head, tail = point(head), point(tail)
    if side not in ('left', 'right'):
        raise ValueError('explicit anatomical side required')
    if isinstance(bow, bool) or not isinstance(bow, (int, float)) or not 0 < bow <= .2:
        raise ValueError('finite authored bow within20cm required')
    if head == tail:
        raise ValueError('collapsed rib endpoints')
    sign = 1 if side == 'left' else -1
    if head[0] * sign <= 0 or tail[0] * sign <= 0:
        raise ValueError('rib endpoints disagree with declared anatomical side')
    points = []
    for i in range(41):
        t = i / 40
        p = tuple(head[j] * (1-t) + tail[j] * t for j in range(3))
        points.append((p[0] + sign * bow * math.sin(math.pi*t)**2, p[1], p[2]))
    points[0], points[-1] = head, tail
    return points
