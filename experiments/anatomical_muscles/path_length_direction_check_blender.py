"""Path-length direction check: do the PROPOSED anchors shorten / lengthen the way the exercise contract says?

Read-only on a hash-checked copy of the pinned ORIGINAL_v1 R41 blend (never saved).  R41's anatomical skeleton
(HGPT_ANATOMICAL_MASTER) has no constraints to the runtime rig, so it is posed directly here, bone by bone in hierarchy
order (clavicle -> scapula -> humerus -> ulna / radius), by rigid rotations about joint centres taken from R41's own
landmark empties (SC, AC, GH, EJC, AA / TS / AI, epicondyles, WJC).  Every rotation sign is fixed by a landmark probe,
not assumed (AC rises with clavicle elevation, AC moves posteriorly with retraction, AI moves laterally with upward
rotation, AI moves anteriorly with posterior tilt, the wrist moves anteriorly with elbow flexion).

Shoulder girdle, as a thorax -> clavicle (SC) -> scapula (AC) chain, coupled to humerothoracic elevation e (deg above
R41's rest) by approximate ratios (rule of thumb after the 3-D scapular kinematics literature, e.g. Ludewig et al. 2009,
McClure et al. 2001; NOT patient values - MODEL below records them):
  scapulothoracic upward rotation 0.33 e (the ~2:1 rhythm; the contract's 5-15 -> 40-60 deg over the press),
  posterior tilt 0.12 e, clavicle elevation 0.08 e, clavicle retraction 0.12 e, scapular external rotation ~0
  (the retraction's yaw is undone at the AC joint).  Clavicle elevation is counted as part of the upward rotation.
PATHCHECK_UR_PIVOT moves the upward-rotation pivot along TS -> AC (in vivo the instantaneous axis migrates from near the
root of the spine early in elevation towards the AC joint late; a pivot away from AC opens the AC joint, reported as
ac_joint_gap_mm, because this rigid chain has no scapulothoracic glide).  GIRDLE=ac_only reproduces the first (crude) run: upward rotation about AC plus clavicle elevation only.

Anchors are the proposal's bone-local points (matrix_world @ pose_bone.matrix @ local_m), so the check also confirms
the proposal's bone bindings follow the native hierarchy.  Paths are straight origin -> insertion lines (wraps are not
reviewed), except serratus anterior, which lies on the rib cage: its path is wrapped on an elliptic cylinder fitted to
the torso skin at the origin's height, inset 15 mm (WRAP).  A phase's change (L_end - L_start) / L_rest is
classified: |x| < ISO -> near_isometric, else shortening / lengthening.  'variable' in the contract accepts any result.

usage: python3.13 path_length_direction_check_blender.py -- COPY.blend SHA256 anchors.json contracts.json OUT.json
env: PATHCHECK_GIRDLE=coupled|ac_only, PATHCHECK_UR_PIVOT=0..1 (1)
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, contracts_p, out = Path(args[0]), args[1], Path(args[2]), Path(args[3]), Path(args[4])
ISO, PLANE_DEG, SAMPLES, INSET = 0.03, 30.0, 12, 0.015
GIRDLE = os.environ.get("PATHCHECK_GIRDLE", "coupled")
UR_PIVOT = float(os.environ.get("PATHCHECK_UR_PIVOT", "1.0"))   # upward-rotation pivot: 0 = root of spine (TS), 1 = AC
MODEL = {"coupled": {"upward_rotation": 0.33, "posterior_tilt": 0.12, "clavicle_elevation": 0.08, "clavicle_retraction": 0.12},
         "ac_only": {"upward_rotation": 0.32, "posterior_tilt": 0.0, "clavicle_elevation": 0.16, "clavicle_retraction": 0.0}}[GIRDLE]
if out.exists():
    raise ValueError("output must be new")
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("copy hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]
MW = anat.matrix_world.copy()
PROP = json.loads(anchors_p.read_text())
S = PROP["side"]; SUF = "L" if S == "left" else "R"


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


SC, AC, GH, EJC = LM(f"clavicle_{S}__SC"), LM(f"clavicle_{S}__AC"), LM(f"scapula_{S}__GH"), LM(f"humerus_{S}__EJC")
AA, TS, AI = LM(f"scapula_{S}__AA"), LM(f"scapula_{S}__TS"), LM(f"scapula_{S}__AI")
EL, EM = LM(f"humerus_{S}__epicondyle_lateral_skin"), LM(f"humerus_{S}__epicondyle_medial_skin")
WJC = LM(f"radius_{S}__WJC")
lat = 1.0 if GH.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
SCAP_N = (AA - TS).cross(AI - TS).normalized()          # normal of the scapular plane (upward-rotation axis)
SPINE = (AA - TS).normalized()                          # scapular spine (posterior-tilt axis)
ELB_AX = (EL - EM).normalized()


def rot_about(p, axis, deg):
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p)


def signed(axis, probe, want, pivot):
    """+1 if a small positive rotation about axis (through pivot) moves probe along want, else -1"""
    return 1.0 if ((rot_about(pivot, axis, 5.0) @ probe) - probe).dot(want) > 0 else -1.0


SIGN = {"clavicle_elevation": signed(ANT, AC, UP, SC), "clavicle_retraction": signed(UP, AC, -ANT, SC),
        "upward_rotation": signed(SCAP_N, AI, LAT, AC), "posterior_tilt": signed(SPINE, AI, ANT, AC),
        "elbow_flexion": signed(ELB_AX, WJC, ANT, EJC)}
CHAIN = [f"anat_clavicle_{S}", f"anat_scapula_{S}", f"anat_humerus_{S}", f"anat_ulna_{S}", f"anat_radius_{S}"]
REST_HT = math.degrees(math.acos((EJC - GH).normalized().dot(-UP)))
REST_ELB = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, (GH - EJC).normalized().dot((WJC - EJC).normalized())))))


def girdle(ht_deg):
    e = max(0.0, ht_deg - REST_HT)
    return {k: v * e for k, v in MODEL.items()}


def pose(ht_deg, elbow_deg):
    """world rigid transforms of the chain at humerothoracic elevation ht_deg and elbow flexion elbow_deg"""
    g = girdle(ht_deg)
    Tc = rot_about(SC, UP, SIGN["clavicle_retraction"] * g["clavicle_retraction"]) @ \
        rot_about(SC, ANT, SIGN["clavicle_elevation"] * g["clavicle_elevation"])
    ac = Tc @ TS.lerp(AC, UR_PIVOT)
    R = Tc.to_3x3()
    ts = rot_about(ac, R @ SCAP_N, SIGN["upward_rotation"] * (g["upward_rotation"] - g["clavicle_elevation"])) @ Tc
    ts = rot_about(ac, ts.to_3x3() @ SPINE, SIGN["posterior_tilt"] * g["posterior_tilt"]) @ ts
    ts = rot_about(ac, UP, -SIGN["clavicle_retraction"] * g["clavicle_retraction"]) @ ts   # scapular ER ~ 0
    gh, ejc = ts @ GH, ts @ EJC
    plane = (math.cos(math.radians(PLANE_DEG)) * LAT + math.sin(math.radians(PLANE_DEG)) * ANT).normalized()
    want = (math.cos(math.radians(ht_deg)) * -UP + math.sin(math.radians(ht_deg)) * plane).normalized()
    q = (ejc - gh).normalized().rotation_difference(want)
    Th = Matrix.Translation(gh) @ q.to_matrix().to_4x4() @ Matrix.Translation(-gh) @ ts
    Tf = Th @ rot_about(EJC, ELB_AX, SIGN["elbow_flexion"] * (elbow_deg - REST_ELB))
    return {CHAIN[0]: Tc, CHAIN[1]: ts, CHAIN[2]: Th, CHAIN[3]: Tf, CHAIN[4]: Tf}


def apply(T):
    for b in CHAIN:                                         # parents first
        anat.pose.bones[b].matrix = MW.inverted() @ T[b] @ MW @ anat.data.bones[b].matrix_local
        bpy.context.view_layer.update()


def anchors_world():
    return {mid: {a["role"]: MW @ anat.pose.bones[a["bone"]].matrix @ Vector(a["local_m"]) for a in rec["anchors"]}
            for mid, rec in PROP["proposals"].items()}


# ------------------------------------------------------------------ thorax wrap for serratus anterior
SER = f"hgpt.muscle.serratus_anterior.{SUF}"
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
z_w = next(a for a in PROP["proposals"][SER]["anchors"] if a["role"] == "origin")["world_rest_m"][2]
band = [body.matrix_world @ v.co for v in body.data.vertices if abs((body.matrix_world @ v.co).z - z_w) < 0.004]
mid_ = [w for w in band if abs(w.x) < 0.01]
Y0 = (min(w.y for w in mid_) + max(w.y for w in mid_)) / 2.0
WB = (max(w.y for w in mid_) - min(w.y for w in mid_)) / 2.0 - INSET
WA = max(abs(w.x) for w in band if abs(w.x) < abs(GH.x) - 0.035 and abs(w.y - GH.y) < 0.01) - INSET
WRAP = {"z_m": round(z_w, 4), "centre_y_m": round(Y0, 4), "semi_axis_x_m": round(WA, 4), "semi_axis_y_m": round(WB, 4)}


def ellipse_arc(t0, t1, n=200):
    s, prev = 0.0, None
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        p = (WA * math.cos(t), WB * math.sin(t))
        if prev:
            s += math.hypot(p[0] - prev[0], p[1] - prev[1])
        prev = p
    return s


def wrapped(o, i):
    to = math.atan2((o.y - Y0) / WB, o.x / WA); ti = math.atan2((i.y - Y0) / WB, i.x / WA)
    return math.hypot(ellipse_arc(to, ti), i.z - o.z)


def lengths():
    aw = anchors_world()
    L = {m: (p["insertion"] - p["origin"]).length for m, p in aw.items()}
    L[SER] = wrapped(aw[SER]["origin"], aw[SER]["insertion"])
    return L


for b in anat.pose.bones:
    b.matrix_basis = Matrix()
bpy.context.view_layer.update()
rt = max((anchors_world()[m][a["role"]] - Vector(a["world_rest_m"])).length
         for m, r in PROP["proposals"].items() for a in r["anchors"])
L_REST = lengths()
apply(pose(REST_HT, REST_ELB))
rt_pose = max(abs(v - L_REST[k]) for k, v in lengths().items())


def sweep(keys):
    """keys: control poses (ht_deg, elbow_deg); linear interpolation, SAMPLES steps between each"""
    res = []
    for k0, k1 in zip(keys[:-1], keys[1:]):
        for i in range(SAMPLES + 1):
            t = i / SAMPLES
            p = [a + (b - a) * t for a, b in zip(k0, k1)]
            apply(pose(*p))
            res.append((p, lengths()))
    return res


def probe_top():
    """girdle landmark displacements (mm) at the press top, for review"""
    T = pose(160, 8)
    return {"girdle_deg": {k: round(v, 1) for k, v in girdle(160).items()},
            "ac_joint_gap_mm": round(((T[CHAIN[1]] @ AC) - (T[CHAIN[0]] @ AC)).length * 1000, 1),
            **{k: [round(x * 1000) for x in (T[CHAIN[1]] @ v - v)] for k, v in {"AC": AC, "TS": TS, "AI": AI, "GH": GH}.items()}}


def classify(x):
    return "near_isometric" if abs(x) < ISO else ("shortening" if x < 0 else "lengthening")


# control poses (humerothoracic elevation, elbow flexion): mid-points of the contract's joint targets
PH = {
    "hgpt.exercise.biceps_curl.bilateral.v1": {"concentric": [(REST_HT, 10), (REST_HT, 112)],
                                                "eccentric": [(REST_HT, 112), (REST_HT, 10)]},
    "hgpt.exercise.shoulder_press.bilateral.v1": {"press": [(35, 92), (160, 8)], "lower": [(160, 8), (35, 92)]},
}
contracts = json.loads(contracts_p.read_text())
report = {"status": "proposal_check_only", "source_sha256": expected, "side": S, "girdle_model": GIRDLE,
          "upward_rotation_pivot_ts_to_ac": UR_PIVOT,
          "girdle_ratios_per_deg_elevation": MODEL, "iso_threshold_fraction": ISO,
          "elevation_plane_deg_anterior_to_frontal": PLANE_DEG, "rest_round_trip_mm": round(rt * 1000, 4),
          "rest_pose_round_trip_mm": round(rt_pose * 1000, 4),
          "r41_rest": {"humerothoracic_elevation_deg": round(REST_HT, 1), "elbow_flexion_deg": round(REST_ELB, 1)},
          "probe_signs": SIGN, "press_top_probe": probe_top(), "serratus_wrap_ellipse": WRAP,
          "path_model": "straight origin->insertion; serratus wrapped on the thorax ellipse; no other wraps",
          "exercises": {}}
summary = {"match": 0, "mismatch": 0, "variable": 0, "no_anchor": 0}
for ex in contracts["exercises"]:
    if ex["id"] not in PH:
        continue
    exr = report["exercises"][ex["id"]] = {}
    for ph in ex["phases"]:
        if ph["id"] not in PH[ex["id"]]:
            continue
        sw = sweep(PH[ex["id"]][ph["id"]])
        L0, L1 = sw[0][1], sw[-1][1]
        rows = {}
        for m in ph["muscles"]:
            mid, want = m["muscle_id"], m["length_change"]
            if not mid.endswith("." + SUF):
                continue
            if mid not in L_REST:
                rows[mid] = {"contract": want, "result": "no_proposed_anchors"}; summary["no_anchor"] += 1
                continue
            series = [s[1][mid] for s in sw]
            x = (L1[mid] - L0[mid]) / L_REST[mid]
            got = classify(x)
            mono = all(b <= a + 1e-6 for a, b in zip(series[:-1], series[1:])) or \
                all(b >= a - 1e-6 for a, b in zip(series[:-1], series[1:]))
            verdict = "variable_ok" if want == "variable" else ("match" if got == want else "MISMATCH")
            summary["match" if verdict == "match" else "mismatch" if verdict == "MISMATCH" else "variable"] += 1
            rows[mid] = {"contract": want, "result": got, "verdict": verdict, "change_fraction_of_rest": round(x, 4),
                         "start_mm": round(L0[mid] * 1000, 1), "end_mm": round(L1[mid] * 1000, 1),
                         "min_mm": round(min(series) * 1000, 1), "max_mm": round(max(series) * 1000, 1),
                         "monotonic": mono}
        exr[ph["id"]] = {"control_poses_ht_elbow": PH[ex["id"]][ph["id"]], "muscles": rows}
report["summary"] = summary
out.write_text(json.dumps(report, indent=1))
print("PATHCHECK", json.dumps({"girdle": GIRDLE, "pivot": UR_PIVOT, "round_trip_mm": report["rest_round_trip_mm"],
                               "pose_round_trip_mm": report["rest_pose_round_trip_mm"], "rest": report["r41_rest"],
                               "top": report["press_top_probe"], "wrap": WRAP, **summary}), flush=True)
for e, phs in report["exercises"].items():
    for p, r in phs.items():
        for m, v in r["muscles"].items():
            print(e.split(".")[2], p, m.split(".")[2], v.get("contract"), v.get("result"), v.get("change_fraction_of_rest"),
                  v.get("monotonic"), v.get("verdict", ""))
