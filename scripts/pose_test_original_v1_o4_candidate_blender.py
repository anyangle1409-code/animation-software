"""Exercise-pose deformation test for the O4 CANDIDATE (never saves).

blender --background --factory-startup ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend \
        --python scripts/pose_test_original_v1_o4_candidate_blender.py -- <out_dir> [pose,pose,...]

Poses are review approximations of the key frames of each exercise, built by
aiming v4 bones in world directions (biomechanical joint angles). They do not
replace the runtime exercise solver; they exercise the mesh/weights through the
same joint ranges. For each pose the script measures volume change, edge
stretch/compression (by body region) and self-intersections, and renders
front / side / three-quarter review images.

POSE DEFINITION REVISION P2 (2026-10-02, owner-authorised skeleton-motion validation): the skeleton-only audits
(scripts/audit_original_v1_finger_flexion_blender.py, audit_original_v1_joint_kinematics_blender.py) proved the rig bones are
sound but the pose CONSTRUCTION produced anatomically wrong joint motion. Corrected here, generically (no exercise-name logic):
  1. finger/thumb flexion uses ONE hinge axis per chain (the parallel-hinge model) instead of re-deriving the axis from the
     already-curled segment, which flipped sign past 90 degrees of cumulative curl and bent the distal joint backwards;
  2. a pronation/supination target that is parallel to the forearm axis is refused instead of silently doing nothing (the
     loaded push-up wrist was 88 degrees of radial deviation instead of wrist extension);
  3. toe dorsiflexion moves the toe tip toward the dorsum (it moved it toward the sole in push-up and lunge);
  4. the humerus is axially rotated so the elbow hinges about the transepicondylar axis and elevated arms are externally
     rotated (previously the forearm carried an 85 degree twist and the elbow bent sideways in the humerus frame);
  5. squat shin/ankle: knee travels over the foot with ankle dorsiflexion (the shin tilted the wrong way);
  6. upd() drives the rig-revision-2 axial twist helper bones (no-op on the 63-bone rig).
The previous definition is preserved verbatim as pose_test_original_v1_o4_candidate_blender_P1_historical.py.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(args[0]) if args else Path(bpy.data.filepath).parent / "pose_tests"
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None
OUT.mkdir(parents=True, exist_ok=True)

scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Pose tests run only on candidate files.")
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig and "SHORTS" not in o.name)
shorts = next((o for o in bpy.data.objects if o.type == "MESH" and "SHORTS" in o.name), None)
region_names = json.loads(scene["hgpt_region_names"])
vreg = np.array([d.value for d in body.data.attributes["hgpt_region"].data])

F = Vector((0, -1, 0))   # character forward
B = -F
U = Vector((0, 0, 1))
D = -U


TWIST_HELPERS = [(f"{seg}_{st}_{s}", f"{seg}_{s}", f) for seg in ("upperarm", "forearm") for s in "lr" for st, f in (("tw0", 0.0), ("tw1", 0.5))]


def drive_twist_helpers():
    """Rig revision rev2 (scripts/original_v1_twist_helpers.py): each helper is a child of its segment bone and rotates about the
    bone's own Y axis by -(1 - f) x (the segment's swing-twist twist), so it carries the segment's swing plus fraction f of its
    axial twist. No-op on the 63-bone rig (no helper bones)."""
    pose = rig.pose.bones
    for name, parent, f in TWIST_HELPERS:
        if name not in pose or parent not in pose:
            continue
        q = pose[parent].matrix_basis.to_quaternion()
        twist = (2.0 * math.atan2(q.y, q.w) + math.pi) % (2.0 * math.pi) - math.pi
        pose[name].matrix_basis = Quaternion((0.0, 1.0, 0.0), -(1.0 - f) * twist).to_matrix().to_4x4()


def upd():
    drive_twist_helpers()
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
    """Pronate/supinate the forearm so the palm faces `target` as closely as possible.
    A target parallel to the forearm axis has no component in the rotation plane: refuse (P1 silently produced garbage)."""
    axis = bdir(f"forearm_{s}")
    n = palm_normal(s)
    t = Vector(target)
    if (t - axis * t.dot(axis)).length < 1e-6 or (n - axis * n.dot(axis)).length < 1e-6:
        raise ValueError("twist_palm target is parallel to the forearm axis")
    n_p = (n - axis * n.dot(axis)).normalized()
    t_p = (t - axis * t.dot(axis)).normalized()
    ang = math.degrees(n_p.angle(t_p))
    sign = 1 if n_p.cross(t_p).dot(axis) > 0 else -1
    rot(f"forearm_{s}", axis, sign * ang)


def grip(s, amount=1.0, thumb=True):
    """Close the fingers toward the palm (cylindrical handle grip). MCP/PIP/DIP are parallel hinges: ONE axis per finger,
    taken from the uncurled proximal bone, is used for all three joints (P1 re-derived it per joint and reversed the DIP)."""
    n = palm_normal(s)
    for f in ("index", "middle", "ring", "pinky"):
        axis = bdir(f"{f}_01_{s}").cross(n).normalized()
        for k, deg in ((1, 70), (2, 88), (3, 55)):
            rot(f"{f}_0{k}_{s}", axis, deg * amount)
    if thumb:
        for k, deg in ((1, 28), (2, 30), (3, 38)):
            name = f"thumb_0{k}_{s}"
            axis = bdir(name).cross(n + bdir(f"index_01_{s}") * 0.6)
            rot(name, axis, deg * amount)


def lat(s):
    return Vector((1.0 if s == "r" else -1.0, 0, 0))


REST3 = {b.name: b.matrix_local.to_3x3() for b in rig.data.bones}


def swing_of(name):
    """Rotation of a posed bone relative to its own rest orientation, in world axes."""
    upd()
    return pb(name).matrix.to_3x3() @ REST3[name].inverted()


def hinge_humerus(s, forearm_target):
    """Axially rotate the humerus so the elbow hinges about the transepicondylar axis.

    The elbow is a hinge: its flexion axis is the humerus' own lateral axis (rest X carried by the humerus swing). For a
    wanted forearm direction the rotation that takes the humerus direction to the forearm direction is about humerus x
    forearm. Flexion is rotation about the humerus' lateral axis by a NEGATIVE angle (the forearm tip moves anteriorly), so
    the lateral axis must point along -(humerus x forearm); a unique humeral axial rotation achieves that (the opposite
    solution would be hyperextension). Without this, elevated arms bend the elbow sideways in the humerus frame and the
    forearm has to carry the missing rotation as an 85 degree twist."""
    name = f"upperarm_{s}"
    h = bdir(name)
    t = Vector(forearm_target).normalized()
    hinge = h.cross(t)
    if hinge.length < 0.26:                       # forearm within ~15 deg of the humerus axis: hinge is ill-defined
        return external_rotation_for_elevation(s)
    want = -hinge.normalized()
    lat_now = swing_of(name) @ Vector((1, 0, 0))
    a = lat_now - h * lat_now.dot(h)
    a.normalize()
    ang = math.degrees(math.atan2(h.dot(a.cross(want)), a.dot(want)))
    rot(name, h, ang)


def external_rotation_for_elevation(s):
    """Straight elevated arm: couple external humeral rotation to elevation (about half of the elevation above 30 deg,
    at most 80 deg), the physiological requirement for clearing the acromion in the frontal plane."""
    name = f"upperarm_{s}"
    h = bdir(name)
    elev = math.degrees(h.angle(D))
    er = min(80.0, 0.5 * max(0.0, elev - 30.0))
    if er < 1.0:
        return
    # external rotation turns the palm side of an arm at the side toward the character's front; find that sign numerically
    Fp = swing_of(name) @ F
    p0 = swing_of(name) @ (-lat(s))               # rest palm side (medial), carried by the humerus swing
    sign = 1.0 if h.cross(p0).dot(Fp) > 0 else -1.0
    rot(name, h, sign * er)


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
        hinge_humerus(s, U + F * 0.1)
        aim(f"forearm_{s}", U + F * 0.1)
        twist_palm(s, F)
        grip(s)


def pose_press_top(rhythm=False):
    for s in "lr":
        if rhythm:
            shoulder_rhythm(s, 1.0)
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U * 1.0 + lat(s) * 0.25)
        hinge_humerus(s, U + lat(s) * -0.05)
        aim(f"forearm_{s}", U + lat(s) * -0.05)
        twist_palm(s, F)
        grip(s)


def pose_squat_bottom():
    for n, deg in (("pelvis", 18), ("spine_01", 6), ("spine_02", 5), ("spine_03", 4)):
        rot(n, X, deg)
    rot("neck", X, -18)
    for s in "lr":
        aim(f"thigh_{s}", F * 1.0 + D * 0.25 + lat(s) * 0.25)
        aim(f"shin_{s}", D * 1.0 + B * 0.45 + lat(s) * 0.12)   # knee over the foot (P1 put the ankle ahead of the knee)
        aim(f"foot_{s}", F + D * 0.3 + lat(s) * 0.15)
        aim(f"upperarm_{s}", F + U * 0.05)
        aim(f"forearm_{s}", F + U * 0.05)
    ground()


def pose_pushup_bottom():
    # whole body tipped face-down (plank) through the root bone; joints aimed in world directions
    rot("root", X, 78)
    for s in "lr":
        aim(f"upperarm_{s}", B * 0.8 + lat(s) * 0.55 + U * 0.15)
        hinge_humerus(s, D + F * 0.18)
        aim(f"forearm_{s}", D + F * 0.18)          # forearm leans so the loaded wrist is extended ~80 deg, not 90
        twist_palm(s, B)                           # pronate: palm faces back; wrist extension then turns it to the floor
        aim(f"hand_{s}", F + lat(s) * 0.12)
        aim(f"foot_{s}", D + F * 0.3)              # ball of the foot under the ankle, heel raised
        rot_toward(f"toe_{s}", X, 70, F)           # toe dorsiflexion: tip toward the dorsum (head direction in the plank)
    ground()


def pose_pullup_hang(rhythm=False):
    for s in "lr":
        if rhythm:
            shoulder_rhythm(s, 1.0)
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U + lat(s) * 0.45)
        hinge_humerus(s, U + lat(s) * 0.35)
        aim(f"forearm_{s}", U + lat(s) * 0.35)
        twist_palm(s, F)
        grip(s)


def pose_pullup_top():
    for s in "lr":
        aim(f"upperarm_{s}", lat(s) * 0.85 + D * 0.45 + F * 0.15)
        hinge_humerus(s, U + lat(s) * 0.15 + F * 0.05)
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
    aim("foot_r", D + F * 0.3)
    rot_toward("toe_r", X, 55, F)                  # dorsiflexion (P1 curled the toe under: tip toward the sole)
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


# ------------------------------------------------ handle grip (contact solve)
HANDLE_RADIUS = 0.017   # 34 mm dumbbell handle
HANDLE = {}


def bone_vertex_sets():
    """Vertices driven mainly (>0.3) by each bone or its descendants."""
    groups = {vg.index: vg.name for vg in body.vertex_groups}
    owners = {}
    for v in body.data.vertices:
        for g in v.groups:
            if g.weight > 0.3:
                owners.setdefault(groups[g.group], []).append(v.index)
    return owners


OWNERS = None


def evaluated_positions(ids):
    upd()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    mw = ev.matrix_world
    return np.array([(mw @ ev.data.vertices[i].co)[:] for i in ids])


def handle_distance(P, s):
    c, a = HANDLE[s]
    d = P - c
    radial = d - np.outer(d @ a, a)
    return np.linalg.norm(radial, axis=1) - HANDLE_RADIUS  # <0 = inside the handle


def place_handle(s):
    """Handle across the palm at the MCP crease, axis along the knuckle line."""
    k = (pb(f"pinky_01_{s}").head - pb(f"index_01_{s}").head).normalized()
    mid = (pb(f"index_01_{s}").head + pb(f"pinky_01_{s}").head) / 2
    n = palm_normal(s)
    c = mid + n * (HANDLE_RADIUS + 0.020) + bdir(f"hand_{s}") * 0.006
    HANDLE[s] = (np.array(c[:]), np.array(k[:]))


def close_on_handle(s):
    global OWNERS
    OWNERS = OWNERS or bone_vertex_sets()
    chains = [[f"{f}_0{k}_{s}" for k in (1, 2, 3)] for f in ("index", "middle", "ring", "pinky")]
    chains.append([f"thumb_0{k}_{s}" for k in (2, 3)])
    limits = {1: 100, 2: 110, 3: 85}
    for chain in chains:
        # one parallel-hinge axis per chain, from the uncurled proximal bone (P1 re-derived it per joint: reversed the DIP)
        toward0 = palm_normal(s) if not chain[0].startswith("thumb") else (Vector(HANDLE[s][0]) - pb(chain[0]).head).normalized()
        axis0 = bdir(chain[0]).cross(toward0).normalized()
        for bone in chain:
            k = int(bone.split("_")[1][1])
            desc = [b for b in chain[chain.index(bone):]]
            ids = sorted({i for b in desc for i in OWNERS.get(b, [])})
            if not ids:
                continue
            lo, hi = 0.0, float(limits[k])
            base = pb(bone).matrix.copy()
            axis = axis0
            free = [i for i, d in zip(ids, handle_distance(evaluated_positions(ids), s)) if d > 0]
            if not free:
                continue
            for _ in range(9):
                mid = 0.5 * (lo + hi)
                pb(bone).matrix = base
                rot(bone, axis, mid)
                if handle_distance(evaluated_positions(free), s).min() < -0.0015:
                    hi = mid
                else:
                    lo = mid
            pb(bone).matrix = base
            rot(bone, axis, lo)


def pose_curl_handle():
    for s in "lr":
        aim(f"upperarm_{s}", D + F * 0.18)
        aim(f"forearm_{s}", U * 0.95 + F * 0.55 + lat(s) * -0.05)
        twist_palm(s, B + U * 0.2)
        place_handle(s)
        close_on_handle(s)


def pose_pullup_bar():
    for s in "lr":
        aim(f"upperarm_{s}", lat(s))
        aim(f"upperarm_{s}", U + lat(s) * 0.45)
        hinge_humerus(s, U + lat(s) * 0.35)
        aim(f"forearm_{s}", U + lat(s) * 0.35)
        twist_palm(s, F)
        place_handle(s)
        close_on_handle(s)


def grip_metrics(s):
    ids = sorted({i for f in ("index", "middle", "ring", "pinky", "thumb") for k in (1, 2, 3)
                  for i in OWNERS.get(f"{f}_0{k}_{s}", [])})
    d = handle_distance(evaluated_positions(ids), s)
    return {"max_penetration_mm": round(float(max(0.0, -d.min())) * 1000, 2),
            "contact_vertices_within_2mm": int((np.abs(d) < 0.002).sum()),
            "finger_vertices": len(ids)}


POSES = {
    "neutral": pose_neutral, "curl_peak": pose_curl_peak, "press_bottom": pose_press_bottom,
    "press_top": pose_press_top, "press_top_rhythm": lambda: pose_press_top(True),
    "squat_bottom": pose_squat_bottom, "pushup_bottom": pose_pushup_bottom,
    "pullup_hang": pose_pullup_hang, "pullup_hang_rhythm": lambda: pose_pullup_hang(True),
    "pullup_top": pose_pullup_top, "lunge": pose_lunge,
    "row": pose_row, "grip": pose_grip_closeup,
    "curl_handle": pose_curl_handle, "pullup_bar": pose_pullup_bar,
}
# Close-up zones per pose: (bone, head|tail) targets on the left side.
CLOSEUPS = {
    "curl_peak": ["elbow", "hand"], "press_top": ["shoulder"], "press_top_rhythm": ["shoulder"],
    "pullup_hang": ["shoulder"], "pullup_hang_rhythm": ["shoulder"], "pullup_top": ["shoulder", "hand"],
    "squat_bottom": ["hip", "knee"], "pushup_bottom": ["shoulder", "hand"], "lunge": ["hip", "knee"],
    "row": ["shoulder", "hip"], "grip": ["hand"], "curl_handle": ["hand", "elbow"], "pullup_bar": ["hand"],
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
_names = [region_names[r] for r in vreg]
# Visible margin bands next to the waistband and hems (the rest is masked when dressed).
UNDER_SHORTS = np.array([(n in ("torso", "pelvis") and 0.975 < z < 1.0) or (n == "leg" and 0.628 < z < 0.652)
                         for n, z in zip(_names, rest_V[:, 2])])
DRESS_MASK = body.modifiers.get("HGPT_DRESSED_MASK")


def set_dressed(on):
    if DRESS_MASK is not None:
        DRESS_MASK.show_viewport = on
        DRESS_MASK.show_render = on
    if shorts is not None:
        shorts.hide_render = not on
        shorts.hide_viewport = not on
    upd()


set_dressed(False)


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
# Blender resolves a RELATIVE render filepath against the drive root, but Python resolves OUT against
# the working directory. With a relative output folder every render landed outside the repository and
# the capture hash read-back below failed on Windows. Make OUT absolute for everything from here on.
# (Placed after the frozen pose/metrics definition on purpose; that region is hash-pinned.)
OUT = OUT.resolve()
# Optional milestone capture changes cameras/presentation only, never poses/metrics.
MILESTONE = len(args) > 2 and args[2] == "--milestone"
METRICS_ONLY = len(args) > 2 and args[2] == "--metrics-only"
if MILESTONE:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from original_v1_milestone_review import load_plan, views
    MILESTONE_PLAN = load_plan()
    MILESTONE_VIEWS = views(MILESTONE_PLAN)
    MILESTONE_PLAN_SHA256 = hashlib.sha256((Path(__file__).resolve().parent.parent / "ORIGINAL_V1_VISUAL_BOARD_PLAN.json").read_bytes()).hexdigest()
CURRENT_MILESTONE_VIEW = None

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
if MILESTONE:
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"


CAPTURE_RECORDS = []
SOURCE_CANDIDATE_SHA256 = hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
RENDER_SCRIPT_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def capture_render():
    bpy.ops.render.render(write_still=True)
    path = Path(scene.render.filepath)
    CAPTURE_RECORDS.append({
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "capture": {
            "protocol": MILESTONE_PLAN["protocol"] if MILESTONE else "original_v1_stress_render_v1",
            "render_script_sha256": RENDER_SCRIPT_SHA256,
            "camera_matrix_world": [list(row) for row in cam.matrix_world],
            "orthographic_scale": cam_data.ortho_scale,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage],
            "engine": scene.render.engine,
            "light_direction": list(scene.display.light_direction),
            "shading_light": scene.display.shading.light,
            "shading_color_type": scene.display.shading.color_type,
            "shadows": scene.display.shading.show_shadows,
            "shadow_intensity": scene.display.shading.shadow_intensity,
            "cavity": scene.display.shading.show_cavity,
            "dressed": not MILESTONE,
            **({"milestone_plan_sha256": MILESTONE_PLAN_SHA256,
                "view_id": CURRENT_MILESTONE_VIEW["file"],
                "pose": CURRENT_MILESTONE_VIEW["pose"]} if MILESTONE else {}),
        },
    })


def render_milestone(name):
    global CURRENT_MILESTONE_VIEW
    set_dressed(False)
    upd()
    for row in MILESTONE_VIEWS:
        if row["pose"] != name:
            continue
        if "centre" in row:
            target = Vector(row["centre"])
        else:
            points = [rig.matrix_world @ (pb(bone).head if end == "head" else pb(bone).tail)
                      for bone, end in row["anchors"]]
            target = sum(points, Vector((0, 0, 0))) / len(points)
        angles = row["angles"]
        if isinstance(angles, str):
            normal = palm_normal("l") * (-1 if angles.startswith("dorsal") else 1)
            if angles.endswith("oblique"):
                normal += bdir("hand_l").normalized() * 0.35
            direction = (rig.matrix_world.to_3x3() @ normal).normalized()
        else:
            az, el = (angles, 15) if isinstance(angles, (int, float)) else angles
            a, e = math.radians(az), math.radians(el)
            direction = Vector((-math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam_data.ortho_scale = row["scale"]
        cam.location = target + direction * 8
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-direction).to_track_quat("-Z", "Y")
        upd()
        if row["set"] != "anatomy":
            evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            inverse = cam.matrix_world.inverted()
            points = [inverse @ (evaluated.matrix_world @ v.co) for v in evaluated.data.vertices]
            half = cam_data.ortho_scale / 2
            if any(abs(p.x) > half or abs(p.y) > half for p in points):
                raise RuntimeError("Milestone fixed frame crops body: " + row["file"] + "; preserve output and inspect; do not auto-fit")
        CURRENT_MILESTONE_VIEW = row
        scene.render.filepath = str(OUT / row["file"])
        capture_render()


def render(name):
    if METRICS_ONLY:
        return
    if MILESTONE:
        render_milestone(name)
        return
    set_dressed(True)
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
        capture_render()
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
            capture_render()
    set_dressed(False)


results = []
for name, fn in POSES.items():
    if ONLY and name not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    upd()
    HANDLE.clear()
    for o in [o for o in bpy.data.objects if o.name.startswith("REVIEW_HANDLE")]:
        bpy.data.objects.remove(o)
    fn()
    res = measure(name)
    for s, (c, a) in HANDLE.items():
        res[f"grip_{s}"] = grip_metrics(s)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=HANDLE_RADIUS, depth=0.13,
                                            location=Vector(c.tolist()))
        h = bpy.context.active_object
        h.name = f"REVIEW_HANDLE_{s}"
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector(a.tolist()))
        hm = bpy.data.materials.new("REVIEW_HANDLE_MAT")
        hm.diffuse_color = (0.12, 0.12, 0.13, 1.0)
        h.data.materials.append(hm)
    results.append(res)
    print("POSE", json.dumps({k: res[k] for k in ("pose", "volume_ratio", "compressed_edges_lt_0_6",
                                                   "stretched_edges_gt_1_6", "self_intersecting_face_pairs")}))
    render(name)

(OUT / "pose_test_report.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print("POSE TESTS DONE", len(results))

(OUT / "render_source_manifest.json").write_text(json.dumps({
    "schema_version": 1,
    "candidate": Path(bpy.data.filepath).name,
    "candidate_sha256": SOURCE_CANDIDATE_SHA256,
    "render_script_sha256": RENDER_SCRIPT_SHA256,
    "pose_report_sha256": hashlib.sha256((OUT / "pose_test_report.json").read_bytes()).hexdigest(),
    "blender_version": bpy.app.version_string,
    "capture_mode": "numeric_replay" if METRICS_ONLY else "milestone" if MILESTONE else "repair",
    "capture_arguments": args,
    "images": CAPTURE_RECORDS,
    "owner_review": "pending",
    "blocking": False,
    "production_approved": False,
}, indent=2) + "\n", encoding="utf-8")
