"""Exercise-pose deformation test for the O4 CANDIDATE (never saves).

blender --background --factory-startup ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend \
        --python scripts/pose_test_original_v1_o4_candidate_blender.py -- <out_dir> [pose,pose,...]

Poses are review approximations of the key frames of each exercise, built by
aiming v4 bones in world directions (biomechanical joint angles). They do not
replace the runtime exercise solver; they exercise the mesh/weights through the
same joint ranges. For each pose the script measures volume change, edge
stretch/compression (by body region) and self-intersections, and renders
front / side / three-quarter review images.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(args[0]) if args else Path(bpy.data.filepath).parent / "pose_tests"
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None
OUT.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Pose tests run only on candidate files.")
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig)
region_names = json.loads(scene["hgpt_region_names"])
vreg = np.array([d.value for d in body.data.attributes["hgpt_region"].data])

F = Vector((0, -1, 0))   # character forward
B = -F
U = Vector((0, 0, 1))
D = -U


def upd():
    bpy.context.view_layer.update()


def pb(name):
    return rig.pose.bones[name]


def bdir(name):
    p = pb(name)
    return (p.tail - p.head).normalized()


def rot(name, axis, deg):
    """Rotate a pose bone about a world axis through its current head."""
    p = pb(name)
    upd()
    axis = Vector(axis)
    if axis.length < 1e-9 or abs(deg) < 1e-9:
        return
    M = p.matrix.copy()
    head = M.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, axis.normalized())
    p.matrix = Matrix.Translation(head) @ R @ Matrix.Translation(-head) @ M
    upd()


def aim(name, target):
    """Minimal rotation that points the bone along a world direction."""
    t = Vector(target).normalized()
    c = bdir(name)
    ang = math.degrees(c.angle(t))
    if ang < 1e-4:
        return
    axis = c.cross(t)
    if axis.length < 1e-9:
        axis = c.orthogonal()
    rot(name, axis, ang)


def palm_normal(s):
    """Palm normal (points out of the palm) from the posed hand bones."""
    h = bdir(f"hand_{s}")
    radial = pb(f"metacarpal_index_{s}").head - pb(f"metacarpal_pinky_{s}").head
    n = h.cross(radial).normalized()
    return n * PALM_SIGN[s]


def twist_palm(s, target):
    """Pronate/supinate the forearm so the palm faces `target` as closely as possible."""
    axis = bdir(f"forearm_{s}")
    n = palm_normal(s)
    t = Vector(target)
    n_p = (n - axis * n.dot(axis)).normalized()
    t_p = (t - axis * t.dot(axis)).normalized()
    ang = math.degrees(n_p.angle(t_p))
    sign = 1 if n_p.cross(t_p).dot(axis) > 0 else -1
    rot(f"forearm_{s}", axis, sign * ang)


def grip(s, amount=1.0, thumb=True):
    """Close the fingers toward the palm (cylindrical handle grip)."""
    for f in ("index", "middle", "ring", "pinky"):
        for k, deg in ((1, 70), (2, 88), (3, 55)):
            name = f"{f}_0{k}_{s}"
            axis = bdir(name).cross(palm_normal(s))
            rot(name, axis, deg * amount)
    if thumb:
        for k, deg in ((1, 28), (2, 30), (3, 38)):
            name = f"thumb_0{k}_{s}"
            n = palm_normal(s)
            axis = bdir(name).cross(n + bdir(f"index_01_{s}") * 0.6)
            rot(name, axis, deg * amount)


def lat(s):
    return Vector((1.0 if s == "r" else -1.0, 0, 0))


def reset():
    for p in rig.pose.bones:
        p.matrix_basis = Matrix.Identity(4)
    upd()


reset()
PALM_SIGN = {}
for s in "lr":
    h = bdir(f"hand_{s}")
    radial = pb(f"metacarpal_index_{s}").head - pb(f"metacarpal_pinky_{s}").head
    n = h.cross(radial).normalized()
    PALM_SIGN[s] = 1 if n.dot(-lat(s)) > 0 else -1  # rest palm faces medially


def ground():
    """Translate the rig so the lowest body point touches z = 0."""
    upd()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    rig.location.z -= zmin
    upd()


# ---------------------------------------------------------------- poses
def pose_neutral():
    pass


def pose_curl_peak():
    for s in "lr":
        aim(f"upperarm_{s}", D + F * 0.18)
        aim(f"forearm_{s}", U * 0.95 + F * 0.55 + lat(s) * -0.05)
        twist_palm(s, B + U * 0.2)          # supinated: palm toward the shoulder
        grip(s)


X = Vector((1, 0, 0))  # rotation about +X leans an upright segment forward


def rot_toward(name, axis, deg, want):
    """Rotate about `axis` by +/-deg, keeping the sign that moves the tail along `want`."""
    before = pb(name).tail.copy()
    rot(name, axis, deg)
    if (pb(name).tail - before).dot(Vector(want)) < 0:
        rot(name, axis, -2 * deg)


def shoulder_rhythm(s, frac):
    """Scapulohumeral rhythm for arm elevation: clavicle elevation and scapular
    upward rotation (about 1:2 with the arm), used by the *_rhythm variants."""
    rot_toward(f"clavicle_{s}", F, 14 * frac, U)
    rot_toward(f"scapula_{s}", F, 28 * frac, lat(s))


def pose_press_bottom(rhythm=False):
    for s in "lr":
        if rhythm:
            shoulder_rhythm(s, 0.45)
        aim(f"upperarm_{s}", lat(s) + D * 0.15 + F * 0.25)
        aim(f"forearm_{s}", U + F * 0.1)
        twist_palm(s, F)
        grip(s)


def pose_press_top(rhythm=False):
    for s in "lr":
        if rhythm:
            shoulder_rhythm(s, 1.0)
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U * 1.0 + lat(s) * 0.25)
        aim(f"forearm_{s}", U + lat(s) * -0.05)
        twist_palm(s, F)
        grip(s)


def pose_squat_bottom():
    for n, deg in (("pelvis", 18), ("spine_01", 6), ("spine_02", 5), ("spine_03", 4)):
        rot(n, X, deg)
    rot("neck", X, -18)
    for s in "lr":
        aim(f"thigh_{s}", F * 1.0 + D * 0.25 + lat(s) * 0.25)
        aim(f"shin_{s}", D * 1.0 + F * 0.35 + lat(s) * 0.12)
        aim(f"foot_{s}", F + D * 0.3 + lat(s) * 0.15)
        aim(f"upperarm_{s}", F + U * 0.05)
        aim(f"forearm_{s}", F + U * 0.05)
    ground()


def pose_pushup_bottom():
    # whole body tipped face-down (plank) through the root bone; joints aimed in world directions
    rot("root", X, 78)
    for s in "lr":
        aim(f"upperarm_{s}", B * 0.8 + lat(s) * 0.55 + U * 0.15)
        aim(f"forearm_{s}", D)
        twist_palm(s, D)
        aim(f"hand_{s}", F + lat(s) * 0.12)
        aim(f"foot_{s}", D + B * 0.25)
        rot_toward(f"toe_{s}", X, 60, B)
    ground()


def pose_pullup_hang(rhythm=False):
    for s in "lr":
        if rhythm:
            shoulder_rhythm(s, 1.0)
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U + lat(s) * 0.45)
        aim(f"forearm_{s}", U + lat(s) * 0.35)
        twist_palm(s, F)
        grip(s)


def pose_pullup_top():
    for s in "lr":
        aim(f"upperarm_{s}", lat(s) * 0.85 + D * 0.45 + F * 0.15)
        aim(f"forearm_{s}", U + lat(s) * 0.15 + F * 0.05)
        twist_palm(s, F)
        grip(s)


def pose_lunge():
    # left leg forward (hip/knee ~90), right leg back with the knee near the floor
    aim("thigh_l", F + D * 0.15)
    aim("shin_l", D + F * 0.05)
    aim("foot_l", F + D * 0.25)
    aim("thigh_r", D + B * 0.35)
    aim("shin_r", B + D * 0.15)
    aim("foot_r", B * 0.3 + D)
    rot_toward("toe_r", X, 55, B)
    ground()


def pose_row():
    for n, deg in (("pelvis", 38), ("spine_01", 4), ("spine_02", 3), ("spine_03", 3)):
        rot(n, X, deg)
    rot("neck", X, -30)
    for s in "lr":
        aim(f"thigh_{s}", D + F * 0.25)
        aim(f"shin_{s}", D + F * 0.2)
        aim(f"foot_{s}", F + D * 0.3)
        aim(f"upperarm_{s}", D * 0.35 + B * 0.9 + lat(s) * 0.2)
        aim(f"forearm_{s}", D + B * 0.05)
        twist_palm(s, -lat(s))
        grip(s)
    ground()


def pose_grip_closeup():
    for s in "lr":
        aim(f"forearm_{s}", F + D * 0.2)
        grip(s)


POSES = {
    "neutral": pose_neutral, "curl_peak": pose_curl_peak, "press_bottom": pose_press_bottom,
    "press_top": pose_press_top, "press_top_rhythm": lambda: pose_press_top(True),
    "squat_bottom": pose_squat_bottom, "pushup_bottom": pose_pushup_bottom,
    "pullup_hang": pose_pullup_hang, "pullup_hang_rhythm": lambda: pose_pullup_hang(True),
    "pullup_top": pose_pullup_top, "lunge": pose_lunge,
    "row": pose_row, "grip": pose_grip_closeup,
}
# Close-up zones per pose: (bone, head|tail) targets on the left side.
CLOSEUPS = {
    "curl_peak": ["elbow", "hand"], "press_top": ["shoulder"], "press_top_rhythm": ["shoulder"],
    "pullup_hang": ["shoulder"], "pullup_hang_rhythm": ["shoulder"], "pullup_top": ["shoulder", "hand"],
    "squat_bottom": ["hip", "knee"], "pushup_bottom": ["shoulder", "hand"], "lunge": ["hip", "knee"],
    "row": ["shoulder", "hip"], "grip": ["hand"],
}
ZONES = {"shoulder": ("upperarm_l", "head", 0.34), "elbow": ("forearm_l", "head", 0.30),
         "hand": ("hand_l", "tail", 0.22), "hip": ("thigh_l", "head", 0.40), "knee": ("shin_l", "head", 0.34)}

# ---------------------------------------------------------------- metrics
rest_mesh = body.data
rest_V = np.array([v.co[:] for v in rest_mesh.vertices])
edges = np.array([e.vertices[:] for e in rest_mesh.edges])
rest_len = np.linalg.norm(rest_V[edges[:, 0]] - rest_V[edges[:, 1]], axis=1)
polys = [tuple(p.vertices) for p in rest_mesh.polygons]
poly_sets = [set(p) for p in polys]


def volume(V):
    vol = 0.0
    for p in polys:
        a = V[p[0]]
        for i in range(1, len(p) - 1):
            vol += np.dot(a, np.cross(V[p[i]], V[p[i + 1]])) / 6
    return vol


REST_VOL = volume(rest_V)


def measure(name):
    upd()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    mw = ev.matrix_world
    V = np.array([(mw @ v.co)[:] for v in ev.data.vertices])
    L = np.linalg.norm(V[edges[:, 0]] - V[edges[:, 1]], axis=1)
    ratio = L / np.maximum(rest_len, 1e-9)
    comp = ratio < 0.6
    stretch = ratio > 1.6
    ereg = vreg[edges[:, 0]]
    by_region = {}
    for r, rn in enumerate(region_names):
        m = ereg == r
        if m.any():
            by_region[rn] = {"compressed": int((comp & m).sum()), "stretched": int((stretch & m).sum()),
                             "min_ratio": round(float(ratio[m].min()), 3), "max_ratio": round(float(ratio[m].max()), 3)}
    tree = BVHTree.FromPolygons([Vector(p) for p in V], polys)
    pairs = tree.overlap(tree)
    inter = [(a, b) for a, b in pairs if a != b and not (poly_sets[a] & poly_sets[b])]
    inter_regions = {}
    for a, _b in inter:
        rn = region_names[vreg[polys[a][0]]]
        inter_regions[rn] = inter_regions.get(rn, 0) + 1
    rest_min = V[:, 2].min()
    return {
        "pose": name,
        "volume_ratio": round(abs(volume(V)) / abs(REST_VOL), 4),
        "edge_ratio_p01": round(float(np.percentile(ratio, 1)), 3),
        "edge_ratio_p99": round(float(np.percentile(ratio, 99)), 3),
        "compressed_edges_lt_0_6": int(comp.sum()),
        "stretched_edges_gt_1_6": int(stretch.sum()),
        "self_intersecting_face_pairs": len(inter) // 2,
        "self_intersection_by_region": {k: v // 2 for k, v in inter_regions.items()},
        "by_region": by_region,
        "lowest_z": round(float(rest_min), 4),
    }


# ---------------------------------------------------------------- rendering
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.show_shadows = True
scene.display.shading.shadow_intensity = 0.45
scene.display.light_direction = (-0.45, -0.35, 0.82)
if body.data.materials and body.data.materials[0] is not None:
    body.data.materials[0].diffuse_color = (0.78, 0.66, 0.58, 1.0)
floor_mesh = bpy.data.meshes.new("REVIEW_FLOOR")
floor_mesh.from_pydata([(-0.9, -1.2, 0), (0.9, -1.2, 0), (0.9, 0.9, 0), (-0.9, 0.9, 0)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("REVIEW_FLOOR", floor_mesh)
floor_mat = bpy.data.materials.new("REVIEW_FLOOR_MAT")
floor_mat.diffuse_color = (0.30, 0.31, 0.33, 1.0)
floor_mesh.materials.append(floor_mat)
scene.collection.objects.link(floor)
cam_data = bpy.data.cameras.new("REVIEW_CAM")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("REVIEW_CAM", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.resolution_x = scene.render.resolution_y = 900


def render(name):
    upd()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    P = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
    lo, hi = P.min(axis=0), P.max(axis=0)
    centre = Vector(((lo + hi) / 2).tolist())
    size = float(max(hi - lo)) * 1.12
    cam_data.ortho_scale = size
    for view, (az, el) in {"front": (0, 5), "side": (90, 5), "three_quarter": (35, 12)}.items():
        a, e = math.radians(az), math.radians(el)
        direction = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = centre + direction * 8
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
        scene.render.filepath = str(OUT / f"pose_{name}_{view}.png")
        bpy.ops.render.render(write_still=True)
    for zone in CLOSEUPS.get(name, []):
        bone, end, scale = ZONES[zone]
        p = pb(bone)
        target = rig.matrix_world @ (p.head if end == "head" else p.tail)
        cam_data.ortho_scale = scale
        for view, (az, el) in {"a": (40, 15), "b": (140, 15)}.items():
            a, e = math.radians(az), math.radians(el)
            direction = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            cam.location = target + direction * 8
            cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
            scene.render.filepath = str(OUT / f"pose_{name}_close_{zone}_{view}.png")
            bpy.ops.render.render(write_still=True)


results = []
for name, fn in POSES.items():
    if ONLY and name not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    upd()
    fn()
    res = measure(name)
    results.append(res)
    print("POSE", json.dumps({k: res[k] for k in ("pose", "volume_ratio", "compressed_edges_lt_0_6",
                                                   "stretched_edges_gt_1_6", "self_intersecting_face_pairs")}))
    render(name)

(OUT / "pose_test_report.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print("POSE TESTS DONE", len(results))
