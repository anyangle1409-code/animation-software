"""Dump the candidate's rest mesh, deform weights and per-pose skinning matrices (never saves).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 \
        --python scripts/dump_original_v1_o4_pose_skinning_blender.py -- <out.npz> [pose,pose,...]

Reuses the pose definitions of scripts/pose_test_original_v1_o4_candidate_blender.py
(executed up to its metrics section) so the stress poses are identical. The dump
is input for scripts/optimize_original_v1_o4_shoulder_weights.py. It reads only
this candidate's own mesh/weights and the v4 rig. It also checks that linear
blend skinning in numpy reproduces Blender's evaluated mesh.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out_path = Path(args[0])
only = set(args[1].split(",")) if len(args) > 1 and args[1] else None

src = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py").read_text(encoding="utf-8")
src = src[:src.index("# ---------------------------------------------------------------- metrics")]
tmp = tempfile.mkdtemp()
saved_argv = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": "pose_test_original_v1_o4_candidate_blender.py"}
exec(compile(src, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv

rig, body, POSES = ns["rig"], ns["body"], ns["POSES"]
arm_mod = next(m for m in body.modifiers if m.type == "ARMATURE")
if arm_mod.use_deform_preserve_volume:
    raise SystemExit("Dual-quaternion skinning is on; the linear model would be wrong.")
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask:
    mask.show_viewport = False

deform = [b.name for b in rig.data.bones if b.use_deform]
bidx = {n: i for i, n in enumerate(deform)}
nv = len(body.data.vertices)
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((nv, len(deform)))
for v in body.data.vertices:
    for g in v.groups:
        n = gname[g.group]
        if n in bidx:
            W[v.index, bidx[n]] = g.weight
W /= np.maximum(W.sum(axis=1, keepdims=True), 1e-12)
rest = np.array([v.co[:] for v in body.data.vertices])
rest_h = np.c_[rest, np.ones(nv)]
edges = np.array([e.vertices[:] for e in body.data.edges])
tris = []
for p in body.data.polygons:
    vs = list(p.vertices)
    for i in range(1, len(vs) - 1):
        tris.append((vs[0], vs[i], vs[i + 1]))
names = json.loads(bpy.context.scene["hgpt_region_names"])
region = np.array([d.value for d in body.data.attributes["hgpt_region"].data])

ns["reset"]()
rig.location = (0, 0, 0)
ns["upd"]()
heads = np.array([(rig.matrix_world @ rig.data.bones[n].head_local)[:] for n in deform])
mats, evald, pose_names = [], [], []
for name, fn in POSES.items():
    if only and name not in only:
        continue
    ns["reset"]()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    ns["upd"]()
    ns["HANDLE"].clear()
    fn()
    ns["upd"]()
    rw = np.array(rig.matrix_world)
    bw = np.array(body.matrix_world)
    # world = rig_world @ pose @ rest^-1 @ rig_world^-1 @ body_world @ v (armature modifier, object space)
    S = np.stack([rw @ np.array(rig.pose.bones[n].matrix) @ np.linalg.inv(np.array(rig.data.bones[n].matrix_local))
                  @ np.linalg.inv(rw) @ bw for n in deform])
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    P = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])
    T = np.einsum("bij,vj->vbi", S[:, :3, :], rest_h)
    lbs = np.einsum("vb,vbi->vi", W, T)
    err = float(np.abs(lbs - P).max())
    print("DUMP", name, "max LBS reconstruction error (m):", f"{err:.2e}")
    if err > 1e-4:
        raise SystemExit(f"LBS reconstruction mismatch in {name}: {err}")
    mats.append(S)
    evald.append(P)
    pose_names.append(name)

source_path = Path(bpy.data.filepath)
source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
np.savez_compressed(out_path, W=W, rest=rest, edges=edges, tris=np.array(tris), region=region,
                    region_names=np.array(names), bones=np.array(deform), heads=heads, mats=np.stack(mats),
                    evaluated=np.stack(evald), poses=np.array(pose_names),
                    source=np.array(source_path.name), source_sha256=np.array(source_sha256),
                    source_size_bytes=np.array(source_path.stat().st_size))
print("DUMP DONE", out_path, len(pose_names), "poses", source_sha256)
