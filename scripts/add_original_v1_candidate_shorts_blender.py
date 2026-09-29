"""Add ORIGINAL fitted athletic shorts + authored materials to the O4 CANDIDATE.

blender --background --factory-startup ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend \
        --python scripts/add_original_v1_candidate_shorts_blender.py

Candidate only (O7 work is gated after O2 review in the production line).
Provenance: the garment surface is derived from THIS project's ORIGINAL v1
body (hip line to mid-thigh), offset for ease, smoothed so fabric bridges the
muscle/cleft detail, then given thickness, waistband and hems. Garment weights
are copied from the nearest ORIGINAL v1 body vertex (first-party to first-party).
Materials are authored numeric values; no textures or external assets.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Candidate files only.")
ROOT = Path(__file__).resolve().parents[1]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig and "SHORTS" not in o.name)
for o in [o for o in bpy.data.objects if "SHORTS" in o.name]:
    bpy.data.objects.remove(o)

WAIST_Z = 1.005          # waistband top (just below the navel / over the iliac crest)
HEM_Z = 0.625            # mid-thigh hem
EASE = 0.006             # fabric ease over the skin (m)
HEM_EASE = 0.016         # looser at the hem
THICKNESS = 0.0028

region_names = json.loads(scene["hgpt_region_names"])
vreg = [region_names[d.value] for d in body.data.attributes["hgpt_region"].data]
bm = bmesh.new()
bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
bm.normal_update()


def inside(v):
    r = vreg[v.index]
    z = v.co.z
    if r in ("torso", "pelvis"):
        return z < WAIST_Z
    if r == "leg":
        return z > HEM_Z
    return False


keep_faces = [f for f in bm.faces if all(inside(v) for v in f.verts)]
new = bmesh.new()
vmap = {}
for f in keep_faces:
    for v in f.verts:
        if v.index not in vmap:
            nv = new.verts.new(v.co + v.normal * 0.0)
            vmap[v.index] = (nv, v)
new.verts.ensure_lookup_table()
for f in keep_faces:
    new.faces.new([vmap[v.index][0] for v in f.verts])
new.normal_update()

# offset for ease (looser toward the hem), then smooth the offset surface so the
# fabric bridges the abdominal grooves, gluteal cleft and hip dimples.
body_normals = {nv: src.normal.copy() for nv, src in vmap.values()}
for nv, src in vmap.values():
    t = max(0.0, min(1.0, (0.80 - src.co.z) / (0.80 - HEM_Z)))
    nv.co = src.co + src.normal * (EASE + (HEM_EASE - EASE) * t)
for _ in range(10):
    moves = {}
    for v in new.verts:
        if v.is_boundary:
            continue
        avg = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        moves[v] = v.co.lerp(avg, 0.5)
    for v, p in moves.items():
        v.co = p
# never inside the skin: push back out along the body normal where smoothing sank it
for nv, src in vmap.values():
    d = (nv.co - src.co).dot(body_normals[nv])
    if d < EASE * 0.7:
        nv.co += body_normals[nv] * (EASE * 0.7 - d)

# clean horizontal waist and hem lines (face selection leaves a staircase edge)
for v in new.verts:
    if v.is_boundary:
        v.co.z = WAIST_Z if v.co.z > 0.85 else HEM_Z
for _ in range(3):  # relax the ring just inside each opening to match the new edge
    for v in new.verts:
        if not v.is_boundary and any(e.other_vert(v).is_boundary for e in v.link_edges):
            avg = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
            v.co = v.co.lerp(avg, 0.5)

# waistband and hems: extrude the open boundaries (turned edge)
new.edges.ensure_lookup_table()
boundary = [e for e in new.edges if e.is_boundary]
res = bmesh.ops.extrude_edge_only(new, edges=boundary)
for v in [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]:
    v.co = v.co + Vector((0, 0, 0.010 if v.co.z > 0.9 else -0.004))
new.normal_update()

mesh = bpy.data.meshes.new("HGPT_ORIGINAL_V1_SHORTS_CANDIDATE_MESH")
new.to_mesh(mesh)
new.free()
bm.free()
shorts = bpy.data.objects.new("HGPT_ORIGINAL_V1_SHORTS_CANDIDATE", mesh)
bpy.data.collections["ORIGINAL_CLOTHING"].objects.link(shorts)
for p in mesh.polygons:
    p.use_smooth = True
solid = shorts.modifiers.new("THICKNESS", "SOLIDIFY")
solid.thickness = THICKNESS
solid.offset = -1.0
solid.use_even_offset = True
bpy.context.view_layer.objects.active = shorts
shorts.select_set(True)
bpy.ops.object.modifier_apply(modifier=solid.name)
bpy.ops.object.shade_smooth()

# --- weights: nearest ORIGINAL v1 body vertex (first-party) + light smoothing ---
# Only trunk/pelvis/leg skin may donate (the rest-pose hand hangs millimetres
# from the hip; hand weights on the garment would tear it when the arms move).
donors = [v for v in body.data.vertices if vreg[v.index] in ("torso", "pelvis", "leg")]
kd = KDTree(len(donors))
for v in donors:
    kd.insert(v.co, v.index)
kd.balance()
names = [vg.name for vg in body.vertex_groups]
bw = np.zeros((len(body.data.vertices), len(names)))
for v in body.data.vertices:
    for g in v.groups:
        bw[v.index, g.group] = g.weight
SW = np.zeros((len(mesh.vertices), len(names)))
for v in mesh.vertices:
    near = kd.find_n(v.co, 4)
    w = np.array([1.0 / max(d, 1e-4) for _co, _i, d in near])
    SW[v.index] = sum(wi * bw[i] for wi, (_co, i, _d) in zip(w, near)) / w.sum()
nbrs = [[] for _ in mesh.vertices]
for e in mesh.edges:
    a, b = e.vertices
    nbrs[a].append(b)
    nbrs[b].append(a)
for _ in range(4):
    SW = np.array([0.5 * SW[i] + 0.5 * SW[n].mean(axis=0) if n else SW[i] for i, n in enumerate(nbrs)])
order = np.argsort(-SW, axis=1)
mask = np.zeros_like(SW, dtype=bool)
mask[np.arange(len(SW))[:, None], order[:, :4]] = True
SW = np.where(mask, SW, 0)
SW /= SW.sum(axis=1, keepdims=True)
for j, n in enumerate(names):
    vg = shorts.vertex_groups.new(name=n)
    for i in np.nonzero(SW[:, j] > 1e-5)[0]:
        vg.add([int(i)], float(SW[i, j]), "REPLACE")
shorts.parent = rig
arm = shorts.modifiers.new("Armature", "ARMATURE")
arm.object = rig

# --- dressed variant: hide body skin fully covered by the garment (2.5 cm margin
# from the waist/hem) so skin cannot show through fabric under deformation. The
# bare variant keeps the whole body (mask disabled).
for vg in [g for g in body.vertex_groups if g.name == "HGPT_UNDER_SHORTS"]:
    body.vertex_groups.remove(vg)
under = body.vertex_groups.new(name="HGPT_UNDER_SHORTS")
for v in body.data.vertices:
    r, z = vreg[v.index], v.co.z
    if (r in ("torso", "pelvis") and z < WAIST_Z - 0.025) or (r == "leg" and z > HEM_Z + 0.025):
        under.add([v.index], 1.0, "REPLACE")
for m in [m for m in body.modifiers if m.type == "MASK"]:
    body.modifiers.remove(m)
mask = body.modifiers.new("HGPT_DRESSED_MASK", "MASK")
mask.vertex_group = "HGPT_UNDER_SHORTS"
mask.invert_vertex_group = True

# --- authored materials (numeric only) ---
def principled(name, color, rough, sss=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    if sss and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = sss
    m.diffuse_color = color
    return m


skin = principled("HGPT_ORIGINAL_V1_SKIN_CANDIDATE", (0.70, 0.52, 0.42, 1.0), 0.48, 0.12)
fabric = principled("HGPT_ORIGINAL_V1_SHORTS_FABRIC_CANDIDATE", (0.055, 0.058, 0.064, 1.0), 0.82)
body.data.materials.clear()
body.data.materials.append(skin)
mesh.materials.append(fabric)

bpy.ops.wm.save_mainfile()
cand = Path(bpy.data.filepath)
record = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "stage": "O7 candidate (not production)",
    "garment": "ORIGINAL fitted athletic shorts derived from ORIGINAL v1 body surface",
    "waist_z": WAIST_Z, "hem_z": HEM_Z, "ease_m": EASE, "hem_ease_m": HEM_EASE, "thickness_m": THICKNESS,
    "vertices": len(mesh.vertices), "faces": len(mesh.polygons),
    "weights": "nearest-4 ORIGINAL v1 body vertices (inverse distance) + smoothing, max 4 influences",
    "materials": {"skin": "authored numeric principled", "fabric": "authored numeric principled"},
    "not_used": ["legacy/third-party garments", "textures", "external materials"],
    "candidate_sha256": hashlib.sha256(cand.read_bytes()).hexdigest(),
}
(cand.parent / "O7_SHORTS_CANDIDATE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("SHORTS", json.dumps(record))
