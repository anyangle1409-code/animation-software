"""Declare the r96 shoulder-yoke topology/weight scope without editing the Blend.

Run in Blender against the exact frozen r95 candidate. The script unions the
existing first-party shoulder, axilla and posterior-lobe masks, restricts that
union to the shoulder/torso/arm regions, closes it through the exact rest-space
mirror map, validates the fail-closed declaration, and writes JSON plus a short
human-readable declaration. It never saves the Blend.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[1]
sys.path.insert(0, str(SCRIPT.parent))
from original_v1_shoulder_yoke_declaration import (  # noqa: E402
    R95_SHA256,
    validate_declaration,
)

BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"
DEFAULT_OUT = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/shoulder_yoke_declared_before_edit.json"
SOURCE_DECLARATIONS = (
    "ORIGINAL_V1_WORK/candidates/repair_preparation/r77_axilla_pit_declared/axilla_pit_mask_declared_before_edit.json",
    "ORIGINAL_V1_WORK/candidates/repair_preparation/r93_clavicle_top_shape_limits_declared/shoulder_corrective_mask_declared_before_solve.json",
    "ORIGINAL_V1_WORK/candidates/repair_preparation/r94_wing_scapula_weight_declared/wing_zone_declared_before_edit.json",
    "ORIGINAL_V1_WORK/candidates/repair_preparation/r95_scapular_lobe_corrective_declared/scapular_lobe_mask_declared_before_solve.json",
)
ISSUES = (
    "WB-AX-001", "WB-PEC-002", "WB-PEC-003", "WB-AX-004",
    "WB-SHO-005", "WB-SHO-006", "WB-CLV-007", "WB-SYM-008",
)
EVIDENCE = (
    "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json",
    "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json",
    "ORIGINAL_V1_WORK/candidates/repair_checks/deformation_layers_r95/deformation_layers_r95.json",
    "ORIGINAL_V1_WORK/candidates/review/milestone_r95/milestone_anatomy_shoulder_1.png",
    "ORIGINAL_V1_WORK/candidates/review/milestone_r95/milestone_anatomy_shoulder_2.png",
    "ORIGINAL_V1_WORK/candidates/review/milestone_r95/milestone_press_top_three_quarter.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def output_path() -> Path:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return Path(args[0]).resolve() if args else DEFAULT_OUT.resolve()


def main() -> int:
    out = output_path()
    markdown = out.with_name("DECLARATION.md")
    if out.exists() or markdown.exists():
        raise SystemExit("refusing to overwrite an existing r96 declaration")

    candidate = Path(bpy.data.filepath).resolve()
    candidate_sha = sha256(candidate)
    if candidate_sha != R95_SHA256:
        raise SystemExit("exact frozen r95 candidate required: " + candidate_sha)
    scene = bpy.context.scene
    if scene.get("hgpt_candidate") != "O4_bind" or not scene.get("hgpt_not_production"):
        raise SystemExit("expected a non-production O4_bind candidate")
    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or body.type != "MESH" or rig is None or rig.type != "ARMATURE":
        raise SystemExit("frozen r95 body or rig is missing")
    if len(rig.data.bones) != 67:
        raise SystemExit("expected the locked r95 rev2c rig with 67 bones")

    names = json.loads(scene["hgpt_region_names"])
    region_attr = body.data.attributes.get("hgpt_region")
    if region_attr is None or region_attr.domain != "POINT":
        raise SystemExit("body has no point-domain hgpt_region attribute")
    regions = [names[item.value] for item in region_attr.data]
    rest = np.asarray([vertex.co[:] for vertex in body.data.vertices], dtype=float)
    count = len(rest)
    key = {tuple(np.round(rest[index], 5)): index for index in range(count)}
    mirror = np.asarray([
        key[tuple(np.round(rest[index] * (-1, 1, 1), 5))]
        for index in range(count)
    ], dtype=int)
    if len(set(int(item) for item in mirror)) != count or not np.all(mirror[mirror] == np.arange(count)):
        raise SystemExit("rest-space mirror map is not a complete involution")

    selected: set[int] = set()
    sources = []
    for relative in SOURCE_DECLARATIONS:
        path = ROOT / relative
        record = read_json(relative)
        ids = set(int(item) for item in record.get("left_owned_vertex_ids", []))
        ids.update(int(item) for item in record.get("mirror_of_strict_left_vertex_ids", []))
        if any(item < 0 or item >= count for item in ids):
            raise SystemExit("source declaration has an out-of-range vertex: " + relative)
        selected.update(ids)
        sources.append({"path": relative, "sha256": sha256(path), "vertex_count": len(ids)})

    allowed_regions = {"shoulder", "torso", "arm"}
    selected = {item for item in selected if regions[item] in allowed_regions}
    # Exact mirror closure is authoritative; retain one left-owned member for
    # each pair and reconstruct the right side from the frozen rest mesh.
    left = sorted(item for item in selected if rest[item, 0] < -1e-8)
    right = [int(mirror[item]) for item in left]
    if not left or len(set(right)) != len(right) or any(rest[item, 0] <= 1e-8 for item in right):
        raise SystemExit("declared shoulder-yoke zone is not strict mirror-closed")

    declaration = {
        "schema_version": 1,
        "declared_utc": datetime.now(timezone.utc).isoformat(),
        "declared_before_edit": True,
        "target_revision": "r96",
        "parent": {
            "revision": "r95",
            "candidate_path": "ORIGINAL_V1_WORK/candidates/" + candidate.name,
            "sha256": candidate_sha,
        },
        "issue_ids": list(ISSUES),
        "evidence_paths": list(EVIDENCE),
        "selection_rule": "mirror-closed union of the committed r77 anterior-axilla, r93 shoulder-yoke, r94 posterior-wing and r95 posterior-lobe zones, restricted to shoulder/torso/arm skin",
        "selection_sources": sources,
        "zone": {
            "left_vertex_ids": left,
            "right_vertex_ids": right,
            "mirror_pairs": [[a, b] for a, b in zip(left, right)],
            "maximum_existing_vertex_count": len(left) + len(right),
            "permitted_regions": sorted(allowed_regions),
            "rest_bbox_min_m": [round(float(value), 6) for value in rest[left].min(axis=0)],
            "rest_bbox_max_m": [round(float(value), 6) for value in rest[left].max(axis=0)],
        },
        "permitted_bones": [
            "clavicle_l", "clavicle_r", "scapula_l", "scapula_r",
            "upperarm_l", "upperarm_r", "spine_02", "spine_03",
        ],
        "topology_intent": {
            "operation": "local_support_loops",
            "anatomical_support": ["anterior_axillary_fold", "posterior_axillary_fold", "deltoid_pectoral_transition", "thoracic_wall_transition"],
            "maximum_new_vertices": 480,
            "maximum_new_faces": 960,
            "preserve_original_vertex_ids": True,
            "preserve_quads": True,
            "preserve_outward_normals": True,
            "broad_remesh_forbidden": True,
        },
        "weight_intent": {
            "scope": "declared_zone_only",
            "maximum_influences": 4,
            "normalized": True,
            "mirror_symmetric": True,
            "new_influences_forbidden": True,
            "weights_only_gate_precedes_correctives": True,
        },
        "protected_zones": ["neck_boundary", "pelvis_boundary", "hands", "feet", "head", "clothing", "frozen_correctives"],
        "invariants": {
            "rig_bones": 67,
            "candidate_parent_immutable": True,
            "p3b1_baseline_unchanged": True,
            "thresholds_unchanged": True,
            "production_approved": False,
        },
        "stop_conditions": ["parent_identity_mismatch", "out_of_scope_edit", "critical_or_high_defect", "material_regression"],
    }
    errors = validate_declaration(declaration, ROOT)
    if errors:
        raise SystemExit("invalid r96 declaration: " + "; ".join(errors))

    out.parent.mkdir(parents=True, exist_ok=False)
    out.write_text(json.dumps(declaration, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# r96 shoulder-yoke declaration\n\n"
        "Declared before any model edit from exact frozen r95.\n\n"
        f"- Parent SHA-256: `{candidate_sha}`\n"
        f"- Existing scoped vertices: {len(left) + len(right)} ({len(left)} mirrored pairs)\n"
        "- Permitted work: local support loops and normalized mirror-symmetric weights using only the declared bones\n"
        "- Correctives: retained but disabled for the weights-only gate; no refit is authorized by this declaration\n"
        "- Stop on identity mismatch, out-of-scope edit, any Critical/High anatomical defect, or material regression\n"
        "- Production approval remains false\n",
        encoding="utf-8",
    )
    print("R96 SHOULDER-YOKE SCOPE DECLARED", out, len(left) + len(right), "vertices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
