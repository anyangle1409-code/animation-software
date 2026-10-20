"""R68 root-cause study of the rear shoulder / armpit deformation (Claude, 20 Oct 2026).  Review only; nothing is saved.

Owner (R67e, 156 deg rear): rear deltoid flat, armpit pinched with no natural posterior fold, teres major / latissimus
undefined.  "Correct the underlying anatomical deformation so it behaves naturally in all positions."

Question: which layer causes it - skeleton/joint motion, skinning method, skin weights, topology or the corrective keys?
The R41 body (Work's immutable model, sha-checked) is deformed by ONE Armature modifier with linear blend skinning
(use_deform_preserve_volume = False) plus ~78 corrective shape keys driven by pose (S1/S3/H1/S5/S7 shoulder families).
This script poses the press and a plain arm raise over 0..166 deg and measures, per configuration:
  A  current      : LBS + all correctives (the R41 review model)
  B  lbs_raw      : LBS, shoulder corrective keys at 0  (what the skin weights alone do)
  C  dqs_raw      : dual-quaternion skinning (Preserve Volume), shoulder keys at 0
  D  dqs_current  : DQS + correctives (correctives were authored for LBS, informative only)
Metrics, per side, on the shoulder region (rest: within 0.13 m of the upper-arm head, posterior half for the "rear" set):
triangle area ratio posed/rest (pinch < 0.5, stretch > 1.8), folds (adjacent faces > 100 deg apart), self-intersections
(BVH overlap, faces sharing a vertex excluded), whole-body volume vs rest, and left/right mirror asymmetry.
  blender --background --python diagnose_shoulder_skinning_blender.py -- <R57 root> <outdir> [render]
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
ROOT = Path(args[0]).resolve(); OUT = Path(args[1]); RENDER = len(args) > 2 and args[2] == "render"
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
os.environ["S7_LOCKOUT_HT"] = "166"
import build_original_review_candidate_r17_blender as r17
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
import original_v1_press_extension as px

MODEL = ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend"
if hashlib.sha256(MODEL.read_bytes()).hexdigest() != "4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e":
    raise ValueError("Original Blender model bytes changed")
res = r17._setup(MODEL)
rig, body = res["runtime"], res["body"]
arm_mod = [m for m in body.modifiers if m.type == "ARMATURE"][0]
if os.environ.get("R68_DQS_BLEND"):
    # R68 option (a): per-vertex linear/dual-quaternion blend in the shoulder only.  A second Armature modifier with
    # Preserve Volume runs on the same input (multi-modifier) and is mixed in by a vertex group: weight R68_DQS_BLEND
    # inside 0.10 m of the measured pinch centre (both sides), smooth falloff to 0 at 0.16 m.
    import numpy as _np
    _mw = body.matrix_world; _co = _np.array([_mw @ v.co for v in body.data.vertices])
    _w = _np.zeros(len(_co))
    for _sg in (-1, 1):
        _d = _np.linalg.norm(_co - _np.array([0.234 * _sg, 0.07, 1.49]), axis=1)
        _x = _np.clip((0.16 - _d) / 0.06, 0, 1); _w = _np.maximum(_w, _x * _x * (3 - 2 * _x))
    _vg = body.vertex_groups.new(name="R68_DQS_MIX")
    for _i in _np.flatnonzero(_w > 1e-4):
        _vg.add([int(_i)], float(_w[_i]) * float(os.environ["R68_DQS_BLEND"]), "REPLACE")
    _m2 = body.modifiers.new("R68_DQS", "ARMATURE"); _m2.object = arm_mod.object; _m2.use_deform_preserve_volume = True
    _m2.use_multi_modifier = True; _m2.vertex_group = "R68_DQS_MIX"
    with bpy.context.temp_override(object=body):
        while body.modifiers[:].index(_m2) > body.modifiers[:].index(arm_mod) + 1:
            bpy.ops.object.modifier_move_up(modifier=_m2.name)
    print("R68_DQS_BLEND_ON", os.environ["R68_DQS_BLEND"], [m.name for m in body.modifiers], flush=True)
if os.environ.get("R69_DENSE"):
    # R69e: install a press candidate's dense S7 increments (Claude's R61 installer copy) on the immutable R41 in memory
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shoulder_r61"))
    from claude_r61_native import install as _install
    _zd = np.load(os.environ["R69_DENSE"])
    _dense = _zd["dense"] if "dense" in _zd.files else _zd["dense_delta"]
    _install(res, _dense.astype(float))
    print("R69_DENSE_INSTALLED", os.environ["R69_DENSE"], flush=True)
keys = body.data.shape_keys.key_blocks
if os.environ.get("R68_S7_NPZ"):
    # R68 fix: corrected S7 key coordinates from rear_restore_s7_blender.py (in memory only)
    z7 = np.load(os.environ["R68_S7_NPZ"])
    for name in z7.files:
        keys[name].data.foreach_set("co", z7[name].astype(np.float32).ravel())
    print("R68_LOADED_S7", len(z7.files), flush=True)
SHOULDER_FAMILIES = ("SHOULDER", "_S1_", "_S3_", "_H1_", "_S5_", "_S7_", "C1_ARMTRUNK")
shoulder_keys = [k for k in keys if k.name != "Basis" and any(f in k.name for f in SHOULDER_FAMILIES)]
faces = np.array([p.vertices[:] for p in body.data.polygons if len(p.vertices) == 3] +
                 [p.vertices[:3] for p in body.data.polygons if len(p.vertices) == 4] +
                 [(p.vertices[0], p.vertices[2], p.vertices[3]) for p in body.data.polygons if len(p.vertices) == 4])
mw = body.matrix_world


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    m = ev.to_mesh()
    co = np.array([mw @ v.co for v in m.vertices])
    ev.to_mesh_clear()
    return co


def tri_area(co):
    a, b, c = co[faces[:, 0]], co[faces[:, 1]], co[faces[:, 2]]
    n = np.cross(b - a, c - a)
    return 0.5 * np.linalg.norm(n, axis=1), n


def volume(co):
    a, b, c = co[faces[:, 0]], co[faces[:, 1]], co[faces[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


bench._reset(rig); bpy.context.view_layer.update()
for k in keys:
    if k.name != "Basis":
        k.value = 0.0
REST = evaluated()
A0, N0 = tri_area(REST)
V0 = volume(REST)
cen = {s: np.array(rig.matrix_world @ rig.pose.bones[f"upperarm_{s}"].head) for s in "lr"}
region = {s: np.flatnonzero(np.linalg.norm(REST - cen[s], axis=1) < 0.13) for s in "lr"}
rear = {s: region[s][REST[region[s], 1] > cen[s][1] - 0.01] for s in "lr"}     # +y is the back
mirror = None
from scipy.spatial import cKDTree
mx = REST.copy(); mx[:, 0] *= -1
d, mirror = cKDTree(REST).query(mx)
mirror_ok = d < 1e-3


def face_set(vids):
    s = np.zeros(len(REST), bool); s[vids] = True
    return np.flatnonzero(s[faces].all(axis=1))


rfaces = {s: face_set(region[s]) for s in "lr"}
rrear = {s: face_set(rear[s]) for s in "lr"}


def self_intersections(co, fids):
    tris = faces[fids]
    used = np.unique(tris)
    remap = -np.ones(len(co), int); remap[used] = np.arange(len(used))
    bvh = BVHTree.FromPolygons([Vector(p) for p in co[used]], remap[tris].tolist(), all_triangles=True)
    n = 0
    for i, j in bvh.overlap(bvh):
        if i < j and not set(tris[i]) & set(tris[j]):
            n += 1
    return n


edges_cache = {}


def folds(co, fids):
    key = id(fids)
    if key not in edges_cache:
        from collections import defaultdict
        e = defaultdict(list)
        for f in fids:
            t = faces[f]
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                e[(min(a_, b_), max(a_, b_))].append(f)
        edges_cache[key] = np.array([v for v in e.values() if len(v) == 2])
    pairs = edges_cache[key]
    _, n = tri_area(co)
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", n[pairs[:, 0]], n[pairs[:, 1]]), -1, 1)))
    return ang


def metrics(co):
    A, _ = tri_area(co)
    out = {"volume_change_pct": round(100 * (volume(co) - V0) / V0, 3)}
    for s in "lr":
        for nm, fids in (("shoulder", rfaces[s]), ("rear", rrear[s])):
            r = A[fids] / np.maximum(A0[fids], 1e-12)
            ang = folds(co, fids)
            out[f"{s}_{nm}"] = {"area_p5": round(float(np.percentile(r, 5)), 3), "area_min": round(float(r.min()), 3),
                               "area_p95": round(float(np.percentile(r, 95)), 3), "pinched_lt_0.5": int((r < 0.5).sum()),
                               "stretched_gt_1.8": int((r > 1.8).sum()), "folds_gt_100deg": int((ang > 100).sum()),
                               "max_fold_deg": round(float(ang.max()), 1)}
        out[f"{s}_self_intersections"] = self_intersections(co, rfaces[s])
    m = mirror_ok
    mco = co[mirror[m]].copy(); mco[:, 0] *= -1
    out["max_asymmetry_mm"] = round(float(np.linalg.norm(co[m] - mco, axis=1).max() * 1000), 2)
    return out


def pose(ht):
    bench._reset(rig)
    if ht >= 70.0:
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if px.press_state(mid)[0] < ht:
                lo = mid
            else:
                hi = mid
        px.pose_press_full(res, 0.5 * (lo + hi))
    else:
        px.apply_pose(res, ht)
    drives.drive(rig, body)
    bpy.context.view_layer.update()


if os.environ.get("R68_MODE") == "rot":
    # arm-rotation robustness: humeral axial rotation -30/0/+30 deg (about the shaft) at 90, 120 and 156 deg
    from mathutils import Matrix
    rr = {}
    for ht in (90.0, 120.0, 156.0):
        for rot in (-30.0, 0.0, 30.0):
            pose(ht)
            for s_, sg in (("l", -1.0), ("r", 1.0)):
                b = rig.pose.bones[f"upperarm_{s_}"]
                d_ = (b.tail - b.head).normalized(); pv = b.head.copy()
                b.matrix = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(sg * rot), 4, d_) @ Matrix.Translation(-pv) @ b.matrix
            bpy.context.view_layer.update(); drives.drive(rig, body); bpy.context.view_layer.update()
            m = metrics(evaluated())
            rr[f"{ht:g}_{rot:g}"] = {"r_rear_pinched": m["r_rear"]["pinched_lt_0.5"], "l_rear_pinched": m["l_rear"]["pinched_lt_0.5"],
                                     "r_folds": m["r_shoulder"]["folds_gt_100deg"], "self_x": [m["r_self_intersections"], m["l_self_intersections"]],
                                     "stretched": m["r_shoulder"]["stretched_gt_1.8"]}
            print("R68ROT", ht, rot, json.dumps(rr[f"{ht:g}_{rot:g}"]), flush=True)
    (OUT / f"rotation_{os.environ.get('R68_TAG', 'x')}.json").write_text(json.dumps(rr, indent=1))
    raise SystemExit
if os.environ.get("R68_MODE") == "outline":
    # Work's approved-outline measure (R48 silhouette: +-x and (+-x,-y)/sqrt2, 1.18-1.62 m) at the marked pose and others
    from original_review_r48_outline import silhouette
    vals = {}
    for ht in (120.0, 135.6, 156.0, 166.0):
        pose(ht); co = evaluated()
        vals[f"{ht:g}"] = [silhouette(co, faces, side, n, h)[0] for sign, side in ((-1, "l"), (1, "r"))
                           for n in (np.array([sign, 0.0, 0.0]), np.array([sign, -1.0, 0.0]) / np.sqrt(2.0)) for h in np.arange(1.18, 1.62, 0.005)]
    (OUT / f"outline_{os.environ.get('R68_TAG', 'x')}.json").write_text(json.dumps(vals))
    print("R68O_DONE", flush=True)
    raise SystemExit
if os.environ.get("R68_MODE") == "armpit_ablate":
    # R69: which layer makes the inner-arm armpit fold?  Region: faces with rest centroid within 0.06 m of
    # (+-0.19, 0.02, 1.37) (medial upper arm at the axilla, front-to-back).  Per family off, LBS raw, DQS raw.
    cfa = REST[faces].mean(1)
    regf = {sd: np.flatnonzero(np.linalg.norm(cfa - np.array([0.19 * sg, 0.02, 1.37]), axis=1) < 0.06) for sd, sg in (("l", -1), ("r", 1))}
    from collections import defaultdict
    def pairs_of(ff):
        ed = defaultdict(list)
        for f in ff:
            t = faces[f]
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                ed[(min(a_, b_), max(a_, b_))].append(f)
        return np.array([v for v in ed.values() if len(v) == 2])
    PR = {sd: pairs_of(regf[sd]) for sd in "lr"}
    def m_ax(co):
        A, n = tri_area(co); n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12); o = {}
        for sd in "lr":
            ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", n[PR[sd][:, 0]], n[PR[sd][:, 1]]), -1, 1)))
            r = A[regf[sd]] / A0[regf[sd]]
            o[sd] = {"max_fold": round(float(ang.max()), 1), "folds45": int((ang > 45).sum()), "pinched": int((r < 0.5).sum()), "p5": round(float(np.percentile(r, 5)), 2)}
        return o
    FAMS = {"S1": ("_S1_",), "S3": ("_S3_",), "S5": ("_S5_",), "S7": ("_S7_",), "H1": ("_H1_",), "CORR": ("SHOULDER_CORR", "SHOULDER_FLEX", "SHOULDER_SCAP"), "C1": ("C1_ARMTRUNK",), "ALL": SHOULDER_FAMILIES}
    for ht in (135.6, 156.0, 166.0):
        for fam, pats in [("current", ())] + list(FAMS.items()):
            pose(ht)
            for k in shoulder_keys:
                if pats and any(p_ in k.name for p_ in pats): k.value = 0.0
            bpy.context.view_layer.update()
            print("R69B", ht, fam, json.dumps(m_ax(evaluated())), flush=True)
        arm_mod.use_deform_preserve_volume = True
        pose(ht)
        for k in shoulder_keys: k.value = 0.0
        bpy.context.view_layer.update(); print("R69B", ht, "dqs_raw", json.dumps(m_ax(evaluated())), flush=True)
        arm_mod.use_deform_preserve_volume = False
    raise SystemExit
if os.environ.get("R68_MODE") == "armpit":
    # R69: where are the remaining defects on the ARM side of the armpit (owner on R68e: "the shoulder looks good but
    # the arm still has that bit at the armpit")?  Right side, faces of the upper arm (upperarm weight > 0.3) within
    # 0.16 m of the arm head: pinched (<0.5 area) and sharp folds (adjacent faces > 45 deg), rest-space locations.
    wv = np.zeros(len(REST))
    gi = body.vertex_groups["upperarm_r"].index
    for v in body.data.vertices:
        for g in v.groups:
            if g.group == gi: wv[v.index] = g.weight
    armf = np.flatnonzero((wv[faces].mean(1) > 0.3) & (np.linalg.norm(REST[faces].mean(1) - cen["r"], axis=1) < 0.16))
    from collections import defaultdict
    ed = defaultdict(list)
    for f in armf:
        t = faces[f]
        for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ed[(min(a_, b_), max(a_, b_))].append(f)
    pairs = np.array([v for v in ed.values() if len(v) == 2])
    for ht in (135.6, 156.0, 166.0):
        pose(ht); co = evaluated(); A, n = tri_area(co)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        ang = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", n[pairs[:, 0]], n[pairs[:, 1]]), -1, 1)))
        fold_f = np.unique(pairs[ang > 45].ravel())
        pin_f = armf[(A[armf] / A0[armf]) < 0.5]
        for nm, ff in (("folds45", fold_f), ("pinched", pin_f)):
            if len(ff) == 0:
                print("R69A", ht, nm, 0, flush=True); continue
            c = REST[faces[ff]].mean(1)
            print("R69A", ht, nm, len(ff), "centroid", np.round(c.mean(0), 3).tolist(), "p10", np.round(np.percentile(c, 10, 0), 3).tolist(),
                  "p90", np.round(np.percentile(c, 90, 0), 3).tolist(), "posed_centroid", np.round(co[faces[ff]].mean((0, 1)), 3).tolist(), flush=True)
    raise SystemExit
if os.environ.get("R68_MODE") == "locate":
    # where (rest space) are the rear-shoulder triangles compressed below half their area, per angle (right side)
    loc = {}
    for ht in (120.0, 135.6, 156.0, 166.0):
        pose(ht); A, _ = tri_area(evaluated())
        f = rrear["r"][(A[rrear["r"]] / A0[rrear["r"]]) < 0.5]
        c = REST[faces[f]].mean(axis=1)
        loc[f"{ht:g}"] = {"n": int(len(f)), "centroid": np.round(c.mean(0), 3).tolist(), "p10": np.round(np.percentile(c, 10, axis=0), 3).tolist(),
                          "p90": np.round(np.percentile(c, 90, axis=0), 3).tolist(), "head": np.round(cen["r"], 3).tolist()}
        print("R68L", ht, json.dumps(loc[f"{ht:g}"]), flush=True)
    raise SystemExit
if os.environ.get("R68_MODE") == "ablate":
    exec(open(Path(__file__).with_name("ablate_corrective_families.py")).read())
    raise SystemExit
CONFIGS = {"current": (False, True), "lbs_raw": (False, False), "dqs_raw": (True, False), "dqs_current": (True, True)}
if os.environ.get("R68_CONFIGS"):
    CONFIGS = {c.split("=")[0]: CONFIGS[c.split("=")[-1]] for c in os.environ["R68_CONFIGS"].split(",")}
ANGLES = [0.0, 45.0, 90.0, 120.0, 135.6, 156.0, 166.0]
results = {}
cams = None
if RENDER:
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    body.data.materials.clear(); body.data.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"; sc.display.shading.show_cavity = True
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.render.resolution_x = sc.render.resolution_y = 700
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"
    cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
    VIEWS = {"rear": ((0.15, 1, 0), 0.42), "rear_34": ((0.75, 0.65, 0.05), 0.42), "side": ((1, 0.1, 0), 0.42),
             "front_34": ((0.75, -0.65, 0.05), 0.42), "back_full": ((0, 1, 0), 1.15)}
for cfg, (dqs, corr) in CONFIGS.items():
    arm_mod.use_deform_preserve_volume = dqs
    results[cfg] = {}
    for ht in ANGLES:
        pose(ht)
        if not corr:
            for k in shoulder_keys:
                k.value = 0.0
        bpy.context.view_layer.update()
        co = evaluated()
        results[cfg][f"{ht:g}"] = metrics(co)
        print("R68", cfg, ht, json.dumps(results[cfg][f"{ht:g}"]), flush=True)
        if RENDER and ht in (0.0, 90.0, 135.6, 156.0, 166.0):
            for view, (dv, scale) in VIEWS.items():
                if view == "back_full":
                    tgt = (rig.matrix_world @ rig.pose.bones["upperarm_l"].head + rig.matrix_world @ rig.pose.bones["upperarm_r"].head) / 2 + Vector((0, 0, 0.05))
                else:
                    tgt = rig.matrix_world @ rig.pose.bones["upperarm_r"].head + Vector((0, 0, -0.06))
                dvec = Vector(dv).normalized()
                cd.ortho_scale = scale
                cam.location = tgt + dvec * 3
                cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
                sc.render.filepath = str(OUT / f"{cfg}_{ht:05.1f}_{view}.png")
                bpy.ops.render.render(write_still=True)
arm_mod.use_deform_preserve_volume = False
(OUT / "r68_skinning_metrics.json").write_text(json.dumps({"configs": {k: {"dqs": v[0], "correctives": v[1]} for k, v in CONFIGS.items()},
                                                          "shoulder_keys": len(shoulder_keys), "angles": ANGLES,
                                                          "results": results}, indent=1))
print("R68_DONE", flush=True)
