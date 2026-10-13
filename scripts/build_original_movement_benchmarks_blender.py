"""M1/M2: movement benchmarks on the ORIGINAL_v1 67-joint rig: squat, bent-over row, overhead press (M1); lunge,
walk stride, trunk rotation, grip (M2).  Lunge/walk are grounded by vertical root adjustment only (lowest skin point
on the floor); no foot-planting or gait-cycle validity is claimed for them.

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
# M2 (anatomical side = runtime suffix per F-SIDE-001: _r is anatomical left, _l anatomical right)
LUNGE = {"front": "r", "front_hip": 90.0, "front_knee": 90.0, "rear_hip_extension": 10.0, "rear_knee": 90.0, "rear_toe_extension": 45.0}
WALK_KEYS = [  # hip (+flex), knee, ankle (+DF), toe (+toe extension), shoulder (+flex), elbow for (lead "r", trail "l")
    {"r": (25, 5, 0, 0, -15, 15), "l": (-10, 35, -15, 30, 15, 15)},
    {"r": (0, 15, 10, 0, 0, 10), "l": (20, 60, 0, 0, 0, 10)},
    {"r": (-10, 35, -15, 30, 15, 15), "l": (25, 5, 0, 0, -15, 15)},
    {"r": (20, 60, 0, 0, 0, 10), "l": (0, 15, 10, 0, 0, 10)},
    {"r": (25, 5, 0, 0, -15, 15), "l": (-10, 35, -15, 30, 15, 15)},
]
TRUNK_ROTATION = {"spine_01": 15.0, "spine_02": 15.0, "spine_03": 15.0, "neck": 15.0}
GRIP = {"01": 80.0, "02": 90.0, "03": 60.0, "thumb_01": 30.0, "thumb_02": 40.0, "thumb_03": 40.0}
GRIP_ARM = {"shoulder_flexion": 45.0, "elbow_flexion": 90.0}   # hands held in front of the body (static during the grip)
EXTRA_CDC = {"hip_extension": "cdc_hip_extension"}


def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def cdc_limits():
    obs = json.loads(ATLAS.read_text())["observations"]
    return {k: obs[v]["value"]["mean"] for k, v in {**CDC_KEYS, **EXTRA_CDC}.items()}


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


def _ground(rig, body):
    """Vertical root adjustment only: the lowest skin point is put on the rest floor (no foot planting claimed)."""
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    root = rig.pose.bones["root"]
    root.matrix = Matrix.Translation(Vector((0.0, 0.0, REST_FLOOR[0] - zmin))) @ root.matrix
    bpy.context.view_layer.update()


REST_FLOOR = [0.0]


def pose_lunge(rig, body, t):
    _reset(rig)
    k = smooth(t)
    f = LUNGE["front"]; r = "l" if f == "r" else "r"
    _rot(rig.pose.bones[f"thigh_{f}"], x=-LUNGE["front_hip"] * k)
    _rot(rig.pose.bones[f"shin_{f}"], x=LUNGE["front_knee"] * k)
    _rot(rig.pose.bones[f"thigh_{r}"], x=LUNGE["rear_hip_extension"] * k)
    _rot(rig.pose.bones[f"shin_{r}"], x=LUNGE["rear_knee"] * k)
    _rot(rig.pose.bones[f"toe_{r}"], x=-LUNGE["rear_toe_extension"] * k)
    bpy.context.view_layer.update()
    # keep the front foot flat
    pb = rig.pose.bones[f"foot_{f}"]
    pb.matrix = Matrix.Translation(pb.matrix.translation) @ rig.data.bones[f"foot_{f}"].matrix_local.to_3x3().to_4x4()
    _ground(rig, body)
    return {"hip_flexion": LUNGE["front_hip"] * k, "knee_flexion": max(LUNGE["front_knee"], LUNGE["rear_knee"]) * k,
            "hip_extension": LUNGE["rear_hip_extension"] * k, "ankle_dorsiflexion": _ankle_dorsiflexion_deg(rig, f)}


def pose_walk(rig, body, t):
    _reset(rig)
    seg = min(len(WALK_KEYS) - 2, int(t * (len(WALK_KEYS) - 1)))
    u = smooth(t * (len(WALK_KEYS) - 1) - seg)
    a, b = WALK_KEYS[seg], WALK_KEYS[seg + 1]
    peak = {"hip_flexion": 0.0, "hip_extension": 0.0, "knee_flexion": 0.0, "ankle_dorsiflexion": 0.0,
            "shoulder_flexion": 0.0, "elbow_flexion": 0.0}
    for s in ("l", "r"):
        hip, knee, ank, toe, sh, el = [(1 - u) * x + u * y for x, y in zip(a[s], b[s])]
        _rot(rig.pose.bones[f"thigh_{s}"], x=-hip)
        _rot(rig.pose.bones[f"shin_{s}"], x=knee)
        _rot(rig.pose.bones[f"foot_{s}"], x=-ank)
        _rot(rig.pose.bones[f"toe_{s}"], x=-toe)
        _rot(rig.pose.bones[f"upperarm_{s}"], x=-sh)
        _rot(rig.pose.bones[f"forearm_{s}"], x=-el)
        peak["hip_flexion"] = max(peak["hip_flexion"], hip)
        peak["hip_extension"] = max(peak["hip_extension"], -hip)
        peak["knee_flexion"] = max(peak["knee_flexion"], knee)
        peak["ankle_dorsiflexion"] = max(peak["ankle_dorsiflexion"], ank)
        peak["shoulder_flexion"] = max(peak["shoulder_flexion"], sh)
        peak["elbow_flexion"] = max(peak["elbow_flexion"], el)
    _ground(rig, body)
    return peak


def pose_trunk_rotation(rig, body, t):
    _reset(rig)
    k = smooth(t)
    for n, a in TRUNK_ROTATION.items():
        _rot(rig.pose.bones[n], y=a * k)
    bpy.context.view_layer.update()
    return {"trunk_axial_rotation_total": sum(TRUNK_ROTATION[n] for n in ("spine_01", "spine_02", "spine_03")) * k}


def _fingertip_palm_mm(rig, s):
    palm = rig.pose.bones[f"hand_{s}"].head
    return sum((rig.pose.bones[f"{d}_03_{s}"].tail - palm).length for d in ("index", "middle", "ring", "pinky")) / 4 * 1000


def _palmar_sign(rig, pb, probe_deg=5.0):
    """Sign of a local-Z rotation that moves this digit bone's tip toward the palm.

    The rig's local digit axes are NOT mirror images between sides (+Z flexes the _r fingers but extends the _l fingers),
    so the sign is measured on the rig itself: at rest the palms face the body, so palmar = toward the midline (the
    convention of scripts/audit_original_v1_joint_kinematics_blender.py).  Call it with the rig at rest.
    """
    saved = pb.rotation_mode, pb.rotation_quaternion.copy(), pb.rotation_euler.copy()
    head = rig.matrix_world @ pb.head
    tip0 = rig.matrix_world @ pb.tail
    _rot(pb, z=probe_deg)
    bpy.context.view_layer.update()
    tip1 = rig.matrix_world @ pb.tail
    pb.rotation_mode = saved[0]
    pb.rotation_quaternion, pb.rotation_euler = saved[1], saved[2]
    bpy.context.view_layer.update()
    medial = -1.0 if head.x > 0 else 1.0
    return 1.0 if (tip1.x - tip0.x) * medial > 0 else -1.0


def pose_grip(rig, body, t):
    _reset(rig)
    bpy.context.view_layer.update()
    k = smooth(t)
    digits = [(f"{d}_{j}_{s}", GRIP[j]) for s in ("l", "r") for d in ("index", "middle", "ring", "pinky") for j in ("01", "02", "03")]
    digits += [(f"{j}_{s}", GRIP[j]) for s in ("l", "r") for j in ("thumb_01", "thumb_02", "thumb_03")]
    signs = {n: _palmar_sign(rig, rig.pose.bones[n]) for n, _ in digits}       # measured at rest (palms face the body)
    for s in ("l", "r"):
        _rot(rig.pose.bones[f"upperarm_{s}"], x=-GRIP_ARM["shoulder_flexion"])
        _rot(rig.pose.bones[f"forearm_{s}"], x=-GRIP_ARM["elbow_flexion"])
    for n, deg in digits:
        _rot(rig.pose.bones[n], z=signs[n] * deg * k)
    bpy.context.view_layer.update()
    return {"mcp_flexion": GRIP["01"] * k, "pip_flexion": GRIP["02"] * k, "dip_flexion": GRIP["03"] * k,
            "shoulder_flexion": GRIP_ARM["shoulder_flexion"], "elbow_flexion": GRIP_ARM["elbow_flexion"],
            "fingertip_to_wrist_mm_l": _fingertip_palm_mm(rig, "l"), "fingertip_to_wrist_mm_r": _fingertip_palm_mm(rig, "r"),
            "digit_tip_mirror_error_mm": _digit_mirror_error_mm(rig)}


def _digit_mirror_error_mm(rig):
    """Largest distance between a left digit tip and the x-mirror of its right counterpart (both hands posed alike)."""
    worst = 0.0
    for d in ("index", "middle", "ring", "pinky", "thumb"):
        for j in ("01", "02", "03"):
            a = rig.matrix_world @ rig.pose.bones[f"{d}_{j}_l"].tail
            b = rig.matrix_world @ rig.pose.bones[f"{d}_{j}_r"].tail
            worst = max(worst, (a - Vector((-b.x, b.y, b.z))).length)
    return worst * 1000


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
    REST_FLOOR[0] = rest_floor
    rest_heads = {s: rig.pose.bones[f"foot_{s}"].head.copy() for s in ("l", "r")}
    dom = dominant_groups(body)
    limits = cdc_limits()
    report = {"benchmarks": {}, "cdc_passive_means_deg": limits, "frames": FRAMES,
              "approved": False, "scope": "authored FK benchmark paths within CDC passive means; diagnostic only"}
    plans = {
        "squat": lambda t: pose_squat(rig, t, rest_heads),
        "bent_over_row": lambda t: pose_row(rig, t, rest_heads, coupled.clavicle_basis),
        "shoulder_press": lambda t: pose_press(result, t, correction),
        "lunge": lambda t: pose_lunge(rig, body, t),
        "walk_stride": lambda t: pose_walk(rig, body, t),
        "trunk_rotation": lambda t: pose_trunk_rotation(rig, body, t),
        "grip": lambda t: pose_grip(rig, body, t),
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
                renders.extend(_render(body, Path(render_dir), f"{name}__t{t:.2f}",
                                       hand=rig.pose.bones["hand_r"].head.copy() if name == "grip" else None))
        report["benchmarks"][name] = {"frames": rows,
                                      "worst": {k: max(r[k] for r in rows) for k in ("collapse_lt_0_1", "stretch_gt_2", "self_intersecting_pairs")},
                                      "volume_change_pct_range": [min(r["body_volume_change_pct"] for r in rows), max(r["body_volume_change_pct"] for r in rows)]}
    _reset(rig)
    report["renders"] = [p.name for p in renders]
    return report


_CAM = {}


def _render(body, out, stem, hand=None):
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
    cam.data.ortho_scale = 0.32 if hand is not None else 2.3
    for view, offset in (("front", (0.0, -5.0, 0.0)), ("side", (5.0, 0.0, 0.0))):
        target = hand if hand is not None else Vector((0.0, 0.0, 0.95))
        cam.location = target + Vector(offset) * (0.2 if hand is not None else 1.0)
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
