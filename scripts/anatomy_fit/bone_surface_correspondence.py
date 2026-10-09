"""Coarse spatial sanity checks between a bone mesh and a skeletal control.

This module deliberately DOES NOT infer anatomical correspondence by accepting
user-supplied anchor coordinates. It checks transformed MESH VERTICES against
skeleton geometry and enforces coarse dimension/side safeguards.

Controls here are coarse engineering guards, NOT medical registration criteria.
They can reject grossly implausible geometries, but cannot prove a correct
bone type, shape, CT fit, landmark, muscle attachment or articular congruence.
"""
import math

BASIS = 'HGPT_LEFT_PLUS_X_POSTERIOR_PLUS_Y_SUPERIOR_PLUS_Z'


def _point_segment_distance(p, a, b):
    d = [b[k] - a[k] for k in range(3)]
    dd = sum(t*t for t in d)
    if dd == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, sum((p[k] - a[k])*d[k] for k in range(3)) / dd))
    return math.dist(p, [a[k] + t*d[k] for k in range(3)])


def check(asset, bone_record, world_vertices, basis=BASIS):
    """Reject remote, wrong-side or implausibly tiny geometry.

    The control's head/tail are registration references, NOT necessarily
    physical articular surface endpoints. These loose geometry thresholds are
    diagnostic, never sufficient for canonical shape acceptance.
    """
    if basis != BASIS:
        raise ValueError('unsupported world basis for spatial registration')
    a = bone_record['head_m']
    b = bone_record['tail_m']
    control_len = math.dist(a, b)
    if not control_len > 1e-6:
        raise ValueError('zero-length control needs independent shape profile')

    xs = [v[0] for v in world_vertices]
    ys = [v[1] for v in world_vertices]
    zs = [v[2] for v in world_vertices]
    box_diag = math.dist(
        [min(xs), min(ys), min(zs)],
        [max(xs), max(ys), max(zs)],
    )
    relative_size = box_diag / control_len
    # Reject wildly small/large proxies without claiming a medical range.
    if relative_size < 0.15:
        raise ValueError('mesh spatial extent is implausibly small versus control length')
    if relative_size > 6:
        raise ValueError('mesh spatial extent is implausibly large versus control length')

    min_head = min(math.dist(v, a) for v in world_vertices)
    min_tail = min(math.dist(v, b) for v in world_vertices)
    # Account for controls that point into the interior of articular volumes.
    # This allows substantial natural bow/offset but catches metre-scale swaps.
    cap = max(0.06, control_len * 0.3)
    if min_head > cap or min_tail > cap:
        raise ValueError('bone mesh is spatially detached from skeleton control endpoints')

    min_axis = min(_point_segment_distance(v, a, b) for v in world_vertices)
    if min_axis > cap:
        raise ValueError('bone mesh has no spatial correspondence to control axis')

    bone_id = asset['bone_id']
    # This test is valid ONLY for explicit, left/right paired bone IDs under
    # the project's left-positive-X basis. A paired shape can intersect the
    # midline but the bulk should remain on its named side.
    side = 'left' if bone_id.endswith('_left') else 'right' if bone_id.endswith('_right') else None
    centre_x = sum(xs) / len(xs)
    # Ignore paired controls too close to the midsagittal plane to have a
    # defensible side-specific shape footprint.
    centre_control_x = (a[0] + b[0]) / 2
    min_separation = max(0.005, control_len * 0.02)
    if side and abs(centre_control_x) > min_separation:
        if (side == 'left' and centre_x < -min_separation or
                side == 'right' and centre_x > min_separation):
            raise ValueError('mesh is on opposite anatomical side from its bone ID')

    return {
        'spatial_registration': 'COARSE_ONLY_NOT_ANATOMY',
        'mesh_bbox_diagonal_m': box_diag,
        'mesh_to_control_length_ratio': relative_size,
        'closest_mesh_vertex_to_head_mm': min_head * 1000,
        'closest_mesh_vertex_to_tail_mm': min_tail * 1000,
        'closest_mesh_vertex_to_axis_mm': min_axis * 1000,
        'world_centroid_x_m': centre_x,
        'side_checked': side is not None and abs(centre_control_x) > min_separation,
        'bone_identity_verified': False,
        'anatomical_landmarks_verified': False,
        'shape_registration_verified': False,
    }
