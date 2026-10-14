#!/usr/bin/env python3
"""ORIGINAL_v1 consolidated review candidate R1 (Claude, 14 Oct 2026): one isolated, reversible review blend.

Parent: foot candidate C5 (C3 280 mm foot skeleton + C4 toes/ball breadth + C5 heel contact; a003 elsewhere).  Adds, each
independently verified on its own branch/PR and NONE accepted:
  * W3 option A shoulder helper (69 deforming joints), stateless reference drive, transfer 0.6, 4 smoothing passes,
    4-ring edge taper, zone z > 1.22 m (docs/CLAUDE_W3A_HELPER_DEFORMER_FEASIBILITY_20261014.md);
  * K1 hinge contact keys: knee at 90/110/130 deg (hard projection), elbow ONLY at 90/110 deg (its 120/140 keys pinched
    the elbow tip / were over-constrained: rejected) (docs/CLAUDE_K1_KNEE_CONTACT_CORRECTIVE_20261013.md).
Motion-side corrections (H1 4 deg arm carriage, H2 solved thumb opposition, P4 families) live in the benchmark/sequence
scripts, not in the blend.  Rejected trials (C3W, hip-fold K1, helper rotation/swing drives, elbow 120/140 keys) are kept
out.  The blend stores the helper vertex groups/weights and reference vectors but not the two helper bones, so it stays a
67-bone rig for the shared bridge guard; scripts/original_v1_review_candidate_drives.py install_helpers() recreates them
(69 joints, in memory) and drive() poses the helpers and keys.  Basis mesh, legacy keys, the 67 original bones and all weights outside the helper zone stay as in C5.

  python3.13 build_original_consolidated_review_candidate_blender.py --blend C5.blend --expect-sha SHA --out R1.blend --report JSON
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

ELBOW_KEYS = (90, 110)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fingerprint(body, rig, deform_only=True):
    me = body.data
    return {
        "basis": [tuple(round(c, 7) for c in v.co) for v in me.vertices],
        "faces": [tuple(p.vertices) for p in me.polygons],
        "legacy_keys": {kb.name: [tuple(round(c, 7) for c in d.co) for d in kb.data] for kb in me.shape_keys.key_blocks[1:]
                        if not kb.name.startswith("HGPT_K1_")},
        "bones": {b.name: [tuple(round(x, 7) for x in row) for row in b.matrix_local] for b in rig.data.bones
                  if not b.name.startswith("deltoid_helper")},
    }


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    for a in ("--blend", "--expect-sha", "--out", "--report"):
        ap.add_argument(a, required=True)
    o = ap.parse_args(argv)
    if Path(o.out).exists():
        raise FileExistsError(o.out)
    parent_sha = sha(o.blend)
    if parent_sha != o.expect_sha:
        raise SystemExit(f"parent SHA mismatch {parent_sha}")
    bpy.ops.wm.open_mainfile(filepath=str(Path(o.blend).resolve()))
    import build_functional_shoulder_correction_blender as correction
    import build_functional_original_attachment_blender as attachment
    import diagnose_shoulder_helper_deformer_blender as w3a
    import build_original_knee_contact_corrective_blender as k1

    result = correction.build_corrected_scene()
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    before = fingerprint(body, rig)
    names = {g.index: g.name for g in body.vertex_groups}
    weights0 = [{names[g.group]: round(g.weight, 6) for g in v.groups} for v in body.data.vertices]

    zone = set(w3a.zone_vertices(body, rig))                 # before the transfer (it lowers girdle/upper-arm weights)
    if w3a.DRIVE != "reference":
        raise RuntimeError("R1 uses the stateless reference drive")
    helper_info = w3a.add_helpers(result)
    for s in ("l", "r"):
        rig[f"hgpt_w3a_ref_{s}"] = list(w3a._REF[s])
    k1_logs = {"knee": k1.build(result, "knee")}
    saved = k1.HINGES["elbow"]["keys"]
    k1.HINGES["elbow"]["keys"] = ELBOW_KEYS
    try:
        k1_logs["elbow"] = k1.build(result, "elbow")
    finally:
        k1.HINGES["elbow"]["keys"] = saved

    # remove the temporary guide objects and the helper BONES (their vertex groups, weights and the reference vectors stay;
    # scripts/original_v1_review_candidate_drives.py install_helpers() recreates the bones), rest pose, keys at 0
    attachment._remove_previous()
    import original_v1_review_candidate_drives as drives
    if abs(drives.HELPER_LENGTH - w3a.HELPER_LENGTH) > 1e-12:
        raise RuntimeError("helper geometry mismatch between builder and drives")
    view = bpy.context.view_layer
    for ob in view.objects:
        ob.select_set(False)
    view.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in ("l", "r"):
        rig.data.edit_bones.remove(rig.data.edit_bones[f"deltoid_helper_{s}"])
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bpy.context.view_layer.update()
    after = fingerprint(body, rig)
    names = {g.index: g.name for g in body.vertex_groups}
    weights1 = [{names[g.group]: round(g.weight, 6) for g in v.groups} for v in body.data.vertices]
    changed_w = [i for i, (a, b) in enumerate(zip(weights0, weights1)) if a != b]
    checks = {
        "basis_faces_legacy_keys_unchanged": all(before[k] == after[k] for k in ("basis", "faces", "legacy_keys")),
        "original_67_bone_rests_unchanged": before["bones"] == after["bones"],
        "deforming_joints_saved": sum(b.use_deform for b in rig.data.bones),
        "helper_vertex_groups": sorted(g.name for g in body.vertex_groups if g.name.startswith("deltoid_helper")),
        "weights_changed_only_in_helper_zone": all(i in zone for i in changed_w),
        "vertices_with_changed_weights": len(changed_w),
        "max_influences": max(sum(1 for g in v.groups if g.weight > 0) for v in body.data.vertices),
        "k1_keys": sorted(kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_K1_")),
        "guide_objects_left": [o.name for o in bpy.data.objects if o.name.endswith("_TMP")],
    }
    ok = (checks["basis_faces_legacy_keys_unchanged"] and checks["original_67_bone_rests_unchanged"]
          and checks["deforming_joints_saved"] == 67 and len(checks["helper_vertex_groups"]) == 2
          and checks["weights_changed_only_in_helper_zone"]
          and checks["max_influences"] <= 4 and len(checks["k1_keys"]) == 2 * (3 + len(ELBOW_KEYS))
          and not checks["guide_objects_left"])
    checks["verdict"] = "PASS" if ok else "FAIL"
    scene = bpy.context.scene
    scene["hgpt_review_candidate"] = "ORIGINAL_V1_CONSOLIDATED_REVIEW_R1_CLAUDE"
    scene["hgpt_review_candidate_approved"] = False
    scene["hgpt_review_candidate_drives"] = "scripts/original_v1_review_candidate_drives.py: drive(rig, body) after every pose"
    rep = {"schema_version": 1, "candidate": "ORIGINAL_V1_CONSOLIDATED_REVIEW_R1_CLAUDE", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED",
           "parent": {"path": Path(o.blend).name, "sha256": parent_sha},
           "contents": {"feet": "C5 (C3 skeleton 279.9 mm, C4 toes/ball 104.1 mm, C5 heel contact)",
                        "shoulder": {"w3a_helper": helper_info, "drive": "reference (stateless)", "transfer": w3a.TRANSFER,
                                     "smooth_passes": w3a.SMOOTH_PASSES, "edge_rings": w3a.EDGE_RINGS, "zone_z_m": w3a.ZONE_Z},
                        "k1": {"knee_keys_deg": list(k1.HINGES["knee"]["keys"]), "elbow_keys_deg": list(ELBOW_KEYS),
                               "solve_logs": k1_logs},
                        "motion_side": ["H1 arm carriage 4 deg", "H2 solved thumb opposition", "P4 families"]},
           "excluded_rejected": ["C3W toe crumple", "K1 hip fold", "W3A rotation/swing drives", "K1 elbow 120/140 keys"],
           "runtime_contract": "69 deforming joints + reference-branch helper drive + K1 driven morphs: owner + Lane G decision required",
           "checks": checks}
    print(json.dumps({k: v for k, v in rep.items() if k != "contents"}, indent=1, default=str))
    if not ok:
        raise SystemExit("checks failed")
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(o.out).resolve()), copy=False)
    rep["output"] = {"path": Path(o.out).name, "sha256": sha(o.out)}
    Path(o.report).write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
