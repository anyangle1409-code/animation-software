"""M1: integration benchmarks (bodyweight squat, overhead shoulder press, bent-over row) on the ORIGINAL_v1 67-joint rig.

Diagnostic movement evidence on the unchanged 17,946-vertex original male; no anatomy, motion, deformation, GLB,
clinical or production approval.  Each benchmark is a 9-frame keyframe path (smoothstep in time).  Peak joint angles
stay at or below the CDC/Soucie 2011 passive means for males aged 20-44 recorded in
ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json (hip flexion 130.4, knee flexion 137.7, shoulder flexion
168.8, elbow flexion 144.6 deg), with one recorded exception: a flat-foot parallel squat needs more ankle dorsiflexion
than the 12.7 deg passive (non-weight-bearing) mean; the required value is measured and reported, not hidden.

Rig sign conventions (measured on the rig; HGPT -Y anterior): hip flexion = thigh -X, knee flexion = shin +X, ankle
dorsiflexion = foot -X, shoulder flexion = upper-arm -X, elbow flexion = forearm -X, trunk flexion = pelvis/spine +X.
The pelvis is the parent of both spine and thighs, so a hip hinge is pelvis +a with thighs -a.  The root is translated
so that both ankle heads stay at their rest positions (feet planted); feet are kept flat by solving the foot rotation.
The shoulder press reuses the reviewed PR110/PR111 coupled shoulder motion (clavicle/scapula/humerus) unchanged.

Per frame: whole-body collapse (< 0.1 area ratio), stretch (> 2), self-intersecting face pairs (no shared vertex,
grouped by dominant skin group pair), exact body volume change, peak joint angles, foot floor offset.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

ATLAS = ROOT / "ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json"
FRAMES = 9
CDC_KEYS = {"hip_flexion": "cdc_hip_flexion", "knee_flexion": "cdc_knee_flexion", "ankle_dorsiflexion": "cdc_ankle_dorsiflexion",
            "shoulder_flexion": "cdc_shoulder_flexion", "elbow_flexion": "cdc_elbow_flexion"}

# peak angles (deg) per benchmark; each ramps from 0 with smoothstep over the frames
SQUAT = {"pelvis_forward_tilt": 25.0, "hip_flexion": 110.0, "knee_flexion": 110.0, "spine_extension": 10.0}
ROW = {"pelvis_forward_tilt": 45.0, "hip_flexion": 45.0, "knee_flexion": 20.0, "shoulder_flexion_start": 45.0,
       "shoulder_extension_end": 40.0, "elbow_flexion": 100.0, "clavicle_retraction": 12.0}
PRESS = {"ht_start": 90.0, "ht_end": 160.0, "elbow_flexion_start": 90.0}


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def cdc_limits():
    obs = json.loads(ATLAS.read_text())["observations"]
    return {k: obs[v]["value"]["mean"] for k, v in CDC_KEYS.items()}


def _reset(rig):
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def _rot(pb, x=0.0, y=0.0, z=0.0):
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ")


def _plant_feet(rig, rest_heads):
    """Keep both feet flat (foot world rotation = rest) and both ankle heads at their rest positions."""
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        pb = rig.pose.bones[f"foot_{s}"]
        rest = rig.data.bones[f"foot_{s}"].matrix_local
        target = Matrix.Translation(pb.matrix.translation) @ rest.to_3x3().to_4x4()
        pb.matrix = target
        bpy.context.view_layer.update()
    offset = sum(((rest_heads[s] - rig.pose.bones[f"foot_{s}"].head) for s in ("l", "r")), Vector()) / 2.0
    root = rig.pose.bones["root"]
    root.matrix = Matrix.Translation(offset) @ root.matrix
    bpy.context.view_layer.update()


def _ankle_dorsiflexion_deg(rig, s):
    shin = rig.pose.bones[f"shin_{s}"]
    foot = rig.pose.bones[f"foot_{s}"]
    rest_rel = rig.data.bones[f"shin_{s}"].matrix_local.inverted() @ rig.data.bones[f"foot_{s}"].matrix_local
    rel = shin.matrix.inverted() @ foot.matrix
    d = (rest_rel.inverted() @ rel).to_euler("XYZ")
    return -math.degrees(d.x)


def pose_squat(rig, t, rest_heads):
    _reset(rig)
    k = smooth(t)
    _rot(rig.pose.bones["pelvis"], x=SQUAT["pelvis_forward_tilt"] * k)
    _rot(rig.pose.bones["spine_01"], x=-SQUAT["spine_extension"] * k)
    for s in ("l", "r"):
        _rot(rig.pose.bones[f"thigh_{s}"], x=-SQUAT["hip_flexion"] * k)
        _rot(rig.pose.bones[f"shin_{s}"], x=SQUAT["knee_flexion"] * k)
    _plant_feet(rig, rest_heads)
    return {"hip_flexion": SQUAT["hip_flexion"] * k, "knee_flexion": SQUAT["knee_flexion"] * k,
            "ankle_dorsiflexion": max(_ankle_dorsiflexion_deg(rig, s) for s in ("l", "r"))}


def pose_row(rig, t, rest_heads, clavicle_basis):
    _reset(rig)
    k_hinge = smooth(min(1.0, t * 2.0))                       # hinge first half, pull second half
    k_pull = smooth(max(0.0, t * 2.0 - 1.0))
    _rot(rig.pose.bones["pelvis"], x=ROW["pelvis_forward_tilt"] * k_hinge)
    for s, side_sign in (("l", -1.0), ("r", 1.0)):
        _rot(rig.pose.bones[f"thigh_{s}"], x=-ROW["hip_flexion"] * k_hinge)
        _rot(rig.pose.bones[f"shin_{s}"], x=ROW["knee_flexion"] * k_hinge)
        shoulder = ROW["shoulder_flexion_start"] * k_hinge - (ROW["shoulder_flexion_start"] + ROW["shoulder_extension_end"]) * k_pull
        _rot(rig.pose.bones[f"upperarm_{s}"], x=-shoulder)
        _rot(rig.pose.bones[f"forearm_{s}"], x=-ROW["elbow_flexion"] * k_pull)
        profile = {"clavicle_elevation_deg": 0.0, "clavicle_posterior_rotation_deg": 0.0,
                   "clavicle_retraction_deg": ROW["clavicle_retraction"] * k_pull}
        rig.pose.bones[f"clavicle_{s}"].matrix_basis = clavicle_basis(profile, side_sign)
    _plant_feet(rig, rest_heads)
    return {"hip_flexion": ROW["hip_flexion"] * k_hinge, "knee_flexion": ROW["knee_flexion"] * k_hinge,
            "shoulder_flexion": max(0.0, ROW["shoulder_flexion_start"] * k_hinge - (ROW["shoulder_flexion_start"] + ROW["shoulder_extension_end"]) * k_pull),
            "elbow_flexion": ROW["elbow_flexion"] * k_pull,
            "ankle_dorsiflexion": max(_ankle_dorsiflexion_deg(rig, s) for s in ("l", "r"))}


def pose_press(result, t, correction):
    k = smooth(t)
    ht = PRESS["ht_start"] + (PRESS["ht_end"] - PRESS["ht_start"]) * k
    correction.apply_corrected_pose(result, ht)
    rig = result["runtime"]
    elbow = PRESS["elbow_flexion_start"] * (1.0 - k)
    for s in ("l", "r"):
        pb = rig.pose.bones[f"forearm_{s}"]
        _rot(pb, x=-elbow)
    bpy.context.view_layer.update()
    return {"humerothoracic_elevation": ht, "elbow_flexion": elbow, "shoulder_flexion": ht * math.sin(math.radians(40.0))}


def _evaluated(body):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    V = [ev.matrix_world @ v.co for v in me.vertices]
    F = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return V, F


def _area(V, f):
    a, b, c = V[f[0]], V[f[1]], V[f[2]]
    return (b - a).cross(c - a).length / 2.0


def frame_metrics(V0, V, F, dom, rest_floor):
    if any(len(f) != 3 for f in F):
        raise RuntimeError("triangulated body required")
    ratios = [_area(V, f) / _area(V0, f) for f in F if _area(V0, f) > 1e-12]
    vol0 = sum(V0[f[0]].dot(V0[f[1]].cross(V0[f[2]])) for f in F) / 6.0
    vol = sum(V[f[0]].dot(V[f[1]].cross(V[f[2]])) for f in F) / 6.0
    tree = BVHTree.FromPolygons(V, F, all_triangles=True)
    fs = [set(f) for f in F]
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and not (fs[a] & fs[b])]

    def g(f):
        names = [dom[v] for v in F[f]]
        return max(set(names), key=names.count)
    classes = Counter(tuple(sorted((g(a), g(b)))) for a, b in pairs)
    return {"collapse_lt_0_1": sum(r < 0.1 for r in ratios), "stretch_gt_2": sum(r > 2 for r in ratios),
            "area_ratio_min": round(min(ratios), 4), "area_ratio_max": round(max(ratios), 4),
            "body_volume_change_pct": round((vol - vol0) / vol0 * 100, 4),
            "self_intersecting_pairs": len(pairs),
            "self_intersection_classes_top": [[a, b, n] for (a, b), n in classes.most_common(6)],
            "lowest_point_z_mm": round((min(v.z for v in V) - rest_floor) * 1000, 2)}


def dominant_groups(body):
    names = {g.index: g.name for g in body.vertex_groups}
    out = []
    for v in body.data.vertices:
        best = max(v.groups, key=lambda e: e.weight, default=None)
        out.append(names[best.group] if best is not None else "none")
    return out


def run(render_dir=None):
    import build_functional_shoulder_correction_blender as correction
    import build_functional_original_coupled_motion_blender as coupled
    result = correction.build_corrected_scene()
    body, rig = result["body"], result["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    _reset(rig)
    V0, F = _evaluated(body)
    rest_floor = min(v.z for v in V0)
    rest_heads = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l", "r")}
    dom = dominant_groups(body)
    limits = cdc_limits()
    report = {"benchmarks": {}, "cdc_passive_means_deg": limits, "frames": FRAMES,
              "approved": False, "scope": "authored FK benchmark paths within CDC passive means; diagnostic only"}
    plans = {
        "squat": lambda t: pose_squat(rig, t, rest_heads),
        "bent_over_row": lambda t: pose_row(rig, t, rest_heads, coupled.clavicle_basis),
        "shoulder_press": lambda t: pose_press(result, t, correction),
    }
    renders = []
    for name, fn in plans.items():
        rows = []
        for i in range(FRAMES):
            t = i / (FRAMES - 1)
            angles = fn(t)
            V, _ = _evaluated(body)
            m = frame_metrics(V0, V, F, dom, rest_floor)
            m["t"] = round(t, 4)
            m["angles_deg"] = {k: round(v, 2) for k, v in angles.items()}
            m["exceeds_cdc_passive_mean"] = {k: round(v - limits[k], 2) for k, v in angles.items() if k in limits and v > limits[k]}
            rows.append(m)
            if render_dir and i in (0, FRAMES // 2, FRAMES - 1):
                renders.extend(_render(body, Path(render_dir), f"{name}__t{t:.2f}"))
        report["benchmarks"][name] = {"frames": rows,
                                      "worst": {k: max(r[k] for r in rows) for k in ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs")},
                                      "volume_change_pct_range": [min(r["body_volume_change_pct"] for r in rows), max(r["body_volume_change_pct"] for r in rows)]}
    _reset(rig)
    report["renders"] = [p.name for p in renders]
    return report


_CAM = {}


def _render(body, out, stem):
    scene = bpy.context.scene
    if not _CAM:
        for obj in scene.objects:
            if obj.type in ("MESH", "CURVE") and obj is not body:
                obj.hide_render = True
        body.data.materials.clear()
        mat = bpy.data.materials.new("HGPT_M1_SKIN_TMP"); mat.diffuse_color = (0.64, 0.44, 0.36, 1.0)
        body.data.materials.append(mat)
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light, scene.display.shading.color_type = "STUDIO", "MATERIAL"
        scene.display.shading.show_cavity = True
        scene.render.resolution_x, scene.render.resolution_y = 700, 900
        scene.render.image_settings.file_format = "PNG"
        cd = bpy.data.cameras.new("HGPT_M1_CAM_TMP"); cd.type = "ORTHO"; cd.ortho_scale = 2.3
        cam = bpy.data.objects.new("HGPT_M1_CAM_TMP", cd); scene.collection.objects.link(cam); scene.camera = cam
        _CAM["cam"] = cam
        out.mkdir(parents=True, exist_ok=True)
    cam = _CAM["cam"]
    written = []
    for view, offset in (("front", (0.0, -5.0, 0.0)), ("side", (5.0, 0.0, 0.0))):
        target = Vector((0.0, 0.0, 0.95))
        cam.location = target + Vector(offset)
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        path = out / f"{stem}__{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        written.append(path)
    return written


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = Path(args[args.index("--out") + 1]) if "--out" in args else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
    renders = Path(args[args.index("--renders") + 1]) if "--renders" in args else None
    if renders and renders.exists():
        raise FileExistsError(renders)
    rep = run(renders)
    text = json.dumps(rep, indent=1)
    if out:
        out.write_text(text + "\n")
    for name, b in rep["benchmarks"].items():
        print("M1", name, json.dumps(b["worst"]), b["volume_change_pct_range"],
              json.dumps(b["frames"][-1]["angles_deg"]), json.dumps(b["frames"][-1]["self_intersection_classes_top"][:3]),
              "lowest", b["frames"][-1]["lowest_point_z_mm"], "exceeds", b["frames"][-1]["exceeds_cdc_passive_mean"])
