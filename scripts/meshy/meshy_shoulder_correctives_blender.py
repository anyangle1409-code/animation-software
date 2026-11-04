"""Shoulder corrective shapes for the bound Meshy mesh (variant B rig copy), experimental.

For each key pose (press mid: humerus 105 deg, press top: 170 deg, both arms, girdle rhythm as in the pose test):
  1. pose the rig and take the linear-blend-skinned surface P;
  2. Delta-Mush correction inside a feathered shoulder mask: smooth the posed surface, then add back the rest
     surface's own detail expressed in local tangent frames (folds / crumples are removed, the sculpted muscle
     detail is kept);
  3. bring the posed-space correction back to the rest pose through the inverse of each vertex's skinning matrix
     (sum of weight x bone deform matrix) and store it as a shape key: CORR_SH_MID, CORR_SH_TOP.
The keys are meant to be driven by humerus elevation (mid peaks at 105 deg, top ramps in from 105 to 170 deg); the
pose test sets them from the same rule.

usage: python3.13 meshy_shoulder_correctives_blender.py -- <meshy_bound.blend (variant B)> <out .blend> [iterations]
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from scipy.sparse import csr_matrix
import os  # noqa: E402

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1]); IT = int(a[2]) if len(a) > 2 else 40
import os  # noqa: E402
FRAME = os.environ.get("CORR_FRAME", "disp")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
rig = bpy.data.objects["MESHY_RIG"]; body = bpy.data.objects["MESHY_BODY"]; me = body.data; n = len(me.vertices)
pb = rig.pose.bones; MW = rig.matrix_world; W2A = MW.to_3x3().inverted(); wp = lambda v: MW @ v
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shoulder_pose_lib import arm_pose, rest_capture, rest_restore  # noqa: E402

R = np.empty(n * 3); me.vertices.foreach_get("co", R); R = R.reshape(-1, 3)
E = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", E); E = E.reshape(-1, 2)
A = csr_matrix((np.ones(2 * len(E)), (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n))
Dinv = 1.0 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)
GN = {g.index: g.name for g in body.vertex_groups}
bones = [b.name for b in rig.data.bones if b.use_deform]; bix = {b: i for i, b in enumerate(bones)}
rows, cols, vals = [], [], []
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm in bix and g.weight > 1e-5:
            rows.append(v.index); cols.append(bix[nm]); vals.append(g.weight)
Wm = csr_matrix((vals, (rows, cols)), shape=(n, len(bones)))
Wm = csr_matrix(Wm.multiply(1.0 / np.maximum(np.asarray(Wm.sum(1)), 1e-9)))
# shoulder mask: weight on upperarm / clavicle / scapula, feathered over the surface
sw = np.asarray(Wm[:, [bix[b] for b in bones if any(k in b for k in ("upperarm", "clavicle", "scapula"))]].sum(1)).ravel()
MASK = os.environ.get("CORR_MASK", "blend")
if MASK == "blend":           # only where skinning blends bones: a single-bone (rigidly moving) vertex gets no correction
    blend = np.clip(2.5 * (1.0 - Wm.max(1).toarray().ravel()), 0, 1)
    region = np.clip(sw * 3.0, 0, 1)
    for _ in range(15):
        region = np.maximum(region, 0.5 * region + 0.5 * (A @ region) * Dinv)
    mask = blend * region
    for _ in range(int(os.environ.get("CORR_FEATHER", "8"))):
        mask = 0.5 * mask + 0.5 * (A @ mask) * Dinv
    mask = np.clip(mask / max(np.percentile(mask[mask > 1e-3], 90), 1e-6), 0, 1)
else:                         # round 1: whole shoulder region (upperarm / clavicle / scapula weight), feathered
    mask = np.clip(sw * 2.0, 0, 1)
    for _ in range(25):
        mask = np.maximum(mask, 0.5 * mask + 0.5 * (A @ mask) * Dinv)
    mask = np.clip(mask, 0, 1)


def smooth(X, it):
    for _ in range(it):
        X = 0.5 * X + 0.5 * (A @ X) * Dinv[:, None]
    return X


def frames(X, Xs):
    """per-vertex orthonormal frame on the smoothed surface: normal from neighbour average, tangent to a neighbour"""
    nb = np.asarray(A.indices); ip = A.indptr
    first = nb[ip[:-1]]
    t = Xs[first] - Xs; Nrm = np.zeros_like(Xs)
    # vertex normals of the smoothed surface from the faces
    me.calc_loop_triangles() if hasattr(me, "calc_loop_triangles") else None
    T = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", T); T = T.reshape(-1, 3)
    fn = np.cross(Xs[T[:, 1]] - Xs[T[:, 0]], Xs[T[:, 2]] - Xs[T[:, 0]])
    for k in range(3):
        np.add.at(Nrm, T[:, k], fn)
    Nrm /= np.maximum(np.linalg.norm(Nrm, axis=1, keepdims=True), 1e-12)
    t = t - Nrm * np.einsum("ij,ij->i", t, Nrm)[:, None]; t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    b = np.cross(Nrm, t)
    return np.stack([t, b, Nrm], 2)                      # (n, 3, 3): columns t, b, n


Rs = smooth(R, IT); F0 = frames(R, Rs); dloc = np.einsum("nji,nj->ni", F0, R - Rs)    # rest detail in local frames


def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); m = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
    V = np.empty(len(m.vertices) * 3); m.vertices.foreach_get("co", V); bpy.data.meshes.remove(m); return V.reshape(-1, 3)


def skin_mats():
    M = np.zeros((len(bones), 3, 3))
    for b, i in bix.items():
        p = pb[b]; M[i] = np.array((p.matrix @ rig.data.bones[b].matrix_local.inverted()).to_3x3())
    out = np.zeros((n, 3, 3))
    for k in range(3):
        for l in range(3):
            out[:, k, l] = Wm @ M[:, k, l]
    return out


if me.shape_keys is None:
    body.shape_key_add(name="Basis", from_mix=False)
rest = rest_capture(rig); rep = {}
for key, (elev, fwd, elbow, clav) in (("CORR_SH_MID", (105, 30, 115, 15)), ("CORR_SH_TOP", (170, 15, 175, 25))):
    rest_restore(rig, rest)
    for sd in ("l", "r"):
        arm_pose(rig, sd, elev, fwd, elbow, clav)
    bpy.context.view_layer.update()
    P = evaluated(); Ps = smooth(P, IT); M = skin_mats()
    if FRAME == "disp":       # smooth the skinning displacement field: rest detail kept wherever the motion is smooth
        C = R + smooth(P - R, IT)
    elif FRAME == "skin":       # rotation part (polar decomposition) of each vertex's blended skinning matrix: never flips
        U, _, Vt = np.linalg.svd(M); Rot = U @ Vt
        C = Ps + np.einsum("nij,nj->ni", Rot, R - Rs)
    else:                     # surface frames (first-neighbour tangent): flips at some vertices -> torn spikes (round 1)
        Fp = frames(P, Ps); C = Ps + np.einsum("nij,nj->ni", Fp, dloc)
    dP = smooth((C - P) * mask[:, None], int(os.environ.get("CORR_POSTSMOOTH", "0")))   # removes mask-edge noise
    dR = np.linalg.solve(M + np.eye(3) * 1e-6, dP[:, :, None])[:, :, 0]
    kb = body.shape_key_add(name=key, from_mix=False)
    kb.data.foreach_set("co", (R + dR).ravel()); kb.value = 0.0
    mv = np.linalg.norm(dP, axis=1)
    rep[key] = {"elevation_deg": elev, "max_correction_mm": round(float(mv.max()) * 1000, 1),
                "p99_correction_mm": round(float(np.percentile(mv[mask > 0.05], 99)) * 1000, 1), "masked_vertices": int((mask > 0.05).sum())}
    print("CORR", key, json.dumps(rep[key]), flush=True)
rest_restore(rig, rest); bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
(OUT.parent / "correctives_report.json").write_text(json.dumps({"iterations": IT, "frame": FRAME, "mask": MASK, **rep}, indent=1)); print("CORR done")
