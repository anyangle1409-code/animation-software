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
TRANSFER = 0.6
HELPER_LENGTH = 0.4
import os as _os
TRANSFER = float(_os.environ.get("W3A_TRANSFER", TRANSFER))
SMOOTH_PASSES = int(_os.environ.get("W3A_SMOOTH", 4))     # diffusion passes of the transfer amount (0 = none)
EDGE_RINGS = int(_os.environ.get("W3A_EDGE", 4))           # rings over which the transfer tapers to 0 at the zone edge
FRACTION = float(_os.environ.get("W3A_FRACTION", FRACTION))
DRIVE = _os.environ.get("W3A_DRIVE", "reference")                              # "stateful" (continuous branch; needs runtime memory), "swing", "rotation"
ZONE_Z, ZONE_X = 1.22, 0.12                      # W4 used z > 1.30: its lower edge left a lateral-chest crease (measured)
ZONE_Z = float(_os.environ.get("W3A_ZONE_Z", ZONE_Z))
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
        if DRIVE in ("stateful", "reference"):        # no constraint: set per pose by _drive_stateful
            continue
        if DRIVE == "swing":                          # half the humeral swing (< 180 deg: never wraps); no axial twist
            c = pb.constraints.new("DAMPED_TRACK")
            c.target, c.subtarget, c.track_axis = rig, f"upperarm_{s}", "TRACK_Y"
            c.head_tail = 1.0
        else:                                         # half the full local rotation (wraps past 180 deg: flips)
            c = pb.constraints.new("COPY_ROTATION")
            c.target, c.subtarget = rig, f"upperarm_{s}"
            c.target_space = c.owner_space = "LOCAL"
        c.influence = fraction
    if DRIVE in ("stateful", "reference"):
        if DRIVE == "reference":
            _set_reference(result)                    # before the wrapper exists: plain coupled pose
        _install_stateful(result, fraction)
    names = {g.index: g.name for g in body.vertex_groups}
    groups = {s: body.vertex_groups.new(name=f"deltoid_helper_{s}") for s in ("l", "r")}
    moved = 0
    cap, tgt = {}, {}
    for i in zone:                                    # transfer target per vertex, then smoothed within the zone
        v = body.data.vertices[i]
        s = "r" if v.co.x > 0 else "l"
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        wu = w.get(f"upperarm_{s}", 0.0)
        wg = sum(x for n, x in w.items() if n.startswith(GIRDLE) and n.endswith(f"_{s}"))
        cap[i] = 2.0 * min(wu, wg)
        tgt[i] = transfer * cap[i]
    if SMOOTH_PASSES:
        zset = set(zone)
        adj = {i: set() for i in zone}
        for e in body.data.edges:
            a, b = e.vertices
            if a in zset and b in zset:
                adj[a].add(b); adj[b].add(a)
        for _ in range(SMOOTH_PASSES):
            tgt = {i: min(cap[i], (tgt[i] + sum(tgt[j] for j in adj[i])) / (1 + len(adj[i]))) for i in zone}
    if EDGE_RINGS:                                    # taper to zero at the zone boundary (no transfer step at its edge)
        zset = set(zone)
        nb = {i: set() for i in range(len(body.data.vertices))}
        for e in body.data.edges:
            a, b = e.vertices
            nb[a].add(b); nb[b].add(a)
        dist = {i: 0 for i in zone if any(j not in zset for j in nb[i])}
        frontier = list(dist)
        while frontier:
            nxt = []
            for i in frontier:
                for j in nb[i]:
                    if j in zset and j not in dist:
                        dist[j] = dist[i] + 1; nxt.append(j)
            frontier = nxt
        for i in zone:
            d = dist.get(i, EDGE_RINGS)
            tgt[i] *= min(1.0, d / EDGE_RINGS) ** 2 * (3 - 2 * min(1.0, d / EDGE_RINGS))
    for i in zone:
        v = body.data.vertices[i]
        s = "r" if v.co.x > 0 else "l"                # F-SIDE-001: runtime _r is +X
        w = {names[g.group]: g.weight for g in v.groups if g.weight > 0}
        wu = w.get(f"upperarm_{s}", 0.0)
        wg = sum(x for n, x in w.items() if n.startswith(GIRDLE) and n.endswith(f"_{s}"))
        t = tgt[i]
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


_STATE = {}
_REF = {}
REF_ELEVATION = float(_os.environ.get("W3A_REF", 120.0))     # mid-elevation reference for the stateless drive


def _set_reference(result):
    """Log-rotation vector of the upper arm relative to the scapula at REF_ELEVATION (unique branch: < 180 deg there)."""
    import build_functional_shoulder_correction_blender as correction
    rig = result["runtime"]
    correction.apply_corrected_pose(result, REF_ELEVATION)
    for s in ("l", "r"):
        q = _rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
        if q.w < 0:
            q.negate()
        _REF[s] = q.axis * q.angle
    correction.apply_corrected_pose(result, 0)


def _rel_quat(rig, child, parent):
    """Rotation of `child` relative to `parent`, relative to rest, in the child's rest frame (= its matrix_basis)."""
    pb, pp = rig.pose.bones[child], rig.pose.bones[parent]
    b, bp = rig.data.bones[child], rig.data.bones[parent]
    rest = bp.matrix_local.inverted() @ b.matrix_local
    return (rest.inverted() @ (pp.matrix.inverted() @ pb.matrix)).to_quaternion()


def _drive_stateful(result, fraction):
    """Half (fraction) of the upper arm's rotation relative to the scapula, taking the axis-angle branch continuous with
    the previous call (theta*n or (theta-2pi)*n), so the drive follows the motion past 180 deg instead of flipping."""
    import math as _m
    from mathutils import Quaternion as _Q, Vector as _V
    rig = result["runtime"]
    for s in ("l", "r"):
        q = _rel_quat(rig, f"upperarm_{s}", f"scapula_{s}")
        if q.w < 0:
            q.negate()
        theta = q.angle
        n = q.axis if theta > 1e-9 else _V((1.0, 0.0, 0.0))
        cands = [n * theta, n * (theta - 2 * _m.pi)]
        if DRIVE == "reference":                      # stateless: branch closest to a fixed mid-elevation reference
            ref = _REF[s]
            v = min(cands, key=lambda c: (c - ref).length)
        else:
            prev = _STATE.get(s)
            v = cands[0] if prev is None else min(cands, key=lambda c: (c - prev).length)
            _STATE[s] = v
        h = rig.pose.bones[f"deltoid_helper_{s}"]
        h.rotation_mode = "QUATERNION"
        ang = v.length * fraction
        h.rotation_quaternion = _Q(v.normalized(), ang) if ang > 1e-12 else _Q()
    bpy.context.view_layer.update()


def _install_stateful(result, fraction):
    import build_functional_shoulder_correction_blender as correction
    if getattr(correction.apply_corrected_pose, "_k_stateful", False):
        return
    original = correction.apply_corrected_pose

    def wrapped(res, ht, *a, **k):
        if ht == 0:
            _STATE.clear()                            # a new trajectory starts from rest
        out = original(res, ht, *a, **k)
        if "deltoid_helper_l" in res["runtime"].pose.bones:
            _drive_stateful(res, fraction)
        return out
    wrapped._k_stateful = True
    correction.apply_corrected_pose = wrapped


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


def render_shoulder(result, out, tag, angles=(0, 90, 145, 160)):
    """Close-ups of the right (+X) shoulder along the coupled motion: front, side (+X) and rear."""
    import build_functional_shoulder_correction_blender as correction
    from mathutils import Vector
    body, rig = result["body"], result["runtime"]
    scene = bpy.context.scene
    for o in scene.objects:
        if o.type in ("MESH", "CURVE") and o is not body:
            o.hide_render = True
    body.data.materials.clear()
    mat = bpy.data.materials.new("HGPT_W3A_SKIN_TMP"); mat.diffuse_color = (0.64, 0.46, 0.38, 1.0)
    body.data.materials.append(mat)
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_cavity = "STUDIO", "MATERIAL", True
    scene.render.resolution_x = scene.render.resolution_y = 600
    scene.render.image_settings.file_format = "PNG"
    cd = bpy.data.cameras.new("HGPT_W3A_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = 0.62
    cam = bpy.data.objects.new("HGPT_W3A_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
    out.mkdir(parents=True, exist_ok=True)
    names = []
    for a in angles:
        correction.apply_corrected_pose(result, a)
        c = rig.pose.bones["upperarm_r"].head.copy() + Vector((0.0, 0.0, 0.02))
        for view, d in (("front", (0, -1, 0)), ("side", (1, 0, 0)), ("rear", (0, 1, 0))):
            cam.location = c + Vector(d) * 3.0
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            n = f"{tag}_{a:03d}_{view}.png"
            scene.render.filepath = str(out / n)
            bpy.ops.render.render(write_still=True)
            names.append(n)
    correction.apply_corrected_pose(result, 0)
    return names


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    import build_functional_shoulder_correction_blender as correction
    import build_original_shoulder_weight_refit_blender as w4
    import build_original_movement_benchmarks_blender as bench
    renders = Path(args[args.index("--renders") + 1]) if "--renders" in args else None
    res = correction.build_corrected_scene()
    for kb in res["body"].data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    zone = zone_vertices(res["body"], res["runtime"])
    before_sigma = sigma_report(res, zone)
    before = w4.sweep_metrics(res)
    if renders:
        render_shoulder(res, renders, "base")
    info = add_helpers(res)
    after_sigma = sigma_report(res, zone)
    after = w4.sweep_metrics(res)
    if renders:
        render_shoulder(res, renders, "helper")
    source = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))       # fresh, unmodified scene for each benchmark run
    press0 = bench.run(None, only=["shoulder_press"])["benchmarks"]["shoulder_press"]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    press1 = bench.run(None, setup=lambda r: add_helpers(r), only=["shoulder_press"])["benchmarks"]["shoulder_press"]
    rep = {"kind": "W3_OPTION_A_FEASIBILITY", "approved": False, "contract_change": "67 -> 69 deforming joints (in memory only)",
           "parameters": {"drive": DRIVE, "fraction": FRACTION, "smooth_passes": SMOOTH_PASSES, "edge_rings": EDGE_RINGS, "transfer": TRANSFER, "helper_length": HELPER_LENGTH, "zone": [ZONE_Z, ZONE_X]},
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
