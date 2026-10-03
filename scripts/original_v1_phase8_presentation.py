#!/usr/bin/env python3
"""Verify ORIGINAL-v1 Phase 8 numeric material and presentation scene evidence.

No render quality, anatomy visibility or owner acceptance is inferred.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite
from original_v1_locked_rig import load_locked_rig
from verify_original_v1_production_promotion import safe_path

TEMPLATE="ORIGINAL_V1_PHASE8_MATERIAL_PROVENANCE_TEMPLATE.json"
HELPER="scripts/original_v1_phase8_presentation.py"
CAPTURE="scripts/capture_original_v1_presentation_scene_blender.py"


def verify_ref(root:Path,ref:dict,label:str)->None:
    if not isinstance(ref,dict) or not ref.get("path") or not re.fullmatch(r"[0-9a-f]{64}",str(ref.get("sha256",""))):
        raise ValueError(label+" path/SHA-256 required")
    p=safe_path(root,ref["path"])
    if not p.is_file() or digest(p)!=ref["sha256"]:raise ValueError(label+" bytes differ")


def material_assignments(scene:dict):
    scopes={}
    material_rows={}
    for scope in ("body","garment"):
        slots=scene.get("materials",{}).get(scope)
        if not isinstance(slots,list):raise ValueError(scope+" material slots missing")
        for slot in slots:
            mat=slot.get("material") if isinstance(slot,dict) else None
            if mat is None:continue
            name=mat.get("name")
            if not isinstance(name,str) or not name:raise ValueError("material name missing")
            scopes.setdefault(name,set()).add(scope)
            if name in material_rows and material_rows[name]!=mat:raise ValueError("same material name has inconsistent captured state")
            material_rows[name]=mat
    return scopes,material_rows


def node_images(tree:dict):
    images=[]
    if not isinstance(tree,dict):return images
    for node in tree.get("nodes",[]):
        if isinstance(node,dict) and node.get("image") is not None:images.append(node["image"])
        if isinstance(node,dict):
            for inp in node.get("inputs",[]):
                default=inp.get("default",{}) if isinstance(inp,dict) else {}
                if isinstance(default,dict) and "unserialized" in default:
                    images.append({"unserialized_socket":node.get("name"),"input":inp.get("name")})
    images.extend(tree.get("images",[]) if isinstance(tree.get("images",[]),list) else [])
    return images


def validate_provenance(root:Path,record:dict,candidate:str,scopes:dict)->list[str]:
    issues=[]
    if record.get("schema_version")!=1 or record.get("status")!="MATERIAL_PROVENANCE_COMPLETE":
        issues.append("material provenance identity/status differs")
    if record.get("phase")!=8 or record.get("phase_complete") is not False or record.get("production_approved") is not False:
        issues.append("material provenance cannot claim phase/production completion")
    if record.get("candidate_sha256")!=candidate:issues.append("material provenance candidate differs")
    policy=record.get("policy")
    expected={"numeric_materials_only":True,"third_party_textures_allowed":False,"external_hdri_allowed":False,
              "linked_material_libraries_allowed":False,"geometry_or_weight_changes_allowed":False}
    if not isinstance(policy,dict):
        issues.append("material policy missing")
    else:
        for k,v in expected.items():
            if policy.get(k) is not v:issues.append("material policy "+k+" differs")
    rows=record.get("materials")
    if not isinstance(rows,list):return issues+["material provenance rows missing"]
    by_name={}
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get("name"),str) or not row["name"]:
            issues.append("invalid material provenance row");continue
        if row["name"] in by_name:issues.append("duplicate material provenance name");continue
        by_name[row["name"]]=row
        assigned=row.get("assigned_scope")
        expected_scopes=sorted(scopes.get(row["name"],set()))
        actual_scopes=sorted(assigned if isinstance(assigned,list) else [assigned] if isinstance(assigned,str) else [])
        if actual_scopes!=expected_scopes:issues.append(row["name"]+": assigned scope differs from scene")
        for key,expected_value in (("independent_authorship",True),("numeric_only",True),
                                   ("third_party_content",False),("external_image_sources",False)):
            if row.get(key) is not expected_value:issues.append(row["name"]+": "+key+" differs")
        refs=row.get("operation_evidence")
        if not isinstance(refs,list) or not refs:issues.append(row["name"]+": operation evidence required")
        else:
            for ref in refs:
                try:verify_ref(root,ref,row["name"]+" material evidence")
                except (OSError,ValueError,KeyError,TypeError) as exc:issues.append(str(exc))
    if set(by_name)!=set(scopes):issues.append("material provenance set differs from assigned scene materials")
    return list(dict.fromkeys(issues))


def verify_scene(root:Path,scene:dict,provenance:dict,manifest:dict)->dict:
    candidate=manifest.get("candidate_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}",str(candidate or "")):raise ValueError("candidate manifest SHA invalid")
    if scene.get("candidate_sha256")!=candidate:raise ValueError("presentation scene candidate differs")
    if scene.get("status")!="EVIDENCE_ONLY" or scene.get("phase_complete") is not False or scene.get("production_approved") is not False:
        raise ValueError("presentation scene status differs")
    locked=load_locked_rig(root)
    expected_lock={"revision":locked["revision"],"rig_structure_sha256":locked["rig_structure_sha256"],
                   "bone_count":locked["bone_count"],"deform_bone_count":locked["deform_bone_count"],
                   "lock":locked["lock"],"payload":locked["payload"]}
    if scene.get("rig_id")!=locked["identity"] or scene.get("locked_rig")!=expected_lock:
        raise ValueError("presentation locked rev2c rig identity differs")
    if scene.get("capture_script")!={"path":CAPTURE,"sha256":digest(root/CAPTURE)}:
        raise ValueError("presentation capture-script identity differs")
    if not re.fullmatch(r"[0-9a-f]{40}",str(scene.get("source_git_commit",""))):
        raise ValueError("presentation source Git commit missing/invalid")
    blockers=[]
    if scene.get("scene_linked_libraries"):blockers.append("scene contains linked external libraries")
    scopes,materials=material_assignments(scene)
    for name,mat in materials.items():
        if mat.get("library"):blockers.append(name+": linked material library present")
        if node_images(mat.get("node_tree",{})):blockers.append(name+": image/unserialized shader input present")
    world=scene.get("world")
    if isinstance(world,dict):
        if world.get("library"):blockers.append("world is linked from external library")
        if node_images(world.get("node_tree",{})):blockers.append("world contains image/HDRI or unresolved input")
    for light in scene.get("lights",[]):
        if light.get("library") or light.get("data_library"):blockers.append("linked external light present: "+str(light.get("object")))
    for cam in scene.get("cameras",[]):
        if cam.get("library") or cam.get("data_library"):blockers.append("linked external camera present: "+str(cam.get("object")))
    if not isinstance(scene.get("render"),dict) or not isinstance(scene.get("colour_management"),dict):
        blockers.append("renderer/colour-management state missing")
    if not isinstance(scene.get("cameras"),list) or not scene["cameras"] or not scene.get("active_camera"):
        blockers.append("active presentation camera missing")
    blockers.extend(validate_provenance(root,provenance,candidate,scopes))
    result={
        "schema_version":1,"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
        "candidate_sha256":candidate,
        "material_scene_status":"BLOCKED" if blockers else "EVIDENCE_COMPLETE",
        "blockers":list(dict.fromkeys(blockers)),
        "material_names":sorted(materials),
        "render_state":scene.get("render"),
        "colour_management":scene.get("colour_management"),
        "active_camera":scene.get("active_camera"),
        "light_count":len(scene.get("lights",[])) if isinstance(scene.get("lights"),list) else None,
        "unresolved_phase8_domains":[
            "actual app-distance bare/dressed render capture",
            "readability review under declared viewing conditions",
            "no-concealed-body-failures review",
            "unchanged geometry/weight audit",
            "published owner-facing review snapshot"
        ],
        "limits":"Numeric material/provenance/presentation-state evidence only. A readable or attractive render is not inferred."
    }
    ensure_finite(result);return result


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene-capture",type=Path,required=True)
    ap.add_argument("--material-provenance",type=Path,required=True)
    ap.add_argument("--candidate-manifest",type=Path,required=True)
    ap.add_argument("--json-out",type=Path,required=True)
    args=ap.parse_args()
    try:
        if args.json_out.exists():raise ValueError("Phase 8 output collision")
        loaded=[]
        for p,label in ((args.scene_capture,"scene"),(args.material_provenance,"provenance"),(args.candidate_manifest,"manifest")):
            path=p.resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():raise ValueError(label+" missing/outside repository")
            data=json.loads(path.read_text(encoding="utf-8-sig"));ensure_finite(data);loaded.append((path,data))
        scene,manifest=loaded[0][1],loaded[2][1]
        manifest_path=loaded[2][0]
        if scene.get("source_candidate_manifest")!={"file":manifest_path.name,"sha256":digest(manifest_path)}:
            raise ValueError("presentation candidate-manifest identity differs")
        result=verify_scene(ROOT,scene,loaded[1][1],manifest)
        result["source_evidence"]=[{"path":p.relative_to(ROOT).as_posix(),"sha256":digest(p)} for p,_ in loaded]
        result["provenance_template"]={"path":TEMPLATE,"sha256":digest(ROOT/TEMPLATE)}
        result["verifier"]={"path":HELPER,"sha256":digest(ROOT/HELPER)}
        result["source_git_commit"]=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        result["generated_utc"]=datetime.now(timezone.utc).isoformat()
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("PHASE 8 MATERIAL/PRESENTATION",result["material_scene_status"],"— evidence only")
        return 0 if result["material_scene_status"]=="EVIDENCE_COMPLETE" else 1
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
