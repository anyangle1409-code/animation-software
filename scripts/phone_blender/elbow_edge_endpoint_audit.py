"""Read-only W8 skin-weight and stored-shape-key evidence at pinned mesh edges.

Source: independently SHA256-verified ranked W8 elbow-edge report from
GitHub Actions run 40060680693, native artifact 12547635497.
Edge IDs are reconstructed W8 mesh IDs, NOT anatomical landmarks or sides.
No pose, operator, model write, or anatomical approval is performed.
"""
import math

W8_SHA256 = "2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c"
TARGETS = (
    ("distal_suffix_l_press_sample0_min", (15645, 53019), 0, 0.167612),
    ("distal_suffix_r_press_sample0_min", (17185, 44317), 0, 0.163126),
    ("middle_suffix_l_press_sample6_max", (29237, 71026), 6, 2.673372),
    ("middle_suffix_r_press_sample6_max", (32352, 71428), 6, 2.648593),
)
STATUS = "READ_ONLY_W8_EDGE_ENDPOINT_METADATA_NOT_ANATOMICAL_APPROVAL"


def xyz(value):
    p = tuple(float(x) for x in value)
    if len(p) != 3 or not all(math.isfinite(x) for x in p):
        raise ValueError("nonfinite or invalid coordinate")
    return p


def distance(a, b):
    return math.dist(a, b)


def weights(vertex, group_names):
    result = {}
    for assignment in vertex.groups:
        index, value = int(assignment.group), float(assignment.weight)
        if index not in group_names or not math.isfinite(value) or value < 0:
            raise ValueError("invalid skin group or weight")
        if index in result:
            raise ValueError("duplicate vertex group assignment")
        if value > 0:
            result[index] = value
    if not result:
        raise ValueError("unweighted pinned endpoint")
    return result


def analyze(body, source_sha256, targets=TARGETS):
    if source_sha256 != W8_SHA256:
        raise ValueError("source is not the immutable W8 reconstruction")
    mesh = body.data
    vertices = mesh.vertices
    shape_keys = getattr(mesh, "shape_keys", None)
    if shape_keys is None or not shape_keys.key_blocks:
        raise ValueError("missing shape-key evidence")
    keys = shape_keys.key_blocks
    if len(keys[0].data) != len(vertices):
        raise ValueError("Basis topology mismatch")
    group_names = {}
    for group in body.vertex_groups:
        if group.index in group_names:
            raise ValueError("duplicate group index")
        group_names[group.index] = group.name
    if len(set(group_names.values())) != len(group_names):
        raise ValueError("duplicate group name")
    edge_set = set()
    names = set()
    for name, pair, sample, saved_ratio in targets:
        a, b = pair
        if (not isinstance(name, str) or not name or name in names
                or not isinstance(a, int) or not isinstance(b, int)
                or a == b or a < 0 or b < 0 or a >= len(vertices) or b >= len(vertices)
                or not isinstance(sample, int) or sample < 0
                or not math.isfinite(float(saved_ratio)) or saved_ratio <= 0):
            raise ValueError("invalid pinned edge record")
        names.add(name)
        edge_set.add(tuple(sorted(pair)))
    observed = set()
    for tri in mesh.loop_triangles:
        ids = tuple(int(x) for x in tri.vertices)
        if len(ids) != 3 or len(set(ids)) != 3 or min(ids) < 0 or max(ids) >= len(vertices):
            raise ValueError("invalid triangle topology")
        for i, j in ((0, 1), (1, 2), (2, 0)):
            edge = tuple(sorted((ids[i], ids[j])))
            if edge in edge_set:
                observed.add(edge)
    if observed != edge_set:
        raise ValueError("pinned edge missing from reconstructed W8 triangle topology")
    for key in keys:
        if len(key.data) != len(vertices):
            raise ValueError("shape-key topology mismatch: " + key.name)
    result = []
    for name, (a, b), sample, saved_ratio in targets:
        coords = (xyz(vertices[a].co), xyz(vertices[b].co))
        rest_len = distance(*coords)
        if not math.isfinite(rest_len) or rest_len <= 1e-10:
            raise ValueError("degenerate pinned rest edge")
        assignments = [weights(vertices[i], group_names) for i in (a, b)]
        endpoint_rows = []
        for i, co, w in zip((a, b), coords, assignments):
            endpoint_rows.append({
                "rest_mesh_vertex_id": i,
                "rest_body_local_m": [round(v, 8) for v in co],
                "total_skin_group_weight": round(sum(w.values()), 7),
                "group_weights_descending": [
                    {"group": group_names[g], "weight": round(value, 7)}
                    for g, value in sorted(w.items(), key=lambda p: (-p[1], group_names[p[0]]))
                ],
            })
        union = set(assignments[0]) | set(assignments[1])
        weight_l1 = sum(abs(assignments[0].get(g, 0) - assignments[1].get(g, 0)) for g in union)
        key_rows = []
        for key in keys[1:]:
            basis_a, basis_b = (xyz(keys[0].data[i].co) for i in (a, b))
            key_a, key_b = (xyz(key.data[i].co) for i in (a, b))
            if distance(basis_a, basis_b) <= 1e-10:
                raise ValueError("degenerate Basis edge")
            ratio = distance(key_a, key_b) / distance(basis_a, basis_b)
            max_endpoint_delta = max(distance(basis_a, key_a), distance(basis_b, key_b))
            if not math.isfinite(ratio):
                raise ValueError("nonfinite stored key ratio")
            key_rows.append({
                "key": key.name,
                "relative_key": key.relative_key.name if getattr(key, "relative_key", None) else None,
                "saved_value_not_pose_activation": round(float(key.value), 6),
                "stored_edge_length_ratio_to_Basis": round(ratio, 7),
                "max_endpoint_stored_delta_from_Basis_mm": round(1000 * max_endpoint_delta, 5),
            })
        key_rows.sort(key=lambda r: (-abs(r["stored_edge_length_ratio_to_Basis"] - 1), r["key"]))
        result.append({
            "ranked_report_label_NOT_anatomical_side": name,
            "rest_mesh_edge_vertex_ids": [a, b],
            "reference_press_sample": sample,
            "archived_pose_over_rest_ratio_descriptive": saved_ratio,
            "rest_edge_length_mm": round(1000 * rest_len, 6),
            "endpoints": endpoint_rows,
            "group_weight_L1_difference_not_tissue_strain": round(weight_l1, 7),
            "shared_positive_weight_group_count": len(set(assignments[0]) & set(assignments[1])),
            "top_stored_shape_keys_by_absolute_edge_ratio_change": key_rows[:12],
        })
    return {
        "status": STATUS, "source_sha256": source_sha256,
        "body_object": body.name, "mesh_vertices": len(vertices),
        "shape_key_count": len(keys), "target_edge_count": len(result),
        "anatomical_side_verified": False, "joint_axes_ISB_calibrated": False,
        "muscle_attachment_approved": False, "skin_deformation_validated": False,
        "source_ranked_report": "run40060680693 artifact12547635497 w8_elbow_edge_continuity.json",
        "limitations": [
            "Vertex IDs and l/r suffixes are authored W8 labels, not anatomical side certification",
            "Archived press ratios are historical geometry; this script does not evaluate a pose",
            "Stored shape-key geometry does not establish whether a key activates during press",
            "Group weights and their differences do not diagnose causality or muscle anatomy",
            "No elbow flexion/forearm rotation or generic human movement test is approved",
        ],
        "edges": result,
    }


def markdown(report):
    rows = [
        "# W8 ranked elbow-region edge endpoints — read-only",
        "",
        "**ANATOMY AND SKIN NOT APPROVED.** Stored rest weights and shape-key geometry only.",
        "",
        "| Ranked edge | Vertex IDs | Rest length (mm) | Weight L1 difference | Top stored key |",
        "|---|---|---:|---:|---|",
    ]
    for edge in report["edges"]:
        key = edge["top_stored_shape_keys_by_absolute_edge_ratio_change"]
        rows.append("| {} | {} | {} | {} | {} |".format(
            edge["ranked_report_label_NOT_anatomical_side"],
            ",".join(map(str, edge["rest_mesh_edge_vertex_ids"])),
            edge["rest_edge_length_mm"],
            edge["group_weight_L1_difference_not_tissue_strain"],
            key[0]["key"] if key else "(none)"))
    rows += ["", "No native movement was executed; no model or source modified.",
             "Saved shape-key values are not sampled activation. ROM means are not limits.", ""]
    return "\n".join(rows)
