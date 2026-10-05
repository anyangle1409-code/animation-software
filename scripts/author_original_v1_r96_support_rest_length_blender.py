"""Author one declared support-row rest-length probe on the exact topology parent."""
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
from original_v1_shoulder_yoke_rest_length import (  # noqa: E402
    R95_SHA256,
    TOPOLOGY_PARENT_SHA256,
    build_mirrored_normal_offsets,
    validate_rest_length_declaration,
)


DECLARATION = ROOT / "ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/r96_support_rest_length_declared_before_edit.json"
BODY_NAME = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
RIG_NAME = "HGPT_CANONICAL_V4_ORIGINAL"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 2:
        raise SystemExit("usage: -- <strength_m> <new_candidate.blend>")
    strength = float(args[0])
    out = Path(args[1]).resolve()
    receipt = out.with_suffix(".json")
    if out.exists() or receipt.exists():
        raise SystemExit("refusing to overwrite an r96 rest-length probe")

    source = Path(bpy.data.filepath).resolve()
    if digest(source) != TOPOLOGY_PARENT_SHA256:
        raise SystemExit("exact declared topology parent required")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8-sig"))
    errors = validate_rest_length_declaration(declaration)
    if errors:
        raise SystemExit("invalid rest-length declaration: " + "; ".join(errors))
    if strength not in [float(value) for value in declaration["probe_strengths_m"]]:
        raise SystemExit("strength is outside the declared probe family")

    body = bpy.data.objects.get(BODY_NAME)
    rig = bpy.data.objects.get(RIG_NAME)
    if body is None or rig is None or len(rig.data.bones) != 67:
        raise SystemExit("frozen body or 67-bone rig is missing")
    mesh = body.data
    if mesh.shape_keys is None or len(mesh.shape_keys.key_blocks) != 7:
        raise SystemExit("expected Basis plus six retained corrective keys")
    mesh.update()

    keys = list(mesh.shape_keys.key_blocks)
    before = {
        key.name: np.asarray([point.co[:] for point in key.data], dtype=float)
        for key in keys
    }
    rest = before[mesh.shape_keys.reference_key.name]
    normals = np.asarray([vertex.normal[:] for vertex in mesh.vertices], dtype=float)
    pairs = [tuple(int(value) for value in pair) for pair in declaration["mirror_pairs"]]
    offsets = build_mirrored_normal_offsets(rest, normals, pairs, strength=strength)
    selected = np.flatnonzero(np.linalg.norm(offsets, axis=1) > 0.0)
    declared_ids = {int(value) for value in declaration["new_support_vertex_ids"]}
    if not set(selected).issubset(declared_ids) or not len(selected):
        raise SystemExit("computed offset field escaped or missed the declared support vertices")

    for key in keys:
        for vertex_id in selected:
            key.data[int(vertex_id)].co = before[key.name][vertex_id] + offsets[vertex_id]
    mesh.update()

    after = {
        key.name: np.asarray([point.co[:] for point in key.data], dtype=float)
        for key in keys
    }
    selected_mask = np.zeros(len(mesh.vertices), dtype=bool)
    selected_mask[selected] = True
    outside_max_change = max(
        float(np.abs(after[key.name][~selected_mask] - before[key.name][~selected_mask]).max())
        for key in keys
    )
    basis_name = mesh.shape_keys.reference_key.name
    basis_delta = after[basis_name] - before[basis_name]
    maximum_displacement = float(np.linalg.norm(basis_delta, axis=1).max())
    relative_shape_delta_error = max(
        float(np.abs((after[key.name] - after[basis_name]) - (before[key.name] - before[basis_name])).max())
        for key in keys
    )
    mirror_error = 0.0
    for left, right in pairs:
        mirror_error = max(
            mirror_error,
            float(np.abs(basis_delta[right] - basis_delta[left] * [-1.0, 1.0, 1.0]).max()),
        )
    if outside_max_change != 0.0 or relative_shape_delta_error > 1.0e-6 or mirror_error > 1.0e-6:
        raise SystemExit("rest-length probe violated the geometry preservation contract")
    if maximum_displacement > strength + 1.0e-6:
        raise SystemExit("rest-length probe exceeded its declared displacement")

    scene = bpy.context.scene
    scene["hgpt_candidate_revision"] = out.stem
    scene["hgpt_candidate_parent_sha256"] = TOPOLOGY_PARENT_SHA256
    scene["hgpt_rest_length_probe_strength_m"] = strength
    bpy.ops.wm.save_as_mainfile(filepath=str(out), copy=True)
    record = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "r96 declared support-row rest-length probe; not production",
        "source_candidate": source.name,
        "source_sha256": TOPOLOGY_PARENT_SHA256,
        "lineage_parent_r95_sha256": R95_SHA256,
        "declaration": DECLARATION.relative_to(ROOT).as_posix(),
        "declaration_sha256": digest(DECLARATION),
        "strength_m": strength,
        "candidate": out.name,
        "candidate_sha256": digest(out),
        "selected_new_vertices": [int(value) for value in selected],
        "selected_vertex_count": int(len(selected)),
        "maximum_displacement_m": maximum_displacement,
        "outside_selected_shape_point_max_change": outside_max_change,
        "relative_shape_delta_max_error": relative_shape_delta_error,
        "mirror_delta_max_error": mirror_error,
        "vertex_count": len(mesh.vertices),
        "face_count": len(mesh.polygons),
        "rig_bones": len(rig.data.bones),
        "correctives_retained": True,
        "correctives_disabled_during_gate": True,
        "production_approved": False,
    }
    receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("R96 REST-LENGTH PROBE", json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
