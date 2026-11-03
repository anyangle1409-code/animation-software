"""REVIEW ONLY: clean single-surface standing sculpt of our first-party Body v2 mesh.

Poses our body (arms ARMS_OUT deg out in the frontal plane, everything else at rest), takes the evaluated surface,
voxel-remeshes it (one even, seam-free surface: removes the patch seams / ripples of the stitched rig mesh) and relaxes
it with a few Laplacian passes.  The result is a STATIC standing sculpt for visual review; it carries no rig or
weights.  If the owner approves the shape, a production retopology + re-bind follows.

  usage: python3.13 remesh_review_blender.py -- <in .blend> <out .blend>
  env:   V2_ARMS_OUT (deg, default 10), V2_VOXEL_MM (default 2.5), V2_RELAX (Laplacian passes, default 4)
"""
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = Path(a[0]), Path(a[1])
AO = float(os.environ.get("V2_ARMS_OUT", "10"))
VOX = float(os.environ.get("V2_VOXEL_MM", "2.5")) / 1000
RELAX = int(os.environ.get("V2_RELAX", "4"))
bpy.ops.wm.open_mainfile(filepath=str(SRC))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import character_profile  # noqa: E402
bn, rn = character_profile.blender_names()
body, rig = bpy.data.objects[bn], bpy.data.objects[rn]
W2A = rig.matrix_world.to_3x3().inverted()
for sd in ("l", "r"):
    ua = rig.pose.bones[f"upperarm_{sd}"]
    lat = 1.0 if (rig.matrix_world @ ua.head).x > 0 else -1.0
    e = math.radians(AO); tgt = (W2A @ Vector((lat * math.sin(e), 0.0, -math.cos(e)))).normalized()
    cur = (ua.tail - ua.head).normalized(); piv = ua.head.copy()
    ua.matrix = Matrix.Translation(piv) @ cur.rotation_difference(tgt).to_matrix().to_4x4() @ Matrix.Translation(-piv) @ ua.matrix
    bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), depsgraph=dg)
new = bpy.data.objects.new("IND_REVIEW_SCULPT", me); bpy.context.scene.collection.objects.link(new)
new.matrix_world = body.matrix_world.copy()
for o in list(bpy.data.objects):
    if o is not new and o.type in ("MESH", "ARMATURE"):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = new; new.select_set(True)
me.remesh_voxel_size = VOX; me.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
if RELAX:
    m = new.modifiers.new("RELAX", "LAPLACIANSMOOTH"); m.iterations = RELAX; m.lambda_factor = 0.4
    m.use_volume_preserve = True
    bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.shade_smooth()
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("REMESH", len(new.data.vertices), flush=True)
