"""Full-trajectory movement tests for a body_v2 blend (read-only; nothing is saved to the blend).

Trajectories (each starts and ends at neutral, so return-to-neutral is measured):
  press  - neutral (16 deg carriage, V2_TRAJ_PRESS_START) -> rack (humerothoracic 90 deg, elbow 90) -> lockout (160, elbow 0) -> rack -> neutral.  Shoulder from the
           r57 coupled path (correction.apply_corrected_pose: clavicle / scapula coupling + humeral axial rotation, plane
           40 deg) - the same path the r57 movement benchmark's shoulder_press uses (project-authored, not cohort-fit).
  curl   - elbow 0 -> 140 -> 0 with the arms at the sides (16 deg carriage).
  squat  - the r57 benchmark squat, depth 0 -> 1 -> 0, with a per-leg foot plant (V2_TRAJ_PLANT=0 for the raw r57 path).
V2_TRAJ_GIRDLE=candidate uses shoulder_girdle_candidate.apply_press_pose (corrected girdle directions) for the press.
r57 drives (correctives, helpers) always run; the R121 candidate drives run unless V2_TRAJ_R121=0.

Per frame (hands and feet excluded unless stated):
  * edges past 35 / 90 deg between their faces, whole body and per region (shoulder, elbow, hip, knee - rest-space boxes);
  * edge length / rest length: p1 / p99 and counts < 0.5 (collapse) and > 2.0 (stretch);
  * non-adjacent self-intersecting triangle pairs (BVH overlap, pairs sharing a vertex dropped) per region pair;
  * left/right asymmetry: |posed(v) - mirror(posed(mirror partner of v))|, p95 / max mm (rest-space mirror partners);
  * feet: lowest skin height relative to the rest floor, horizontal slide of the rest sole vertices (mm);
  * return to neutral: last frame vs first frame, max vertex distance (mm).
Writes <out>/trajectory_report.json and frame renders <out>/frame_<movement>_<frame>_<view>.png (V2_TRAJ_RENDER=0 skips);
trajectory_sheets.py turns them into phone review sheets.

usage: python3.13 movement_trajectory_test_blender.py -- <body.blend> <r57src> <out dir> [press curl squat]
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, ROOT, OUT = Path(args[0]), Path(args[1]), Path(args[2])
MOVES = args[3:] or ["press", "curl", "squat"]
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit"), str(Path(__file__).resolve().parent)]
bpy.ops.wm.open_mainfile(filepath=str(SRC))
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import build_functional_shoulder_correction_blender as correction  # noqa: E402
import functional_shoulder_correction as corr  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402
import shoulder_girdle_candidate as girdle  # noqa: E402

USE_R121 = os.environ.get("V2_TRAJ_R121", "1") == "1"
GIRDLE = os.environ.get("V2_TRAJ_GIRDLE", "r57")           # r57: apply_corrected_pose; candidate: shoulder_girdle_candidate
NF = int(os.environ.get("V2_TRAJ_FRAMES", "17"))           # frames per trajectory (odd: the turning point is sampled)
RENDER = os.environ.get("V2_TRAJ_RENDER", "1") == "1"
PLANT = os.environ.get("V2_TRAJ_PLANT", "1") == "1"
SQUAT_ARMS = os.environ.get("V2_TRAJ_SQUAT_ARMS", "hang")   # hang (r57 path) or forward (counterbalance cue)      # per-leg foot plant in the squat (the r57 path plants the mean only)
HT0 = float(os.environ.get("V2_TRAJ_PRESS_START", "16"))   # press neutral: humerothoracic 16 deg (the standing carriage);
#                                                          0 points the arm straight down through the hip (test artifact)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
n = len(me.vertices)
dg = bpy.context.evaluated_depsgraph_get()

# ------------------------------------------------------------------ rest data
bench._reset(rig)
for kb in me.shape_keys.key_blocks[1:]:
    kb.value = 0.0
bpy.context.view_layer.update()


def evaluated():
    bpy.context.view_layer.update()
    ev = body.evaluated_get(dg); m_ = ev.to_mesh()
    P = np.empty(n * 3); m_.vertices.foreach_get("co", P); ev.to_mesh_clear()
    return P.reshape(-1, 3)


R = evaluated()
z0 = float(R[:, 2].min()); H = float(R[:, 2].max()) - z0
fz = (R[:, 2] - z0) / H
GN = [g.name for g in body.vertex_groups]
W = {}
for v in me.vertices:
    for g in v.groups:
        W.setdefault(GN[g.group], {})[v.index] = g.weight


def gw(*keys):
    w = np.zeros(n)
    for name, d in W.items():
        if any(k in name for k in keys):
            for i, x in d.items():
                w[i] += x
    return w


HOLD = (gw("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal") > 0.3) | (gw("foot", "toe", "ball") > 0.3)
ax_ = np.abs(R[:, 0])
REG = {"shoulder": (fz > 0.70) & (fz < 0.84) & (ax_ > 0.11),
       "elbow": (gw("upperarm", "forearm") > 0.5) & (fz > 0.50) & (fz < 0.68),
       "hip": (fz > 0.40) & (fz < 0.60) & (ax_ < 0.20) & (gw("upperarm", "forearm") < 0.3),
       "knee": (fz > 0.22) & (fz < 0.34)}
POLY3 = np.array([p.vertices[:3] for p in me.polygons])        # polygon normal from its first three corners
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons
                for k in range(1, len(p.vertices) - 1)])          # fan triangles (the legs keep V14's quads)
EV = np.array([e.vertices[:] for e in me.edges])
REST_LEN = np.linalg.norm(R[EV[:, 0]] - R[EV[:, 1]], axis=1)
EOK = ~(HOLD[EV[:, 0]] | HOLD[EV[:, 1]]) & (REST_LEN > 1e-7)
ek = {}
for fi, p in enumerate(me.polygons):
    for a, b in p.edge_keys:
        ek.setdefault((a, b), []).append(fi)
EF = np.array([(k[0], k[1], f[0], f[1]) for k, f in ek.items() if len(f) == 2])
EF = EF[~(HOLD[EF[:, 0]] | HOLD[EF[:, 1]])]
# mirror partners (rest space)
Rm = R * np.array([-1.0, 1.0, 1.0])
dmir, MIR = cKDTree(R).query(Rm)
MOK = (dmir < 0.004) & ~HOLD
# a partner only counts if its dominant bone is the mirror of the vertex's own: where the hanging hands touch the
# thighs at rest, a thigh vertex's mirror image lands on the other hand's fingers (229 such pairs made the max
# asymmetry read ~800 mm while p95 was ~1.3 mm)
DOM = np.full(n, "", dtype=object); DW = np.zeros(n)
for name, d in W.items():
    for i, w in d.items():
        if w > DW[i]:
            DW[i], DOM[i] = w, name


def _mirror_name(s):
    return s[:-2] + {"_l": "_r", "_r": "_l"}[s[-2:]] if s[-2:] in ("_l", "_r") else s


MOK &= np.array([_mirror_name(DOM[i]) == DOM[MIR[i]] for i in range(n)])
# feet
SOLE = (gw("foot", "toe", "ball") > 0.3) & (R[:, 2] < z0 + 0.012)
# triangle region label for intersection pairs (by first vertex)
TREG = np.full(len(TRI), "other", dtype=object)
for name, m in REG.items():
    TREG[m[TRI[:, 0]]] = name
TREG[HOLD[TRI[:, 0]]] = "hand_foot"

# humeral rest axial angles, as build_corrected_scene computes them
RESULT = {"runtime": rig, "humeral_rest_axial_deg": {}}
for side, name in correction.HUMERI:
    b = rig.data.bones[name]
    RESULT["humeral_rest_axial_deg"][name] = corr.humeral_axial_angle_deg(
        tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
REST_HEADS = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l", "r")}


def finish_pose():
    bpy.context.view_layer.update(); drives.drive(rig, body)
    if USE_R121:
        r121_drives.drive(rig, body)
    else:
        for kb in me.shape_keys.key_blocks:
            if kb.name.startswith(("R121_ARM_", "R121_FLEX_", "R121_HIP_", "R121_ELBOW_", "R121_KNEE_", "R121_COMBO_", "R121_REST_")):
                kb.value = 0.0
    bpy.context.view_layer.update()


def elbows(deg):
    for s in ("l", "r"):
        pb = rig.pose.bones[f"forearm_{s}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (math.radians(-deg), 0.0, 0.0)
    bpy.context.view_layer.update()


def press(u):
    """u in [0, 1] out and back: 0 neutral, 0.25 rack, 0.5 lockout, 0.75 rack, 1 neutral"""
    p = 1.0 - abs(2.0 * u - 1.0)                                  # 0 -> 1 -> 0
    if p <= 0.5:                                                    # neutral (standing carriage) -> rack
        k = bench.smooth(p / 0.5); ht, elb = HT0 + (90.0 - HT0) * k, 90.0 * k
    else:                                                           # rack -> lockout (the benchmark's own path)
        k = bench.smooth((p - 0.5) / 0.5); ht, elb = 90.0 + 70.0 * k, 90.0 * (1.0 - k)
    bench._reset(rig)
    if GIRDLE == "candidate":
        girdle.apply_press_pose(rig, ht, RESULT["humeral_rest_axial_deg"])
    else:
        correction.apply_corrected_pose(RESULT, ht)
    elbows(elb)
    return {"humerothoracic_target_deg": round(ht, 2), "elbow_flexion_deg": round(elb, 2)}


def curl(u):
    p = 1.0 - abs(2.0 * u - 1.0); elb = 140.0 * bench.smooth(p)
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * 16.0))
    elbows(elb)
    return {"elbow_flexion_deg": round(elb, 2)}


def plant_feet(iters=4):
    """the r57 benchmark squat plants only the average of the two ankles (root translation), so each ankle drifts ~16 mm
    medially at depth with the feet flat.  Per leg: turn the thigh about the forward axis through its hip until the
    ankle is back over its rest position (the knee tracks a little outwards), then re-plant the feet flat."""
    from mathutils import Matrix
    for _ in range(iters):
        for s in ("l", "r"):
            th = rig.pose.bones[f"thigh_{s}"]; hip = th.head.copy()
            a = rig.pose.bones[f"foot_{s}"].head - hip; t = REST_HEADS[s] - hip
            ang = math.atan2(t.x, -t.z) - math.atan2(a.x, -a.z)      # in the frontal plane, about the forward axis
            th.matrix = Matrix.Translation(hip) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Translation(-hip) @ th.matrix
            bpy.context.view_layer.update()
        bench._plant_feet(rig, REST_HEADS)


def squat(u):
    p = 1.0 - abs(2.0 * u - 1.0)
    out = bench.pose_squat(rig, p, REST_HEADS)
    if PLANT:
        plant_feet()
    if SQUAT_ARMS == "forward":                                     # arms raised forwards to horizontal with the descent
        girdle.apply_arm_pose(rig, 16.0 + 74.0 * bench.smooth(min(1.0, p / 0.6)), 90.0, reset=False)
    return {k: round(float(v), 2) for k, v in out.items()} | {"depth": round(p, 3)}


MOVE_FN = {"press": press, "curl": curl, "squat": squat}


def metrics(P):
    out = {}
    a, b, c = P[POLY3[:, 0]], P[POLY3[:, 1]], P[POLY3[:, 2]]
    fn = np.cross(b - a, c - a); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-15)
    d = np.einsum("ij,ij->i", fn[EF[:, 2]], fn[EF[:, 3]])
    out["edges_gt35"] = int((d < 0.82).sum()); out["edges_gt90"] = int((d < 0.0).sum())
    for name, m in REG.items():
        mm = m[EF[:, 0]]
        out[f"{name}_gt35"] = int((d[mm] < 0.82).sum()); out[f"{name}_gt90"] = int((d[mm] < 0.0).sum())
    L = np.linalg.norm(P[EV[:, 0]] - P[EV[:, 1]], axis=1)[EOK] / REST_LEN[EOK]
    out["edge_ratio_p1"] = round(float(np.percentile(L, 1)), 3); out["edge_ratio_p99"] = round(float(np.percentile(L, 99)), 3)
    out["edges_collapse_lt0.5"] = int((L < 0.5).sum()); out["edges_stretch_gt2"] = int((L > 2.0).sum())
    # self-intersection (non-adjacent pairs)
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], TRI.tolist(), all_triangles=True)
    pairs = np.array(bvh.overlap(bvh), dtype=np.int64).reshape(-1, 2)
    if len(pairs):
        pairs = pairs[pairs[:, 0] < pairs[:, 1]]
        ta, tb = TRI[pairs[:, 0]], TRI[pairs[:, 1]]
        share = (ta[:, :, None] == tb[:, None, :]).any(axis=(1, 2))
        pairs = pairs[~share]
    out["self_intersections"] = int(len(pairs))
    reg_pairs = {}
    for i, j in pairs:
        k = "|".join(sorted((TREG[i], TREG[j])))
        reg_pairs[k] = reg_pairs.get(k, 0) + 1
    out["self_intersections_by_region"] = dict(sorted(reg_pairs.items(), key=lambda t: -t[1])[:6])
    # symmetry
    Pm = P[MIR] * np.array([-1.0, 1.0, 1.0])
    asym = np.linalg.norm(P - Pm, axis=1)[MOK] * 1000
    out["asymmetry_p95_mm"] = round(float(np.percentile(asym, 95)), 2); out["asymmetry_max_mm"] = round(float(asym.max()), 2)
    # feet
    out["lowest_skin_vs_rest_floor_mm"] = round(float((P[:, 2].min() - z0) * 1000), 2)
    out["sole_slide_max_mm"] = round(float(np.linalg.norm((P - R)[SOLE][:, :2], axis=1).max() * 1000), 2)
    out["sole_lift_max_mm"] = round(float(((P - R)[SOLE][:, 2]).max() * 1000), 2)
    return out


REP = {"source": SRC.name, "r121_drives": USE_R121, "press_girdle": GIRDLE, "frames_per_trajectory": NF, "vertices": n,
       "regions": {k: int(v.sum()) for k, v in REG.items()}, "mirror_partners": int(MOK.sum()), "movements": {}}
FRAMES = {}
for mv in MOVES:
    rows = []; Ps = []
    for i in range(NF):
        u = i / (NF - 1)
        pose = MOVE_FN[mv](u); finish_pose()
        P = evaluated(); Ps.append(P)
        m = metrics(P); m.update(pose); m["u"] = round(u, 4)
        rows.append(m)
        print("TRAJ", mv, i, json.dumps({k: m[k] for k in ("edges_gt90", "edges_gt35", "self_intersections", "asymmetry_p95_mm")}), flush=True)
    ret = float(np.linalg.norm(Ps[-1] - Ps[0], axis=1).max() * 1000)
    peak = {k: max(r[k] for r in rows) for k in rows[0] if isinstance(rows[0][k], (int, float)) and not k.startswith(("u", "depth"))}
    REP["movements"][mv] = {"frames": rows, "return_to_neutral_max_mm": round(ret, 4), "peaks": peak}
    FRAMES[mv] = [0, NF // 4, NF // 2, (3 * NF) // 4]
    (OUT / "trajectory_report.json").write_text(json.dumps(REP, indent=1))

# ------------------------------------------------------------------ phone review sheets (workbench, cavity)
if RENDER:
    sc = bpy.context.scene
    for ob in sc.objects:
        if ob.type in ("MESH", "CURVE") and ob is not body:
            ob.hide_render = True
    cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
    sc.camera = cam; cd.ortho_scale = 2.05
    mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
    me.materials.clear(); me.materials.append(mat)
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_cavity = True; sc.render.resolution_x = 560; sc.render.resolution_y = 1000
    files = {}
    for mv in MOVES:
        for fi in FRAMES[mv]:
            MOVE_FN[mv](fi / (NF - 1)); finish_pose()
            centre = Vector((0.0, 0.0, z0 + 0.52 * H))
            for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "back": (0, 1, 0)}.items():
                dvec = Vector(dv); cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"
                cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
                f = OUT / f"frame_{mv}_{fi:02d}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
                files.setdefault((mv, view), []).append(str(f))
    bench._reset(rig)
    (OUT / "frames_index.json").write_text(json.dumps({"frames": FRAMES, "frames_per_trajectory": NF}))
print("TRAJECTORY done", flush=True)
