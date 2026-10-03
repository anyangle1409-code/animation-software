#!/usr/bin/env python3
"""Verify and publish actual Phase 5 regional anatomy captures."""
from __future__ import annotations
import json,re,shutil
from pathlib import Path
from original_v1_production_control import ROOT,CAND,RC,digest,ensure_finite,read
CAPTURE_PLAN="ORIGINAL_V1_PHASE5_REGION_CAPTURE_PLAN.json";PHASE5_PLAN="ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json"
def load_capture_plan(root=ROOT):
    plan=read(root,CAPTURE_PLAN);p5=read(root,PHASE5_PLAN);ensure_finite(plan)
    if plan.get("schema_version")!=1 or plan.get("status")!="PREPARED_PHASE5_REGION_CAPTURE_PLAN" or plan.get("phase")!=5 or plan.get("production_approved") is not False or plan.get("dressed") is not False: raise ValueError("unexpected Phase 5 capture-plan contract")
    if set(plan.get("regions",{}))!=set(p5["order"]): raise ValueError("Phase 5 capture regions differ from execution plan")
    known={"neutral"}|set().union(*map(set,read(root,"ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json")["required_pose_groups"].values()))
    for region in p5["order"]:
        caps=plan["regions"][region].get("captures");ids=[x.get("id") for x in caps or []]
        if not caps or ids!=p5["regions"][region].get("required_views") or len(ids)!=len(set(ids)): raise ValueError(region+" capture IDs differ from anatomy required views")
        for row in caps:
            if row.get("pose") not in known: raise ValueError(region+" capture uses unknown pose")
            cam=row.get("camera",{})
            if cam.get("mode") not in ("fixed","anchors","hand_surface") or not isinstance(cam.get("orthographic_scale"),(int,float)) or cam["orthographic_scale"]<=0: raise ValueError(region+" invalid camera")
    return plan
def expected_files(plan,region): return {x["id"]:f"phase5_{region}_{x['id']}.png" for x in plan["regions"][region]["captures"]}
def verify_source_metadata(root,path,region,candidate_sha,plan):
    d=json.loads(path.read_text(encoding="utf-8"));ensure_finite(d);exp=expected_files(plan,region)
    if d.get("schema_version")!=1 or d.get("status")!="PHASE5_REGION_CAPTURE_COMPLETE" or d.get("region")!=region or d.get("candidate_sha256")!=candidate_sha: raise ValueError("regional capture identity differs")
    if d.get("production_approved") is not False or d.get("phase_complete") is not False or d.get("capture_plan_sha256")!=digest(root/CAPTURE_PLAN): raise ValueError("regional capture contract/hash differs")
    rows=d.get("images",[]);ids=[x.get("capture_id") for x in rows]
    if ids!=list(exp): raise ValueError("regional capture coverage/order differs")
    pose_by={x["id"]:x["pose"] for x in plan["regions"][region]["captures"]}
    for row in rows:
        cid=row["capture_id"];cap=row.get("capture",{})
        if row.get("file")!=exp[cid] or not re.fullmatch(r"[0-9a-f]{64}",str(row.get("sha256",""))) or cap.get("capture_id")!=cid or cap.get("region")!=region or cap.get("pose")!=pose_by[cid]: raise ValueError("regional capture row differs")
    return d
def publish(root,region,revision):
    if not re.fullmatch(r"5[A-G]",region) or not re.fullmatch(r"r\d+[a-z]?",revision,re.I): raise ValueError("valid region/revision required")
    plan=load_capture_plan(root);cp=root/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{revision}.json";cand=read(root,cp.relative_to(root).as_posix());sha=cand["candidate_sha256"]
    srcdir=root/RC/f"phase5_{region}_{revision}";src=srcdir/"render_source_manifest.json"
    if not src.is_file(): raise ValueError("regional raw capture manifest missing")
    data=verify_source_metadata(root,src,region,sha,plan);exp=expected_files(plan,region)
    for row in data["images"]:
        p=srcdir/row["file"]
        if not p.is_file() or digest(p)!=row["sha256"]: raise ValueError("regional raw PNG bytes differ")
    out=root/CAND/f"review/phase5_{region}_{revision}"
    if out.exists(): raise ValueError("regional published review output collision")
    out.mkdir(parents=True);by={x["capture_id"]:x for x in data["images"]};files=[]
    for cid,name in exp.items():
        dst=out/name;shutil.copyfile(srcdir/name,dst);files.append({"capture_id":cid,"output":dst.relative_to(root).as_posix(),"sha256":by[cid]["sha256"],"capture":by[cid]["capture"]})
    result={"schema_version":1,"phase":5,"region":region,"candidate_revision":revision,"candidate_sha256":sha,"candidate_manifest_sha256":digest(cp),"capture_plan_sha256":digest(root/CAPTURE_PLAN),"source_manifest":{"path":src.relative_to(root).as_posix(),"sha256":digest(src)},"owner_review":"pending","blocking":False,"phase_complete":False,"production_approved":False,"files":files,"note":"Actual regional anatomy renders; no acceptance inferred."}
    (out/"visual_review_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    lines=[f"# {revision} / {region} anatomy review","",f"Candidate SHA: `{sha}`","","EXPERIMENTAL — owner_review: pending — NON-BLOCKING.",""]
    for row in files: lines += [f"## {row['capture_id']}","",f"![{row['capture_id']}]({Path(row['output']).name})",""]
    (out/"README.md").write_text("\n".join(lines)+"\n",encoding="utf-8");return out
def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("region");ap.add_argument("revision");a=ap.parse_args()
    try: print("PHASE5 REGIONAL REVIEW READY",publish(ROOT,a.region,a.revision),"owner_review pending; NON-BLOCKING");return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc: print("STOP — "+str(exc));return 2
if __name__=="__main__": raise SystemExit(main())
