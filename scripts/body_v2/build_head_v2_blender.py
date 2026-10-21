"""Head v2: a detailed separate head for the ORIGINAL_v1 body (Claude, 21 Oct 2026).  Review candidate only.

Owner (21 Oct), asked how to handle the mannequin-like head: "Detailed separate head".  The body's face has 318
vertices at ~10 mm spacing - too coarse for eyes, lips or a defined nose - and the body mesh must stay unchanged
(Work's topology, gates and correctives).  So:
  1. the body's head above a cut line (rest z >= CUT) is copied into a separate mesh; its boundary vertices coincide
     with the body's, so the seam has no gap (in review renders the body's own head faces are hidden by a mask);
  2. the copy is subdivided linearly (edges cut into 4 -> ~2.5 mm) and its interior relaxed with the boundary fixed;
  3. the face is sculpted with smooth displacement fields along the normal, placed on the measured head surface:
     eye sockets, eyeballs and lids, brow ridge, nose (bridge, tip, wings, nostrils), cheekbones, philtrum and lips,
     mouth corners, chin, jaw angle, ears.  Proportions from standard adult male head canons (eye line at half head
     height, nose base at about 1/3 of the face, mouth a third of the way from nose to chin); no third-party assets.
  blender python: build_head_v2_blender.py -- <R57 root> <out dir> [body v2 offsets npz | none]
Writes <out>/head_v2.npz (vertices, faces, boundary map to body vertex ids) and front / three-quarter / side renders.
"""
import json
import os
import sys
from pathlib import Path

import bpy
import bmesh  # after bpy (bpy as a module)
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
ROOT = Path(args[0]).resolve(); OUT = Path(args[1]); OUT.mkdir(parents=True, exist_ok=True)
OFF = args[2] if len(args) > 2 else "none"
CUT = float(os.environ.get("HEAD_CUT_Z", "1.585"))
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts/anatomy_fit")]
import build_original_review_candidate_r17_blender as r17

res = r17._setup(ROOT / "ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend")
body = res["body"]; me = body.data
rest = np.array([v.co[:] for v in me.vertices])
if OFF != "none":
    rest = rest + np.load(OFF)["offsets"]
faces = np.array([p.vertices[:] for p in me.polygons])

# 1. head region copy
keep_f = np.all(rest[faces][:, :, 2] >= CUT, axis=1)
used = np.unique(faces[keep_f]); remap = -np.ones(len(rest), int); remap[used] = np.arange(len(used))
bm = bmesh.new()
vs = [bm.verts.new(Vector(rest[i])) for i in used]
bm.verts.ensure_lookup_table()
for f in faces[keep_f]:
    bm.faces.new([vs[remap[i]] for i in f])
bm.edges.ensure_lookup_table()
boundary0 = {v.index for v in bm.verts if v.is_boundary}
# 2. linear subdivision x2 (each original edge -> 4)
for _ in range(2):
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
bmesh.ops.triangulate(bm, faces=list(bm.faces))
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
P = np.array([v.co[:] for v in bm.verts]); F = np.array([[v.index for v in f.verts] for f in bm.faces])
bnd = np.array([v.is_boundary for v in bm.verts])
nv = len(P)
nb = [[] for _ in range(nv)]
for a, b, c in F:
    nb[a] += [b, c]; nb[b] += [a, c]; nb[c] += [a, b]
nb = [np.unique(n) for n in nb]
rows = np.repeat(np.arange(nv), [len(n) for n in nb]); cols = np.concatenate(nb); deg = np.array([len(n) for n in nb], float)


def lap(X):
    acc = np.zeros_like(X); np.add.at(acc, rows, X[cols]); return acc / deg[:, None] - X


free = (~bnd)[:, None].astype(float)
for _ in range(12):                                   # Taubin: removes the faceting of the linear subdivision, no shrink
    P = P + 0.5 * free * lap(P); P = P - 0.53 * free * lap(P)


def normals(X):
    tri = X[F]; fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    vn = np.zeros_like(X); np.add.at(vn, F.ravel(), np.repeat(fn, 3, axis=0))
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


N = normals(P)


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def surf_front(x, z):
    """front surface (min y) of the head near (x, z)"""
    m = (np.abs(P[:, 0] - x) < 0.006) & (np.abs(P[:, 2] - z) < 0.006) & (P[:, 1] < 0)
    return float(P[m, 1].min()) if m.any() else float(P[P[:, 1] < 0, 1].min())


def surf_side(y, z, sg):
    m = (np.abs(P[:, 1] - y) < 0.006) & (np.abs(P[:, 2] - z) < 0.006) & (sg * P[:, 0] > 0)
    return float(np.abs(P[m, 0]).max()) if m.any() else 0.078


# head landmarks (rest): vertex 1.820, chin ~1.620 -> head height 0.20; eye line at the middle
ztop = float(P[:, 2].max()); zchin = 1.622
H = ztop - zchin
z_eye = zchin + 0.50 * H; z_brow = z_eye + 0.085 * H; z_nose = zchin + 0.27 * H; z_mouth = zchin + 0.155 * H
FEAT = []      # (centre, radii, amp m, facing) - centre placed on the surface
# H2 (after the first pass read as separate bumps with hole-like eyes): almond eyes with lids, one continuous nose
# ridge, wider mouth with defined lips, broader chin and jaw, larger cheekbones
for sg in (-1.0, 1.0):
    ex = 0.031 * sg
    fy = surf_front(ex, z_eye)
    FEAT += [((ex, fy + 0.003, z_eye), (0.023, 0.016, 0.013), -0.0045, (0, -1, 0)),            # eye socket, shallow and wide
             ((ex, fy + 0.004, z_eye), (0.0125, 0.010, 0.0068), 0.0040, (0, -1, 0)),            # eyeball under the lids
             ((ex, fy + 0.001, z_eye + 0.0062), (0.0145, 0.008, 0.0028), 0.0016, (0, -1, 0.4)),  # upper lid
             ((ex, fy + 0.002, z_eye - 0.0068), (0.0125, 0.008, 0.0024), 0.0011, (0, -1, -0.3)), # lower lid
             ((ex * 1.06, surf_front(ex, z_brow), z_brow), (0.024, 0.012, 0.008), 0.0035, (0, -1, 0.4)),   # brow ridge
             ((0.050 * sg, surf_front(0.050 * sg, z_eye - 0.024), z_eye - 0.024), (0.028, 0.020, 0.016), 0.0040, (sg, -1, 0)),  # cheekbone
             ((0.044 * sg, surf_front(0.044 * sg, z_nose - 0.014), z_nose - 0.014), (0.020, 0.016, 0.016), -0.0020, (sg, -1, 0)),  # cheek hollow
             ((0.0135 * sg, surf_front(0.0135 * sg, z_nose + 0.004) + 0.004, z_nose + 0.004), (0.0090, 0.010, 0.0085), 0.0042, (sg, -1, 0)),  # nose wing
             ((0.024 * sg, surf_front(0.024 * sg, z_mouth), z_mouth), (0.0055, 0.006, 0.0060), -0.0016, (0, -1, 0)),       # mouth corner
             ((0.052 * sg, -0.030, zchin + 0.014), (0.020, 0.032, 0.018), 0.0060, (sg, -0.2, -0.5)),                       # jaw angle
             ((surf_side(0.004, z_eye - 0.008, sg) * sg, 0.004, z_eye - 0.008), (0.006, 0.018, 0.031), 0.0105, (sg, 0.2, 0)),  # ear
             ((surf_side(0.004, z_eye - 0.006, sg) * sg, -0.001, z_eye - 0.006), (0.006, 0.009, 0.013), -0.0045, (sg, 0, 0)),  # ear bowl
             ]
# nose: one ridge from the glabella to the tip (chain of overlapping ellipsoids, rising toward the tip)
for k, (dz, amp, rx) in enumerate(((0.012, 0.0015, 0.008), (0.000, 0.0030, 0.0075), (-0.012, 0.0050, 0.0075), (-0.024, 0.0070, 0.0080), (-0.034, 0.0085, 0.0090))):
    zz = z_eye + dz
    FEAT.append(((0, surf_front(0, zz), zz), (rx, 0.012, 0.010), amp, (0, -1, 0)))
FEAT += [((0, surf_front(0, z_nose + 0.006), z_nose + 0.006), (0.0105, 0.012, 0.0095), 0.0060, (0, -1, -0.2)),   # nose tip
         ((0, surf_front(0, z_nose - 0.002) + 0.004, z_nose - 0.002), (0.011, 0.010, 0.004), -0.0025, (0, -0.5, -1)),  # under the nose
         ((0, surf_front(0, z_mouth + 0.010), z_mouth + 0.010), (0.0055, 0.006, 0.007), -0.0012, (0, -1, 0)),   # philtrum
         ((0, surf_front(0, z_mouth + 0.0045), z_mouth + 0.0045), (0.025, 0.008, 0.0050), 0.0030, (0, -1, 0)),  # upper lip
         ((0, surf_front(0, z_mouth), z_mouth), (0.026, 0.006, 0.0015), -0.0022, (0, -1, 0)),                  # mouth line
         ((0, surf_front(0, z_mouth - 0.0055), z_mouth - 0.0055), (0.021, 0.008, 0.0050), 0.0034, (0, -1, 0)),  # lower lip
         ((0, surf_front(0, z_mouth - 0.015), z_mouth - 0.015), (0.017, 0.008, 0.004), -0.0016, (0, -1, 0)),   # chin crease
         ((0, surf_front(0, zchin + 0.007), zchin + 0.007), (0.024, 0.016, 0.013), 0.0060, (0, -1, -0.3)),     # chin
         ]
disp = np.zeros(nv)
for cen, rad, amp, face in FEAT:
    q = (P - np.array(cen)) / np.array(rad); r = np.linalg.norm(q, axis=1)
    f = np.array(face, float); f /= np.linalg.norm(f)
    disp += amp * ss(1 - r) ** 1.4 * ss((N @ f + 0.2) / 1.2)
disp[bnd] = 0.0
# keep the seam still: fade the sculpt to zero over 15 mm above the cut
disp *= ss((P[:, 2] - CUT) / 0.015)
P2 = P + N * disp[:, None]
for _ in range(2):
    P2 = P2 + 0.3 * free * lap(P2)
# boundary map back to body vertices (exact coincidence)
from scipy.spatial import cKDTree
d_, j_ = cKDTree(rest).query(P2[bnd])
report = {"cut_z": CUT, "head_vertices": nv, "head_faces": int(len(F)), "body_head_faces_replaced": int(keep_f.sum()),
          "boundary_vertices": int(bnd.sum()), "boundary_max_gap_mm": round(float(d_.max() * 1000), 4),
          "landmarks_z": {"eye": round(z_eye, 3), "brow": round(z_brow, 3), "nose_base": round(z_nose, 3), "mouth": round(z_mouth, 3), "chin": zchin, "top": round(ztop, 3)},
          "max_sculpt_mm": round(float(np.abs(disp).max() * 1000), 2)}
np.savez_compressed(OUT / "head_v2.npz", vertices=P2.astype(np.float32), faces=F.astype(np.int32),
                    boundary_body_ids=j_.astype(np.int32), replaced_body_faces=np.flatnonzero(keep_f).astype(np.int32))
(OUT / "head_v2_report.json").write_text(json.dumps(report, indent=1))
print("HEAD_V2", json.dumps(report), flush=True)

# review renders: body with its own head faces hidden + the new head
hm = bpy.data.meshes.new("HEAD_V2"); hm.from_pydata(P2.tolist(), [], F.tolist()); hm.update()
for p in hm.polygons:
    p.use_smooth = True
head = bpy.data.objects.new("HEAD_V2", hm); bpy.context.scene.collection.objects.link(head)
key = body.shape_key_add(name="V2", from_mix=False); key.data.foreach_set("co", rest.ravel().astype(np.float32)); key.value = 1.0
# hide the replaced faces: a vertex-group mask on vertices used only by replaced faces
only = np.ones(len(rest), bool); only[np.unique(faces[~keep_f])] = False
vg = body.vertex_groups.new(name="REVIEW_KEEP"); vg.add([int(i) for i in np.flatnonzero(~only)], 1.0, "REPLACE")
for m in list(body.modifiers):
    if m.type == "ARMATURE":
        m.show_render = m.show_viewport = False
mask = body.modifiers.new("REVIEW_HIDE_HEAD", "MASK"); mask.vertex_group = "REVIEW_KEEP"
sc = bpy.context.scene
for ob in sc.objects:
    if ob.type in ("MESH", "CURVE") and ob not in (body, head):
        ob.hide_render = True
mat = bpy.data.materials.new("REVIEW_ONLY"); mat.diffuse_color = (.72, .55, .45, 1)
for ob in (body, head):
    ob.data.materials.clear(); ob.data.materials.append(mat)
for p in me.polygons:
    p.use_smooth = True
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.display.shading.show_cavity = True; sc.render.resolution_x = sc.render.resolution_y = 800
cd = bpy.data.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 0.32; cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, 0, 1.69))
for view, dv in {"front": (0, -1, 0), "front34": (0.7, -0.7, 0), "side": (1, 0, 0), "back34": (0.7, 0.7, 0.1)}.items():
    d = Vector(dv).normalized(); cam.location = tgt + d * 3; cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    sc.render.filepath = str(OUT / f"head_v2_{view}.png"); bpy.ops.render.render(write_still=True)
print("HEAD_V2_RENDERED", flush=True)
