"""Read-only deform-bone weight and driver audit for the declared r96 zone."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import bpy


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_declaration import R95_SHA256, validate_declaration  # noqa: E402
from original_v1_shoulder_yoke_weights import (  # noqa: E402
    classify_vertex,
    compare_mirror_rows,
    edge_l1,
    normalise_deform_row,
)

DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/shoulder_yoke_declared_before_edit.json"
DEFAULT_OUT = DECLARATION.with_name("r95_declared_zone_weight_audit.json")
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = q * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def driver_snapshot(body) -> list[dict]:
    keys = body.data.shape_keys
    animation = keys.animation_data if keys else None
    rows = []
    for curve in animation.drivers if animation else []:
        if "HGPT_SHOULDER" not in curve.data_path:
            continue
        variables = []
        for variable in curve.driver.variables:
            variables.append({
                "name": variable.name,
                "type": variable.type,
                "targets": [{"bone_target": target.bone_target, "transform_type": target.transform_type,
                             "transform_space": target.transform_space, "data_path": target.data_path} for target in variable.targets],
            })
        rows.append({"data_path": curve.data_path, "expression": curve.driver.expression, "variables": variables})
    return sorted(rows, key=lambda item: item["data_path"])


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(args[0]).resolve() if args else DEFAULT_OUT.resolve()
    if out.exists():
        raise SystemExit("refusing to overwrite " + str(out))
    candidate = Path(bpy.data.filepath).resolve()
    if digest(candidate) != R95_SHA256:
        raise SystemExit("exact frozen r95 candidate required")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8-sig"))
    errors = validate_declaration(declaration, ROOT)
    if errors:
        raise SystemExit("invalid declaration: " + "; ".join(errors))
    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or rig is None:
        raise SystemExit("frozen body or rig is missing")

    deform = {bone.name for bone in rig.data.bones if bone.use_deform}
    group_names = {group.index: group.name for group in body.vertex_groups}
    rows = []
    for vertex in body.data.vertices:
        raw = {group_names[item.group]: float(item.weight) for item in vertex.groups if item.group in group_names}
        rows.append(normalise_deform_row(raw, deform))

    zone = declaration["zone"]
    left = zone["left_vertex_ids"]
    right = zone["right_vertex_ids"]
    permitted = set(declaration["permitted_bones"])
    classifications = []
    symmetry = []
    unexpected = Counter()
    for left_id, right_id in zip(left, right):
        for vertex_id, side in ((left_id, "l"), (right_id, "r")):
            result = classify_vertex(rows[vertex_id], side)
            for bone in set(rows[vertex_id]) - permitted:
                unexpected[bone] += 1
            if result["cross_side_bones"] or result["excessive_single_bone_dominance"] or result["missing_shared_influence"]:
                classifications.append({"vertex_id": vertex_id, "side": side, **result, "weights": rows[vertex_id]})
        symmetry.append({"left_vertex_id": left_id, "right_vertex_id": right_id, **compare_mirror_rows(rows[left_id], rows[right_id])})

    declared = set(left) | set(right)
    gradients = []
    for edge in body.data.edges:
        a, b = (int(edge.vertices[0]), int(edge.vertices[1]))
        if a not in declared and b not in declared:
            continue
        gradients.append({"vertices": [a, b], "both_declared": a in declared and b in declared, "l1": edge_l1(rows[a], rows[b])})
    gradients.sort(key=lambda item: (-item["l1"], item["vertices"]))
    symmetry_errors = [row["l1_error"] for row in symmetry]

    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_revision": "r95",
        "candidate_sha256": digest(candidate),
        "declaration": DECLARATION.relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(DECLARATION),
        "read_only": True,
        "deform_bone_count": len(deform),
        "declared_vertex_count": len(declared),
        "mirror_pair_count": len(symmetry),
        "driver_snapshot": driver_snapshot(body),
        "findings": {
            "cross_side_vertex_count": sum(bool(row["cross_side_bones"]) for row in classifications),
            "excessive_single_bone_vertex_count": sum(row["excessive_single_bone_dominance"] for row in classifications),
            "missing_shared_influence_vertex_count": sum(row["missing_shared_influence"] for row in classifications),
            "unexpected_existing_bones": dict(sorted(unexpected.items())),
            "mirror_l1_mean": statistics.fmean(symmetry_errors) if symmetry_errors else 0.0,
            "mirror_l1_p99": percentile(symmetry_errors, 0.99),
            "mirror_l1_max": max(symmetry_errors, default=0.0),
            "declared_edge_l1_p95": percentile([row["l1"] for row in gradients], 0.95),
            "declared_edge_l1_p99": percentile([row["l1"] for row in gradients], 0.99),
            "declared_edge_l1_max": max((row["l1"] for row in gradients), default=0.0),
        },
        "flagged_vertices": classifications,
        "worst_mirror_pairs": sorted(symmetry, key=lambda item: (-item["l1_error"], item["left_vertex_id"]))[:100],
        "worst_declared_edges": gradients[:100],
        "interpretation_boundary": "Diagnostics identify candidate weight discontinuities and scope; anatomical review across motion remains mandatory.",
        "production_approved": False,
    }
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("R96 DECLARED-ZONE WEIGHT AUDIT", out, json.dumps(report["findings"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
