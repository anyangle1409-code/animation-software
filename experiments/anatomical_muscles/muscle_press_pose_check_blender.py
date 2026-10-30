"""Read-only check: how the bound muscle ENVELOPE PROXIES (MG1 arm, MG4 deltoid, MG5 armpit-fold fans) follow the
press when R41's anatomical chain is posed natively.

The chain (clavicle -> scapula -> humerus -> ulna / radius) is posed by rigid rotations about R41's own landmark joint
centres with the coupled girdle of path_length_direction_check_blender.py (upward rotation 0.33 e, posterior tilt
0.12 e, clavicle elevation 0.08 e, retraction 0.12 e; humerus in a plane 30 deg anterior of the frontal plane; signs fixed
by landmark probes) - re-implemented here, as that script runs on import.  Press path: humerothoracic elevation and
elbow flexion at rest -> rack (90 deg, elbow 90) -> lockout (160, elbow 0).  The skin is not posed (R41's anatomical
master is a guide skeleton; the body follows its own rig), so this measures the envelopes against each other only.

Per pose and muscle: belly volume / rest, edge length ratio p1 / p99, self-intersecting face pairs; and face overlaps
between muscles.  Renders (anterior / lateral / posterior) at each pose.  Nothing is saved to the blend.

usage: python3.13 muscle_press_pose_check_blender.py -- MG5.blend MG5_SHA256 OUT_DIR [left|right]
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:]
src, expected, outdir = Path(args[0]), args[1], Path(args[2])
S = args[3] if len(args) > 3 else "left"
SUF = "L" if S == "left" else "R"
outdir.mkdir(parents=True, exist_ok=True)
if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
    raise ValueError("input blend hash mismatch")
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()), load_ui=False, use_scripts=False)
anat = bpy.data.objects["HGPT_ANATOMICAL_MASTER"]; body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
MW = anat.matrix_world.copy()
PLANE_DEG = 30.0
MODEL = {"upward_rotation": 0.33, "posterior_tilt": 0.12, "clavicle_elevation": 0.08, "clavicle_retraction": 0.12}


def LM(n):
    return bpy.data.objects[f"LM_{n}"].matrix_world.translation.copy()


SC, AC, GH, EJC = LM(f"clavicle_{S}__SC"), LM(f"clavicle_{S}__AC"), LM(f"scapula_{S}__GH"), LM(f"humerus_{S}__EJC")
AA, TS, AI = LM(f"scapula_{S}__AA"), LM(f"scapula_{S}__TS"), LM(f"scapula_{S}__AI")
EL, EM = LM(f"humerus_{S}__epicondyle_lateral_skin"), LM(f"humerus_{S}__epicondyle_medial_skin")
WJC = LM(f"radius_{S}__WJC")
lat = 1.0 if GH.x > 0 else -1.0
LAT, ANT, UP = Vector((lat, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
SCAP_N = (AA - TS).cross(AI - TS).normalized(); SPINE = (AA - TS).normalized(); ELB_AX = (EL - EM).normalized()


def rot_about(p, axis, deg):
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-p)


def signed(axis, probe, want, pivot):
    return 1.0 if ((rot_about(pivot, axis, 5.0) @ probe) - probe).dot(want) > 0 else -1.0


SIGN = {"clavicle_elevation": signed(ANT, AC, UP, SC), "clavicle_retraction": signed(UP, AC, -ANT, SC),
        "upward_rotation": signed(SCAP_N, AI, LAT, AC), "posterior_tilt": signed(SPINE, AI, ANT, AC),
        "elbow_flexion": signed(ELB_AX, WJC, ANT, EJC)}
CHAIN = [f"anat_clavicle_{S}", f"anat_scapula_{S}", f"anat_humerus_{S}", f"anat_ulna_{S}", f"anat_radius_{S}"]
REST_HT = math.degrees(math.acos((EJC - GH).normalized().dot(-UP)))
REST_ELB = 180.0 - math.degrees(math.acos(max(-1.0, min(1.0, (GH - EJC).normalized().dot((WJC - EJC).normalized())))))


def pose_T(ht_deg, elbow_deg):
    e = max(0.0, ht_deg - REST_HT); g = {k: v * e for k, v in MODEL.items()}
    elev, retr = g["clavicle_elevation"], g["clavicle_retraction"]
    Tc = rot_about(SC, UP, SIGN["clavicle_retraction"] * retr) @ rot_about(SC, ANT, SIGN["clavicle_elevation"] * elev)
    ac = Tc @ AC; R = Tc.to_3x3()
    ts = rot_about(ac, R @ SCAP_N, SIGN["upward_rotation"] * (g["upward_rotation"] - elev)) @ Tc
    ts = rot_about(ac, ts.to_3x3() @ SPINE, SIGN["posterior_tilt"] * g["posterior_tilt"]) @ ts
    ts = rot_about(ac, UP, -SIGN["clavicle_retraction"] * retr) @ ts
    gh, ejc = ts @ GH, ts @ EJC
    plane = (math.cos(math.radians(PLANE_DEG)) * LAT + math.sin(math.radians(PLANE_DEG)) * ANT).normalized()
    want = (math.cos(math.radians(ht_deg)) * -UP + math.sin(math.radians(ht_deg)) * plane).normalized()
    q = (ejc - gh).normalized().rotation_difference(want)
    Th = Matrix.Translation(gh) @ q.to_matrix().to_4x4() @ Matrix.Translation(-gh) @ ts
    Tf = Th @ rot_about(EJC, ELB_AX, SIGN["elbow_flexion"] * (elbow_deg - REST_ELB))
    return {CHAIN[0]: Tc, CHAIN[1]: ts, CHAIN[2]: Th, CHAIN[3]: Tf, CHAIN[4]: Tf}


def apply(T):
    for b in CHAIN:
        anat.pose.bones[b].matrix = MW.inverted() @ T[b] @ MW @ anat.data.bones[b].matrix_local
        bpy.context.view_layer.update()


MUS = [o for o in bpy.data.collections["HGPT_EXPERIMENT_MUSCLES"].objects if o.name.endswith(f".{SUF}")]
TEN = [o for o in bpy.data.collections["HGPT_EXPERIMENT_TENDONS"].objects if o.name.split(".")[3] == SUF]


def evaluated(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    P = np.array([e.matrix_world @ v.co for v in m.vertices], dtype=np.float64); F = [tuple(p.vertices) for p in m.polygons]
    e.to_mesh_clear(); return P, F


def volume(P, F):
    v = 0.0
    for f in F:
        for k in range(1, len(f) - 1):
            v += np.dot(P[f[0]], np.cross(P[f[k]], P[f[k + 1]])) / 6.0
    return abs(float(v))


EDGES = {o.name: np.array([e.vertices[:] for e in o.data.edges]) for o in MUS}
REST = {}
for o in MUS:
    P, F = evaluated(o); REST[o.name] = (P, volume(P, F))
POSES = [("rest", REST_HT, REST_ELB), ("ht60", 60.0, 45.0), ("rack90", 90.0, 90.0), ("ht120", 120.0, 45.0),
         ("lockout160", 160.0, 0.0)]
rep = {"status": "READ_ONLY_CHECK", "input": src.name, "input_sha256": expected, "side": S,
       "girdle": {"model": MODEL, "plane_deg": PLANE_DEG, "rest_ht_deg": round(REST_HT, 1), "rest_elbow_deg": round(REST_ELB, 1)},
       "poses": {}}
sc = bpy.context.scene
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.75
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = 480; sc.render.resolution_y = 560
for ob in sc.objects:
    if ob.type == "MESH" and ob not in MUS and ob not in TEN:
        ob.hide_render = True
for tag, ht, elb in POSES:
    apply(pose_T(ht, elb))
    per, trees = {}, {}
    for o in MUS:
        P, F = evaluated(o); P0, V0 = REST[o.name]; E = EDGES[o.name]
        L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
        r = L / np.maximum(L0, 1e-9)
        tr = BVHTree.FromPolygons([Vector(p) for p in P], F); trees[o.name] = tr
        selfx = sum(1 for a, b in tr.overlap(tr) if a < b and not (set(F[a]) & set(F[b])))
        per[o.name.split(".")[2]] = {"volume_ratio": round(volume(P, F) / max(V0, 1e-12), 3),
                                     "edge_ratio_p1_p99": [round(float(np.percentile(r, 1)), 3), round(float(np.percentile(r, 99)), 3)],
                                     "edge_ratio_min_max": [round(float(r.min()), 3), round(float(r.max()), 3)],
                                     "self_intersecting_face_pairs": selfx}
    pairs = {}
    names = list(trees)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ov = trees[a].overlap(trees[b])
            if ov:
                pairs[f"{a.split('.')[2]} | {b.split('.')[2]}"] = len(ov)
    rep["poses"][tag] = {"humerothoracic_deg": round(ht, 1), "elbow_deg": round(elb, 1), "muscles": per,
                         "overlap_pairs": pairs, "overlap_total": sum(pairs.values())}
    print("POSE", tag, json.dumps({"overlap_total": rep["poses"][tag]["overlap_total"],
                                   "worst_volume": min((v["volume_ratio"], k) for k, v in per.items()),
                                   "worst_stretch": max((v["edge_ratio_min_max"][1], k) for k, v in per.items()),
                                   "self": sum(v["self_intersecting_face_pairs"] for v in per.values())}), flush=True)
    gh = anat.matrix_world @ anat.pose.bones[f"anat_humerus_{S}"].head
    centre = Vector((gh.x * 0.55, 0.0, gh.z - 0.05))
    for view, dv in {"anterior": (0, -1, 0), "lateral": (lat, 0, 0), "posterior": (0, 1, 0)}.items():
        d = Vector(dv); cam.location = centre + d * 2.5; cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
        sc.render.filepath = str(outdir / f"mg6a_{S}_{tag}_{view}.png"); bpy.ops.render.render(write_still=True)
apply(pose_T(REST_HT, REST_ELB))
rep["input_unchanged"] = hashlib.sha256(src.read_bytes()).hexdigest() == expected
(outdir / f"mg6a_{S}_press_pose_report.json").write_text(json.dumps(rep, indent=1))
print("DONE", flush=True)
