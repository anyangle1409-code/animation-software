"""Complete bounded AABB candidates for supplied triangles in one source frame.

No native BVH quantization, local-origin changes, snapping, island filtering or
anatomical inference. Box overlap is only a conservative candidate, not contact.
"""
import heapq

from source_triangle_intersection import _triangle


def _boxes(triangles):
    if not isinstance(triangles, (list, tuple)) or not 1 <= len(triangles) <= 100_000:
        raise ValueError('Expected a nonempty bounded original triangle sequence')
    boxes = []
    for triangle in triangles:
        # Share the exact supplied-value validation; deliberately keep degenerate
        # faces and duplicates here. Their narrow-phase disposition stays open.
        vertices = _triangle(triangle)
        boxes.append((tuple(min(v[k] for v in vertices) for k in range(3)),
                      tuple(max(v[k] for v in vertices) for k in range(3))))
    return boxes


def candidate_pairs(triangles_a, triangles_b, *, max_checks=250_000):
    """Return all cross-set overlapping closed boxes, or raise without a result.

    Exact rational coordinate comparisons preserve the input binary values.
    Original list indices identify every face, including duplicates/degenerates.
    Sweep X; expire only boxes strictly left of the next starting coordinate.
    Each pair is checked once when its later event starts. Over-limit scans
    raise; never expose a partial iterator/report as a complete candidate set.
    Caller must independently verify both lists share the intended source frame.
    """
    if type(max_checks) is not int or not 1 <= max_checks <= 2_000_000:
        raise ValueError('Expected bounded positive integer comparison limit')
    boxes = [_boxes(triangles_a), _boxes(triangles_b)]
    events = sorted((box[0][0], side, i)
                    for side in (0,1) for i, box in enumerate(boxes[side]))
    active, expiry = [{},{}], [[],[]]
    pairs = []
    checks = 0
    for x, side, i in events:
        for s in (0,1):
            while expiry[s] and expiry[s][0][0] < x:
                _, old = heapq.heappop(expiry[s])
                del active[s][old]
        lo, hi = boxes[side][i]
        for j, (other_lo, other_hi) in active[1-side].items():
            checks += 1
            if checks > max_checks:
                raise RuntimeError('Candidate comparison limit reached; no complete result')
            if all(hi[k] >= other_lo[k] and other_hi[k] >= lo[k] for k in (1,2)):
                pairs.append([i,j] if side == 0 else [j,i])
        active[side][i] = (lo,hi)
        heapq.heappush(expiry[side],(hi[0],i))
    return {'triangle_index_pairs': sorted(pairs), 'candidate_comparisons': checks,
            'source_triangle_counts': [len(boxes[0]),len(boxes[1])],
            'supplied_box_enumeration_complete': True,
            'whole_surface_clearance_verified': False,
            'anatomical_contact_accepted': False, 'physical_units_verified': False}
