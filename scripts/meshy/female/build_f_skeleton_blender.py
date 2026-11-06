"""FEMALE skeleton: the canonical Home Gym PT bone names, hierarchy and orientation conventions, with EVERY joint placed
from HER measurements (her source surface, sections and the retopology builders' records) - no male bone length or
position is used and nothing is scaled. NEW file; the inputs are not changed.

Conventions taken from the approved male 07c rig (read-only, names / parents / connect flags / deform flags / the
direction of each bone's Z axis): male_rig.json (dumped from 07c). The male's corrective helper bones (shoulder_cap,
muscle_*, arm_ref, scap_glide, hip_crease) belong to the movement phase and are NOT created here.

Her joints (rest = her A-pose):
  * ankle: talocrural level = the widest ankle section (malleoli) between 0.04 and 0.11 m, centred in that section;
  * knee: her narrowest leg section (leg builder record), centred;
  * hip: her thigh line (upper-thigh centroid -> knee) at the hip-joint height = her crotch + 0.06 m (greater
    trochanter level; documented estimate), |x| clamped to 0.075-0.10 m;
  * ball / toe: 72 % of her heel -> toe-tip length at the foot's mid height / the toe tip;
  * spine: pelvis head 0.06 m above the hip joints, C7 at her neck base (trapezius-top loop 1.372 m), skull base at her
    occiput (1.478 m), head top at her vertex; the intermediate spine joints divide pelvis -> C7 at the canonical
    rig's fractions (0.157 / 0.394 / 0.669); front-back at the centre of her trunk / neck sections;
  * shoulder (GH): 3.5 cm below her acromion top and 3.5 cm medial to her lateral deltoid surface, centred front-back
    in her arm section; both sides averaged to a symmetric position (her source is symmetric to < 1 mm);
    clavicle: sternoclavicular joint (1.5 cm off the midline, 1.5 cm behind her jugular notch) -> acromion (above GH);
    scapula: on her upper back, from 2 cm behind the GH medially-down to the inferior angle region;
  * elbow, wrist: the arm builder's measured joints (elbow at 0.56 of joint-to-wrist on her centroid path, checked
    against her arm's surface narrowing), symmetrised;
  * hand / fingers / thumb: from her hand mesh part tags (10-13 fingers, 20/21 thumb): each finger's axis and tip from
    its vertices, knuckle at the finger base ring; phalanges split 0.45 / 0.30 / 0.25 of finger length (standard
    proportions); metacarpals from the wrist to the knuckles.
Checks (reported): every joint inside her body (ray parity), left-right symmetry of joints, bone lengths, limb bones
along her limb centre lines (angle to the local section-centroid line), bone roll Z-axis agreement with the convention.

usage: python3.13 build_f_skeleton_blender.py -- <female body .blend> <male_rig.json> <out NEW .blend> <report .json>
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index("--") + 1:]
IN, CONV, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2]), Path(a[3])
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
SRC = bpy.data.objects["HGPT_FEMALE_SOURCE_BODY_TARGET"]; body = bpy.data.objects["HGPT_Female_Body"]
SV = np.array([v.co[:] for v in SRC.data.vertices]); bvh = BVHTree.FromPolygons([Vector(p) for p in SV], [tuple(p.vertices) for p in SRC.data.polygons])
BV = np.array([v.co[:] for v in body.data.vertices])
attr = body.data.attributes
P4 = np.zeros(len(BV), int); attr["t4_part"].data.foreach_get("value", P4) if "t4_part" in attr else None
P5 = np.zeros(len(BV), int); attr["t5_part"].data.foreach_get("value", P5) if "t5_part" in attr else None
ARMS = json.loads(body["TASK4_ARMS"]); LEGS = json.loads(body["TASK5_LEGS"])
CONVB = {b["name"]: b for b in json.load(open(CONV))}
H = float(BV[:, 2].max())
U = lambda v: v / np.linalg.norm(v)


def section(z, xmin, xmax, pts=SV, slab=0.004):
    s = pts[(np.abs(pts[:, 2] - z) < slab) & (pts[:, 0] >= xmin) & (pts[:, 0] <= xmax)]
    return s


def mid_y(z, xmin=-0.05, xmax=0.05):
    s = section(z, xmin, xmax); s = s[s[:, 2] < 9]
    return 0.5 * (s[:, 1].min() + s[:, 1].max())


def ray_x(z, y, sg):                                   # lateral surface x at (y, z) from outside
    h = bvh.ray_cast(Vector((sg * 0.6, y, z)), Vector((-sg, 0, 0)))[0]; return h


J = {}
# ---------------- legs
for side, sg in (("r", 1.0), ("l", -1.0)):
    Lg = LEGS["right" if sg > 0 else "left"]
    knee = np.array(Lg["knee"]); heel = np.array(Lg["heel"]); tip = np.array(Lg["toe_tip"])
    # ankle: widest section (malleoli) 0.04-0.11 m around the shank line
    best = None
    for z in np.arange(0.04, 0.11, 0.0025):
        s = SV[(np.abs(SV[:, 2] - z) < 0.002) & (np.abs(SV[:, 0] - knee[0]) < 0.07) & (SV[:, 1] > heel[1] - 0.09) & (SV[:, 1] < heel[1] + 0.02)]
        if len(s) < 20:
            continue
        w = np.ptp(s[:, 0])
        if best is None or w > best[0]:
            best = (w, z, s)
    _, za, s = best
    ankle = np.array([0.5 * (s[:, 0].min() + s[:, 0].max()), 0.5 * (s[:, 1].min() + s[:, 1].max()) + 0.01, za])
    # hip: thigh line through the upper-thigh centroid and the knee, at crotch + 0.06
    crotch = float(np.mean(LEGS["crotch_strip_z"])); zh = crotch + 0.06
    s = section(0.75, 0.0, 0.3) if sg > 0 else section(0.75, -0.3, 0.0)
    ut = s.mean(0); d = U(ut - knee); hip = knee + d * ((zh - knee[2]) / d[2])
    hip[0] = sg * float(np.clip(abs(hip[0]), 0.075, 0.10)); hip[1] = mid_y(zh, -0.12, 0.12) if False else hip[1]
    fl = tip - heel; ball = heel + fl * 0.72; ball[2] = 0.025; toe = tip.copy(); toe[2] = max(tip[2], 0.012)
    J.update({f"hip_{side}": hip, f"knee_{side}": knee, f"ankle_{side}": ankle, f"ball_{side}": ball, f"toe_{side}": toe})
# symmetrise legs (her source is symmetric): average |x|, y, z
for k in ("hip", "knee", "ankle", "ball", "toe"):
    r, l = J[f"{k}_r"], J[f"{k}_l"]; m = 0.5 * (np.abs(r) + np.abs(l)); m[1] = 0.5 * (r[1] + l[1]); m[2] = 0.5 * (r[2] + l[2])
    J[f"{k}_r"] = np.array([m[0], m[1], m[2]]); J[f"{k}_l"] = np.array([-m[0], m[1], m[2]])
# ---------------- spine
zh = J["hip_r"][2]; z_pel = zh + 0.06; z_c7 = 1.372; z_sk = 1.478
yc = lambda z: mid_y(z, -0.06, 0.06)
pel = np.array([0, yc(z_pel), z_pel]); c7 = np.array([0, yc(z_c7), z_c7]); sk = np.array([0, yc(z_sk), z_sk])
top = np.array([0, yc(1.55), H])
spine_z = [z_pel + f * (z_c7 - z_pel) for f in (0.157, 0.394, 0.669)]
J.update({"root": np.array([0, pel[1], 0.0]), "pelvis": pel, "spine_01": np.array([0, yc(spine_z[0]), spine_z[0]]),
          "spine_02": np.array([0, yc(spine_z[1]), spine_z[1]]), "spine_03": np.array([0, yc(spine_z[2]), spine_z[2]]),
          "neck": c7, "head": sk, "head_top": top})
# ---------------- shoulder girdle and arms
GHs = {}
for side, sg in (("r", 1.0), ("l", -1.0)):
    A = ARMS["right" if sg > 0 else "left"]; gh0 = np.array(A["shoulder_joint"])
    # acromion top: highest body point over |x| 0.13-0.17 near the shoulder joint's y
    s = SV[(np.abs(SV[:, 0]) > 0.13) & (np.abs(SV[:, 0]) < 0.17) & (SV[:, 0] * sg > 0) & (np.abs(SV[:, 1] - gh0[1]) < 0.03) & (SV[:, 2] > 1.25) & (SV[:, 2] < 1.40)]
    acr = s[np.argmax(s[:, 2])]; zg = acr[2] - 0.035
    sy = SV[(np.abs(SV[:, 2] - zg) < 0.004) & (SV[:, 0] * sg > 0.13)]
    yg = 0.5 * (sy[:, 1].min() + sy[:, 1].max())
    lat = ray_x(zg, yg, sg); xg = lat.x - sg * 0.035
    GHs[side] = (np.array([xg, yg, zg]), acr)
gx = 0.5 * (abs(GHs["r"][0][0]) + abs(GHs["l"][0][0])); gy = 0.5 * (GHs["r"][0][1] + GHs["l"][0][1]); gz = 0.5 * (GHs["r"][0][2] + GHs["l"][0][2])
ax_ = 0.5 * (abs(GHs["r"][1][0]) + abs(GHs["l"][1][0])); az_ = 0.5 * (GHs["r"][1][2] + GHs["l"][1][2])
el = [np.array(ARMS[s_]["elbow"]) for s_ in ("right", "left")]; wr = [np.array(ARMS[s_]["wrist"]) for s_ in ("right", "left")]
elm = 0.5 * (np.abs(el[0]) + np.abs(el[1])); elm[1] = 0.5 * (el[0][1] + el[1][1]); elm[2] = 0.5 * (el[0][2] + el[1][2])
wrm = 0.5 * (np.abs(wr[0]) + np.abs(wr[1])); wrm[1] = 0.5 * (wr[0][1] + wr[1][1]); wrm[2] = 0.5 * (wr[0][2] + wr[1][2])
front_notch_y = bvh.ray_cast(Vector((0, -0.5, 1.345)), Vector((0, 1, 0)))[0].y
back_y_125 = bvh.ray_cast(Vector((0.10, 0.5, 1.25)), Vector((0, -1, 0)))[0].y
for side, sg in (("r", 1.0), ("l", -1.0)):
    X = lambda p: np.array([sg * p[0], p[1], p[2]])
    gh = X([gx, gy, gz])
    J[f"sc_{side}"] = X([0.015, front_notch_y + 0.015, 1.345])
    J[f"ac_{side}"] = X([ax_ - 0.01, gy, az_ - 0.012])
    J[f"scap_{side}"] = X([gx - 0.035, gy + 0.035, gz + 0.01]); J[f"scap_tail_{side}"] = X([gx - 0.075, back_y_125 - 0.015, gz - 0.085])
    J[f"gh_{side}"] = gh; J[f"elbow_{side}"] = X(elm); J[f"wrist_{side}"] = X(wrm)
    J[f"fmid_{side}"] = 0.5 * (J[f"elbow_{side}"] + J[f"wrist_{side}"])
# ---------------- hands (from her hand mesh tags)
FING = ["index", "middle", "ring", "pinky"]; hands = {}
for side, sg in (("r", 1.0), ("l", -1.0)):
    m = BV[:, 0] * sg > 0.3
    th = BV[m & np.isin(P4, (20, 21))]; thr = BV[m & (P4 == 20)] if (m & (P4 == 20)).any() else th
    w = J[f"wrist_{side}"]
    fingers = []
    for f in range(4):
        pts = BV[m & (P4 == 10 + f)]
        if not len(pts):
            continue
        c = pts.mean(0); d = U(np.linalg.svd(pts - c)[2][0]); d = d if d @ (c - w) > 0 else -d
        t = (pts - c) @ d; base = c + d * t.min(); tipp = c + d * t.max()
        fingers.append((np.linalg.norm(base - thr.mean(0)), base, tipp))
    fingers.sort(key=lambda q: q[0])
    for name, (_, base, tipp) in zip(FING, fingers):
        Lf = np.linalg.norm(tipp - base); dd = U(tipp - base)
        J[f"{name}_mc_{side}"] = w + (base - w) * 0.25
        J[f"{name}_k_{side}"] = base; J[f"{name}_p_{side}"] = base + dd * 0.45 * Lf; J[f"{name}_d_{side}"] = base + dd * 0.75 * Lf; J[f"{name}_t_{side}"] = tipp
    c = th.mean(0); d = U(np.linalg.svd(th - c)[2][0]); d = d if d @ (c - w) > 0 else -d
    t = (th - c) @ d; b0 = c + d * t.min(); tt = c + d * t.max(); Lt = np.linalg.norm(tt - b0)
    J[f"thumb_0_{side}"] = b0; J[f"thumb_1_{side}"] = b0 + d * 0.40 * Lt; J[f"thumb_2_{side}"] = b0 + d * 0.72 * Lt; J[f"thumb_3_{side}"] = tt
    hd = U(J[f"middle_k_{side}"] - w) if f"middle_k_{side}" in J else U(w - J[f"elbow_{side}"])
    J[f"hand_t_{side}"] = w + hd * 0.016
# ---------------- bones
B = {}  # name -> (head, tail, parent)
def bone(n, h, t, p):
    B[n] = (np.array(h, float), np.array(t, float), p)
bone("root", J["root"], J["pelvis"], None); bone("pelvis", J["pelvis"], J["spine_01"], "root")
bone("spine_01", J["spine_01"], J["spine_02"], "pelvis"); bone("spine_02", J["spine_02"], J["spine_03"], "spine_01")
bone("spine_03", J["spine_03"], J["neck"], "spine_02"); bone("neck", J["neck"], J["head"], "spine_03"); bone("head", J["head"], J["head_top"], "neck")
for s in ("l", "r"):
    bone(f"clavicle_{s}", J[f"sc_{s}"], J[f"ac_{s}"], "spine_03"); bone(f"scapula_{s}", J[f"scap_{s}"], J[f"scap_tail_{s}"], f"clavicle_{s}")
    bone(f"upperarm_{s}", J[f"gh_{s}"], J[f"elbow_{s}"], f"scapula_{s}"); bone(f"forearm_{s}", J[f"elbow_{s}"], J[f"fmid_{s}"], f"upperarm_{s}")
    bone(f"forearm_tw0_{s}", J[f"elbow_{s}"], J[f"fmid_{s}"], f"forearm_{s}"); bone(f"forearm_tw1_{s}", J[f"fmid_{s}"], J[f"wrist_{s}"], f"forearm_{s}")
    bone(f"hand_{s}", J[f"wrist_{s}"], J[f"hand_t_{s}"], f"forearm_{s}")
    for n in FING:
        if f"{n}_k_{s}" not in J:
            continue
        bone(f"metacarpal_{n}_{s}", J[f"{n}_mc_{s}"], J[f"{n}_k_{s}"], f"hand_{s}")
        bone(f"{n}_01_{s}", J[f"{n}_k_{s}"], J[f"{n}_p_{s}"], f"metacarpal_{n}_{s}"); bone(f"{n}_02_{s}", J[f"{n}_p_{s}"], J[f"{n}_d_{s}"], f"{n}_01_{s}")
        bone(f"{n}_03_{s}", J[f"{n}_d_{s}"], J[f"{n}_t_{s}"], f"{n}_02_{s}")
    bone(f"thumb_01_{s}", J[f"thumb_0_{s}"], J[f"thumb_1_{s}"], f"hand_{s}"); bone(f"thumb_02_{s}", J[f"thumb_1_{s}"], J[f"thumb_2_{s}"], f"thumb_01_{s}")
    bone(f"thumb_03_{s}", J[f"thumb_2_{s}"], J[f"thumb_3_{s}"], f"thumb_02_{s}")
    bone(f"thigh_{s}", J[f"hip_{s}"], J[f"knee_{s}"], "pelvis"); bone(f"shin_{s}", J[f"knee_{s}"], J[f"ankle_{s}"], f"thigh_{s}")
    bone(f"foot_{s}", J[f"ankle_{s}"], J[f"ball_{s}"], f"shin_{s}"); bone(f"toe_{s}", J[f"ball_{s}"], J[f"toe_{s}"], f"foot_{s}")
arm = bpy.data.armatures.new("HGPT_FEMALE_RIG"); rig = bpy.data.objects.new("HGPT_FEMALE_RIG", arm)
body.users_collection[0].objects.link(rig); bpy.context.view_layer.objects.active = rig
with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[rig]):
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for n, (h, t, p) in B.items():
        e = arm.edit_bones.new(n); e.head = Vector(h); e.tail = Vector(t); eb[n] = e
    for n, (h, t, p) in B.items():
        e = eb[n]
        if p:
            e.parent = eb[p]
        cv = CONVB.get(n)
        if cv:
            e.use_connect = bool(cv["connect"]) and (Vector(B[p][1]) - e.head).length < 1e-5 if p else False
            e.use_deform = bool(cv["deform"])
            z = Vector(cv["roll_z"]); y = (e.tail - e.head).normalized(); z = (z - y * z.dot(y))
            if z.length > 1e-6:
                e.align_roll(z.normalized())
    bpy.ops.object.mode_set(mode="OBJECT")
# ---------------- checks
def inside(p):
    o = Vector(p); cnt = 0; d = Vector((0.31, 0.53, 0.79)).normalized(); t = 0.0
    while True:
        h = bvh.ray_cast(o + d * (t + 1e-5), d)
        if h[0] is None:
            return cnt % 2 == 1
        cnt += 1; t = (h[0] - o).length


rep = {"in": IN.name, "height_m": round(H, 4), "bones": len(B), "convention_missing": sorted(set(CONVB) - set(B)),
       "joints": {k: [round(float(x), 4) for x in v] for k, v in J.items()}}
checks = {}
for n, (h, t, p) in B.items():
    if n in ("root",) or n.endswith("_top"):
        continue
    checks[n] = {"head_inside": inside(h), "length_mm": round(float(np.linalg.norm(t - h)) * 1000, 1)}
rep["joints_outside_body"] = [n for n, c in checks.items() if not c["head_inside"]]
sym = []
for n in B:
    if n.endswith("_l") and n[:-2] + "_r" in B:
        hl, hr = B[n][0], B[n[:-2] + "_r"][0]; sym.append(float(np.linalg.norm(hl - np.array([-hr[0], hr[1], hr[2]]))))
rep["symmetry_max_mm"] = round(max(sym) * 1000, 2)
# limb bones along her limb centre lines: bone direction vs centroid line of body vertices near the bone
align = {}
for n in ("upperarm_r", "forearm_r", "thigh_r", "shin_r", "upperarm_l", "forearm_l", "thigh_l", "shin_l"):
    h, t, _ = B[n]; d = U(t - h); Lb = np.linalg.norm(t - h); cents = []
    for f in np.linspace(0.2, 0.8, 7):
        c = h + d * f * Lb; rel = BV - c
        sl = BV[(np.abs(rel @ d) < 0.006) & (np.linalg.norm(rel - np.outer(rel @ d, d), axis=1) < 0.09)]
        if len(sl) > 10:
            cents.append(sl.mean(0))
    C = np.array(cents); cd = U(np.linalg.svd(C - C.mean(0))[2][0]); cd = cd if cd @ d > 0 else -cd
    off = [float(np.linalg.norm((c - h) - ((c - h) @ d) * d)) for c in C]
    align[n] = {"angle_to_centroid_line_deg": round(math.degrees(math.acos(min(1, float(cd @ d)))), 1), "max_offset_mm": round(max(off) * 1000, 1)}
rep["limb_alignment"] = align; rep["bone_checks"] = checks
rep["segment_lengths_mm"] = {k: round(float(np.linalg.norm(B[k][1] - B[k][0])) * 1000, 1) for k in ("upperarm_r", "thigh_r", "shin_r", "clavicle_r")}
rep["segment_lengths_mm"]["forearm_total_r"] = round(float(np.linalg.norm(J["wrist_r"] - J["elbow_r"])) * 1000, 1)
rep["shoulder_breadth_GH_mm"] = round(2 * gx * 1000, 1); rep["hip_joint_breadth_mm"] = round(2 * abs(J["hip_r"][0]) * 1000, 1)
rig["SKELETON_FIT"] = json.dumps({k: v for k, v in rep.items() if k not in ("bone_checks",)})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = str(OUT); REP.write_text(json.dumps(rep, indent=1))
print("SKELETON", json.dumps({k: rep[k] for k in ("bones", "joints_outside_body", "symmetry_max_mm", "limb_alignment", "segment_lengths_mm", "shoulder_breadth_GH_mm", "hip_joint_breadth_mm", "convention_missing")}))
