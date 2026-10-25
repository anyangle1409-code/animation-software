"""Squat path-length direction check: do the PROPOSED lower-limb anchors shorten / lengthen as the squat contract says?

Read-only on a hash-checked copy of the pinned ORIGINAL_v1 R41 blend (never saved).  R41's anatomical skeleton is posed
directly (it has no constraints to the runtime rig): the pelvis stays fixed (only joint angles matter for muscle
length), the femur flexes about HJC on the mediolateral axis, the tibia (with fibula, talus, calcaneus as children)
flexes about KJC on the epicondyle axis, and the talus (with the calcaneus) dorsiflexes about AJC on the malleolar axis.
Signs are fixed by landmark probes (hip flexion moves KJC anteriorly, knee flexion moves AJC posteriorly, dorsiflexion
moves the forefoot up), not assumed.

Paths: straight origin -> insertion, except where the proposal has a `wrap_hint`: a cylinder about the knee flexion axis
(through KJC, moving with the femur) or the hip flexion axis (through HJC, pelvis-fixed) of the given radius, passed on
the given side (quadriceps anteriorly over the patella / trochlea, hamstrings and gastrocnemius posteriorly over the
condyles, gluteus maximus behind the hip).  The wrapped length is the 2-D
tangent-arc-tangent length in the plane normal to the axis, combined with the axial offset.

Phases (contract mid-points): descent hip 5 -> 100, knee 5 -> 102, ankle dorsiflexion 2 -> 17 deg; ascent reversed.
Fan muscles (a proposal with `fibres`) are judged on the mean of their fibres' changes; each fibre is reported.
(L_end - L_start) / L_rest is classified: |x| < ISO near_isometric, else shortening / lengthening.

usage: python3.13 squat_path_length_check_blender.py -- COPY.blend SHA256 anchors_lower.json contracts.json OUT.json
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, anchors_p, contracts_p, out = Path(args[0]), args[1], Path(args[2]), Path(args[3]), Path(args[4])
ISO, SAMPLES = 0.03, 12
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


HJC, KJC, AJC = LM(f"hip_bone_{S}__HJC"), LM(f"femur_{S}__KJC"), LM(f"tibia_{S}__AJC")
EL, EM = LM(f"femur_{S}__epicondyle_lateral_skin"), LM(f"femur_{S}__epicondyle_medial_skin")
ML, MM = LM(f"tibia_{S}__malleolus_lateral_skin"), LM(f"tibia_{S}__malleolus_medial_skin")
TOE = MW @ anat.data.bones[f"anat_metatarsal_2_{S}"].tail_local
lat = 1.0 if HJC.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
KNEE_AX, ANK_AX = (EL - EM).normalized(), (ML - MM).normalized()


def rot_about(p, axis, deg):
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p)


def signed(axis, probe, want, pivot):
    return 1.0 if ((rot_about(pivot, axis, 5.0) @ probe) - probe).dot(want) > 0 else -1.0


SIGN = {"hip_flexion": signed(LAT, KJC, ANT, HJC), "knee_flexion": signed(KNEE_AX, AJC, -ANT, KJC),
        "ankle_dorsiflexion": signed(ANK_AX, TOE, UP, AJC)}
CHAIN = [f"anat_femur_{S}", f"anat_tibia_{S}", f"anat_talus_{S}"]


def pose(hip, knee, ankle):
    Tf = rot_about(HJC, LAT, SIGN["hip_flexion"] * hip)
    Tt = Tf @ rot_about(KJC, KNEE_AX, SIGN["knee_flexion"] * knee)
    Ta = Tt @ rot_about(AJC, ANK_AX, SIGN["ankle_dorsiflexion"] * ankle)
    return {CHAIN[0]: Tf, CHAIN[1]: Tt, CHAIN[2]: Ta}


def apply(T):
    for b in CHAIN:
        anat.pose.bones[b].matrix = MW.inverted() @ T[b] @ MW @ anat.data.bones[b].matrix_local
        bpy.context.view_layer.update()
    return T


def wrapped_length(p, q, c, axis, side, r):
    """shortest path p -> q passing the cylinder (centre c, axis, radius r) on `side`"""
    a = axis.normalized()
    e1 = (side - a * side.dot(a)).normalized(); e2 = a.cross(e1)
    P = Vector(((p - c).dot(e1), (p - c).dot(e2))); Q = Vector(((q - c).dot(e1), (q - c).dot(e2)))
    dz = (q - p).dot(a)
    d = Q - P
    n = Vector((-d.y, d.x)).normalized()
    if n.x < 0:                                     # normal pointing to the wrap side (+e1)
        n = -n
    h = P.dot(n)
    if h >= r or P.length <= r or Q.length <= r:   # line clears the cylinder on its side (or an anchor sits inside it)
        return (q - p).length, False

    def tangent_angle(X):
        th, be = math.atan2(X.y, X.x), math.acos(r / X.length)
        cands = (th + be, th - be)
        return max(cands, key=lambda t: math.cos(t))  # the tangent point on the +e1 (wrap) side
    ap, aq = tangent_angle(P), tangent_angle(Q)
    arc = abs(math.atan2(math.sin(aq - ap), math.cos(aq - ap)))
    L2 = math.sqrt(P.length ** 2 - r * r) + math.sqrt(Q.length ** 2 - r * r) + r * arc
    return math.hypot(L2, dz), True


def path_length(T, o, i, w):
    if w and w["joint"] == "knee":                     # moves with the femur
        R = T[CHAIN[0]].to_3x3()
        side = R @ (ANT if w["side"] == "anterior" else -ANT)
        return wrapped_length(o, i, T[CHAIN[0]] @ KJC, R @ KNEE_AX, side, w["radius_m"])
    if w and w["joint"] == "hip":                      # pelvis-fixed
        return wrapped_length(o, i, HJC, LAT, ANT if w["side"] == "anterior" else -ANT, w["radius_m"])
    return (i - o).length, False


def world(a):
    return MW @ anat.pose.bones[a["bone"]].matrix @ Vector(a["local_m"])


def lengths(T):
    """per muscle: path length (for a fan muscle, keyed per fibre as mid + '#' + fibre name as well)"""
    res, wr = {}, {}
    for mid, rec in PROP["proposals"].items():
        pts = {a["role"]: world(a) for a in rec["anchors"]}
        res[mid], wr[mid] = path_length(T, pts["origin"], pts["insertion"], rec.get("wrap_hint"))
        for fb in rec.get("fibres", []):
            res[f"{mid}#{fb['name']}"], wr[f"{mid}#{fb['name']}"] = path_length(T, world(fb["origin"]), pts["insertion"], rec.get("wrap_hint"))
    return res, wr


for b in anat.pose.bones:
    b.matrix_basis = Matrix()
bpy.context.view_layer.update()
rt = max((MW @ anat.pose.bones[a["bone"]].matrix @ Vector(a["local_m"]) - Vector(a["world_rest_m"])).length
         for r in PROP["proposals"].values() for a in r["anchors"])
L_REST, _ = lengths(apply(pose(0, 0, 0)))
REST_KNEE = 180 - math.degrees(math.acos((HJC - KJC).normalized().dot((AJC - KJC).normalized())))


def sweep(k0, k1):
    res = []
    for i in range(SAMPLES + 1):
        t = i / SAMPLES
        p = [a + (b - a) * t for a, b in zip(k0, k1)]
        res.append((p, *lengths(apply(pose(*p)))))
    return res


PH = {"descent": [(5, 5, 2), (100, 102, 17)], "ascent": [(100, 102, 17), (5, 5, 2)]}
contracts = json.loads(contracts_p.read_text())
ex = next(e for e in contracts["exercises"] if e["id"] == "hgpt.exercise.squat.bodyweight.v1")
report = {"status": "proposal_check_only", "source_sha256": expected, "side": S, "iso_threshold_fraction": ISO,
          "rest_round_trip_mm": round(rt * 1000, 4), "r41_rest_knee_flexion_deg": round(REST_KNEE, 1),
          "probe_signs": SIGN, "path_model": "straight; knee cylinder wrap where the proposal has a wrap_hint",
          "phases": {}}
summary = {"match": 0, "mismatch": 0, "variable": 0, "no_anchor": 0}
for ph in ex["phases"]:
    if ph["id"] not in PH:
        continue
    sw = sweep(*PH[ph["id"]])
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
        fib = {k.split("#")[1]: round((L1[k] - L0[k]) / L_REST[k], 4) for k in L_REST if k.startswith(mid + "#")}
        x = sum(fib.values()) / len(fib) if fib else (L1[mid] - L0[mid]) / L_REST[mid]   # a fan: mean fibre change
        got = "near_isometric" if abs(x) < ISO else ("shortening" if x < 0 else "lengthening")
        verdict = "variable_ok" if want == "variable" else ("match" if got == want else "MISMATCH")
        summary["match" if verdict == "match" else "mismatch" if verdict == "MISMATCH" else "variable"] += 1
        rows[mid] = {"contract": want, "result": got, "verdict": verdict, "change_fraction_of_rest": round(x, 4),
                     "start_mm": round(L0[mid] * 1000, 1), "end_mm": round(L1[mid] * 1000, 1),
                     "min_mm": round(min(series) * 1000, 1), "max_mm": round(max(series) * 1000, 1),
                     "wrapped_frames": sum(1 for s in sw if s[2][mid]), "frames": len(sw),
                     **({"fibres_change_fraction": fib, "judged_on": "mean fibre change"} if fib else {})}
    report["phases"][ph["id"]] = {"control_poses_hip_knee_ankle": PH[ph["id"]], "muscles": rows}
report["summary"] = summary
out.write_text(json.dumps(report, indent=1))
print("SQUATCHECK", json.dumps({"round_trip_mm": report["rest_round_trip_mm"], "rest_knee": report["r41_rest_knee_flexion_deg"],
                                "signs": SIGN, **summary}), flush=True)
for p, r in report["phases"].items():
    for m, v in r["muscles"].items():
        print(p, m.split(".")[2], v.get("contract"), v.get("result"), v.get("change_fraction_of_rest"),
              v.get("wrapped_frames"), v.get("verdict", ""))
