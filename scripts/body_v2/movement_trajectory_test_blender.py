"""Full-trajectory movement tests for a body_v2 blend (read-only; nothing is saved to the blend).

Trajectories (each starts and ends at neutral, so return-to-neutral is measured):
  press  - neutral (16 deg carriage, V2_TRAJ_PRESS_START) -> rack (humerothoracic 90 deg, elbow 90) -> lockout (160, elbow 0) -> rack -> neutral.  Shoulder from the
           r57 coupled path (correction.apply_corrected_pose: clavicle / scapula coupling + humeral axial rotation, plane
           40 deg) - the same path the r57 movement benchmark's shoulder_press uses (project-authored, not cohort-fit).
  curl   - elbow 0 -> 140 -> 0 with the arms at the sides (16 deg carriage).
  squat  - the r57 benchmark squat, depth 0 -> 1 -> 0, with a per-leg foot plant (V2_TRAJ_PLANT=0 for the raw r57 path).
  lateral_raise / front_raise (on request) - straight arms raised sideways / forwards from the 16 deg carriage to 90 deg
           and back, coupled girdle: movements the keys were not authored for, testing that the angle-driven keys
           generalise.
  deadlift / lunge (on request) - the r57 benchmark poses (deadlift: solved hip hinge with soft knees; lunge: one leg
           forward, asymmetric by design, so its asymmetry numbers are not meaningful).
  overhead_extension / pulldown (on request) - combinations no key was authored at: arms up the press path to 160 deg,
           then the elbows bend overhead to V2_TRAJ_OHE_ELBOW (130; forearms behind the head), or the arms are pulled
           down to V2_TRAJ_PULL_HT (50 deg) with the elbows bending to V2_TRAJ_PULL_ELBOW (130).
  external_rotation (on request) - arms at the sides, elbows at 90, humeral external rotation 0 -> V2_TRAJ_ER_DEG (60)
           -> 0: axial rotation alone.  internal_rotation: the same inwards to V2_TRAJ_IR_DEG (45).
  bent_over_row / walk_stride / trunk_rotation / single_leg_stance / calf_raise / push_up / forearm_rotation /
           wrist_circuit / grip (on request) - the rest of the r57 movement benchmark's poses, as authored there.
  hip_abduction / sumo_squat (on request) - both legs abducted to V2_TRAJ_HIP_ABD_DEG (35); the squat with the thighs
           abducted V2_TRAJ_SUMO_ABD (25) and turned out V2_TRAJ_SUMO_ER (25).  Skin tests: the feet are not planted.
  row (on request) - standing row: the humerus extends behind the trunk to V2_TRAJ_ROW_EXT (50 deg) with the elbows
           bending to V2_TRAJ_ROW_ELBOW (100).
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
ANIM = os.environ.get("V2_TRAJ_ANIM", "0") == "1"           # render EVERY frame from fixed cameras (MP4 frames):
ANIM_VIEWS = [v for v in os.environ.get("V2_TRAJ_ANIM_VIEWS", "front,side,back").split(",") if v]   # <out>/anim/
ANIM_ONLY = {int(x) for x in os.environ.get("V2_TRAJ_ANIM_ONLY", "").split(",") if x.strip()}   # stills: render only
# these frame indices (e.g. 0,4,7,8 of a 17-frame press = start, rack, near lockout, lockout); empty = every frame
ANIM_W, ANIM_H = (int(x) for x in os.environ.get("V2_TRAJ_ANIM_RES", "480x854").split("x"))         # <mv>_<view>_<i>.png
METRICS = os.environ.get("V2_TRAJ_METRICS", "1") == "1"      # 0: skip the per-frame metrics (animation-only runs)
BAKE_GLB = os.environ.get("V2_TRAJ_BAKE_GLB", "")           # path: export rig + body as a GLB with one animation per
# movement (bones and the driven shape-key weights baked per test frame); a REVIEW CANDIDATE, nothing is saved to a blend
BAKE_FPS = int(os.environ.get("V2_TRAJ_BAKE_FPS", "24"))
BAKE = {}
PLANT = os.environ.get("V2_TRAJ_PLANT", "1") == "1"
SQUAT_ARMS = os.environ.get("V2_TRAJ_SQUAT_ARMS", "hang")   # hang (r57 path) or forward (counterbalance cue)      # per-leg foot plant in the squat (the r57 path plants the mean only)
LUNGE_ARMS = os.environ.get("V2_TRAJ_LUNGE_ARMS", "bench")  # bench (r57 path: the hanging hands meet the rising front thigh)
#                                                          or side (22 deg abduction, as when carrying dumbbells at the sides)
HT0 = float(os.environ.get("V2_TRAJ_PRESS_START", "16"))   # press neutral: humerothoracic 16 deg (the standing carriage);
#                                                          0 points the arm straight down through the hip (test artifact)
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data
n = len(me.vertices)
UA_TWIST = os.environ.get("V2_TRAJ_UA_TWIST", "0") == "1"   # CANDIDATE upper-arm twist bones (upperarm_twist_candidate)
HELPER_SWING = os.environ.get("V2_TRAJ_UA_TWIST_HELPERS", "swing") == "swing"
TW_SOURCE = os.environ.get("V2_TRAJ_UA_TWIST_SOURCE", "band")   # band: the candidate's runtime rule (the pose's twist
#   outside the band the authored paths use); path: the axial rotation the test path itself added (diagnostics)
TW_CFG = {"end": float(os.environ.get("V2_TRAJ_UA_TWIST_END", "0.85")),
          "start": float(os.environ.get("V2_TRAJ_UA_TWIST_START", "0")),
          "power": float(os.environ.get("V2_TRAJ_UA_TWIST_POW", "1")),
          "shape": os.environ.get("V2_TRAJ_UA_TWIST_SHAPE", "smooth")}
if UA_TWIST:
    import upperarm_twist_candidate as uatw                   # in memory only: nothing is saved
    uatw.install(rig, body, **TW_CFG)
FA_REWEIGHT = os.environ.get("V2_TRAJ_FA_REWEIGHT", "0") == "1"   # CANDIDATE: forearm rotation kept out of the elbow
if FA_REWEIGHT:                                                  # crease (forearm_twist_candidate; in memory only)
    import forearm_twist_candidate as fatw
    FA_REWEIGHTED = fatw.reweight(rig, body)
PRUNE_N = int(os.environ.get("V2_TRAJ_PRUNE", "4" if os.environ.get("V2_TRAJ_PRUNE4", "0") == "1" else "0"))
PRUNE4 = PRUNE_N > 0                                             # APP CHECK: keep each vertex's N largest deform weights,
if PRUNE4:                                                       # renormalised (4: one glTF joint set, what stock three.js
                                                                 # plays; 8: two joint sets) - in memory
    _def = {b.name for b in rig.data.bones if b.use_deform}
    _gi = {g.index: g for g in body.vertex_groups if g.name in _def}
    PRUNED = 0
    for v in body.data.vertices:
        ws = sorted(((g.weight, g.group) for g in v.groups if g.group in _gi and g.weight > 0.0), reverse=True)
        if len(ws) > PRUNE_N:
            keep = ws[:PRUNE_N]; tot = sum(w for w, _ in keep)
            for w, gi in ws[PRUNE_N:]:
                _gi[gi].remove([v.index])
            for w, gi in keep:
                _gi[gi].add([v.index], w / tot, "REPLACE")
            PRUNED += 1
    print("PRUNE", PRUNE_N, "vertices", PRUNED, flush=True)
SAVE_POS = os.environ.get("V2_TRAJ_SAVE_POS", "0")            # 1: <out>/positions_<movement>.npy (frames x n x 3);
# bones: only <out>/deform_<movement>.npy (frames x deform bones x 3 x 4, world deform matrices) and <out>/binding.npz
# (rest positions, deform weights) - the training data for fit_app_binding.py; 1 also writes those
WEIGHTS4 = os.environ.get("V2_TRAJ_WEIGHTS4", "")               # APP BINDING: apply a fitted 4-influence binding (npz from
if WEIGHTS4:                                                     # fit_app_binding.py) in memory, replacing deform weights
    _z = np.load(WEIGHTS4, allow_pickle=False)
    _names = [str(x) for x in _z["bones"]]; _bi = _z["bone_idx"]; _bw = _z["weights"]
    _vg = {nm: body.vertex_groups.get(nm) or body.vertex_groups.new(name=nm) for nm in _names}
    _dset = set(_names)
    for g in body.vertex_groups:
        if g.name in _dset:
            g.remove(list(range(len(me.vertices))))
    for vi in range(len(me.vertices)):
        for k in range(_bi.shape[1]):
            if _bw[vi, k] > 0.0:
                _vg[_names[_bi[vi, k]]].add([vi], float(_bw[vi, k]), "REPLACE")
    print("WEIGHTS4 applied", WEIGHTS4, flush=True)
K1_WRIST = os.environ.get("V2_TRAJ_K1_WRIST_REBUILD", "0")      # CANDIDATE: re-author the K1 wrist keys on this surface
if K1_WRIST in ("1", "noguard"):                                 # (they date from before the R121 rebuild); in memory only
    import build_original_knee_contact_corrective_blender as k1
    for kb in [kb for kb in me.shape_keys.key_blocks if kb.name.startswith(k1.HINGES["wrist"]["prefix"])]:
        body.shape_key_remove(kb)
    if K1_WRIST == "noguard":
        k1.HINGES["wrist"] = {k: v for k, v in k1.HINGES["wrist"].items() if k != "guard"}
    _ev = bench._evaluated                                      # the K1 builder assumes triangles; this surface has quads
    bench._evaluated = lambda o: (lambda VF: (VF[0], [(f[0], f[i], f[i + 1]) for f in VF[1] for i in range(1, len(f) - 1)]))(_ev(o))
    k1.bench._evaluated = bench._evaluated
    K1_WRIST_LOG = k1.build({"body": body, "runtime": rig}, "wrist")
    bench._evaluated = k1.bench._evaluated = _ev
    bench._reset(rig)
TWIST = {"l": 0.0, "r": 0.0}                                  # rad: the axial rotation the test path added (path mode),
TW_DIAG = {}                                                  # then the twist the drive used


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
# ... and its rest normal must be the mirror of the vertex's: where the arms rest against the torso, torso and arm skin
# lie within the 4 mm tolerance of each other's mirror images but face opposite ways (512 such pairs on L4)
_N = np.empty(n * 3); me.vertices.foreach_get("normal", _N); _N = _N.reshape(-1, 3)
MOK &= np.einsum("ij,ij->i", _N, _N[MIR] * np.array([-1.0, 1.0, 1.0])) > 0.7
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
    bpy.context.view_layer.update()
    if UA_TWIST:
        tw, diag = uatw.drive(rig, body, drives.drive, twist=dict(TWIST) if TW_SOURCE == "path" else None,
                              helpers_swing=HELPER_SWING)
        TWIST.update(tw); TW_DIAG.clear(); TW_DIAG.update(diag)
    else:
        drives.drive(rig, body)
    if USE_R121:
        r121_drives.drive(rig, body)
    else:
        for kb in me.shape_keys.key_blocks:
            if kb.name.startswith(("R121_ARM_", "R121_FLEX_", "R121_HIP_", "R121_ELBOW_", "R121_KNEE_", "R121_COMBO_", "R121_REST_", "R121_WRIST_", "R121_WFLEX_", "R121_EXT_", "R121_GRIP_", "R121_ARMBAND_")):
                kb.value = 0.0
    if MUTE_KEYS:                                            # diagnosis: these key families off after the drives ran
        for kb in me.shape_keys.key_blocks[1:]:
            if MUTE_KEYS == ("*",) or kb.name.startswith(MUTE_KEYS):
                kb.value = 0.0
    bpy.context.view_layer.update()


MUTE_KEYS = tuple(x for x in os.environ.get("V2_TRAJ_MUTE_KEYS", "").split(",") if x)   # prefixes, or * for all


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


def press_pose(ht, elb):
    """the press's shoulder (girdle + humeral axial rotation for this humerothoracic elevation), then the elbows"""
    bench._reset(rig)
    if GIRDLE == "candidate":
        girdle.apply_press_pose(rig, ht, RESULT["humeral_rest_axial_deg"])
    else:
        correction.apply_corrected_pose(RESULT, ht)
    elbows(elb)


OHE_ELBOW = float(os.environ.get("V2_TRAJ_OHE_ELBOW", "130"))
PULL_HT, PULL_ELBOW = float(os.environ.get("V2_TRAJ_PULL_HT", "50")), float(os.environ.get("V2_TRAJ_PULL_ELBOW", "130"))


OHE_PATH = os.environ.get("V2_TRAJ_OHE_PATH", "front")      # front: up the forward-raise path (elbows forwards);
                                                           # press: the press path, the humerus then turned about its
                                                           # axis so the forearms still go back (V2_TRAJ_OHE_BACK)
OHE_BACK = os.environ.get("V2_TRAJ_OHE_BACK", "1") == "1"


def turn_forearms_back(frac):
    """turn each humerus about its own axis (by frac of the needed angle) so that elbow flexion carries the forearm
    backwards (+y), behind the head, instead of in the press's flexion plane (medially, hands into each other)"""
    from mathutils import Matrix
    out = {}
    for s_ in ("l", "r"):
        ub, fb = rig.pose.bones[f"upperarm_{s_}"], rig.pose.bones[f"forearm_{s_}"]
        e0 = fb.rotation_euler.copy(); fb.rotation_mode = "XYZ"
        t0 = fb.tail.copy(); fb.rotation_euler = (e0.x - math.radians(10.0), e0.y, e0.z); bpy.context.view_layer.update()
        mv = fb.tail - t0; fb.rotation_euler = e0; bpy.context.view_layer.update()
        d = (ub.tail - ub.head).normalized(); mv = mv - d * mv.dot(d); want = Vector((0.0, 1.0, 0.0)); want = want - d * want.dot(d)
        if mv.length < 1e-9 or want.length < 1e-9:
            continue
        mv.normalize(); want.normalize()
        ang = math.atan2(mv.cross(want).dot(d), mv.dot(want)) * frac; piv = ub.head.copy()
        ub.matrix = Matrix.Translation(piv) @ Matrix.Rotation(ang, 4, d) @ Matrix.Translation(-piv) @ ub.matrix
        bpy.context.view_layer.update(); out[s_] = round(math.degrees(ang), 1); TWIST[s_] = ang
    return out


ER_TOP = float(os.environ.get("V2_TRAJ_ER_DEG", "60"))


def turn_humeri(deg):
    """humeral axial rotation by deg on both sides, + = external (with the elbow bent, the hand swings outwards)"""
    from mathutils import Matrix
    for s_ in ("l", "r"):
        ub, fb = rig.pose.bones[f"upperarm_{s_}"], rig.pose.bones[f"forearm_{s_}"]
        d = (ub.tail - ub.head).normalized(); piv = ub.head.copy(); h0 = fb.tail.copy()
        lat = 1.0 if ub.head.x > 0 else -1.0
        probe = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(5.0), 4, d) @ Matrix.Translation(-piv)
        sg = 1.0 if ((probe @ h0) - h0).x * lat > 0 else -1.0
        ub.matrix = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(sg * deg), 4, d) @ Matrix.Translation(-piv) @ ub.matrix
        bpy.context.view_layer.update(); TWIST[s_] = math.radians(sg * deg)


def _rotation_at_side(u, top):
    p = 1.0 - abs(2.0 * u - 1.0); er = top * bench.smooth(p)
    bench._reset(rig)
    for sd, sg in (("r", -1.0), ("l", 1.0)):
        pb = rig.pose.bones[f"upperarm_{sd}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, 0.0, math.radians(sg * 16.0))
    bpy.context.view_layer.update(); elbows(90.0); turn_humeri(er)
    return {"external_rotation_deg": round(er, 2), "elbow_flexion_deg": 90.0}


def external_rotation(u):
    """the rotator-cuff staple: upper arms at the sides (16 deg carriage, as the curl), elbows at 90, the humerus turned
    outwards about its own axis to ER_TOP (60) and back - humeral axial rotation alone, which no key is indexed by"""
    return _rotation_at_side(u, ER_TOP)


IR_TOP = float(os.environ.get("V2_TRAJ_IR_DEG", "45"))
ROW_EXT, ROW_ELBOW = float(os.environ.get("V2_TRAJ_ROW_EXT", "50")), float(os.environ.get("V2_TRAJ_ROW_ELBOW", "100"))
ROW_PLANE = float(os.environ.get("V2_TRAJ_ROW_PLANE", "-70"))   # -90: straight back, the humerus then has no outward
#                                                          component and its inner side passes through the trunk's side


def internal_rotation(u):
    """as external_rotation, turned inwards to IR_TOP (45; the forearm reaches the abdomen not far beyond)"""
    return _rotation_at_side(u, -IR_TOP)


def row(u):
    """standing row: from the standing carriage the humerus goes back and a little out (plane ROW_PLANE, -70) to ROW_EXT
    (50) while the elbows bend to ROW_ELBOW (100), and back - a region no arm key was authored in (the raises go
    forwards and sideways)"""
    p = 1.0 - abs(2.0 * u - 1.0); k = bench.smooth(p); e = HT0 + (ROW_EXT - HT0) * k; pl = ROW_PLANE * k
    bench._reset(rig); girdle.apply_arm_pose(rig, e, pl); elbows(ROW_ELBOW * k)   # from the standing carriage
    return {"humeral_extension_deg": round(e, 2), "plane_deg": round(pl, 1), "elbow_flexion_deg": round(ROW_ELBOW * k, 2)}


def overhead_extension(u):
    """overhead triceps extension: straight arms up to 160 deg (OHE_PATH: the forward-raise path, elbows forwards, by
    default; or the press path), then the elbows bend to
    OHE_ELBOW with the arm held overhead and back.  With OHE_BACK the humerus turns about its own axis as the elbow
    starts to bend, so the forearms go back behind the head as in the exercise, not into each other.  The overhead
    shoulder keys and the elbow keys are on together, a combination neither was authored at."""
    p = 1.0 - abs(2.0 * u - 1.0)
    if p <= 0.5:
        k = bench.smooth(p / 0.5); ht, elb = HT0 + (160.0 - HT0) * k, 0.0
    else:
        k = bench.smooth((p - 0.5) / 0.5); ht, elb = 160.0, OHE_ELBOW * k
    if OHE_PATH == "front":
        bench._reset(rig); girdle.apply_arm_pose(rig, ht, 90.0)
    else:
        press_pose(ht, 0.0)
    turned = turn_forearms_back(min(1.0, 2.0 * bench.smooth(max(0.0, (p - 0.5) / 0.5)))) if OHE_BACK else {}
    elbows(elb)
    return {"humerothoracic_target_deg": round(ht, 2), "elbow_flexion_deg": round(elb, 2), "humeral_turn_deg": turned}


def pulldown(u):
    """lat pulldown / pull-up: straight arms up the press path to 160 deg, then pulled down to PULL_HT with the elbows
    bending to PULL_ELBOW (hands by the shoulders), and back - deeper elbow flexion at lower elevation than the press's
    rack (90 / 90)"""
    p = 1.0 - abs(2.0 * u - 1.0)
    if p <= 0.5:
        k = bench.smooth(p / 0.5); ht, elb = HT0 + (160.0 - HT0) * k, 0.0
    else:
        k = bench.smooth((p - 0.5) / 0.5); ht, elb = 160.0 - (160.0 - PULL_HT) * k, PULL_ELBOW * k
    press_pose(ht, elb)
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


def deadlift(u):
    out = bench.pose_deadlift(rig, 1.0 - abs(2.0 * u - 1.0), REST_HEADS)
    if PLANT:                                                       # same per-leg plant as the squat
        plant_feet()
    return {k: round(float(v), 2) for k, v in out.items()}


def lunge(u):
    out = {k: round(float(v), 2) for k, v in bench.pose_lunge(rig, body, 1.0 - abs(2.0 * u - 1.0)).items()}
    if LUNGE_ARMS == "side":
        girdle.apply_arm_pose(rig, 22.0, 0.0, reset=False)
    return out


def raise_in_plane(plane_deg, top=90.0):
    """straight-arm raise in a fixed plane (0 = sideways / lateral raise, 90 = forwards / front raise), from the 16 deg
    standing carriage to `top` deg humerothoracic elevation and back, with the coupled girdle (apply_arm_pose)"""
    def fn(u):
        p = 1.0 - abs(2.0 * u - 1.0); e = HT0 + (top - HT0) * bench.smooth(p)
        bench._reset(rig)
        girdle.apply_arm_pose(rig, e, plane_deg)
        elbows(0.0)
        return {"humerothoracic_target_deg": round(e, 2), "plane_deg": plane_deg}
    return fn


HIP_ABD = float(os.environ.get("V2_TRAJ_HIP_ABD_DEG", "35"))
SUMO_ABD, SUMO_ER = float(os.environ.get("V2_TRAJ_SUMO_ABD", "25")), float(os.environ.get("V2_TRAJ_SUMO_ER", "25"))


def _turn_thighs(abd, er=0.0):
    """each thigh abducted by abd (about the pelvis's anterior-posterior axis through its hip; the foot moves outwards)
    and turned outwards about its own axis by er (the knee points outwards)"""
    from mathutils import Matrix
    pel = rig.pose.bones["pelvis"]
    ap = (pel.matrix.to_3x3() @ rig.data.bones["pelvis"].matrix_local.to_3x3().inverted()) @ Vector((0.0, 1.0, 0.0))
    for s_ in ("l", "r"):
        th = rig.pose.bones[f"thigh_{s_}"]; hip = th.head.copy(); lat = 1.0 if hip.x > 0 else -1.0
        t0 = th.tail.copy(); probe = Matrix.Translation(hip) @ Matrix.Rotation(math.radians(5.0), 4, ap) @ Matrix.Translation(-hip)
        sg = 1.0 if ((probe @ t0) - t0).x * lat > 0 else -1.0
        th.matrix = Matrix.Translation(hip) @ Matrix.Rotation(math.radians(sg * abd), 4, ap) @ Matrix.Translation(-hip) @ th.matrix
        bpy.context.view_layer.update()
        if er:
            d = (th.tail - th.head).normalized(); kn = th.tail.copy(); fwd = Vector((0.0, -1.0, 0.0))
            pr = Matrix.Translation(hip) @ Matrix.Rotation(math.radians(5.0), 4, d) @ Matrix.Translation(-hip)
            sh = rig.pose.bones[f"shin_{s_}"]; kp = sh.tail.copy()   # with the knee bent, the shin swings outwards
            sg2 = 1.0 if ((pr @ kp) - kp).x * lat > 0 else -1.0
            th.matrix = Matrix.Translation(hip) @ Matrix.Rotation(math.radians(sg2 * er), 4, d) @ Matrix.Translation(-hip) @ th.matrix
            bpy.context.view_layer.update()


def hip_abduction(u):
    """standing, arms 45 deg out sideways, both legs abducted to HIP_ABD (35) and back, knees straight (a skin test: the
    feet leave the floor)"""
    p = 1.0 - abs(2.0 * u - 1.0); a = HIP_ABD * bench.smooth(p)
    bench._reset(rig); girdle.apply_arm_pose(rig, 45.0, 0.0)   # arms out sideways: the legs swing into hanging hands
    _turn_thighs(a)
    return {"hip_abduction_deg": round(a, 2)}


def sumo_squat(u):
    """the benchmark squat with the thighs abducted SUMO_ABD (25) and turned out SUMO_ER (25) - knees out over a wide
    stance (a skin test: the feet are not re-planted)"""
    p = 1.0 - abs(2.0 * u - 1.0); k = bench.smooth(p)
    out = bench.pose_squat(rig, p, REST_HEADS)
    _turn_thighs(SUMO_ABD * k, SUMO_ER * k)
    if SQUAT_ARMS == "forward":
        girdle.apply_arm_pose(rig, 16.0 + 74.0 * bench.smooth(min(1.0, p / 0.6)), 90.0, reset=False)
    return {k_: round(float(v), 2) for k_, v in out.items()} | {"depth": round(p, 3), "hip_abduction_deg": round(SUMO_ABD * k, 2)}


def _clavicle_basis():
    import build_functional_original_coupled_motion_blender as coupled
    return coupled.clavicle_basis


BENCH_CARRY = float(os.environ.get("V2_TRAJ_BENCH_CARRY", "0"))   # extra arm carriage (deg, about the thorax's AP
#   axis) on the benchmark's row / trunk rotation / walk / single-leg poses: its 4 deg (row: none) lets the hanging hands
#   and the extending humerus meet the hips, thighs and the trunk's side


PUSHUP_GIRDLE = os.environ.get("V2_TRAJ_PUSHUP_GIRDLE", "0") == "1"   # the benchmark's push-up moves no shoulder
#   girdle; with this the coupled girdle for each arm's measured elevation is applied and the humerus re-aimed along
#   its benchmark direction (forearm and hand follow), as every shoulder key was authored


GRIP_GIRDLE = os.environ.get("V2_TRAJ_GRIP_GIRDLE", "0") == "1"   # the benchmark's grip holds the arms forward 45 deg
# with no shoulder-girdle motion (shoulder keys were authored with the coupled girdle): same option as the push-up's


def _with_girdle(out, enabled=None):
    if not (PUSHUP_GIRDLE if enabled is None else enabled):
        return out
    import functional_original_coupled_motion as motion
    from mathutils import Matrix
    dirs = {s_: (rig.pose.bones[f"upperarm_{s_}"].tail - rig.pose.bones[f"upperarm_{s_}"].head).normalized() for s_ in ("l", "r")}
    e = sum(drives.elevation_deg(rig, s_) for s_ in ("l", "r")) / 2.0
    for s_ in ("l", "r"):                                    # the girdle is set from its rest (the benchmark set none)
        for nm in ("clavicle", "scapula"):
            rig.pose.bones[f"{nm}_{s_}"].matrix_basis.identity()
    bpy.context.view_layer.update()
    girdle.apply_girdle(rig, motion.pose_profile(min(max(e, 0.0), 160.0)))
    for s_ in ("l", "r"):
        ub = rig.pose.bones[f"upperarm_{s_}"]; piv = ub.head.copy(); cur = (ub.tail - ub.head).normalized()
        ub.matrix = Matrix.Translation(piv) @ cur.rotation_difference(dirs[s_]).to_matrix().to_4x4() @ Matrix.Translation(-piv) @ ub.matrix
        bpy.context.view_layer.update()
    return {**(out or {}), "girdle_elevation_deg": round(e, 1)}


WALK_CYCLE = os.environ.get("V2_TRAJ_WALK_CYCLE", "forward")   # forward: the r57 stride is a whole gait cycle (its t = 0
# and t = 1 are the same heel strike), so the walk plays it once, forward, and loops; outback (runs before 1 Nov 2026):
# t = 0 -> 1 -> 0 like the other movements, i.e. the cycle forward and then the same cycle walked backwards


def _bench(fn, u, carry=False, cyclic=False):
    """an r57 benchmark pose at t = 0 -> 1 -> 0, or t = 0 -> 1 for a cyclic one (its numbers rounded into the record)"""
    out = fn(u if cyclic else 1.0 - abs(2.0 * u - 1.0)) or {}
    if carry and BENCH_CARRY:
        bench._carry_arms(rig, BENCH_CARRY)
    return {k: (round(float(v), 2) if isinstance(v, (int, float)) else v) for k, v in out.items()
            if isinstance(v, (int, float, str))}


GRIP_COLLAPSE = os.environ.get("V2_TRAJ_GRIP_COLLAPSE", "fist")   # the grip's thumb search (r57 _solve_thumb) accepts a
# placement only with no collapsed hand face; on this surface the closed fist alone collapses 20-23 palmar-knuckle faces
# per hand (80 deg MCP flexion; 0 at 40 deg), so every placement was rejected and the grip never ran.  fist: the thumb may
# not ADD collapse beyond the fist's own (measured with the fingers closed, thumb at rest); strict: the r57 rule.
GRIP_BASE = {}
if GRIP_COLLAPSE == "fist":
    _solve0, _coll0 = bench._solve_thumb, bench._hand_collapse

    def _solve_thumb_vs_fist(rig_, s, signs, body_=None):
        # the baseline is the closed fist WITH the thumb's own MCP / IP flexion (the search applies it before every
        # candidate; measured without it, its few crease faces counted as "added" collapse and every placement failed)
        pb_ = rig_.pose.bones
        bench._rot(pb_[f"thumb_02_{s}"], z=signs[f"thumb_02_{s}"] * bench.THUMB_OPPOSITION["mcp_deg"])
        bench._rot(pb_[f"thumb_03_{s}"], z=signs[f"thumb_03_{s}"] * bench.THUMB_OPPOSITION["ip_deg"])
        bpy.context.view_layer.update()
        base = GRIP_BASE[s] = _coll0(body_, s) if body_ is not None else 0
        bench._hand_collapse = lambda b, s_: max(0, _coll0(b, s_) - base)
        lim0 = bench.THUMB_OPPOSITION["max_pairs"]
        try:
            for lim in (() if os.environ.get("V2_TRAJ_GRIP_SKELETON_THUMB") == "1" else (lim0, 10, 20, 40, 80)):              # the r57 limit (5 thumb / finger pairs) first, then relaxed
                bench.THUMB_OPPOSITION["max_pairs"] = lim
                try:
                    out = _solve0(rig_, s, signs, body_)
                    GRIP_BASE[s + "_pair_limit_used"] = lim
                    return out
                except RuntimeError:
                    continue
            # no placement satisfies the mesh rules (the thumb's own MCP / IP flexion already collapses a few crease faces
            # in every candidate): use the r57 SKELETON-only solution (closest tip, bony clearance) - independent of the
            # mesh under test, so every model plays the same thumb; its skin contacts are measured, not hidden
            GRIP_BASE[s + "_pair_limit_used"] = "skeleton-only (no mesh placement within 80 pairs)"
            return _solve0(rig_, s, signs, None)
        finally:
            bench._hand_collapse = _coll0; bench.THUMB_OPPOSITION["max_pairs"] = lim0
    bench._solve_thumb = _solve_thumb_vs_fist
GRIP_THUMB = os.environ.get("V2_TRAJ_GRIP_THUMB", "")           # json: load the solved thumb placement if the file exists
if GRIP_THUMB and Path(GRIP_THUMB).exists():                    # (same thumb path for every model), else save it there
    bench._THUMB_CACHE["solution"] = {k: (tuple(v[0]), v[1]) for k, v in json.loads(Path(GRIP_THUMB).read_text()).items()}


MOVE_FN = {"press": press, "curl": curl, "squat": squat,
           "lateral_raise": raise_in_plane(0.0), "front_raise": raise_in_plane(90.0),
           "deadlift": lambda u: deadlift(u), "overhead_extension": overhead_extension, "pulldown": pulldown,
           "external_rotation": external_rotation, "internal_rotation": internal_rotation, "row": row,
           "hip_abduction": hip_abduction, "sumo_squat": sumo_squat,
           # the rest of the r57 movement benchmark, as authored there (out and back here)
           "bent_over_row": lambda u: _bench(lambda t: bench.pose_row(rig, t, REST_HEADS, _clavicle_basis()), u, carry=True),
           "walk_stride": lambda u: _bench(lambda t: bench.pose_walk(rig, body, t), u, carry=True,
                                           cyclic=WALK_CYCLE == "forward"),
           "trunk_rotation": lambda u: _bench(lambda t: bench.pose_trunk_rotation(rig, body, t), u, carry=True),
           "single_leg_stance": lambda u: _bench(lambda t: bench.pose_single_leg(rig, body, t), u, carry=True),
           "calf_raise": lambda u: _bench(lambda t: bench.pose_calf_raise(rig, body, t), u),
           "push_up": lambda u: _bench(lambda t: _with_girdle(bench.pose_pushup(rig, body, t)), u),
           "forearm_rotation": lambda u: _bench(lambda t: bench.pose_forearm_rotation(rig, body, t), u),
           "wrist_circuit": lambda u: _bench(lambda t: bench.pose_wrist(rig, body, t), u),
           "grip": lambda u: _bench(lambda t: _with_girdle(bench.pose_grip(rig, body, t), GRIP_GIRDLE), u),
           "lunge": lambda u: lunge(u)}


KEY_DIAG = os.environ.get("V2_TRAJ_KEY_DIAG", "0") == "1"   # per frame: which shape keys push the arm root outward,
# and the arm-root girth with and without keys (diagnosis: corrective keys vs skinning vs bones; read-only)
if KEY_DIAG:
    _B0 = np.empty(n * 3); me.shape_keys.key_blocks[0].data.foreach_get("co", _B0); _B0 = _B0.reshape(-1, 3)
    _KD = {}
    for s_ in ("l", "r"):
        ub = rig.data.bones[f"upperarm_{s_}"]; h_ = np.array(rig.matrix_world @ ub.head_local)
        t_ = np.array(rig.matrix_world @ ub.tail_local); L_ = np.linalg.norm(t_ - h_); ax_ = (t_ - h_) / L_
        rel = R - h_; along = rel @ ax_ / L_; rad = rel - np.outer(rel @ ax_, ax_); rr = np.linalg.norm(rad, axis=1)
        root = (along > -0.15) & (along < 0.45) & (rr < 0.11) & (np.abs(R[:, 0]) > 0.12)   # the arm root, rest space
        ring = root & (np.abs(along - 0.30) < 0.04)          # a girth ring 30 % down the humerus
        out_dir = np.where(rr[:, None] > 1e-6, rad / np.maximum(rr, 1e-6)[:, None], 0.0)
        arm = (rr < 0.11) & (gw(f"upperarm_{s_}", f"upperarm_tw_{s_}") >= 0.5)   # skin that follows the humerus
        bins = {round(b, 1): np.where(arm & (np.abs(along - b) < 0.04))[0] for b in np.arange(-0.1, 0.95, 0.1)}
        _KD[s_] = dict(h=h_, L=L_, root=np.where(root)[0], ring=np.where(ring)[0], out=out_dir, rr=rr, bins=bins)


def key_diag():
    """rest-space attribution: per active key, the mean outward (from the humerus axis) offset x value over the arm
    root, mm; and the posed girth ring's mean radius relative to its humerus, with keys and with every key at 0"""
    kbs = me.shape_keys.key_blocks; res = {}
    acts = [(kb.name, kb.value) for kb in kbs[1:] if abs(kb.value) > 0.01 and not kb.mute]
    tmp = np.empty(n * 3)
    for s_ in ("l", "r"):
        d_ = _KD[s_]; idx = d_["root"]; contrib = []
        for name, val in acts:
            kbs[name].data.foreach_get("co", tmp); off = (tmp.reshape(-1, 3)[idx] - _B0[idx]) * val
            o = (off * d_["out"][idx]).sum(1)
            if np.abs(o).max() > 0.0005:
                contrib.append((name, round(float(val), 3), round(float(o.mean() * 1000), 2), round(float(o.max() * 1000), 1)))
        contrib.sort(key=lambda c: -c[3])
        res[s_] = {"keys_outward_mean_max_mm": contrib[:8]}
    def girth(P):
        g = {}
        for s_ in ("l", "r"):
            pb = rig.pose.bones[f"upperarm_{s_}"]; h_ = np.array(rig.matrix_world @ pb.head); t_ = np.array(rig.matrix_world @ pb.tail)
            ax_ = (t_ - h_) / np.linalg.norm(t_ - h_)
            def rad(ix):
                rel = P[ix] - h_
                return float(np.linalg.norm(rel - np.outer(rel @ ax_, ax_), axis=1).mean() * 1000) if len(ix) else 0.0
            g[s_] = rad(_KD[s_]["ring"]) / 1000.0
            g[s_ + "_profile"] = {b: round(rad(ix), 1) for b, ix in _KD[s_]["bins"].items()}
        return g
    P1 = evaluated(); g1 = girth(P1)
    vals = [kb.value for kb in kbs]
    for kb in kbs[1:]:
        kb.value = 0.0
    g0 = girth(evaluated())
    for kb, v in zip(kbs, vals):
        kb.value = v
    bpy.context.view_layer.update()
    for s_ in ("l", "r"):
        r0 = float(_KD[s_]["rr"][_KD[s_]["ring"]].mean())
        res[s_].update(ring_radius_rest_mm=round(r0 * 1000, 1), ring_radius_posed_mm=round(g1[s_] * 1000, 1),
                       ring_radius_lbs_only_mm=round(g0[s_] * 1000, 1),
                       profile_rest_mm={b: round(float(_KD[s_]["rr"][ix].mean() * 1000), 1) if len(ix) else 0.0
                                        for b, ix in _KD[s_]["bins"].items()},
                       profile_posed_mm=g1[s_ + "_profile"], profile_lbs_only_mm=g0[s_ + "_profile"])
    return res


DIAG_GROUPS = os.environ.get("V2_TRAJ_DIAG_GROUPS", "0") == "1"
if DIAG_GROUPS:
    _gn = {g.index: g.name for g in body.vertex_groups}
    DOMG = [(_gn[max(v.groups, key=lambda e: e.weight).group] if len(v.groups) else "none") for v in me.vertices]


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
    if DIAG_GROUPS and len(pairs):                              # (diagnostics) dominant vertex group of each crossing
        cnt = {}                                                # triangle pair, as "group a | group b"
        for i, j in pairs:
            k = "|".join(sorted((DOMG[TRI[i][0]], DOMG[TRI[j][0]])))
            cnt[k] = cnt.get(k, 0) + 1
        out["self_intersections_by_group"] = dict(sorted(cnt.items(), key=lambda t: -t[1])[:8])
        cen = (P[TRI[pairs[:, 0]]].mean(axis=1) + P[TRI[pairs[:, 1]]].mean(axis=1)) / 2.0   # where they are, per side
        out["self_intersections_where_mm"] = {
            sd: {"n": int(m_.sum()), "centroid": [round(float(x) * 1000, 1) for x in cen[m_].mean(axis=0)]}
            for sd, m_ in (("x>0", cen[:, 0] > 0), ("x<0", cen[:, 0] <= 0)) if m_.any()}
    if DIAG_GROUPS and (d < 0.0).any():                         # (diagnostics) dominant vertex group of each fold edge
        fe = np.nonzero(d < 0.0)[0]; cnt = {}
        for e_ in fe:
            k = DOMG[int(EF[e_, 0])]
            cnt[k] = cnt.get(k, 0) + 1
        out["folds_gt90_by_group"] = dict(sorted(cnt.items(), key=lambda t: -t[1])[:8])
    if DIAG_GROUPS:                                             # (diagnostics) the shape keys active on this frame
        act = [(kb.name, kb.value) for kb in me.shape_keys.key_blocks[1:] if abs(kb.value) > 0.02]
        out["active_keys"] = {k: round(v, 3) for k, v in sorted(act, key=lambda t: -abs(t[1]))[:16]}
    # symmetry
    Pm = P[MIR] * np.array([-1.0, 1.0, 1.0])
    asym = np.linalg.norm(P - Pm, axis=1)[MOK] * 1000
    out["asymmetry_p95_mm"] = round(float(np.percentile(asym, 95)), 2); out["asymmetry_max_mm"] = round(float(asym.max()), 2)
    # feet
    out["lowest_skin_vs_rest_floor_mm"] = round(float((P[:, 2].min() - z0) * 1000), 2)
    out["sole_slide_max_mm"] = round(float(np.linalg.norm((P - R)[SOLE][:, :2], axis=1).max() * 1000), 2)
    out["sole_lift_max_mm"] = round(float(((P - R)[SOLE][:, 2]).max() * 1000), 2)
    return out


REP = {"source": SRC.name, "r121_drives": USE_R121, "press_girdle": GIRDLE, "upper_arm_twist_prototype": UA_TWIST,
       "upper_arm_twist": {"source": TW_SOURCE, **TW_CFG, "helpers": "swing" if HELPER_SWING else "full"} if UA_TWIST else None,
       "forearm_crease_reweight": {"t0": fatw.T0, "t1": fatw.T1, "vertices": FA_REWEIGHTED} if FA_REWEIGHT else None,
       "k1_wrist_rebuilt": K1_WRIST_LOG if K1_WRIST in ("1", "noguard") else None,
       "girdle_frame": os.environ.get("V2_GIRDLE_FRAME", "plane35"), "squat_arms": SQUAT_ARMS, "lunge_arms": LUNGE_ARMS,
       "frames_per_trajectory": NF, "vertices": n,
       "regions": {k: int(v.sum()) for k, v in REG.items()}, "mirror_partners": int(MOK.sum()), "movements": {}}
# ------------------------------------------------------------------ renders (workbench, cavity; review only)
VIEWS = {"front": ((0, -1, 0), 0.635, 2.45), "side": ((1, 0, 0), 0.635, 2.45), "back": ((0, 1, 0), 0.635, 2.45),
         "back_upper": ((0, 1, 0), 0.80, 1.05), "front_upper": ((0, -1, 0), 0.80, 1.05),
         "side_upper": ((1, 0, 0), 0.80, 1.05),
         # three-quarter front (camera to the front-right, 45 deg): whole body and shoulders
         "front34": ((0.7071, -0.7071, 0), 0.635, 2.45), "front34_upper": ((0.7071, -0.7071, 0), 0.80, 1.05),
         # hinged trunk (bent-over row): the shoulders sit near mid-height
         "back_mid": ((0, 1, 0), 0.52, 1.3), "side_mid": ((1, 0, 0), 0.52, 1.3),
         # horizontal body (push-up): wide frames near the floor
         "side_wide": ((1, 0, 0), 0.30, 3.6), "front_wide": ((0, -1, 0), 0.30, 3.6),
         "side_low": ((1, 0, 0), 0.22, 1.6)}   # view: (camera direction, centre height / H, ortho scale m)
# framed per movement from the SKELETON (bone heads and tails at neutral and at the turning point), rounded to 5 cm -
# fixed for every frame of the movement and identical for any model on this rig: (direction, focus bones or None = the
# whole skeleton with a margin, ortho scale for focus views)
AUTO_VIEWS = {"front_fit": ((0, -1, 0), None, None), "side_fit": ((1, 0, 0), None, None), "back_fit": ((0, 1, 0), None, None),
              "back_top": ((0, 0.55, 0.85), ("upperarm_l", "upperarm_r", "spine_03"), 1.15),
              "side_shoulder": ((1, 0, 0), ("upperarm_l", "upperarm_r", "clavicle_l", "clavicle_r"), 1.0),
              "front_shoulder": ((0, -1, 0), ("upperarm_l", "upperarm_r", "clavicle_l", "clavicle_r"), 1.0),
              "hands_front": ((0, -1, 0), ("hand_l", "hand_r"), 1.3),
              "hand_l_side": ((1, 0, 0), ("hand_l", "forearm_l"), 0.6),
              # the posterior shoulders close up, from behind / above / outside (mirror pair; left is -x)
              "post_shoulder_l": ((-0.5, 0.6, 0.62), ("upperarm_l", "scapula_l"), 0.5),
              "post_shoulder_r": ((0.5, 0.6, 0.62), ("upperarm_r", "scapula_r"), 0.5),
              # the left upper arm from behind, centred between the shoulder and the elbow at the turning point
              # (the triceps bands at the press lockout)
              "arm_back_l": ((0, 1, 0), ("upperarm_l", "forearm_l"), 0.5)}
CAM_FIT = {}


def fit_cameras(mv, views):
    """per-movement camera centres / scales from the skeleton at u = 0 and the turning point (u = 0.5)"""
    pts = []
    for u in (0.0, 0.5):
        TWIST.update(l=0.0, r=0.0); MOVE_FN[mv](u); finish_pose()
        for pb in rig.pose.bones:
            pts.append(np.array(rig.matrix_world @ pb.head)); pts.append(np.array(rig.matrix_world @ pb.tail))
        if u == 0.5:
            focus = {pb.name: np.array(rig.matrix_world @ pb.head) for pb in rig.pose.bones}
    P_ = np.array(pts); lo_, hi_ = P_.min(0), P_.max(0); lo_[2] = min(lo_[2], z0)
    aspect = ANIM_W / ANIM_H
    for v in views:
        if v not in AUTO_VIEWS:
            continue
        dv, fb, sc_ = AUTO_VIEWS[v]; d_ = np.array(dv, float); d_ /= np.linalg.norm(d_)
        if fb is None:                                  # whole skeleton + margin (skin ~ 0.15 m beyond the bones)
            c = (lo_ + hi_) / 2; ext = hi_ - lo_ + 0.30
            horiz = ext[1] if abs(d_[0]) > 0.5 else ext[0]
            sc_ = max(ext[2], horiz / aspect) * 1.08
        else:
            c = np.mean([focus[b] for b in fb if b in focus], 0)
        c = np.round(c / 0.05) * 0.05; sc_ = float(np.ceil(sc_ / 0.05) * 0.05)
        CAM_FIT.setdefault(mv, {})[v] = (Vector(c.tolist()), sc_)

_RSET = {}


def setup_render():
    """camera, floor and the review material, once (other meshes hidden; nothing is saved)"""
    if _RSET:
        return _RSET
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
    _RSET.update(sc=sc, cam=cam, cd=cd)
    if ANIM:                                                 # light ground, display colours, a floor at the rest
        if sc.world is None:                                 # sole height (cameras 7 deg above it), so contact reads
            sc.world = bpy.data.worlds.new("REVIEW_ONLY")
        sc.world.color = (0.86, 0.88, 0.88); sc.view_settings.view_transform = "Standard"
        mat.diffuse_color = (0.80, 0.60, 0.48, 1)
        fm = bpy.data.meshes.new("FLOOR_REVIEW_ONLY"); a = 3.0
        fm.from_pydata([(-a, -a, z0), (a, -a, z0), (a, a, z0), (-a, a, z0)], [], [(0, 1, 2, 3)])
        fo = bpy.data.objects.new("FLOOR_REVIEW_ONLY", fm); sc.collection.objects.link(fo)
        fmat = bpy.data.materials.new("FLOOR_REVIEW_ONLY"); fmat.diffuse_color = (.80, .82, .84, 1); fm.materials.append(fmat)
        sc.display.shading.show_shadows = True
    return _RSET


def render_views(mv, i, views, out_dir, res):
    """render the current (posed, driven) frame from fixed cameras: identical for every model and frame"""
    r = setup_render(); sc, cam, cd = r["sc"], r["cam"], r["cd"]
    out_dir.mkdir(parents=True, exist_ok=True)
    sc.render.resolution_x, sc.render.resolution_y = res
    for view in views:
        if view in AUTO_VIEWS:
            dvec = Vector(AUTO_VIEWS[view][0]) + Vector((0.0, 0.0, 0.12)); dvec.normalize()
            centre, scale = CAM_FIT[mv][view]
        else:
            dv, hc, scale = VIEWS[view]
            dvec = Vector(dv) + Vector((0.0, 0.0, 0.12)); dvec.normalize(); centre = Vector((0.0, 0.0, z0 + hc * H))
        cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"; cd.ortho_scale = scale
        cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
        sc.render.filepath = str(out_dir / f"{mv}_{view}_{i:03d}.png"); bpy.ops.render.render(write_still=True)


DEFORM_NAMES = [b.name for b in rig.data.bones if b.use_deform]
if SAVE_POS in ("1", "bones"):                                   # the full binding the fit reproduces (world rest space)
    _gidx = {g.index: g.name for g in body.vertex_groups}; _dn = {nm: i for i, nm in enumerate(DEFORM_NAMES)}
    _vi, _bj, _ww = [], [], []
    for v in me.vertices:
        for g in v.groups:
            nm = _gidx.get(g.group)
            if nm in _dn and g.weight > 0.0:
                _vi.append(v.index); _bj.append(_dn[nm]); _ww.append(g.weight)
    _B0w = np.empty(n * 3); me.shape_keys.key_blocks[0].data.foreach_get("co", _B0w)
    _B0w = _B0w.reshape(-1, 3) @ np.array(body.matrix_world)[:3, :3].T + np.array(body.matrix_world)[:3, 3]
    np.savez_compressed(OUT / "binding.npz", rest=_B0w, vi=np.array(_vi, np.int32), bj=np.array(_bj, np.int32),
                        w=np.array(_ww, np.float32), bones=np.array(DEFORM_NAMES))
AUTHOR = os.environ.get("V2_TRAJ_AUTHOR_CONTACT", "")   # "grip": author the closed fist's skin contact as rest-space
# offsets for R121_GRIP_<s> and write <OUT>/grip_contact_keys.npz (+ .json) - nothing is saved into the blend here (the
# harness changes weights in memory, e.g. V2_TRAJ_FA_REWEIGHT); add_grip_contact_keys_blender.py adds them to a copy.
# Real fist (docs/REAL_BODY_DEFORMATION_REFERENCE_20261101.md): the skin folds at the palmar creases and the folded
# sides press flat against each other - they meet, they do not pass through.  At the fist (grip u = 0.5, every drive on),
# the hand's intersecting triangle pairs push each other's penetrating corners out along the other face's normal to a
# 0.4 mm margin (half each), the step smoothed over the hand skin, iterated until no pair is left; then the posed offset
# is taken back to rest through each vertex's measured deformation matrix (three probe offsets) with two fixed-point
# passes, as the R121 keys are.
if AUTHOR == "grip":
    from mathutils.bvhtree import BVHTree as _BVH
    from scipy.sparse import csr_matrix as _csr
    _A = _csr((np.ones(2 * len(EV)), (np.r_[EV[:, 0], EV[:, 1]], np.r_[EV[:, 1], EV[:, 0]])), shape=(n, n))
    _Di = 1.0 / np.maximum(np.asarray(_A.sum(1)).ravel(), 1)
    _handw = gw("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal")
    REGV = _handw > 0.5
    tri_reg = TRI[REGV[TRI].all(1)]
    MOVE_FN["grip"](0.5); finish_pose()
    P0 = evaluated()
    D = np.zeros_like(P0); margin = 0.0004; hist = []; best = (10 ** 9, D.copy())
    # (first run: three spreading rounds per step and no damping overshot - pairs 155 -> 50 by step 6, then back up to
    # 368 with 14 mm moves - so: one spreading round, steps damped to 0.8, the best step kept, stop once pairs rise twice)
    for it_ in range(int(os.environ.get("V2_TRAJ_AUTHOR_ITERS", "30"))):
        Pc = P0 + D
        bvh_ = _BVH.FromPolygons([Vector(p) for p in Pc], tri_reg.tolist(), all_triangles=True)
        pr = np.array(bvh_.overlap(bvh_), dtype=np.int64).reshape(-1, 2)
        if len(pr):
            pr = pr[pr[:, 0] < pr[:, 1]]
            ta_, tb_ = tri_reg[pr[:, 0]], tri_reg[pr[:, 1]]
            pr = pr[~(ta_[:, :, None] == tb_[:, None, :]).any(axis=(1, 2))]
        hist.append(int(len(pr)))
        if len(pr) < best[0]:
            best = (int(len(pr)), D.copy())
        if not len(pr) or (len(hist) >= 3 and hist[-1] > hist[-2] > hist[-3]):
            break
        step = np.zeros_like(P0); cnt = np.zeros(n)
        for a_, b_ in pr:
            for x_, y_ in ((tri_reg[a_], tri_reg[b_]), (tri_reg[b_], tri_reg[a_])):
                q = Pc[y_]; nn = np.cross(q[1] - q[0], q[2] - q[0]); ln = np.linalg.norm(nn)
                if ln < 1e-12:
                    continue
                nn /= ln
                for v in x_:
                    d_ = float(np.dot(Pc[v] - q[0], nn))
                    if -0.006 < d_ < margin:                    # behind the other face, by a contact-sized depth
                        step[v] += nn * 0.5 * (margin - d_); cnt[v] += 1
        step[cnt > 0] /= cnt[cnt > 0, None]
        step = np.where(REGV[:, None], 0.6 * step + 0.4 * (_A @ step) * _Di[:, None], 0.0)   # one ring
        D += 0.8 * step
    D = best[1]
    T_ = P0 + D
    sel = np.nonzero(np.linalg.norm(D, axis=1) > 1e-7)[0]
    B0 = np.empty(n * 3); me.shape_keys.key_blocks[0].data.foreach_get("co", B0); B0 = B0.reshape(-1, 3)
    tmp = body.shape_key_add(name="TMP_GRIP_PROBE", from_mix=False); tmp.value = 1.0

    def _setk(d):
        tmp.data.foreach_set("co", (B0 + d).ravel()); me.update()
    M = np.zeros((n, 3, 3))
    for j in range(3):
        d = np.zeros((n, 3)); d[:, j] = 1e-3; _setk(d)
        M[:, :, j] = (evaluated() - P0) / 1e-3
    Dk = np.zeros((n, 3))
    Dk[sel] = np.linalg.solve(M[sel], D[sel][:, :, None])[:, :, 0]
    for _ in range(2):
        _setk(Dk); r_ = T_ - evaluated()
        Dk[sel] += np.linalg.solve(M[sel], r_[sel][:, :, None])[:, :, 0]
    _setk(Dk); resid = float(np.linalg.norm(T_ - evaluated(), axis=1).max() * 1000)
    body.shape_key_remove(tmp)
    lx = 1.0 if rig.data.bones["hand_l"].head_local.x > 0 else -1.0
    curl = {s_: round(float(r121_drives.finger_curl_deg(rig, s_)), 2) for s_ in ("l", "r")}
    np.savez_compressed(OUT / "grip_contact_keys.npz", l=Dk * (np.sign(B0[:, 0]) == lx)[:, None],
                        r=Dk * (np.sign(B0[:, 0]) == -lx)[:, None])
    info = {"pairs_history": hist, "pairs_kept": best[0], "vertices": int(len(sel)), "max_offset_mm": round(float(np.linalg.norm(Dk, axis=1).max() * 1000), 2),
            "posed_max_move_mm": round(float(np.linalg.norm(D, axis=1).max() * 1000), 2), "fit_residual_max_mm": round(resid, 4),
            "finger_curl_deg": curl, "margin_mm": margin * 1000}
    (OUT / "grip_contact_keys.json").write_text(json.dumps(info, indent=1))
    print("AUTHOR grip", json.dumps(info), flush=True)
    sys.exit(0)

FRAMES = {}
for mv in MOVES:
    rows = []; Ps = []; DEFORM_MATS = []
    if ANIM and any(v in AUTO_VIEWS for v in ANIM_VIEWS):
        fit_cameras(mv, ANIM_VIEWS)
        print("CAMERAS", mv, {v: ([round(x, 2) for x in c], s_) for v, (c, s_) in CAM_FIT[mv].items()}, flush=True)
    for i in range(NF):
        u = i / (NF - 1); TWIST.update(l=0.0, r=0.0)
        pose = MOVE_FN[mv](u); finish_pose()
        P = evaluated(); Ps.append(P)
        m = metrics(P) if METRICS else {}; m.update(pose); m["u"] = round(u, 4)
        if KEY_DIAG:
            m["key_diag"] = key_diag()
        if SAVE_POS in ("1", "bones"):
            DEFORM_MATS.append(np.array([[list(r) for r in (rig.matrix_world @ rig.pose.bones[b].matrix
                                          @ rig.data.bones[b].matrix_local.inverted() @ rig.matrix_world.inverted())][:3]
                                         for b in DEFORM_NAMES]))
        if BAKE_GLB:
            BAKE.setdefault(mv, []).append((
                {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones},
                [kb.value for kb in me.shape_keys.key_blocks]))
        if ANIM and (not ANIM_ONLY or i in ANIM_ONLY):
            render_views(mv, i, ANIM_VIEWS, OUT / "anim", (ANIM_W, ANIM_H))
        if UA_TWIST:
            m["upper_arm_twist_deg"] = {k: round(math.degrees(v), 1) for k, v in TWIST.items()}
            if TW_DIAG:
                m["upper_arm_twist_raw_elev_pf"] = {k: [round(x, 2) for x in v] for k, v in TW_DIAG.items()}
        rows.append(m)
        print("TRAJ", mv, i, json.dumps({k: m.get(k) for k in ("edges_gt90", "edges_gt35", "self_intersections", "asymmetry_p95_mm")}), flush=True)
    if SAVE_POS == "1":
        np.save(OUT / f"positions_{mv}.npy", np.stack(Ps).astype(np.float32))
    if SAVE_POS in ("1", "bones"):
        np.save(OUT / f"deform_{mv}.npy", np.stack(DEFORM_MATS).astype(np.float64))
    ret = float(np.linalg.norm(Ps[-1] - Ps[0], axis=1).max() * 1000)
    peak = {k: max(r.get(k, 0) for r in rows) for k in rows[0] if isinstance(rows[0][k], (int, float)) and not k.startswith(("u", "depth"))}
    REP["movements"][mv] = {"frames": rows, "return_to_neutral_max_mm": round(ret, 4), "peaks": peak}
    if mv == "grip" and GRIP_THUMB and not Path(GRIP_THUMB).exists() and "solution" in bench._THUMB_CACHE:
        Path(GRIP_THUMB).write_text(json.dumps({k: [list(v[0]), v[1]] for k, v in bench._THUMB_CACHE["solution"].items()}))
    if mv == "grip":
        REP["movements"][mv]["thumb_search"] = {"collapse_rule": GRIP_COLLAPSE, "fist_collapse_faces": dict(GRIP_BASE),
                                                "solution": {k: list(v[0]) + [v[1]] for k, v in bench._THUMB_CACHE.get("solution", {}).items()}}
    FRAMES[mv] = [0, NF // 4, NF // 2, (3 * NF) // 4]
    (OUT / "trajectory_report.json").write_text(json.dumps(REP, indent=1))

# ------------------------------------------------------------------ phone review sheets (workbench, cavity)
if RENDER:
    r_ = setup_render(); sc, cam, cd = r_["sc"], r_["cam"], r_["cd"]
    sc.render.resolution_x = 560; sc.render.resolution_y = 1000; cd.ortho_scale = 2.05
    files = {}
    for mv in MOVES:
        for fi in FRAMES[mv]:
            TWIST.update(l=0.0, r=0.0); MOVE_FN[mv](fi / (NF - 1)); finish_pose()
            centre = Vector((0.0, 0.0, z0 + 0.52 * H))
            for view, dv in {"front": (0, -1, 0), "side": (1, 0, 0), "back": (0, 1, 0)}.items():
                dvec = Vector(dv); cam.location = centre + dvec * 4; cam.rotation_mode = "QUATERNION"
                cam.rotation_quaternion = (-dvec).to_track_quat("-Z", "Y")
                f = OUT / f"frame_{mv}_{fi:02d}_{view}.png"; sc.render.filepath = str(f); bpy.ops.render.render(write_still=True)
                files.setdefault((mv, view), []).append(str(f))
    bench._reset(rig)
    (OUT / "frames_index.json").write_text(json.dumps({"frames": FRAMES, "frames_per_trajectory": NF}))
if BAKE and os.environ.get("V2_TRAJ_BAKE_SELFCHECK", "0") == "1":   # does the recorded state reproduce each frame?
    for mv_, frames_ in BAKE.items():
        Ps_ = np.load(OUT / f"positions_{mv_}.npy") if (OUT / f"positions_{mv_}.npy").exists() else None
        for f_ in sorted({0, (len(frames_) - 1) // 2, len(frames_) - 1}):
            mats_, vals_ = frames_[f_]
            for pb in rig.pose.bones:
                pb.matrix_basis = mats_[pb.name]
            for kb, v in zip(me.shape_keys.key_blocks, vals_):
                kb.value = v
            Pr = evaluated()
            d_ = float(np.linalg.norm(Pr - Ps_[f_], axis=1).max() * 1000) if Ps_ is not None else None
            print("BAKE_SELFCHECK", mv_, f_, "max_mm", None if d_ is None else round(d_, 3),
                  "object", [round(x, 4) for x in rig.matrix_world.translation], flush=True)
if BAKE_GLB:
    import glb_bake_export                                    # noqa: E402
    _lod = float(os.environ.get("V2_TRAJ_BAKE_LOD", "0")) or None     # app LOD decimate ratio (app_lod.py)
    GLB_REPORT = glb_bake_export.export(rig, body, BAKE, Path(BAKE_GLB), fps=BAKE_FPS, source=SRC, report=REP,
                                        lod_ratio=_lod, lod_tol_mm=float(os.environ.get("V2_TRAJ_BAKE_LOD_TOL_MM", "0.05")))
    print("GLB", json.dumps(GLB_REPORT)[:400], flush=True)
print("TRAJECTORY done", flush=True)
