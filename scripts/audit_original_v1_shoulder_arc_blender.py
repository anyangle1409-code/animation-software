"""Read-only continuous shoulder-arc audit (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_shoulder_arc_blender.py -- <out.json> <pose[,pose...]> [n_samples=17]

Each pose is built by the pose script, then replayed continuously from rest (fraction 0) to the final pose (fraction 1) with the same
swing/twist interpolation as audit_original_v1_joint_kinematics_blender.py. At every sample it records, per side:
  * humerothoracic elevation  theta = angle between the humerus direction and the downward trunk axis (-spine_03 direction), in the
    armature frame (so it includes clavicle + scapula + glenohumeral contributions and is independent of world orientation);
  * scapular upward rotation proxy (angle of the scapula bone about the anterior axis relative to rest);
and for the mesh: torso/shoulder drift = largest distance of any vertex from where the TRUNK bones alone would put it (the 'tent flap'
measure), the largest and smallest edge ratio in the torso and shoulder regions, the 99th-percentile edge ratio and the volume ratio.
Used to derive the activation curve of the shoulder corrective from data and to validate the corrective through the whole arc.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 2:
    raise SystemExit("Usage: ... -- <out.json> <pose[,pose]> [n_samples]")
OUT = Path(args[0]).resolve()
POSE_LIST = args[1].split(",")
NS = int(args[2]) if len(args) > 2 else 17

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "pose_test_defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd, pb = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"], ns["pb"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
names = json.loads(bpy.context.scene["hgpt_region_names"])
region = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
rest = np.array([v.co[:] for v in body.data.vertices])
edges = np.array([e.vertices[:] for e in body.data.edges])
L0 = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
polys = [tuple(p.vertices) for p in body.data.polygons]
bone_names = [b.name for b in rig.data.bones]
gname = {vg.index: vg.name for vg in body.vertex_groups}
W = np.zeros((len(rest), len(bone_names)))
bidx = {n: i for i, n in enumerate(bone_names)}
for v in body.data.vertices:
    for g in v.groups:
        n = gname[g.group]
        if n in bidx:
            W[v.index, bidx[n]] = g.weight
TRUNK = [bidx[n] for n in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "neck", "head") if n in bidx]
Wt = np.zeros_like(W)
Wt[:, TRUNK] = W[:, TRUNK]
Wt = Wt / np.maximum(Wt.sum(axis=1, keepdims=True), 1e-9)
rw, bw = np.array(rig.matrix_world), np.array(body.matrix_world)
rest_h = np.c_[rest, np.ones(len(rest))]
REST_INV = {n: np.linalg.inv(np.array(rig.data.bones[n].matrix_local)) for n in bone_names}
tor, sho = region == names.index("torso"), region == names.index("shoulder")
etor = tor[edges[:, 0]] & tor[edges[:, 1]]
esho = sho[edges[:, 0]] & sho[edges[:, 1]]


def volume(P):
    v = 0.0
    for p in polys:
        a = P[p[0]]
        for i in range(1, len(p) - 1):
            v += float(np.dot(a, np.cross(P[p[i]], P[p[i + 1]]))) / 6.0
    return v


VOL0 = volume(rest)


def skin_mats():
    upd()
    return np.stack([rw @ np.array(pb(n).matrix) @ REST_INV[n] @ np.linalg.inv(rw) @ bw for n in bone_names])


def evaluate():
    M = skin_mats()
    T = np.einsum("bij,vj->vbi", M[:, :3, :], rest_h)
    Tt = T
    sk = body.data.shape_keys
    if sk is not None:                       # corrective shape keys act on the rest position before skinning
        eff = rest.copy()
        for kb in sk.key_blocks:
            if kb.name != "Basis" and kb.value != 0.0:
                eff += kb.value * (np.array([d.co[:] for d in kb.data]) - rest)
        T = np.einsum("bij,vj->vbi", M[:, :3, :], np.c_[eff, np.ones(len(eff))])
    # P = what the candidate actually shows; Pt = where the trunk bones alone would put the UNcorrected rest mesh
    return np.einsum("vb,vbi->vi", W, T), np.einsum("vb,vbi->vi", Wt, Tt)


def swing_twist(q):
    v = Vector((q.x, q.y, q.z))
    proj = Vector((0, 1, 0)) * v.dot(Vector((0, 1, 0)))
    tw = Quaternion((q.w, proj.x, proj.y, proj.z))
    if tw.magnitude < 1e-12:
        tw = Quaternion((1, 0, 0, 0))
    tw.normalize()
    return q @ tw.inverted(), tw


def apply_fraction(final, f):
    for p in rig.pose.bones:
        q, t = final[p.name]
        sw, tw = swing_twist(q)
        ang = (2.0 * math.atan2(tw.y, tw.w) + math.pi) % (2.0 * math.pi) - math.pi
        qf = Quaternion((1, 0, 0, 0)).slerp(sw, f) @ Quaternion((0.0, 1.0, 0.0), f * ang)
        p.matrix_basis = Matrix.Translation(t * f) @ qf.to_matrix().to_4x4()
    upd()


def elevation(side):
    h = (pb(f"upperarm_{side}").tail - pb(f"upperarm_{side}").head).normalized()
    down = -(pb("spine_03").tail - pb("spine_03").head).normalized()
    return math.degrees(h.angle(down))


def scap_rot(side):
    rest_dir = (rig.data.bones[f"scapula_{side}"].tail_local - rig.data.bones[f"scapula_{side}"].head_local).normalized()
    cur = (pb(f"scapula_{side}").tail - pb(f"scapula_{side}").head).normalized()
    clav_rest = (rig.data.bones[f"clavicle_{side}"].tail_local - rig.data.bones[f"clavicle_{side}"].head_local).normalized()
    clav = (pb(f"clavicle_{side}").tail - pb(f"clavicle_{side}").head).normalized()
    q = (Quaternion(clav_rest.rotation_difference(clav)).inverted() @ Quaternion(rest_dir.rotation_difference(cur)))
    return math.degrees(q.angle)


result = {"schema_version": 1, "source_candidate": Path(bpy.data.filepath).name,
          "source_candidate_sha256": hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(), "samples": NS, "poses": {}}
for name in POSE_LIST:
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[name]()
    upd()
    final = {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}
    rows = []
    for k in range(NS):
        f = k / (NS - 1)
        apply_fraction(final, f)
        P, Pt = evaluate()
        drift = np.linalg.norm(P - Pt, axis=1)
        r = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1) / L0
        rows.append({"fraction": round(f, 4), "elevation_l_deg": round(elevation("l"), 3), "elevation_r_deg": round(elevation("r"), 3),
                     "scapula_rot_l_deg": round(scap_rot("l"), 3), "scapula_rot_r_deg": round(scap_rot("r"), 3),
                     "torso_drift_max_m": round(float(drift[tor].max()), 4), "torso_drift_n_over_5cm": int((drift[tor] > 0.05).sum()),
                     "torso_drift_n_over_10cm": int((drift[tor] > 0.10).sum()),
                     "torso_edge_max": round(float(r[etor].max()), 3), "torso_edge_min": round(float(r[etor].min()), 3),
                     "shoulder_edge_max": round(float(r[esho].max()), 3), "shoulder_edge_min": round(float(r[esho].min()), 3),
                     "edge_p99": round(float(np.percentile(r, 99)), 3), "volume_ratio": round(abs(volume(P)) / abs(VOL0), 4)})
    result["poses"][name] = rows
    print("SHOULDER ARC", name, "max drift %.3f" % max(x["torso_drift_max_m"] for x in rows))
reset()
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print("SHOULDER ARC AUDIT", OUT)
