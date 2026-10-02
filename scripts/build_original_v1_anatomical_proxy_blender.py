"""First-party diagnostic anatomical proxy + joint-centre fit audit (never saves the .blend; not production geometry).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/build_original_v1_anatomical_proxy_blender.py -- <out_dir> [pose,pose,...]

Builds a SIMPLE project-generated proxy inside the candidate's own body mesh to inspect the skeleton/skin relationship:
  * rib-cage shell: a stack of elliptical rings lofted between the neck base and the lowest rib level, sized from THIS body's own torso
    cross-sections minus a stated soft-tissue inset (parameter THORAX_INSET_M, a diagnostic assumption, not a measurement);
  * sternum capsule on the anterior midline, pelvis basin ring, scapula plates (hung from the scapula bones), humeral-head spheres at
    the shoulder joint centres, long-bone shafts and joint-centre spheres from the armature.
It follows the posed armature (proxy parts are parented to the bones), is rendered with the skin semi-transparent, and writes
a numeric joint-centre fit audit at rest: for each long bone the centring of its axis inside the skin (left/right and front/back
surface distances along rays perpendicular to the axis) and the depth of every joint centre below the skin surface.
No third-party anatomy is used; the proxy is generated from this candidate's own mesh and rig only.
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out_dir> [pose,...]")
OUT = Path(args[0]).resolve()
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else {"neutral", "press_top", "pullup_top", "pushup_bottom"}
OUT.mkdir(parents=True, exist_ok=True)
THORAX_INSET_M = 0.025

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
saved = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src[:src.index("# ---------------------------------------------------------------- metrics")], "pose_test_defs", "exec"), ns)
sys.argv = saved
rig, body, POSES, reset, upd = ns["rig"], ns["body"], ns["POSES"], ns["reset"], ns["upd"]
mask = body.modifiers.get("HGPT_DRESSED_MASK")
if mask is not None:
    mask.show_viewport = False
    mask.show_render = False
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o is not body:
        o.hide_render = True
        o.hide_viewport = True
region_names = json.loads(bpy.context.scene["hgpt_region_names"])
vreg = [d.value for d in body.data.attributes["hgpt_region"].data]
reset()
rig.location = (0, 0, 0)
upd()

# ---------------------------------------------------------------- fit audit at rest
bvh = BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices], [tuple(p.vertices) for p in body.data.polygons])


def surface_dist(p, d):
    hit = bvh.ray_cast(p, d.normalized(), 2.0)
    return hit[3] if hit[0] is not None else None


def perp_axes(ax):
    a = ax.cross(Vector((1, 0, 0)))
    if a.length < 1e-3:
        a = ax.cross(Vector((0, 1, 0)))
    a.normalize()
    return a, ax.cross(a).normalized()


LONG = ["upperarm", "forearm", "thigh", "shin"]
fit = {"long_bones": {}, "joint_centres": {}}
for side in "lr":
    for seg in LONG:
        b = rig.data.bones[f"{seg}_{side}"]
        h, t = Vector(b.head_local), Vector(b.tail_local)
        ax = (t - h).normalized()
        u, w = perp_axes(ax)
        rows = []
        for f in (0.25, 0.5, 0.75):
            c = h + (t - h) * f
            r = [surface_dist(c, d) for d in (u, -u, w, -w)]
            if None in r:
                continue
            rows.append({"fraction": f, "dist_pos_u": round(r[0], 4), "dist_neg_u": round(r[1], 4), "dist_pos_w": round(r[2], 4), "dist_neg_w": round(r[3], 4),
                         "centring_u": round(abs(r[0] - r[1]) / (r[0] + r[1]), 4), "centring_w": round(abs(r[2] - r[3]) / (r[2] + r[3]), 4)})
        fit["long_bones"][f"{seg}_{side}"] = rows
    for name in ("upperarm", "forearm", "hand", "thigh", "shin", "foot"):
        b = rig.data.bones[f"{name}_{side}"]
        c = Vector(b.head_local)
        depths = {}
        for lbl, d in (("lateral", Vector((-1 if side == "l" else 1, 0, 0))), ("anterior", Vector((0, -1, 0))), ("posterior", Vector((0, 1, 0)))):
            x = surface_dist(c, d)
            depths[lbl] = round(x, 4) if x is not None else None
        fit["joint_centres"][f"{name}_{side}_head"] = depths
(OUT / "joint_centre_fit_rest.json").write_text(json.dumps({"source": Path(bpy.data.filepath).name, "thorax_inset_m": THORAX_INSET_M, **fit}, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- proxy objects
coll = bpy.data.collections.new("HGPT_PROXY_TMP")
bpy.context.scene.collection.children.link(coll)
mat = bpy.data.materials.new("HGPT_PROXY_MAT_TMP")
mat.diffuse_color = (0.93, 0.9, 0.78, 1.0)
mat2 = bpy.data.materials.new("HGPT_PROXY_JOINT_TMP")
mat2.diffuse_color = (0.85, 0.2, 0.2, 1.0)


def link(obj, material):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    obj.data.materials.append(material)


def parent_to(obj, bone):
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    # BONE parenting puts the child in the bone's tail-based frame; compensate to keep the world rest placement
    obj.matrix_parent_inverse = (rig.matrix_world @ rig.pose.bones[bone].matrix @ Matrix.Translation((0, rig.data.bones[bone].length, 0))).inverted()


def make(kind, loc, bone, material, **kw):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=kw["r"], location=loc)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=kw["r"], depth=kw["L"], location=loc)
        bpy.context.object.rotation_mode = "QUATERNION"
        bpy.context.object.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(kw["axis"])
    o = bpy.context.object
    link(o, material)
    if "scale" in kw:
        o.scale = kw["scale"]
    parent_to(o, bone)
    return o


# torso cross-sections from this body's own mesh
tv = [v.co for v, r in zip(body.data.vertices, vreg) if region_names[r] == "torso"]
z_lo, z_hi = Vector(rig.data.bones["spine_01"].head_local).z, Vector(rig.data.bones["neck"].head_local).z
rings = []
for k in range(9):
    z = z_lo + (z_hi - z_lo) * k / 8
    pts = [(p.x, p.y) for p in tv if abs(p.z - z) < 0.012]
    if len(pts) < 8:
        continue
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    rings.append((z, (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(xs) - min(xs)) / 2 - THORAX_INSET_M, (max(ys) - min(ys)) / 2 - THORAX_INSET_M))
bm = bmesh.new()
verts = []
for z, cx, cy, a, b in rings:
    verts.append([bm.verts.new((cx + a * math.cos(t), cy + b * math.sin(t), z)) for t in [2 * math.pi * i / 24 for i in range(24)]])
for r0, r1 in zip(verts, verts[1:]):
    for i in range(24):
        bm.faces.new((r0[i], r0[(i + 1) % 24], r1[(i + 1) % 24], r1[i]))
me = bpy.data.meshes.new("HGPT_PROXY_THORAX_TMP")
bm.to_mesh(me)
bm.free()
thorax = bpy.data.objects.new("HGPT_PROXY_THORAX_TMP", me)
coll.objects.link(thorax)
me.materials.append(mat)
thorax.parent = rig
thorax.parent_type = "BONE"
thorax.parent_bone = "spine_02"
thorax.matrix_parent_inverse = (rig.matrix_world @ rig.pose.bones["spine_02"].matrix @ Matrix.Translation((0, rig.data.bones["spine_02"].length, 0))).inverted()
mod = thorax.modifiers.new("wire", "WIREFRAME")
mod.thickness = 0.002

for side in "lr":
    for seg in ("upperarm", "forearm", "thigh", "shin"):
        b = rig.data.bones[f"{seg}_{side}"]
        h, t = Vector(b.head_local), Vector(b.tail_local)
        make("cyl", (h + t) / 2, f"{seg}_{side}", mat, r=0.012, L=(t - h).length * 0.96, axis=(t - h).normalized())
    for name in ("upperarm", "forearm", "hand", "thigh", "shin", "foot"):
        make("sphere", Vector(rig.data.bones[f"{name}_{side}"].head_local), f"{name}_{side}", mat2, r=0.017)
    sc = rig.data.bones[f"scapula_{side}"]
    h, t = Vector(sc.head_local), Vector(sc.tail_local)
    make("sphere", (h + t) / 2 + Vector((0, 0.01, 0)), f"scapula_{side}", mat, r=0.05, scale=(0.35, 0.9, 1.6))
make("cyl", Vector((0, -0.035, 1.40)), "spine_03", mat, r=0.014, L=0.17, axis=Vector((0, 0, 1)))
bm = bmesh.new()
bmesh.ops.create_circle(bm, cap_ends=False, radius=1.0, segments=24)
pm = bpy.data.meshes.new("HGPT_PROXY_PELVIS_TMP")
bm.to_mesh(pm)
bm.free()
pelvis = bpy.data.objects.new("HGPT_PROXY_PELVIS_TMP", pm)
coll.objects.link(pelvis)
pm.materials.append(mat)
pelvis.location = (0, 0.0, 1.0)
pelvis.scale = (0.13, 0.09, 1.0)
pelvis.parent = rig
pelvis.parent_type = "BONE"
pelvis.parent_bone = "pelvis"
pelvis.matrix_parent_inverse = (rig.matrix_world @ rig.pose.bones["pelvis"].matrix @ Matrix.Translation((0, rig.data.bones["pelvis"].length, 0))).inverted() @ Matrix.Translation(Vector((0, 0, 0)))
pm_mod = pelvis.modifiers.new("wire", "WIREFRAME")
pm_mod.thickness = 0.002

# ---------------------------------------------------------------- render
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
body_mat = bpy.data.materials.new("HGPT_PROXY_SKIN_TMP")
body_mat.diffuse_color = (0.7, 0.6, 0.55, 0.22)
body_mat.blend_method = "BLEND" if hasattr(body_mat, "blend_method") else None
body.data.materials.clear()
body.data.materials.append(body_mat)
body.show_transparent = True
stage = bpy.data.collections.new("HGPT_PROXY_STAGE_TMP")
scene.collection.children.link(stage)
cam_data = bpy.data.cameras.new("HGPT_PROXY_CAM_TMP")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("HGPT_PROXY_CAM_TMP", cam_data)
stage.objects.link(cam)
scene.camera = cam
written = []
for pose in POSES:
    if pose not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    ns["HANDLE"].clear()
    POSES[pose]()
    upd()
    target = rig.matrix_world @ rig.pose.bones["spine_03"].head
    cam_data.ortho_scale = 1.1 if pose != "pushup_bottom" else 2.4
    for view, off in (("front", Vector((0, -4, 0))), ("side", Vector((4, 0, 0))), ("three_quarter", Vector((3, -3, 1)))):
        cam.location = target + off
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
        path = OUT / f"{pose}__proxy_{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        written.append(path.name)
print("ANATOMICAL PROXY", OUT, len(written), "renders")
