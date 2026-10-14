"""Shoulder root-cause diagnostic (14 Oct 2026; docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md). Diagnostic only."""
import pathlib as _pl
ROOT = str(_pl.Path(__file__).resolve().parents[2])
import sys, math, json
sys.path.insert(0, ROOT + "/scripts"); sys.path.insert(0, ROOT + "/scripts/anatomy_fit")
import bpy, numpy as np
from mathutils import Vector
P = ROOT + "/ORIGINAL_V1_WORK/anatomy/"
FILES = {"a003": (P + "audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend", False),
         "R3": (P + "candidates/claude_review_r3_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R3_CLAUDE.blend", True)}
OUT = sys.argv[-1]
import build_original_movement_benchmarks_blender as bench
import original_v1_review_candidate_drives as drives
rep = {}
for tag, (path, drv) in FILES.items():
    bpy.ops.wm.open_mainfile(filepath=path)
    import build_functional_shoulder_correction_blender as correction
    res = correction.build_corrected_scene(); rig, body = res["runtime"], res["body"]
    for kb in body.data.shape_keys.key_blocks[1:]: kb.value = 0.0
    if drv: drives.install_helpers(rig)
    names = {g.index: g.name for g in body.vertex_groups}
    deform = [b.name for b in rig.data.bones if b.use_deform]
    W = [{names[g.group]: g.weight for g in v.groups if names[g.group] in deform and g.weight > 0} for v in body.data.vertices]
    R = [v.co.copy() for v in body.data.vertices]
    head = rig.data.bones["upperarm_r"].head_local.copy()
    # 1. pivot: sphere fit to the deltoid cap (upper-arm-weighted skin above and lateral of the joint, within 9 cm)
    cap = [R[i] for i in range(len(R)) if W[i].get("upperarm_r", 0) > 0.3 and (R[i] - head).length < 0.09 and R[i].z > head.z - 0.01 and R[i].x > head.x - 0.01]
    A = np.array([[2*p.x, 2*p.y, 2*p.z, 1] for p in cap]); b = np.array([p.dot(p) for p in cap])
    c = np.linalg.lstsq(A, b, rcond=None)[0]; centre = Vector(c[:3]); radius = math.sqrt(c[3] + centre.dot(centre))
    # 2. weight band: shoulder-ring skin (|x| > 0.12, z > 1.2), upper-arm weight vs distance from the joint along the arm
    axis = (rig.data.bones["upperarm_r"].tail_local - head).normalized()
    band = sorted(((R[i] - head).dot(axis), W[i].get("upperarm_r", 0) + W[i].get("deltoid_helper_r", 0) * 0.5)
                  for i in range(len(R)) if R[i].x > 0.12 and R[i].z > 1.2 and (R[i] - head).length < 0.15)
    def at(level):
        xs = [d for d, w in band if abs(w - level) < 0.05]; return round(float(np.median(xs)) * 1000, 1) if xs else None
    # 3. relative rotation + blended-matrix conditioning at 90 and 160
    rows = {}
    for ht in (90, 160):
        correction.apply_corrected_pose(res, ht)
        if drv: drives.drive(rig, body)
        q = drives._rel_quat(rig, "upperarm_r", "scapula_r")
        mats = {n: np.array((rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted()).to_3x3()) for n in deform}
        sig = []
        for i, w in enumerate(W):
            if R[i].x > 0.10 and R[i].z > 1.15 and sum(x for n, x in w.items() if n.endswith("_r") and n.startswith(("upperarm", "scapula", "clavicle", "deltoid"))) > 0.3:
                sig.append((i, float(np.linalg.svd(sum(x * mats[n] for n, x in w.items()), compute_uv=False).min())))
        s = [x for _, x in sig]
        rows[ht] = {"arm_rotation_rel_scapula_deg": round(math.degrees(min(q.angle, 2*math.pi - q.angle)), 1),
                    "zone_vertices": len(s), "sigma_min": round(min(s), 3), "lt_0_3": sum(x < 0.3 for x in s), "lt_0_5": sum(x < 0.5 for x in s), "median": round(float(np.median(s)), 3)}
        if ht == 160:
            col = body.data.color_attributes.new("SIG", "FLOAT_COLOR", "POINT")
            sd = dict(sig)
            for i in range(len(R)):
                x = sd.get(i)
                col.data[i].color = (0.62, 0.6, 0.58, 1) if x is None else ((0.85, 0.1, 0.1, 1) if x < 0.3 else (0.95, 0.65, 0.1, 1) if x < 0.6 else (0.25, 0.55, 0.85, 1))
            body.data.color_attributes.active_color = col
            sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sh = sc.display.shading
            sh.light, sh.color_type = "STUDIO", "VERTEX"
            for o in sc.objects:
                if o.type in ("MESH", "CURVE") and o is not body: o.hide_render = True
            sc.render.resolution_x = sc.render.resolution_y = 700
            cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.7
            cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
            tgt = rig.pose.bones["upperarm_r"].head.copy()
            for vname, d in (("front", (0, -1, 0)), ("rear", (0, 1, 0))):
                cam.location = tgt + Vector(d) * 3; cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
                sc.render.filepath = f"{OUT}/{tag}_{vname}.png"; bpy.ops.render.render(write_still=True)
    rep[tag] = {"pivot_offset_mm": round((centre - head).length * 1000, 1), "pivot_offset_xyz_mm": [round(v * 1000, 1) for v in centre - head],
                "cap_sphere_radius_mm": round(radius * 1000, 1), "cap_vertices": len(cap),
                "weight_band_mm_along_arm": {"w0.1": at(0.1), "w0.5": at(0.5), "w0.9": at(0.9)}, "poses": rows}
    print("WHY", tag, json.dumps(rep[tag]))
