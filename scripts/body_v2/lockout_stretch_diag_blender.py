"""Diagnostic (read-only): where the press lockout stretches / compresses the skin, and what causes it.

The trajectory test counts ~9,000 edges stretched over 2x (and ~5,400 compressed under 0.5x) at the press lockout of T3.
Here the lockout (shoulder_girdle_candidate.apply_press_pose at 160 deg, elbows straight) is measured with the key
families switched on / off - all keys, without the R121 keys, plain skinning - and every stretched / compressed edge is
attributed to the dominant bone of its two vertices and to a rest-space zone.  Also: the rest length of the affected
edges (tiny edges stretching matter less than long ones), the stretched length in mm, triangle area ratios, and front /
back / side heat-map renders of the per-vertex max edge ratio (blue compressed, white 1x, red 2x+).  Nothing is saved.

usage: python3.13 lockout_stretch_diag_blender.py -- <body.blend> <r57src> <out_dir> [ht_deg]
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]; SRC, ROOT, OUT = a[0], a[1], a[2]
HT = float(a[3]) if len(a) > 3 else 160.0
os.makedirs(OUT, exist_ok=True)
sys.path[:0] = [ROOT + "/scripts", ROOT + "/scripts/anatomy_fit", os.path.dirname(os.path.abspath(__file__))]
bpy.ops.wm.open_mainfile(filepath=SRC)
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402
import r121_drives  # noqa: E402
import build_functional_shoulder_correction_blender as correction  # noqa: E402
import functional_shoulder_correction as corr  # noqa: E402
import shoulder_girdle_candidate as girdle  # noqa: E402

body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
me = body.data; n = len(me.vertices)
AX = {}
for side, name in correction.HUMERI:
    b = rig.data.bones[name]
    AX[name] = corr.humeral_axial_angle_deg(tuple(b.tail_local - b.head_local), tuple(b.matrix_local.col[0].xyz), 40.0, side)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
TRI = np.array([(p.vertices[0], p.vertices[k], p.vertices[k + 1]) for p in me.polygons for k in range(1, len(p.vertices) - 1)])
GN = [g.name for g in body.vertex_groups]
DOM = np.full(n, "", dtype=object); DW = np.zeros(n)
for v in me.vertices:
    for g in v.groups:
        if g.weight > DW[v.index]:
            DW[v.index], DOM[v.index] = g.weight, GN[g.group]
HOLD = np.array([any(k in d for k in ("hand", "thumb", "index", "middle", "ring", "pinky", "metacarpal", "foot", "toe", "ball"))
                 for d in DOM])
L0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1)
EOK = ~(HOLD[E[:, 0]] | HOLD[E[:, 1]]) & (L0 > 1e-7)
z0 = float(R[:, 2].min()); H = float(R[:, 2].max()) - z0


def zone(P):
    """rest-space zone of points (anatomical left = +x)"""
    x, y, z = np.abs(P[:, 0]), P[:, 1], (P[:, 2] - z0) / H
    out = np.full(len(P), "other", dtype=object)
    out[(z > 0.62) & (x < 0.10)] = "torso_mid"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y < -0.02)] = "chest_side_pec"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y > 0.04)] = "back_side_lat"
    out[(z > 0.66) & (z < 0.80) & (x >= 0.10) & (x < 0.19) & (y >= -0.02) & (y <= 0.04)] = "axilla_floor"
    out[(z > 0.80) & (x >= 0.06) & (x < 0.17)] = "trapezius_neck"
    out[(z > 0.74) & (x >= 0.17)] = "deltoid_cap"
    out[(z > 0.62) & (z <= 0.74) & (x >= 0.19)] = "upper_arm"
    return out


EZ = zone(0.5 * (R[E[:, 0]] + R[E[:, 1]]))
EB = np.where(DW[E[:, 0]] >= DW[E[:, 1]], DOM[E[:, 0]], DOM[E[:, 1]])


def ev():
    dg = bpy.context.evaluated_depsgraph_get(); e = body.evaluated_get(dg); m = e.to_mesh()
    P = np.empty(n * 3); m.vertices.foreach_get("co", P); e.to_mesh_clear(); return P.reshape(-1, 3)


def pose(r121=True, legacy=True):
    bench._reset(rig)
    for kb in me.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    girdle.apply_press_pose(rig, HT, AX)
    for s in ("l", "r"):
        pb = rig.pose.bones[f"forearm_{s}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    if legacy:
        drives.drive(rig, body)
    if r121:
        r121_drives.drive(rig, body)
    bpy.context.view_layer.update()


def tally(mask, key):
    out = {}
    for k in np.unique(key[mask]):
        out[str(k)] = int((mask & (key == k)).sum())
    return dict(sorted(out.items(), key=lambda t: -t[1])[:8])


def tri_area(P):
    return 0.5 * np.linalg.norm(np.cross(P[TRI[:, 1]] - P[TRI[:, 0]], P[TRI[:, 2]] - P[TRI[:, 0]]), axis=1)


A0 = tri_area(R); TOK = ~HOLD[TRI].any(1) & (A0 > 1e-12)
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH", "CURVE") and ob is not body:
        ob.hide_render = True
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam)
sc.camera = cam; cd.ortho_scale = 0.9
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "VERTEX"
sc.render.resolution_x = 700; sc.render.resolution_y = 700
attr = me.color_attributes.get("HGPT_STRETCH") or me.color_attributes.new("HGPT_STRETCH", "FLOAT_COLOR", "POINT")
me.color_attributes.active_color = attr
rep = {"press_ht_deg": HT, "edges": int(EOK.sum())}
for tag, r121, leg in (("lock_all", True, True), ("lock_no_r121", False, True), ("lock_lbs_only", False, False)):
    pose(r121, leg); P = ev()
    L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    ratio = np.where(EOK, L / np.maximum(L0, 1e-12), 1.0)
    st, co = EOK & (ratio > 2.0), EOK & (ratio < 0.5)
    ar = tri_area(P) / np.maximum(A0, 1e-15)
    rep[tag] = {"stretch_gt2": int(st.sum()), "compress_lt0.5": int(co.sum()),
                "stretch_gt1.5": int((EOK & (ratio > 1.5)).sum()),
                "stretched_rest_len_mm_p50": round(float(np.median(L0[st])) * 1000, 2) if st.any() else 0,
                "all_rest_len_mm_p50": round(float(np.median(L0[EOK])) * 1000, 2),
                "stretched_len_mm_p50_p95": [round(float(np.percentile(L[st], q)) * 1000, 2) for q in (50, 95)] if st.any() else 0,
                "stretch_by_zone": tally(st, EZ), "stretch_by_bone": tally(st, EB),
                "compress_by_zone": tally(co, EZ), "compress_by_bone": tally(co, EB),
                "tri_area_gt3": int((TOK & (ar > 3)).sum()), "tri_area_lt0.25": int((TOK & (ar < 0.25)).sum()),
                "max_ratio": round(float(ratio[EOK].max()), 2)}
    if st.any():
        mid = 0.5 * (R[E[st, 0]] + R[E[st, 1]])
        for s, sg in (("left(+x)", 1), ("right(-x)", -1)):
            m_ = np.sign(mid[:, 0]) == sg
            if m_.any():
                rep[tag][f"stretch_rest_bbox_{s}_m"] = [np.round(mid[m_].min(0), 3).tolist(), np.round(mid[m_].max(0), 3).tolist()]
    print("STRETCH", tag, json.dumps(rep[tag]), flush=True)
    vr = np.ones(n)                                            # per-vertex: the most extreme adjacent edge ratio (log)
    lr = np.log2(np.clip(ratio, 0.25, 4.0))
    vmax = np.zeros(n); vmin = np.zeros(n)
    np.maximum.at(vmax, E[:, 0], lr); np.maximum.at(vmax, E[:, 1], lr)
    np.minimum.at(vmin, E[:, 0], lr); np.minimum.at(vmin, E[:, 1], lr)
    vr = np.where(vmax >= -vmin, vmax, vmin)                  # +1 = 2x stretched, -1 = 0.5x
    t = np.clip(vr, -1, 1)
    col = np.ones((n, 4))
    col[:, 0] = np.where(t < 0, 1 + t, 1.0); col[:, 1] = 1 - np.abs(t); col[:, 2] = np.where(t > 0, 1 - t, 1.0)
    attr.data.foreach_set("color", col.ravel())
    if tag in ("lock_all", "lock_lbs_only"):
        sh = rig.pose.bones["upperarm_l"].head
        for view, dv in {"front": (0, -1, 0), "back": (0, 1, 0), "side": (1, 0, 0)}.items():
            d = Vector(dv); c = Vector((sh.x * 0.6 if view != "side" else 0, 0, sh.z))
            cam.location = c + d * 3; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
            sc.render.filepath = f"{OUT}/{tag}_{view}.png"; bpy.ops.render.render(write_still=True)
json.dump(rep, open(f"{OUT}/lockout_stretch_diag.json", "w"), indent=1)
print("DIAG done", flush=True)
