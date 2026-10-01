"""Create deterministic first-party PGM QA masks from the current Blender scene.

The current pose/camera must already match the supplied source PNG. This script
projects evaluated triangles through the active camera and uses the project-owned
z-buffer rasterizer. It does not save or alter the scene.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_v1_garment_evidence import capture,NAMES
from original_v1_mask_raster import rasterize,write_p5,read_png_dimensions
from original_v1_production_control import digest,ensure_finite

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument("source_image",type=Path)
ap.add_argument("out_dir",type=Path)
ap.add_argument("--dressed",action="store_true")
ap.add_argument("--equipment-object",action="append",default=[])
args=ap.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])

source=args.source_image.resolve();out=args.out_dir.resolve()
if not source.is_relative_to(ROOT.resolve()) or not source.is_file():raise SystemExit("STOP — source PNG must exist inside repository")
if not out.is_relative_to(ROOT.resolve()) or out.exists():raise SystemExit("STOP — mask output must be a fresh repository folder")

HAND_TOKENS=("hand","thumb","index","middle","ring","pinky","metacarpal")
FOOT_TOKENS=("foot","toe")


def side_role(group_names,tokens):
    roles=set()
    for name in group_names:
        low=name.lower()
        if not any(token in low for token in tokens):continue
        if low.endswith("_l") or low.endswith(".l"):roles.add("l")
        if low.endswith("_r") or low.endswith(".r"):roles.add("r")
    return roles


def triangles_for(obj,base_roles,region_roles=False):
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    try:
        mesh.calc_loop_triangles()
        group_names={g.index:g.name for g in evaluated.vertex_groups}
        camera=bpy.context.scene.camera
        camera_inv=camera.matrix_world.inverted()
        rows=[]
        for tri in mesh.loop_triangles:
            labels=set(base_roles)
            if region_roles:
                names=set()
                for vid in tri.vertices:
                    for membership in mesh.vertices[vid].groups:
                        name=group_names.get(membership.group)
                        if name:names.add(name)
                hs=side_role(names,HAND_TOKENS);fs=side_role(names,FOOT_TOKENS)
                if "l" in hs:labels.add("hand_l")
                if "r" in hs:labels.add("hand_r")
                if "l" in fs:labels.add("foot_l")
                if "r" in fs:labels.add("foot_r")
            points=[]
            valid=True
            for vid in tri.vertices:
                world=evaluated.matrix_world @ mesh.vertices[vid].co
                camera_local=camera_inv @ world
                depth=-float(camera_local.z)
                if depth<=1e-6:
                    valid=False;break
                co=world_to_camera_view(bpy.context.scene,camera,world)
                points.append([float(co.x)*WIDTH,(1.0-float(co.y))*HEIGHT,depth])
            if valid:rows.append({"points":points,"roles":sorted(labels)})
        return rows
    finally:
        evaluated.to_mesh_clear()


try:
    raw=capture(bpy,"body")
    if args.dressed:
        garment_raw=capture(bpy,"garment")
        if garment_raw["candidate_sha256"]!=raw["candidate_sha256"]:raise ValueError("garment candidate differs")
    camera=bpy.context.scene.camera
    if camera is None:raise ValueError("active scene camera required")
    WIDTH,HEIGHT=read_png_dimensions(source)
    render=bpy.context.scene.render
    expected_w=round(render.resolution_x*render.resolution_percentage/100)
    expected_h=round(render.resolution_y*render.resolution_percentage/100)
    if (WIDTH,HEIGHT)!=(expected_w,expected_h):
        raise ValueError(f"source PNG dimensions {(WIDTH,HEIGHT)} differ from current render {(expected_w,expected_h)}")

    body=bpy.data.objects.get(NAMES["body"])
    if body is None:raise ValueError("body object missing")
    triangles=triangles_for(body,["subject","body"],True)
    if args.dressed:
        garment=bpy.data.objects.get(NAMES["garment"])
        if garment is None:raise ValueError("garment object missing")
        triangles.extend(triangles_for(garment,["subject","garment"],False))
    equipment_names=[]
    for name in args.equipment_object:
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!="MESH":raise ValueError("equipment mesh missing: "+name)
        equipment_names.append(name);triangles.extend(triangles_for(obj,["equipment"],False))

    result=rasterize(triangles,WIDTH,HEIGHT)
    expected_roles=["subject","body","hand_l","hand_r","foot_l","foot_r"]
    if args.dressed:expected_roles.append("garment")
    if equipment_names:expected_roles.append("equipment")
    out.mkdir(parents=True)
    masks=[]
    for role in expected_roles:
        pixels=result["masks"].get(role,bytearray(WIDTH*HEIGHT))
        path=out/(role+".pgm");write_p5(path,WIDTH,HEIGHT,pixels)
        masks.append({"role":role,"path":path.relative_to(ROOT).as_posix(),"sha256":digest(path),
                      "pixel_count":sum(v>0 for v in pixels)})

    bundle={
        "schema_version":1,"status":"MASK_CAPTURE_EVIDENCE","phase_complete":False,"production_approved":False,
        "candidate_sha256":raw["candidate_sha256"],"source_candidate":raw["source_candidate"],
        "source_image":{"path":source.relative_to(ROOT).as_posix(),"sha256":digest(source),"width":WIDTH,"height":HEIGHT},
        "dressed":bool(args.dressed),"equipment_objects":equipment_names,
        "camera":{"name":camera.name,"matrix_world":[list(row) for row in camera.matrix_world],
                  "type":camera.data.type,"lens":float(camera.data.lens),"ortho_scale":float(camera.data.ortho_scale)},
        "render":{"resolution_x":expected_w,"resolution_y":expected_h,"engine":bpy.context.scene.render.engine},
        "masks":masks,
        "triangle_count":len(triangles),"visible_pixel_count":result["visible_pixel_count"],
        "rasterizer":{"path":"scripts/original_v1_mask_raster.py","sha256":digest(ROOT/"scripts/original_v1_mask_raster.py")},
        "capture_script":{"path":"scripts/capture_original_v1_visual_qa_masks_blender.py",
                          "sha256":digest(ROOT/"scripts/capture_original_v1_visual_qa_masks_blender.py")},
        "source_git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "capture_command":list(sys.argv),"generated_utc":datetime.now(timezone.utc).isoformat(),
        "limits":[
            "Source scene must still be at the exact pose/camera used for the source PNG.",
            "Near-plane-crossing triangles are omitted rather than clipped; normal review cameras should keep the character fully in front of the near plane.",
            "Hand/foot roles derive from evaluated deform-group names; zero-pixel masks remain explicit evidence and can be caught by the visual-QA visibility detector.",
            "This is Blender/model-side mask evidence. Final Phase 11 runtime masks must bind the exact Phase 10 runtime frame/commit."
        ]
    }
    ensure_finite(bundle)
    manifest=out/"mask_bundle.json"
    manifest.write_text(json.dumps(bundle,indent=2)+"\n",encoding="utf-8")
    print("VISUAL QA MASK BUNDLE WRITTEN",manifest)
except (OSError,ValueError,KeyError,TypeError,ArithmeticError,subprocess.SubprocessError) as exc:
    raise SystemExit("STOP — "+str(exc))
