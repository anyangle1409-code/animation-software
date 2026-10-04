"""Skinning dump of the 15 stress poses PLUS continuous-arc samples of the shoulder poses (never saves).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/dump_original_v1_arc_skinning_blender.py -- <out.npz> [fractions=0.25,0.375,0.5,0.625,0.75,0.875] [extra arc poses, comma list]

Same arrays as dump_original_v1_o4_pose_skinning_blender.py; extra pose entries are named '<pose>@<fraction>' and are built by replaying the
pose from rest with the swing/twist interpolation of the joint-kinematics audit. Extra array `theta` (poses, 2) = humerothoracic elevation
(deg, left/right) used to drive the shoulder corrective. Input for scripts/optimize_original_v1_shoulder_corrective.py.
"""
import hashlib
import json
import os
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

args = sys.argv[sys.argv.index("--") + 1:]
out_path = Path(args[0])
FRACS = [float(x) for x in args[1].split(",")] if len(args) > 1 and args[1] else [0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
ARC_POSES = ("press_bottom", "press_top", "press_top_rhythm", "pullup_hang", "pullup_hang_rhythm", "pullup_top")
if len(args) > 2 and args[2]:
    ARC_POSES = tuple(ARC_POSES) + tuple(x for x in args[2].split(",") if x and x not in ARC_POSES)   # optional extra arc poses (default behaviour unchanged)

src = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py").read_text(encoding="utf-8")
src = src[:src.index("# ---------------------------------------------------------------- metrics")]
tmp = tempfile.mkdtemp()
saved_argv = sys.argv
sys.argv = ["blender", "--", tmp, ""]
ns = {"__name__": "pose_defs", "__file__": "pose_test_original_v1_o4_candidate_blender.py"}
exec(compile(src, "pose_test_defs", "exec"), ns)
# optional driver of the post-pin corrective keys (flexion r86+, scapular r95+); only active when the dumped candidate carries them (SCRIPT_DUMP_DRIVER=0 disables)
if os.environ.get("HGPT_DUMP_DRIVER", "1") != "0":
    import importlib.util as _ilu
    _sp = _ilu.spec_from_file_location("original_v1_flexion_driver", str(Path(__file__).with_name("original_v1_flexion_driver.py")))
    _fd = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(_fd)
    _fd.install(ns)
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
mats, evald, pose_names, thetas, lams = [], [], [], [], []
pb_ = ns["pb"]


def elevation(side):
    h = (pb_(f"upperarm_{side}").tail - pb_(f"upperarm_{side}").head).normalized()
    down = -(pb_("spine_03").tail - pb_("spine_03").head).normalized()
    return math.degrees(h.angle(down))


def abduction_fraction(side):
    """Plane of elevation: share of the humerus' horizontal (trunk-frame) direction that is lateral rather than anterior (1 = pure abduction,
    0 = pure flexion); defined as h_lat^2 / (h_lat^2 + h_ant^2), 1 when the arm is vertical. Trunk frame = spine_03 rotation relative to rest."""
    h = (pb_(f"upperarm_{side}").tail - pb_(f"upperarm_{side}").head).normalized()
    R = pb_("spine_03").matrix.to_3x3() @ rig.data.bones["spine_03"].matrix_local.to_3x3().inverted()
    hl, ha = h.dot(R @ Vector((1, 0, 0))), h.dot(R @ Vector((0, -1, 0)))
    n = hl * hl + ha * ha
    return 1.0 if n < 1e-6 else hl * hl / n


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
    ns["upd"]()


def current_pre_skin_positions():
    """Return the exact local-space surface entering the armature modifier.

    On pre-corrective candidates this is simply the rest/Basis mesh. On r55+ the
    pose script actively drives the relative shoulder corrective keys, so those
    key deltas must be included before validating the linear skinning model.
    """
    keys = body.data.shape_keys
    if keys is None or not keys.key_blocks:
        return rest
    blocks = keys.key_blocks
    basis = blocks.get("Basis") or blocks[0]
    base = np.array([d.co[:] for d in basis.data], dtype=float)
    if base.shape != rest.shape or float(np.abs(base - rest).max()) > 1e-9:
        raise SystemExit("shape-key Basis differs from mesh rest coordinates")
    pre = base.copy()
    for kb in blocks:
        if kb == basis or kb.mute or abs(float(kb.value)) <= 1e-12:
            continue
        if kb.relative_key != basis:
            raise SystemExit(f"unsupported non-Basis relative shape key: {kb.name}")
        if kb.vertex_group:
            raise SystemExit(f"unsupported vertex-group-limited shape key: {kb.name}")
        key_pos = np.array([d.co[:] for d in kb.data], dtype=float)
        pre += float(kb.value) * (key_pos - base)
    return pre


def record(label):
    rw = np.array(rig.matrix_world)
    bw = np.array(body.matrix_world)
    S = np.stack([rw @ np.array(rig.pose.bones[n].matrix) @ np.linalg.inv(np.array(rig.data.bones[n].matrix_local))
                  @ np.linalg.inv(rw) @ bw for n in deform])
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    P = np.array([(ev.matrix_world @ v.co)[:] for v in ev.data.vertices])

    pre = current_pre_skin_positions()
    pre_h = np.c_[pre, np.ones(nv)]
    T = np.einsum("bij,vj->vbi", S[:, :3, :], pre_h)
    reconstructed = np.einsum("vb,vbi->vi", W, T)
    err = float(np.abs(reconstructed - P).max())
    if err > 1e-4:
        raise SystemExit(f"LBS + active-shape reconstruction mismatch in {label}: {err}")
    mats.append(S)
    evald.append(P)
    pose_names.append(label)
    thetas.append([elevation("l"), elevation("r")])
    lams.append([abduction_fraction("l"), abduction_fraction("r")])


for name, fn in POSES.items():
    ns["reset"]()
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, 0)
    ns["upd"]()
    ns["HANDLE"].clear()
    fn()
    ns["upd"]()
    record(name)
    if name in ARC_POSES:
        final = {p.name: (p.matrix_basis.to_quaternion(), p.matrix_basis.to_translation()) for p in rig.pose.bones}
        for f in FRACS:
            apply_fraction(final, f)
            record(f"{name}@{f:.3f}")
print("ARC DUMP", len(pose_names), "entries")

source_path = Path(bpy.data.filepath)
source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
np.savez_compressed(out_path, W=W, rest=rest, edges=edges, tris=np.array(tris), region=region,
                    region_names=np.array(names), bones=np.array(deform), heads=heads, mats=np.stack(mats),
                    evaluated=np.stack(evald), poses=np.array(pose_names), theta=np.array(thetas), lam=np.array(lams),
                    source=np.array(source_path.name), source_sha256=np.array(source_sha256),
                    source_size_bytes=np.array(source_path.stat().st_size))
print("DUMP DONE", out_path, len(pose_names), "entries", source_sha256)
