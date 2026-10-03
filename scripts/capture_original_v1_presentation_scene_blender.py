"""Read-only Phase 8 numeric material / presentation scene capture.

Records body/garment shader graphs and numeric values, scene world, lights, cameras,
renderer and colour management. Never saves the Blend or changes presentation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from original_v1_garment_evidence import capture,NAMES
from original_v1_production_control import digest,ensure_finite

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=1: raise SystemExit("STOP — expected one fresh output JSON")
out=Path(args[0])
if out.exists(): raise SystemExit("STOP — output already exists")


def scalar(value):
    if value is None or isinstance(value,(bool,int,str)): return value
    if isinstance(value,float):
        if not math.isfinite(value): raise ValueError("non-finite presentation value")
        return value
    if hasattr(value,"to_list"): return value.to_list()
    try:
        values=list(value)
        if all(isinstance(x,(bool,int,float,str)) for x in values):
            return [scalar(x) for x in values]
    except TypeError:
        pass
    raise TypeError(type(value).__name__)


def socket_value(sock):
    if not hasattr(sock,"default_value"):
        return {"available":False}
    try:
        return {"available":True,"value":scalar(sock.default_value)}
    except (TypeError,ValueError) as exc:
        return {"available":True,"unserialized":type(sock.default_value).__name__,"reason":str(exc)}


def image_ref(image):
    if image is None:return None
    return {
        "name":image.name,
        "library":image.library.filepath if image.library else None,
        "filepath":image.filepath,
        "packed":image.packed_file is not None,
        "source":image.source,
        "colorspace":image.colorspace_settings.name,
    }


def node_tree_receipt(tree):
    if tree is None:return {"nodes":[],"links":[]}
    nodes=[]
    images=[]
    for node in tree.nodes:
        row={
            "name":node.name,"type":node.type,"bl_idname":node.bl_idname,
            "mute":bool(node.mute),"label":node.label,
            "inputs":[{"name":s.name,"identifier":s.identifier,"default":socket_value(s)} for s in node.inputs],
        }
        if hasattr(node,"image"):
            img=image_ref(getattr(node,"image",None))
            if img is not None:
                row["image"]=img;images.append(img)
        nodes.append(row)
    links=[{
        "from_node":l.from_node.name,"from_socket":l.from_socket.identifier,
        "to_node":l.to_node.name,"to_socket":l.to_socket.identifier
    } for l in tree.links]
    return {"nodes":nodes,"links":links,"images":images}


def material_receipt(mat):
    return {
        "name":mat.name,
        "library":mat.library.filepath if mat.library else None,
        "use_nodes":bool(mat.use_nodes),
        "diffuse_color":list(mat.diffuse_color),
        "metallic":float(getattr(mat,"metallic",0.0)),
        "roughness":float(getattr(mat,"roughness",0.0)),
        "node_tree":node_tree_receipt(mat.node_tree if mat.use_nodes else None),
    }


def object_materials(obj):
    rows=[]
    for index,slot in enumerate(obj.material_slots):
        rows.append({
            "slot_index":index,
            "slot_name":slot.name,
            "material":material_receipt(slot.material) if slot.material else None,
        })
    return rows


def light_receipt(obj):
    data=obj.data
    return {
        "object":obj.name,"library":obj.library.filepath if obj.library else None,
        "data_library":data.library.filepath if data.library else None,
        "type":data.type,"energy":float(data.energy),"color":list(data.color),
        "matrix_world":[list(r) for r in obj.matrix_world],
        "shadow_soft_size":float(getattr(data,"shadow_soft_size",0.0)),
        "size":float(getattr(data,"size",0.0)) if hasattr(data,"size") else None,
        "spot_size":float(getattr(data,"spot_size",0.0)) if hasattr(data,"spot_size") else None,
    }


def camera_receipt(obj):
    data=obj.data
    return {
        "object":obj.name,"library":obj.library.filepath if obj.library else None,
        "data_library":data.library.filepath if data.library else None,
        "type":data.type,"lens":float(data.lens),"ortho_scale":float(data.ortho_scale),
        "clip_start":float(data.clip_start),"clip_end":float(data.clip_end),
        "sensor_width":float(data.sensor_width),
        "matrix_world":[list(r) for r in obj.matrix_world],
    }


try:
    body_raw=capture(bpy,"body");garment_raw=capture(bpy,"garment")
    if body_raw["candidate_sha256"]!=garment_raw["candidate_sha256"]:raise ValueError("body/garment candidate differs")
    body=bpy.data.objects.get(NAMES["body"]);garment=bpy.data.objects.get(NAMES["garment"])
    if body is None or garment is None:raise ValueError("body/garment objects missing")
    scene=bpy.context.scene
    world=scene.world
    world_receipt=None
    if world:
        world_receipt={
            "name":world.name,"library":world.library.filepath if world.library else None,
            "color":list(world.color),"use_nodes":bool(world.use_nodes),
            "node_tree":node_tree_receipt(world.node_tree if world.use_nodes else None),
        }
    view=scene.view_settings
    display=scene.display_settings
    render=scene.render
    image=render.image_settings
    result={
        "schema_version":1,"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
        "candidate_sha256":body_raw["candidate_sha256"],"source_candidate":body_raw["source_candidate"],
        "rig_id":body_raw["rig_id"],"locked_rig":body_raw.get("locked_rig"),"blender_version":bpy.app.version_string,
        "materials":{"body":object_materials(body),"garment":object_materials(garment)},
        "world":world_receipt,
        "lights":[light_receipt(o) for o in sorted((x for x in scene.objects if x.type=="LIGHT"),key=lambda x:x.name)],
        "cameras":[camera_receipt(o) for o in sorted((x for x in scene.objects if x.type=="CAMERA"),key=lambda x:x.name)],
        "active_camera":scene.camera.name if scene.camera else None,
        "render":{
            "engine":scene.render.engine,
            "resolution_x":render.resolution_x,"resolution_y":render.resolution_y,
            "resolution_percentage":render.resolution_percentage,
            "film_transparent":bool(render.film_transparent),
            "image_file_format":image.file_format,"image_color_mode":image.color_mode,
        },
        "colour_management":{
            "display_device":display.display_device,
            "view_transform":view.view_transform,
            "look":view.look,
            "exposure":float(view.exposure),"gamma":float(view.gamma),
            "use_curve_mapping":bool(view.use_curve_mapping),
        },
        "scene_linked_libraries":sorted(lib.filepath for lib in bpy.data.libraries),
        "source_candidate_manifest":body_raw["source_candidate_manifest"],
        "capture_script":{"path":"scripts/capture_original_v1_presentation_scene_blender.py",
                          "sha256":digest(ROOT/"scripts/capture_original_v1_presentation_scene_blender.py")},
        "source_git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "capture_command":list(sys.argv),"generated_utc":datetime.now(timezone.utc).isoformat(),
        "limits":[
            "Scene/material state only; app-distance readability requires real render review.",
            "Image nodes/references are captured so the numeric-only Phase 8 verifier can reject them.",
            "No geometry/weight equality or phase completion is inferred.",
        ],
    }
    ensure_finite(result)
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as handle:handle.write(json.dumps(result,indent=2)+"\n")
    print("PHASE 8 PRESENTATION SCENE EVIDENCE WRITTEN — EVIDENCE_ONLY")
except (OSError,ValueError,KeyError,TypeError,ArithmeticError,subprocess.SubprocessError) as exc:
    raise SystemExit("STOP — "+str(exc))
