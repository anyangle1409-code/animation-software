"""Render matched V13e vs V15f proof for one Stage-B digit directly from Blend.

Usage inside Blender:
  blender --background --python scripts/render_v15f_stage_b_digit_blender.py -- index_L
"""
from __future__ import annotations
import bpy, json, sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend"
CAND=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend"
BODY="Mike_Freeman"
ALLOWED=("index_L","index_R","middle_L","middle_R")
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if not args or args[0] not in ALLOWED:
    raise SystemExit("Pass one of: "+", ".join(ALLOWED))
KEY=args[0]
DIGIT,SIDE=KEY.rsplit("_",1)
OUT=ROOT/"renders_v15f_stage_b"/KEY
META=ROOT/"reports"/f"v15f_stage_b_{KEY}_visual_proof.json"
VIEWS={
    "yneg":Vector((0,-1,0.18)),
    "ypos":Vector((0,1,0.18)),
    "xside":Vector((1 if SIDE=="L" else -1,0,0.12)),
    "oblique":Vector((0.72 if SIDE=="L" else -0.72,-0.72,0.32)),
}

def owned_world(body):
    gids={
        g.index for g in body.vertex_groups
        if f"DEF-f_{DIGIT}." in g.name and g.name.endswith("."+SIDE)
    }
    if not gids:
        raise RuntimeError(f"Missing {KEY} deform groups")
    points=[]
    for v in body.data.vertices:
        weight=sum(x.weight for x in v.groups if x.group in gids)
        if weight>0.65:
            points.append(body.matrix_world@v.co)
    if not points:
        raise RuntimeError(f"No {KEY} owned vertices")
    return points

def bounds(points):
    lo=Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)))
    hi=Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)))
    return (lo+hi)*0.5,hi-lo

def setup(body):
    sc=bpy.context.scene
    sc.render.engine="BLENDER_WORKBENCH"
    sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG";sc.render.film_transparent=False
    sc.world.color=(.12,.12,.12);sc.view_settings.view_transform="Standard"
    sh=sc.display.shading;sh.light="STUDIO";sh.studiolight_rotate_z=.4
    sh.color_type="SINGLE";sh.single_color=(.62,.62,.62)
    sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type="BOTH"
    sh.curvature_ridge_factor=1.5;sh.curvature_valley_factor=1.0
    sh.show_specular_highlight=False;sh.background_type="WORLD"
    for obj in sc.objects: obj.hide_render=obj!=body
    ca=bpy.data.cameras.new("V15f Stage-B proof camera")
    cam=bpy.data.objects.new("V15f Stage-B proof camera",ca)
    sc.collection.objects.link(cam);sc.camera=cam;ca.type="ORTHO"
    return sc,cam

def render_file(path,label,focus,scale):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body=bpy.data.objects[BODY]
    points=owned_world(body)
    sc,cam=setup(body)
    OUT.mkdir(parents=True,exist_ok=True)
    images={}
    for name,raw in VIEWS.items():
        direction=raw.normalized()
        cam.location=focus+direction*.45
        cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.ortho_scale=scale
        target=OUT/f"{label}_{KEY}_{name}.png"
        sc.render.filepath=str(target);bpy.ops.render.render(write_still=True)
        images[name]=target.name
    center,extent=bounds(points)
    return {
        "owned_vertices":len(points),
        "center":[float(x) for x in center],
        "extent":[float(x) for x in extent],
        "images":images,
    }

if not BASE.is_file() or not CAND.is_file():
    raise SystemExit("Missing V13e or V15f Blend")

bpy.ops.wm.open_mainfile(filepath=str(BASE))
basebody=bpy.data.objects[BODY]
basepoints=owned_world(basebody)
focus,extent=bounds(basepoints)
scale=max(.105,max(extent.x,extent.y,extent.z)*1.65)

baseline=render_file(BASE,"V13e",focus,scale)
candidate=render_file(CAND,"V15f",focus,scale)
payload={
    "digit":KEY,
    "baseline":baseline,
    "candidate":candidate,
    "camera_focus_from_v13e":[float(x) for x in focus],
    "ortho_scale":float(scale),
    "views":{k:[float(x) for x in v] for k,v in VIEWS.items()},
    "promotion":"none",
}
META.parent.mkdir(parents=True,exist_ok=True)
META.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print("V15F_STAGE_B_VISUAL_META",META,flush=True)
