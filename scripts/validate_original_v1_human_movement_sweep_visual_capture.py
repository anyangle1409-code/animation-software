#!/usr/bin/env python3
"""Validate exact-candidate visual capture manifests for human movement sweeps."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def resolve(base,p):
    q=Path(p); return q if q.is_absolute() else base/q

def validate(d,base,require_complete=False):
    plan=read(PLAN)
    if d.get("schema_version")!=1: raise ValueError("schema_version must be 1")
    if d.get("production_approved") is not False: raise ValueError("visual capture may not claim production approval")
    if not re.fullmatch(r"r\d+[a-z]?",str(d.get("candidate_revision","")),re.I): raise ValueError("candidate_revision invalid")
    csha=str(d.get("candidate_sha256",""))
    if not SHA_RE.fullmatch(csha): raise ValueError("candidate_sha256 invalid")
    sweep=d.get("sweep_id")
    if sweep not in plan.get("sweeps",{}): raise ValueError("unknown sweep_id")
    authority=plan["sweeps"][sweep]
    expected_labels=list(authority.get("samples") or [])
    rows=d.get("samples") or []
    if require_complete and [x.get("label") for x in rows]!=expected_labels:
        raise ValueError("visual sample order/coverage differs")
    if rows and [x.get("label") for x in rows]!=expected_labels[:len(rows)]:
        raise ValueError("visual samples must follow authoritative order")
    required_cameras=list(authority.get("cameras") or [])
    for row in rows:
        label=row["label"]
        views=row.get("views") or []
        camera_ids=[x.get("camera_id") for x in views]
        if len(camera_ids)!=len(set(camera_ids)): raise ValueError(f"{label}: duplicate camera ids")
        if require_complete and set(camera_ids)!=set(required_cameras):
            raise ValueError(f"{label}: required camera coverage differs")
        unknown=set(camera_ids)-set(required_cameras)
        if unknown: raise ValueError(f"{label}: unknown cameras {sorted(unknown)}")
        for rec in views:
            camera=rec.get("camera_id"); path=rec.get("path"); digest=rec.get("sha256")
            if not camera or not path or not SHA_RE.fullmatch(str(digest or "")):
                raise ValueError(f"{label}: invalid visual capture record")
            p=resolve(base,path)
            if not p.is_file(): raise ValueError(f"{label}/{camera}: image missing {path}")
            if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
                raise ValueError(f"{label}/{camera}: image SHA mismatch")
            cap=rec.get("capture") or {}
            if cap.get("candidate_sha256")!=csha: raise ValueError(f"{label}/{camera}: candidate identity mismatch")
            if cap.get("sweep_id")!=sweep or cap.get("sample_label")!=label or cap.get("camera_id")!=camera:
                raise ValueError(f"{label}/{camera}: capture identity mismatch")
            if not cap.get("runner_script_sha256") or not SHA_RE.fullmatch(str(cap.get("runner_script_sha256"))):
                raise ValueError(f"{label}/{camera}: runner hash missing")
            if not cap.get("camera_matrix_world") or not cap.get("resolution"):
                raise ValueError(f"{label}/{camera}: camera metadata incomplete")
    review=d.get("engineering_review")
    if review not in {"PENDING","PASS","FAIL"}: raise ValueError("engineering_review invalid")
    if d.get("owner_review") not in {"PENDING","PASS","FAIL"}: raise ValueError("owner_review invalid")
    if require_complete and review!="PASS": raise ValueError("complete visual capture requires engineering review PASS")
    return {"sweep_id":sweep,"candidate_sha256":csha,"samples":len(rows),"engineering_review":review}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("manifest"); ap.add_argument("--require-complete",action="store_true")
    a=ap.parse_args(); p=Path(a.manifest)
    try:
        out=validate(read(p),p.parent,a.require_complete)
        print("HUMAN SWEEP VISUAL CAPTURE: PASS"); print(json.dumps(out,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
