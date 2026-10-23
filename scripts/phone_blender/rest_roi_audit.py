"""Read-only sample of rest-mesh weights and shape-key deltas near 5cm hotspots.

No bpy import, operators, or saving. Side names refer to signed body-object X,
not verified anatomical left/right. Shape-key deltas are not driven activation.
"""
import math
from collections import defaultdict, Counter

SIDE_LENGTH = 0.05
ROI_CENTRES = {
    "press_posterior_posX_high": (0.125, 0.175, 1.475),
    "press_posterior_negX_high": (-0.125, 0.175, 1.475),
    "press_posterior_posX_low": (0.125, 0.175, 1.425),
    "press_posterior_negX_low": (-0.125, 0.175, 1.425),
    "press_clav_neck_negX": (-0.075, 0.125, 1.575),
    "press_clav_neck_posX": (0.175, 0.075, 1.575),
}

def vector(v):
    xyz = tuple(float(c) for c in v)
    if len(xyz) != 3 or not all(math.isfinite(c) for c in xyz):
        raise ValueError("nonfinite or invalid three-dimensional coordinate")
    return xyz

def analyze(body):
    mesh = body.data
    if mesh.shape_keys is None or not mesh.shape_keys.key_blocks:
        raise ValueError("missing shape-key block inventory")
    keys = mesh.shape_keys.key_blocks
    basis = keys[0]
    if len(basis.data) != len(mesh.vertices):
        raise ValueError("Basis shape key does not match mesh topology")
    group_names = {g.index: g.name for g in body.vertex_groups}
    selected = {name: [] for name in ROI_CENTRES}
    for v in mesh.vertices:
        xyz = vector(v.co)
        for name, centre in ROI_CENTRES.items():
            if all(abs(a - b) < SIDE_LENGTH / 2.0 for a, b in zip(xyz, centre)):
                selected[name].append(v.index)
    cells = []
    for name, centre in ROI_CENTRES.items():
        indices = selected[name]
        n = len(indices)
        group_sum = defaultdict(float)
        dominant = Counter()
        totals = []
        for i in indices:
            weights = []
            for assignment in mesh.vertices[i].groups:
                weight = float(assignment.weight)
                if not math.isfinite(weight) or weight < 0 or assignment.group not in group_names:
                    raise ValueError(f"{name}: invalid group or influence")
                if weight > 0:
                    group_sum[group_names[assignment.group]] += weight
                    weights.append((group_names[assignment.group], weight))
            totals.append(sum(w for _, w in weights))
            if weights:
                dominant[max(weights, key=lambda x: (x[1], x[0]))[0]] += 1
        influence_groups = sorted(group_sum, key=lambda g: (-group_sum[g], g))
        shape_keys = []
        for key in keys[1:]:
            if len(key.data) != len(mesh.vertices):
                raise ValueError(f"{name}: shape key {key.name} mismatches mesh topology")
            deltas = []
            for i in indices:
                baseline = vector(basis.data[i].co)
                location = vector(key.data[i].co)
                deltas.append(1000 * math.dist(baseline, location))
            shape_keys.append({
                "name": key.name,
                "relative_key_name": key.relative_key.name if getattr(key, "relative_key", None) else None,
                "saved_key_value": round(float(key.value), 6),
                "mean_absolute_delta_from_basis_mm": round(sum(deltas) / n, 4) if n else None,
                "maximum_absolute_delta_from_basis_mm": round(max(deltas), 4) if n else None,
            })
        shape_keys.sort(key=lambda k: (
            -1 if k["mean_absolute_delta_from_basis_mm"] is None else -k["mean_absolute_delta_from_basis_mm"], k["name"]
        ))
        cells.append({
            "name": name, "centre_body_local_m": list(centre), "cube_side_m": SIDE_LENGTH,
            "sampled_vertices": n, "warning": "FEWER_THAN_10_VERTICES" if n < 10 else None,
            "mean_total_skin_weight": round(sum(totals) / n, 5) if n else None,
            "min_total_skin_weight": round(min(totals), 5) if n else None,
            "unweighted_sample_vertices": sum(w <= 0 for w in totals),
            "top_influence_group_means": [
                {"name": g, "mean_weight_per_sample_vertex": round(group_sum[g] / n, 5)}
                for g in influence_groups[:12]
            ] if n else [],
            "dominant_group_vertex_counts": [
                {"name": g, "vertices": c} for g, c in dominant.most_common(12)
            ],
            "largest_stored_shape_key_deltas": shape_keys[:15],
        })
    return {
        "status": "READ_ONLY_REST_MESH_PROBE_NOT_ANATOMICAL_APPROVAL",
        "body_object": body.name, "mesh_vertices": len(mesh.vertices),
        "shape_key_count": len(keys), "vertex_group_count": len(body.vertex_groups),
        "roi_reference": "Saved W8 75% shoulder press triangle-hotspot rest-space centres, 5cm cubes",
        "limitations": [
            "Mesh-coordinates and native pose snapshot rest frames must be cross-checked before treating cell locations as equivalent",
            "Coordinates are object local; positive/negative X do not certify anatomical left/right",
            "Dominant skin group / shape-key deltas do not prove deformation cause, activation or attachment",
            "Shape-key deltas are absolute from Basis, not evaluated driven response at press sample6",
            "Different topologies prevent cross-model vertex-count comparison as a quality score",
        ],
        "regions": cells,
    }
