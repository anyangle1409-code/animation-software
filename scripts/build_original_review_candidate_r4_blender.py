#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R4 (Claude, 14 Oct 2026): the shoulder rebuilt on the anatomical scapula (owner-approved:
"do all four including lowering the pivot").  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R4_20261014.md.

Parent: foot candidate C5 (not R3: R1-R3's W3A helper and S1 keys were tuned to the old, wrong-way scapula and are left out).
  * arm pivot: upperarm_<s> head moved to the anatomical glenohumeral-centre landmark (53 mm lower; tail unchanged);
  * weights: scapula influence tapered with distance from the AC joint; deltoid-cap girdle weight moved to the upper arm;
    at most 4 influences per vertex (top 4, renormalised);
  * K1 contact keys re-solved on this base: knee 90/110/130, elbow 90/110, wrist extension 60/80/100;
  * runtime: scene["hgpt_shoulder_drive"] = "R4" - scripts/original_v1_review_candidate_drives.setup() installs
    scripts/original_v1_shoulder_r4.py (ISB-frame scapula + thorax contact) before posing; drive() runs the K1 keys.
Basis mesh, faces, legacy keys and every bone except the two upper arms are unchanged from C5.  Review only.

  python3.13 build_original_review_candidate_r4_blender.py -- --blend C5.blend --out R4.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_knee_contact_corrective_blender as k1  # noqa: E402
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_shoulder_r4 as r4  # noqa: E402

ELBOW_KEYS = (90, 110)
MAX_INFLUENCES = 4


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def limit_influences(body):
    names = {g.index: g.name for g in body.vertex_groups}
    fixed = 0
    for v in body.data.vertices:
        w = [(names[g.group], g.weight) for g in v.groups if g.weight > 0]
        if len(w) <= MAX_INFLUENCES:
            continue
        keep = sorted(w, key=lambda kv: -kv[1])[:MAX_INFLUENCES]
        tot = sum(x for _, x in keep)
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([v.index])
        for n, x in keep:
            body.vertex_groups[n].add([v.index], x / tot, "REPLACE")
        fixed += 1
    return fixed


def sweep(result, angles=range(0, 161, 20)):
    import build_functional_shoulder_correction_blender as correction
    body, rig = result["body"], result["runtime"]
    bench._reset(rig)
    V0, F = bench._evaluated(body)
    dom = bench.dominant_groups(body)
    rows = []
    for ht in angles:
        correction.apply_corrected_pose(result, ht)
        V, _ = bench._evaluated(body)
        m = bench.frame_metrics(V0, V, F, dom, min(v.z for v in V0))
        rows.append({"ht": ht, "collapse": m["collapse_lt_0_1"], "stretch": m["stretch_gt_2"],
                     "pairs": m["self_intersecting_pairs"], "volume_pct": m["body_volume_change_pct"],
                     "contact": r4._S.get("last")})
    bench._reset(rig)
    return rows


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    parent, out, report = get("--blend"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    import build_functional_shoulder_correction_blender as correction
    import build_functional_original_attachment_blender as attachment

    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    base = correction.build_corrected_scene()
    for kb in base["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    before = sweep(base)                                       # C5 with today's coupled motion

    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    result = correction.build_corrected_scene()
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    basis0 = [v.co.copy() for v in body.data.vertices]
    bones0 = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    pivot = r4.lower_pivot(result)
    w = r4.reweight(result)
    w["influence_limited"] = limit_influences(body)
    r4.install(result)
    after = sweep(result)
    k1_logs = {"knee": k1.build(result, "knee")}
    saved = k1.HINGES["elbow"]["keys"]
    k1.HINGES["elbow"]["keys"] = ELBOW_KEYS
    try:
        k1_logs["elbow"] = k1.build(result, "elbow")
    finally:
        k1.HINGES["elbow"]["keys"] = saved
    k1_logs["wrist"] = k1.build(result, "wrist")
    attachment._remove_previous()
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    bpy.context.view_layer.update()
    moved_bones = sorted(n for n, m in bones0.items() if any(abs(a - b) > 1e-6 for ra, rb in zip(m, rig.data.bones[n].matrix_local) for a, b in zip(ra, rb)))
    checks = {
        "basis_unchanged": max((a - b.co).length for a, b in zip(basis0, body.data.vertices)) < 1e-9,
        "deforming_joints": sum(b.use_deform for b in rig.data.bones),
        "bones_moved": moved_bones,
        "max_influences": max(sum(1 for g in v.groups if g.weight > 0) for v in body.data.vertices),
        "k1_keys": sorted(kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith("HGPT_K1_")),
        "guide_objects_left": [o.name for o in bpy.data.objects if o.name.endswith("_TMP")],
    }
    ok = (checks["basis_unchanged"] and checks["deforming_joints"] == 67 and moved_bones == ["upperarm_l", "upperarm_r"]
          and checks["max_influences"] <= MAX_INFLUENCES and len(checks["k1_keys"]) == 2 * (3 + len(ELBOW_KEYS) + 3)
          and not checks["guide_objects_left"])
    checks["verdict"] = "PASS" if ok else "FAIL"
    print("R4CHECK", json.dumps(checks))
    if not ok:
        raise SystemExit("checks failed")
    scene = bpy.context.scene
    scene["hgpt_review_candidate"] = "ORIGINAL_V1_CONSOLIDATED_REVIEW_R4_CLAUDE"
    scene["hgpt_review_candidate_approved"] = False
    scene["hgpt_shoulder_drive"] = "R4"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R4", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "parent": {"path": Path(parent).name, "sha256": sha(parent)}, "output": {"path": out.name, "sha256": sha(out)},
           "pivot_move_mm": pivot, "weights": w,
           "shoulder_params": {"taper_m": [r4.TAPER_R0, r4.TAPER_R1], "deltoid_shift": r4.DELTOID_SHIFT,
                               "deltoid_band_m": list(r4.DELTOID_BAND), "contact_penalty": list(r4.CONTACT_PENALTY),
                               "thorax_ellipsoid_centre_m": list(r4._S["centre"]), "thorax_ellipsoid_radii_m": list(r4._S["radii"]),
                               "rest_contact_distance_m": r4._S["d0"]},
           "k1": {"logs": k1_logs, "elbow_keys": list(ELBOW_KEYS)},
           "coupled_sweep_c5_today": before, "coupled_sweep_r4": after, "checks": checks}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")
    for a, b in zip(before, after):
        print("R4SW", a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))


if __name__ == "__main__":
    main()
