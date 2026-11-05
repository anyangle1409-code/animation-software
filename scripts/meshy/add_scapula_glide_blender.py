"""Scapular glide helper (controlled mechanism) on the bound retopology - writes a NEW file.

Why: with the existing girdle the skin over the shoulder blade does not show the scapula's upward rotation, but
rotating the scapula bone itself drags its bone-heat weights over the whole upper back (hump), and re-weighting the
girdle bones (06d) was worse. This adds a separate helper that touches nothing else:
  * arm_ref_<s>   non-deforming reference bone at the shoulder joint, pointing straight down, child of spine_03.
                  ROTATION_DIFF(upperarm, arm_ref) is the arm's elevation relative to the trunk.
  * scap_glide_<s> deforming helper, child of spine_03, pivot near the root of the scapular spine (superomedial
                  corner) on the back surface, its long axis along the back-surface normal. Driven by the elevation
                  e above the rest elevation e0: rotation about its axis = ROT_K * (e - e0) / 3 (the scapula's upward
                  rotation is about one third of arm elevation; ROT_K is the share the skin follows), lift UP_M at
                  170 deg.
  * weights: only over the shoulder blade on the back (ellipse SCAP_C / SCAP_AX with a FADE fall-off, back-facing
    surfaces, faded to zero by |x| = X_MAX so the posterior armpit wall never slides, never on skin with upper-arm weight) and ONLY taken from the spine bones' share of each vertex (spine_01..03). Upper arm, clavicle, scapula,
    deltoid and armpit weights are not changed.
Drivers use simple expressions (no scripts), so they evaluate in background renders; for GLB export the helper's
motion is baked like any bone.

usage: python3.13 add_scapula_glide_blender.py -- <bound .blend> <out NEW .blend> <report .json> [rot_k] [lift_m]
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
IN, OUT, REP = Path(a[0]), Path(a[1]), Path(a[2])
ROT_K = float(a[3]) if len(a) > 3 else 0.6
UP_M = float(a[4]) if len(a) > 4 else 0.015
if OUT.exists():
    raise FileExistsError(f"will not overwrite {OUT}")
SCAP_C, SCAP_AX, FADE = (0.105, -0.08), (0.05, 0.10), 0.04
X_MAX = 0.16                     # no glide weight lateral of this |x| (the armpit walls must not slide)
PIVOT = (0.08, -0.01)            # |x| from midline, z relative to the shoulder joint (root of the scapular spine)
SPINE = ("spine_01", "spine_02", "spine_03")
bpy.ops.wm.open_mainfile(filepath=str(IN), load_ui=False)
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data
V = np.array([v.co[:] for v in me.vertices]); NRM = np.array([v.normal[:] for v in me.vertices]); NV = len(V)
from mathutils.bvhtree import BVHTree  # noqa: E402
bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
rep = {"method": __doc__.split("usage")[0].strip(), "rot_k": ROT_K, "lift_m": UP_M, "sides": {}}
bpy.context.view_layer.objects.active = rig; rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT"); eb = rig.data.edit_bones; info = {}
for sd, sg in (("r", 1), ("l", -1)):
    gh = eb[f"upperarm_{sd}"].head.copy()
    ref = eb.new(f"arm_ref_{sd}"); ref.head = gh; ref.tail = gh + Vector((0, 0, -0.10)); ref.parent = eb["spine_03"]; ref.use_deform = False
    # pivot on the back surface: ray from inside towards the back
    p_in = Vector((PIVOT[0] * sg, 0.0, gh.z + PIVOT[1])); h = bvh.ray_cast(p_in, Vector((0, 1, 0)), 0.5)
    piv = h[0] if h[0] is not None else Vector((PIVOT[0] * sg, 0.12, gh.z + PIVOT[1])); n = h[1] if h[0] is not None else Vector((0, 1, 0))
    gb = eb.new(f"scap_glide_{sd}"); gb.head = piv - n * 0.02; gb.tail = piv - n * 0.06     # long axis along the inward normal
    gb.parent = eb["spine_03"]; gb.use_deform = True; gb.align_roll(Vector((0, 0, 1)))
    info[sd] = {"pivot": [round(x, 4) for x in piv], "normal": [round(x, 3) for x in n]}
bpy.ops.object.mode_set(mode="OBJECT")
pb = rig.pose.bones; MW = rig.matrix_world
for sd, sg in (("r", 1), ("l", -1)):
    pg = pb[f"scap_glide_{sd}"]; pg.rotation_mode = "XYZ"
    # rest elevation e0 (A-pose) measured now
    # e0 = the driver's own value at rest (ROTATION_DIFF compares whole bone orientations, roll included)
    qa = rig.data.bones[f"upperarm_{sd}"].matrix_local.to_quaternion(); qr = rig.data.bones[f"arm_ref_{sd}"].matrix_local.to_quaternion()
    e0 = qr.rotation_difference(qa).angle
    # which sign of local-Y rotation swings the inferior angle laterally? test with a probe point below the pivot
    Mb = (MW @ rig.data.bones[f"scap_glide_{sd}"].matrix_local); yax = Mb.to_3x3().col[1].normalized()
    probe = Vector((0, 0, -0.1)); from mathutils import Matrix  # noqa: E402
    sgn = 1.0 if (Matrix.Rotation(0.2, 3, yax) @ probe).x * sg > 0 else -1.0
    # lift: world +z expressed in the bone's local axes
    upl = Mb.to_3x3().inverted() @ Vector((0, 0, 1))
    def drv(path, idx, expr):
        fc = pg.driver_add(path, idx); d = fc.driver; d.type = "SCRIPTED"
        v = d.variables.new(); v.name = "e"; v.type = "ROTATION_DIFF"
        v.targets[0].id = rig; v.targets[0].bone_target = f"upperarm_{sd}"; v.targets[1].id = rig; v.targets[1].bone_target = f"arm_ref_{sd}"
        d.expression = expr
    f_expr = f"max(0.0, e - {e0:.5f}) / {math.radians(170) - e0:.5f}"
    drv("rotation_euler", 1, f"{sgn * ROT_K / 3.0:.5f} * max(0.0, e - {e0:.5f})")
    for k in range(3):
        if abs(upl[k]) > 1e-3:
            drv("location", k, f"{UP_M * upl[k]:.6f} * {f_expr}")
    info[sd].update(rest_elevation_deg=round(math.degrees(e0), 1), rot_sign=sgn)
# weights: from the spine share only, over the shoulder blade on the back
GN = {g.index: g.name for g in body.vertex_groups}; W = [dict() for _ in range(NV)]
for v in me.vertices:
    for g in v.groups:
        W[v.index][GN[g.group]] = g.weight


def smooth01(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)


for sd, sg in (("r", 1), ("l", -1)):
    gh = np.array(MW @ rig.data.bones[f"upperarm_{sd}"].head_local)
    ex = (np.abs(V[:, 0]) - SCAP_C[0]) / SCAP_AX[0]; ez = (V[:, 2] - (gh[2] + SCAP_C[1])) / SCAP_AX[1]; r = np.sqrt(ex * ex + ez * ez)
    g = np.where(r <= 1, 1.0, 1 - smooth01((r - 1) * min(SCAP_AX) / FADE)) * smooth01(NRM[:, 1] / 0.4) * (V[:, 0] * sg > 0.02)
    g *= 1 - smooth01((np.abs(V[:, 0]) - (X_MAX - 0.03)) / 0.03)     # fully faded before the posterior axillary fold
    g *= np.array([W[i].get(f"upperarm_{sd}", 0.0) < 0.02 for i in range(NV)])   # never on skin the arm moves
    nm = f"scap_glide_{sd}"; n_ch = 0
    for i in np.where(g > 0.01)[0]:
        sp = {b: W[i].get(b, 0.0) for b in SPINE}; tot = sum(sp.values())
        if tot <= 1e-4:
            continue
        take = float(g[i]) * tot
        for b in SPINE:
            if sp[b] > 0:
                W[i][b] = sp[b] * (1 - g[i])
        W[i][nm] = W[i].get(nm, 0.0) + take; n_ch += 1
        top = sorted(((b, x) for b, x in W[i].items() if x > 1e-5), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top)
        W[i] = {b: x / s for b, x in top}
    rep["sides"][sd] = {**info[sd], "glide_vertices": n_ch}
for gname in list(body.vertex_groups):
    body.vertex_groups.remove(gname)
groups = {}
for i in range(NV):
    for b, x in W[i].items():
        if b not in groups:
            groups[b] = body.vertex_groups.new(name=b)
        groups[b].add([i], x, "REPLACE")
body["PHASE3_SCAPULA_GLIDE"] = json.dumps({k: v for k, v in rep.items() if k != "method"})
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), check_existing=False)
rep["out"] = OUT.name; REP.write_text(json.dumps(rep, indent=1)); print("GLIDE", json.dumps({k: v for k, v in rep.items() if k != "method"}))
