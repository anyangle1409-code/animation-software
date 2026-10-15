#!/usr/bin/env python3
"""Muscle-line lengths of the shoulder muscles along the full press path (bpy; evidence for R14's muscle-line helpers).
Attachments from standard descriptive anatomy placed on this skeleton's own landmarks (LM_* empties), each carried by its
bone; straight-line (or via-point) lengths, wrapping ignored, as % of rest.  No third-party model data.

  python3.13 measure_original_muscle_lines_blender.py -- BLEND   (env OUT=json)
"""
import sys, os, json, math
sys.path.insert(0, "/home/user/p5/scripts"); sys.path.insert(0, "/home/user/p5/scripts/anatomy_fit")
import bpy
from mathutils import Vector
import original_v1_review_candidate_drives as drives
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
LM = {o.name: o.matrix_world.translation.copy() for o in bpy.data.objects if o.name.startswith("LM_")}
import build_functional_shoulder_correction_blender as correction
import build_original_movement_benchmarks_blender as bench
import build_original_sculpt_corrective_blender as s4
import original_v1_press_extension as px
res = correction.build_corrected_scene(); body, rig = res["body"], res["runtime"]
drives.setup(res); px.install(); bench._reset(rig)
print("LMcount", len(LM))
s, side = "r", "left"   # runtime _r = anatomical LEFT (F-SIDE-001)
L = lambda n: LM[f"LM_{n}"]
GH, EJC = L(f"scapula_{side}__GH"), L(f"humerus_{side}__EJC")
SC, AC = L(f"clavicle_{side}__SC"), L(f"clavicle_{side}__AC")
AA, AI, TS = L(f"scapula_{side}__AA"), L(f"scapula_{side}__AI"), L(f"scapula_{side}__TS")
IJ, PX = L("sternum__ij_skin"), L("sternum__px_skin")
sign = 1.0 if GH.x > 0 else -1.0
hum = lambda f: GH + (EJC - GH) * f
inward = Vector((0, 0.025, 0))     # skin landmarks on the sternum -> ~2.5 cm deep to bone
# attachments from standard anatomy (Gray's / Netter descriptions), placed on this skeleton's landmarks; each point
# carried by its bone: thorax = spine_03, clavicle, scapula, humerus = upperarm
A = {
 "pec_clavicular": [("clavicle", SC.lerp(AC, 0.33)), ("upperarm", hum(0.17) + Vector((0, -0.012, 0)))],
 "pec_sternal":    [("spine_03", IJ.lerp(PX, 0.5) + inward + Vector((sign * 0.02, 0, 0))), ("upperarm", hum(0.17) + Vector((0, -0.012, 0)))],
 "lat":            [("spine_03", Vector((sign * 0.05, AI.y + 0.03, AI.z - 0.16))), ("scapula", AI), ("upperarm", hum(0.14) + Vector((-sign * 0.008, -0.004, 0)))],
 "delt_anterior":  [("clavicle", SC.lerp(AC, 0.8)), ("upperarm", hum(0.45))],
 "delt_middle":    [("scapula", AC.lerp(AA, 0.5)), ("upperarm", hum(0.45))],
 "delt_posterior": [("scapula", AA.lerp(TS, 0.35)), ("upperarm", hum(0.45))],
 "trap_upper":     [("neck", Vector((sign * 0.02, IJ.y + 0.12, IJ.z + 0.12))), ("clavicle", SC.lerp(AC, 0.85))],
 "teres_major":    [("scapula", AI.lerp(AA, 0.15)), ("upperarm", hum(0.15))],
}
pb = rig.pose.bones
def mat(bn):
    return pb[bn].matrix @ rig.data.bones[bn].matrix_local.inverted()
bone = {"clavicle": f"clavicle_{s}", "scapula": f"scapula_{s}", "upperarm": f"upperarm_{s}", "spine_03": "spine_03", "neck": "neck"}
def lengths():
    out = {}
    for m, pts in A.items():
        P = [mat(bone[b]) @ p for b, p in pts]
        out[m] = sum((P[i + 1] - P[i]).length for i in range(len(P) - 1))
    return out
bench._reset(rig); L0 = lengths()
rows = {}
for ht in (70, 100, 130, 150, 172):
    bench._reset(rig); s4.press_pose(res, ht); drives.drive(rig, body)
    Lh = lengths(); rows[ht] = {m: round(100 * Lh[m] / L0[m], 1) for m in A}
print("ML rest lengths cm", {m: round(L0[m] * 100, 1) for m in A})
for ht, r in rows.items(): print("ML", ht, r)
json.dump({"rest_cm": {m: round(L0[m] * 100, 2) for m in A}, "pct_of_rest": rows}, open(os.environ["OUT"], "w"), indent=1)
