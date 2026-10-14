"""W3 option A feasibility: half-elevation shoulder-top helper deformer, measured in memory (diagnostic only).

W2/W4 showed the shoulder-top/axilla skin cannot be fixed inside the 67-joint linear-blend contract: its vertices
average the upper arm with the clavicle/scapula while their rotations differ by 120-180 deg, so the blended matrices
become nearly singular.  The W3 proposal (option A) asks the owner to approve a review-only trial of a helper deformer
on a separate copy.  This script does NOT perform that trial or change any asset: it only measures, in memory, whether
option A addresses the defect, so the A/B/C decision can be made with data.

Helper (per side): `deltoid_helper_<s>` with the upper arm's rest frame (same head, direction and roll, 40 % length),
parented to the scapula like the upper arm, deforming, driven at FRACTION (0.5) of the humeral motion relative to the
scapula.  DRIVE "swing" (default) = DAMPED_TRACK to the upper-arm tail, i.e. half the humeral swing without axial twist.
DRIVE "rotation" = COPY_ROTATION in local space; measured and rejected: the upper arm turns 116 deg relative to the
scapula at 90 deg elevation and ~177 deg by 140 deg (hanging rest + axial rotation), so the half rotation flips sides
past 180 deg (body volume +3.1 % -> -7.1 % between 140 and 145 deg).
Weights: in the W4 shoulder-top zone, a vertex with upper-arm weight wu and girdle weight wg (clavicle + scapula)
moves t = TRANSFER * 2 * min(wu, wg) onto the helper, taking t/2 from each (a 50/50 vertex becomes 100 % helper, i.e.
rigid at half the rotation).  Other weights and every other vertex are unchanged; still <= 4 influences.
Measured: smallest singular value of the blended matrices per zone vertex (90-160 deg) and the W2/W4 region metrics
along the coupled 0-160 motion, before/after; plus the M1 shoulder-press benchmark.  69 joints = a contract change.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

FRACTION = 0.5
TRANSFER = 1.0
HELPER_LENGTH = 0.4
DRIVE = "swing"                                  # "swing" (damped track) or "rotation" (copy rotation; flips > 180 deg)
ZONE_Z, ZONE_X = 1.30, 0.12                      # same zone as W4
GIRDLE = ("clavicle_", "scapula_")
POSES = (90, 120, 140, 160)
MAX_INFLUENCES = 4


def zone_vertices(body, rig):
    names = {g.index: g.name for g in body.vertex_groups}
    out = []
    for v in body.data.vertices:
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        region = sum(x for n, x in w.items() if n.startswith(("upperarm_",) + GIRDLE))
        if region > 0.05 and v.co.z > ZONE_Z and abs(v.co.x) > ZONE_X:
            out.append(v.index)
    return out


def add_helpers(result, fraction=FRACTION, transfer=TRANSFER):
    body, rig = result["body"], result["runtime"]
    if not body.matrix_world.is_identity or not rig.matrix_world.is_identity:
        raise RuntimeError("identity object transforms required")
    zone = zone_vertices(body, rig)
    view = bpy.context.view_layer
    for o in view.objects:
        o.select_set(False)
    view.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in ("l", "r"):
        up = rig.data.edit_bones[f"upperarm_{s}"]
        h = rig.data.edit_bones.new(f"deltoid_helper_{s}")
        h.head = up.head.copy()
        h.tail = up.head + (up.tail - up.head) * HELPER_LENGTH
        h.roll = up.roll
        h.parent = up.parent
        h.use_connect = False
        h.use_deform = True
    bpy.ops.object.mode_set(mode="OBJECT")
    for s in ("l", "r"):
        pb = rig.pose.bones[f"deltoid_helper_{s}"]
        if DRIVE == "swing":                          # half the humeral swing (< 180 deg: never wraps); no axial twist
            c = pb.constraints.new("DAMPED_TRACK")
            c.target, c.subtarget, c.track_axis = rig, f"upperarm_{s}", "TRACK_Y"
            c.head_tail = 1.0
        else:                                         # half the full local rotation (wraps past 180 deg: flips)
            c = pb.constraints.new("COPY_ROTATION")
            c.target, c.subtarget = rig, f"upperarm_{s}"
            c.target_space = c.owner_space = "LOCAL"
        c.influence = fraction
    names = {g.index: g.name for g in body.vertex_groups}
    groups = {s: body.vertex_groups.new(name=f"deltoid_helper_{s}") for s in ("l", "r")}
    moved = 0
    for i in zone:
        v = body.data.vertices[i]
        s = "r" if v.co.x > 0 else "l"                # F-SIDE-001: runtime _r is +X
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        wu = w.get(f"upperarm_{s}", 0.0)
        wg = sum(x for n, x in w.items() if n.startswith(GIRDLE) and n.endswith(f"_{s}"))
        t = transfer * 2.0 * min(wu, wg)
        if t <= 1e-4:
            continue
        w[f"upperarm_{s}"] = wu - t / 2
        for n in [n for n in w if n.startswith(GIRDLE) and n.endswith(f"_{s}")]:
            w[n] -= (t / 2) * (w[n] / wg)
        w[f"deltoid_helper_{s}"] = t
        top = dict(sorted(((n, x) for n, x in w.items() if x > 1e-6), key=lambda kv: -kv[1])[:MAX_INFLUENCES])
        tot = sum(top.values())
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([i])
        for n, x in top.items():
            grp = body.vertex_groups.get(n) or groups[s]
            grp.add([i], x / tot, "REPLACE")
        moved += 1
    view.update()
    return {"zone_vertices": len(zone), "vertices_reweighted": moved, "joints": sum(b.use_deform for b in rig.data.bones)}


def sigma_report(result, zone, poses=POSES):
    import build_functional_shoulder_correction_blender as correction
    body, rig = result["body"], result["runtime"]
    names = {g.index: g.name for g in body.vertex_groups}
    deform = {b.name for b in rig.data.bones if b.use_deform}
    W = {i: {names[g.group]: g.weight for g in body.data.vertices[i].groups if names[g.group] in deform and g.weight > 0} for i in zone}
    worst = {i: 1.0 for i in zone}
    for p in poses:
        correction.apply_corrected_pose(result, p)
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        for i in zone:
            A = sum(x * mats[n] for n, x in W[i].items())
            worst[i] = min(worst[i], float(np.linalg.svd(A, compute_uv=False).min()))
    correction.apply_corrected_pose(result, 0)
    s = list(worst.values())
    return {"sigma_min": round(min(s), 4), "vertices_lt_0_1": sum(x < 0.1 for x in s), "vertices_lt_0_3": sum(x < 0.3 for x in s),
            "median": round(float(np.median(s)), 4)}


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    import build_functional_shoulder_correction_blender as correction
    import build_original_shoulder_weight_refit_blender as w4
    import build_original_movement_benchmarks_blender as bench
    res = correction.build_corrected_scene()
    for kb in res["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    zone = zone_vertices(res["body"], res["runtime"])
    before_sigma = sigma_report(res, zone)
    before = w4.sweep_metrics(res)
    info = add_helpers(res)
    after_sigma = sigma_report(res, zone)
    after = w4.sweep_metrics(res)
    source = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))       # fresh, unmodified scene for each benchmark run
    press0 = bench.run(None, only=["shoulder_press"])["benchmarks"]["shoulder_press"]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    press1 = bench.run(None, setup=lambda r: add_helpers(r), only=["shoulder_press"])["benchmarks"]["shoulder_press"]
    rep = {"kind": "W3_OPTION_A_FEASIBILITY", "approved": False, "contract_change": "67 -> 69 deforming joints (in memory only)",
           "parameters": {"drive": DRIVE, "fraction": FRACTION, "transfer": TRANSFER, "helper_length": HELPER_LENGTH, "zone": [ZONE_Z, ZONE_X]},
           "helpers": info, "zone_sigma": {"before": before_sigma, "after": after_sigma},
           "coupled_sweep": {"before": before, "after": after},
           "press_benchmark": {"before": {"worst": press0["worst"], "volume": press0["volume_change_pct_range"]},
                               "after": {"worst": press1["worst"], "volume": press1["volume_change_pct_range"]}}}
    print("W3A", json.dumps({k: rep[k] for k in ("helpers", "zone_sigma", "press_benchmark")}))
    for a in before:
        b, c = before[a], after[a]
        print("W3A sweep", a, "collapse", b["collapse_faces_ratio_lt_0_1"], "->", c["collapse_faces_ratio_lt_0_1"],
              "pairs", b["self_intersecting_face_pairs_in_region"], "->", c["self_intersecting_face_pairs_in_region"],
              "stretch", b["stretched_faces_ratio_gt_2"], "->", c["stretched_faces_ratio_gt_2"],
              "vol", b["body_volume_change_pct"], "->", c["body_volume_change_pct"])
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, indent=1, default=str) + "\n")
