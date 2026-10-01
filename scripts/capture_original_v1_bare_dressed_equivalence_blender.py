"""Capture exact bare-vs-dressed underlying-body equivalence for ORIGINAL-v1 Phase 7.

Blender-only, read-only. For each frozen stress pose it compares the evaluated body
with the garment hidden versus garment visible while the dressed body-hide mask is
disabled in both states. No tolerance/quality threshold is invented: it records
whether the underlying body/rig/metrics are identical under the presentation toggle.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

import bpy
import numpy as np

ARGS=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(ARGS)!=2:raise SystemExit("STOP — usage: -- <fresh-output-dir> <rN>")
OUT=Path(ARGS[0]);REV=ARGS[1]
if not REV.startswith("r") or not REV[1:].isdigit():raise SystemExit("STOP — numbered revision required")
OUT.mkdir(parents=True,exist_ok=False)

ROOT=Path(__file__).resolve().parents[1]
POSE_SCRIPT=ROOT/"scripts/pose_test_original_v1_o4_candidate_blender.py"
SCRIPT=Path(__file__).resolve()
SOURCE=Path(bpy.data.filepath);MANIFEST=SOURCE.with_suffix(".json")


def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


if not SOURCE.is_file() or not MANIFEST.is_file():raise SystemExit("STOP — saved candidate Blend/manifest required")
source_sha=digest(SOURCE);manifest=json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
if manifest.get("candidate")!=SOURCE.name or manifest.get("candidate_sha256")!=source_sha:
    raise SystemExit("STOP — candidate manifest identity differs")
if f"_{REV}.blend" not in SOURCE.name:raise SystemExit("STOP — requested revision differs from opened Blend")

pose_source=OUT/"pose_source"
old=sys.argv[:]
try:
    sys.argv=[str(POSE_SCRIPT),"--",str(pose_source),"","--metrics-only"]
    ns=runpy.run_path(str(POSE_SCRIPT),run_name="__hgpt_equivalence_pose_source__")
finally:
    sys.argv=old

body=ns["body"];shorts=ns["shorts"];rig=ns["rig"];poses=ns["POSES"]
reset=ns["reset"];upd=ns["upd"];measure=ns["measure"];handle=ns["HANDLE"]
dress_mask=ns.get("DRESS_MASK")
if shorts is None or shorts.type!="MESH":raise SystemExit("STOP — named candidate garment required")
if len(rig.data.bones)!=63 or body.find_armature()!=rig or shorts.find_armature()!=rig:
    raise SystemExit("STOP — shared canonical 63-bone rig required")


def apply_pose(name):
    reset();rig.location=(0,0,0);rig.rotation_euler=(0,0,0);upd();handle.clear()
    for obj in [o for o in bpy.data.objects if o.name.startswith("REVIEW_HANDLE")]:
        bpy.data.objects.remove(obj)
    poses[name]();upd()


def set_state(garment_visible:bool):
    # Underlying body identity comparison: never delete/hide body vertices.
    if dress_mask is not None:
        dress_mask.show_viewport=False;dress_mask.show_render=False
    shorts.hide_viewport=not garment_visible;shorts.hide_render=not garment_visible
    upd()


def body_vertices():
    dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mw=ev.matrix_world
    return np.array([(mw@v.co)[:] for v in ev.data.vertices],dtype=float),len(ev.data.polygons)


def vertex_hash(vertices):
    rounded=np.round(vertices,9)
    return hashlib.sha256(rounded.tobytes(order="C")).hexdigest()


def pose_hash():
    payload=[{"name":p.name,"matrix":[[round(float(v),9) for v in row] for row in p.matrix]}
             for p in sorted(rig.pose.bones,key=lambda x:x.name)]
    return hashlib.sha256(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,separators=(",",":"),sort_keys=True).encode()).hexdigest()


rows=[]
for name in poses:
    apply_pose(name)
    set_state(False)
    bare, bare_faces=body_vertices();bare_pose=pose_hash();bare_metrics=measure(name)
    set_state(True)
    dressed,dressed_faces=body_vertices();dressed_pose=pose_hash();dressed_metrics=measure(name)

    same_shape=bare.shape==dressed.shape
    if same_shape and len(bare):
        distances=np.linalg.norm(dressed-bare,axis=1)*1000.0
        max_delta=float(distances.max());mean_delta=float(distances.mean());changed=int((distances>0).sum())
    else:
        max_delta=mean_delta=None;changed=None
    bh=vertex_hash(bare);dh=vertex_hash(dressed)
    bm=canonical_hash(bare_metrics);dm=canonical_hash(dressed_metrics)
    identical=(same_shape and bare_faces==dressed_faces and bh==dh and bare_pose==dressed_pose and bm==dm)
    rows.append({
        "pose":name,
        "status":"IDENTICAL" if identical else "DIFFERENT",
        "body_mask_disabled_both_states":dress_mask is not None,
        "bare":{"vertex_count":int(len(bare)),"face_count":int(bare_faces),"vertex_sha256_round9":bh,
                "pose_state_sha256":bare_pose,"metrics_sha256":bm},
        "dressed_presence":{"vertex_count":int(len(dressed)),"face_count":int(dressed_faces),"vertex_sha256_round9":dh,
                            "pose_state_sha256":dressed_pose,"metrics_sha256":dm},
        "max_vertex_delta_mm":max_delta,
        "mean_vertex_delta_mm":mean_delta,
        "changed_vertex_count_exact_float":changed,
    })

report={
    "schema_version":1,"status":"EVIDENCE_ONLY","phase_complete":False,"production_approved":False,
    "candidate_revision":REV,"candidate":SOURCE.name,"candidate_sha256":source_sha,
    "candidate_manifest_sha256":digest(MANIFEST),"rig_id":"hgpt_canonical_v4_original",
    "comparison_semantics":"same pose and same full underlying body; garment hidden vs visible; body dressed-mask disabled in both states",
    "pose_count":len(rows),"poses":rows,
    "source_pose_script":POSE_SCRIPT.relative_to(ROOT).as_posix(),"source_pose_script_sha256":digest(POSE_SCRIPT),
    "capture_script":SCRIPT.relative_to(ROOT).as_posix(),"capture_script_sha256":digest(SCRIPT),
    "source_git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
    "blender_version":bpy.app.version_string,"generated_utc":datetime.now(timezone.utc).isoformat(),
    "limits":[
        "Identity check only; it does not assess garment clearance, visual quality or contact legitimacy.",
        "The dressed body-hide mask is disabled in both states so topology deletion cannot masquerade as body deformation.",
        "IDENTICAL means rounded evaluated body coordinates, rig pose hash and body metrics are equal under garment visibility toggle."
    ]
}
(OUT/"bare_dressed_equivalence.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("BARE/DRESSED BODY EQUIVALENCE CAPTURED — EVIDENCE_ONLY")
