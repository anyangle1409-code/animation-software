"""REVIEW PRESENTATION ONLY: dress a defined / fitted body like the owner's reference sheet so the comparison is fair.

The Option 5 reference shows short dark hair, eyebrows and dark grey trunks.  This adds, to a copy saved next to the
input:
  * hair: Cycles particle hair on the scalp (vertex-group density from the MakeHuman rig's head weights and the
    direction from the head centre: crown and back of the head, not the face);
  * eyebrows: short dense particle hair along the brow line;
  * trunks: a shell of the body skin between the waistband (0.565 H) and the mid-thigh (0.405 H), offset 4 mm along the
    normals, with a dark grey fabric material.
Nothing here is part of the body mesh; it is a separate review dressing.

usage: python3.13 dress_review_blender.py -- <defined .blend> <out .blend>
"""
import sys
from pathlib import Path

import bpy
import bmesh  # noqa: E402  (after bpy)
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
bpy.ops.wm.open_mainfile(filepath=str(SRC))
ob = bpy.data.objects["MPFB_DEFINED_REVIEW"]
src = max((o for o in bpy.data.objects if o.type == "MESH" and o is not ob and "FLOOR" not in o.name), key=lambda o: len(o.data.vertices))
me = ob.data; n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
mw = np.array(ob.matrix_world); W = V @ mw[:3, :3].T + mw[:3, 3]
Nn = np.empty(n * 3); me.vertices.foreach_get("normal", Nn); Nn = Nn.reshape(-1, 3)
GN = {g.index: g.name for g in src.vertex_groups}; G = {}
for v in me.vertices:
    for g in v.groups:
        nm = GN.get(g.group)
        if nm:
            G.setdefault(nm, np.zeros(n))[v.index] = g.weight
gw = lambda *ks: np.clip(sum((w for nm, w in G.items() if any(k in nm for k in ks)), np.zeros(n)), 0, 1)
z0 = W[:, 2].min(); H = W[:, 2].max() - z0; f = (W[:, 2] - z0) / H
head = gw("head") > 0.5
hc = W[head].mean(0); hc[2] = W[head, 2].max() - 0.115
d = W - hc; d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
up, back, side = d[:, 2], d[:, 1], np.abs(d[:, 0])
hair = head & ((up > 0.42) | ((back > 0.15) & (up > -0.30)) | ((side > 0.75) & (up > 0.05)))
hair &= ~((back < -0.35) & (up < 0.62))                               # keep the forehead clear
hw = hair.astype(float)
# ears out of the hair: lateral points near ear height
hw[(side > 0.88) & (np.abs(W[:, 2] - (hc[2] + 0.005)) < 0.035)] = 0.0
vg = ob.vertex_groups.new(name="HAIR_REVIEW"); idx = np.nonzero(hw > 0)[0].tolist(); vg.add(idx, 1.0, "REPLACE")
# eyebrows: a thin band above each eye socket
br = head & (back < -0.60) & (d[:, 2] > 0.20) & (d[:, 2] < 0.27) & (side > 0.10) & (side < 0.48)
vb = ob.vertex_groups.new(name="BROW_REVIEW"); vb.add(np.nonzero(br)[0].tolist(), 1.0, "REPLACE")


def hair_sys(name, group, count, length, children, mat_color, rough=0.35):
    mod = ob.modifiers.new(name, "PARTICLE_SYSTEM"); ps = mod.particle_system; st = ps.settings
    st.type = "HAIR"; st.count = count; st.hair_length = length; st.use_advanced_hair = True
    st.normal_factor = 0.35; st.tangent_factor = 0.0
    st.object_align_factor = (0.0, 0.012, 0.012) if name.startswith("HAIR") else (0.0, 0.0, 0.0)   # combed up and back
    st.emit_from = "FACE"; st.use_emit_random = True
    ps.vertex_group_density = group
    for k_, v_ in (("child_type", "INTERPOLATED"), ("rendered_child_count", children), ("child_percent", max(1, children // 4)),
                   ("root_radius", 0.6), ("tip_radius", 0.1), ("radius_scale", 0.0012), ("child_length", 1.0),
                   ("clump_factor", 0.15), ("roughness_1", 0.004), ("roughness_endpoint", 0.002), ("kink", "NO")):
        try:
            setattr(st, k_, v_)
        except (AttributeError, TypeError):
            pass
    m = bpy.data.materials.new(name + "_MAT"); m.use_nodes = True; nt = m.node_tree
    for nd in list(nt.nodes):
        if nd.type == "BSDF_PRINCIPLED":
            nt.nodes.remove(nd)
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    try:
        hb.parametrization = "MELANIN"
        hb.inputs["Melanin"].default_value = mat_color; hb.inputs["Roughness"].default_value = rough
        hb.inputs["Melanin Redness"].default_value = 0.25
    except Exception:
        pass
    nt.links.new(hb.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    ob.data.materials.append(m); st.material = len(ob.data.materials)
    return ps


# the skin material slot stays first; hair materials after it
if not ob.data.materials:
    ob.data.materials.append(bpy.data.materials.new("SKIN_PLACEHOLDER"))
hair_sys("HAIR_REVIEW", "HAIR_REVIEW", 14000, 0.022, 40, 0.97, 0.45)
hair_sys("BROW_REVIEW", "BROW_REVIEW", 700, 0.006, 4, 0.97, 0.5)
# trunks: shell of the skin between 0.405 H and 0.565 H (arms and hands excluded)
arm = gw("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky") > 0.3
keep = (f > 0.405) & (f < 0.565) & ~arm
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep[v.index]], context="VERTS")
for v in bm.verts:
    v.co = v.co + v.normal * 0.004
tm = bpy.data.meshes.new("TRUNKS_REVIEW"); bm.to_mesh(tm); bm.free()
to = bpy.data.objects.new("TRUNKS_REVIEW", tm); bpy.context.scene.collection.objects.link(to); to.matrix_world = ob.matrix_world.copy()
for p in tm.polygons:
    p.use_smooth = True
sol = to.modifiers.new("THICK", "SOLIDIFY"); sol.thickness = 0.002
fm = bpy.data.materials.new("TRUNKS_FABRIC"); fm.use_nodes = True
b = fm.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1); b.inputs["Roughness"].default_value = 0.85
tm.materials.append(fm)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("DRESS hair_verts", int(hair.sum()), "brow_verts", int(br.sum()), flush=True)
