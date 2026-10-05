#!/usr/bin/env python3
"""Create a complete post-edit evidence workspace for one ORIGINAL-v1 candidate.

This is scaffold generation only. It never marks evidence PASS/CLEAR and never
edits a Blend. It copies immutable pre-edit declarations into the bundle and
creates draft post-edit execution records bound to the final candidate SHA.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
COUPLING=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json"
DEFECTS=ROOT/"ORIGINAL_V1_DEFECT_COUPLING_MAP.json"
ISSUES=ROOT/"ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"
WO_TEMPLATE=ROOT/"ORIGINAL_V1_WEIGHTS_ONLY_ACCEPTANCE_TEMPLATE.json"
COUPLING_TEMPLATE=ROOT/"ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json"
MOVEMENT_TEMPLATE=ROOT/"ORIGINAL_V1_MOVEMENT_COUPLING_EVIDENCE_TEMPLATE.json"
VISUAL_TEMPLATE=ROOT/"ORIGINAL_V1_CANDIDATE_SURFACE_VISUAL_REVIEW_TEMPLATE.json"
VISUAL_REQ=ROOT/"ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json"
COMPARE_TEMPLATE=ROOT/"ORIGINAL_V1_CANDIDATE_COMPARISON_MANIFEST_TEMPLATE.json"
EXEC_TEMPLATE=ROOT/"ORIGINAL_V1_REPAIR_EXECUTION_RECORD_TEMPLATE.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen: out.append(x); seen.add(x)
    return out

def build(package_ids,candidate,csha,source_branch,declaration_paths,outdir):
    if not re.fullmatch(r"r\d+[a-z]?",candidate,re.I): raise ValueError("candidate revision invalid")
    if not SHA_RE.fullmatch(csha): raise ValueError("final candidate SHA invalid")
    packages=read(PACKAGES); coupling=read(COUPLING); defects=read(DEFECTS)
    issue_ledger=read(ISSUES); wo=read(WO_TEMPLATE); ce=read(COUPLING_TEMPLATE)
    me=read(MOVEMENT_TEMPLATE); vr=read(VISUAL_TEMPLATE); visual_req=read(VISUAL_REQ)
    compare=read(COMPARE_TEMPLATE); exec_t=read(EXEC_TEMPLATE)
    pby={x["id"]:x for x in packages["packages"]}; cby={x["id"]:x for x in coupling["coupling_systems"]}
    unknown=[x for x in package_ids if x not in pby]
    if unknown: raise ValueError(f"unknown repair packages {unknown}")
    selected_cids=uniq([pby[x]["coupling_system_id"] for x in package_ids])
    region_ids=uniq([r for cid in selected_cids for r in cby[cid]["body_regions"]])
    selected_set=set(selected_cids)
    defect_ids=uniq([
        x["issue_id"] for x in defects["mappings"]
        if set(x["required_coupling_system_ids"]) and set(x["required_coupling_system_ids"]).issubset(selected_set)
    ])

    # Load and verify declarations cover every package before scaffold creation.
    declarations=[]
    for p in declaration_paths:
        path=Path(p)
        if not path.exists(): raise ValueError(f"declaration not found: {p}")
        obj=read(path)
        if obj.get("candidate_revision")!=candidate: raise ValueError(f"declaration revision differs: {p}")
        declarations.append((path,obj))
    covered={obj.get("repair_package_id") for _,obj in declarations}
    missing=sorted(set(package_ids)-covered)
    if missing: raise ValueError(f"missing pre-edit declarations for packages {missing}")

    if outdir.exists():
        if any(outdir.iterdir()): raise ValueError(f"output directory is not empty: {outdir}")
    else:
        outdir.mkdir(parents=True)

    # Immutable declaration copies + execution drafts.
    dec_dir=outdir/"declarations"; exe_dir=outdir/"execution_records"
    dec_rel=[]; exe_rel=[]
    for i,(src,obj) in enumerate(declarations,1):
        safe=f"{i:02d}_{obj.get('repair_package_id','package')}_{obj.get('side','side')}.json"
        dst=dec_dir/safe; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
        digest=hashlib.sha256(dst.read_bytes()).hexdigest()
        rel=dst.relative_to(outdir).as_posix(); dec_rel.append(rel)
        er=copy.deepcopy(exec_t); er["status"]="REPAIR_EXECUTION_RECORD_DRAFT"
        er["candidate_revision"]=candidate; er["source_branch"]=source_branch
        er["repair_package_id"]=obj.get("repair_package_id"); er["coupling_system_id"]=obj.get("coupling_system_id"); er["side"]=obj.get("side")
        er["repair_declaration_path"]=f"../declarations/{safe}"
        er["repair_declaration_sha256"]=digest
        er["pre_edit_candidate_sha256"]=obj.get("pre_edit_candidate_sha256") or obj.get("candidate_sha256")
        er["final_candidate_sha256"]=csha
        ep=exe_dir/f"{i:02d}_{obj.get('repair_package_id','package')}_{obj.get('side','side')}_execution.json"
        write(ep,er); exe_rel.append(ep.relative_to(outdir).as_posix())

    # Candidate ledgers: preserve parent history, update exact candidate identity.
    parent_ledger=copy.deepcopy(issue_ledger)
    candidate_ledger=copy.deepcopy(issue_ledger)
    parent_identity=copy.deepcopy(issue_ledger.get("candidate_under_review"))
    candidate_ledger["candidate_under_review"]={"revision":candidate,"sha256":csha}
    candidate_ledger["inherited_parent_candidate"]=parent_identity
    candidate_ledger["candidate_ledger_note"]="Inherited open/dispositioned issues from comparator; every closure must be re-evidenced against this exact candidate."
    write(outdir/"parent_issue_ledger.json",parent_ledger)
    write(outdir/"candidate_issue_ledger.json",candidate_ledger)

    # Weights-only review.
    wo["status"]="WEIGHTS_ONLY_ACCEPTANCE_IN_PROGRESS"; wo["candidate_revision"]=candidate; wo["candidate_sha256"]=csha; wo["source_branch"]=source_branch
    wo["scope_region_ids"]=region_ids
    for row in wo["regions"]:
        if row["id"] in region_ids:
            row["linked_defect_ids"]=[iid for iid in defect_ids]
    write(outdir/"weights_only_acceptance.json",wo)

    # Anatomical coupling review.
    ce["status"]="COUPLING_EVIDENCE_IN_PROGRESS"; ce["candidate_revision"]=candidate; ce["candidate_sha256"]=csha; ce["source_branch"]=source_branch
    for row in ce["systems"]:
        cid=row["coupling_system_id"]
        if cid in selected_cids:
            pkg=next(pby[p] for p in package_ids if pby[p]["coupling_system_id"]==cid)
            row["movement_families"]=list(pkg["proof_movements"])
            row["linked_defect_ids"]=[x["issue_id"] for x in defects["mappings"] if cid in x["required_coupling_system_ids"]]
    write(outdir/"anatomical_coupling_evidence.json",ce)

    # Per-sample movement coupling starts empty but exact-candidate bound.
    me["status"]="MOVEMENT_COUPLING_EVIDENCE_IN_PROGRESS"; me["candidate_revision"]=candidate; me["candidate_sha256"]=csha; me["source_branch"]=source_branch
    me["scope_coupling_system_ids"]=selected_cids
    write(outdir/"movement_coupling_evidence.json",me)

    # Human surface review prefilled with current applicable human refs.
    vr["status"]="CANDIDATE_SURFACE_VISUAL_REVIEW"; vr["candidate_revision"]=candidate; vr["candidate_sha256"]=csha; vr["source_branch"]=source_branch
    vr["scope_region_ids"]=region_ids
    vby={x["id"]:x for x in visual_req["regions"]}
    for row in vr["regions"]:
        if row["id"] in region_ids:
            row["human_evidence_ids"]=list(vby[row["id"]].get("current_visual_evidence_ids",[]))
    write(outdir/"surface_visual_review.json",vr)

    # Candidate comparison skeleton.
    compare["status"]="CANDIDATE_COMPARISON_MANIFEST"
    compare["candidate"]={"revision":candidate,"sha256":csha,"source_branch":source_branch,"issue_ledger_path":"candidate_issue_ledger.json"}
    compare["parent"]["issue_ledger_path"]="parent_issue_ledger.json"
    compare["scope"]={"repair_package_ids":package_ids,"coupling_system_ids":selected_cids,"region_ids":region_ids,"defect_ids":defect_ids}
    ev=compare["evidence"]
    ev["weights_only_acceptance_path"]="weights_only_acceptance.json"
    ev["anatomical_coupling_evidence_path"]="anatomical_coupling_evidence.json"
    ev["movement_coupling_evidence_path"]="movement_coupling_evidence.json"
    ev["repair_declaration_paths"]=dec_rel
    ev["repair_execution_record_paths"]=exe_rel
    ev["surface_visual_review_path"]="surface_visual_review.json"
    write(outdir/"candidate_comparison_manifest.json",compare)

    manifest={
      "schema_version":1,"status":"POST_EDIT_EVIDENCE_BUNDLE_INITIALIZED","production_approved":False,
      "candidate_revision":candidate,"candidate_sha256":csha,"source_branch":source_branch,
      "repair_package_ids":package_ids,"coupling_system_ids":selected_cids,"region_ids":region_ids,"defect_ids":defect_ids,
      "files":[
        "parent_issue_ledger.json","candidate_issue_ledger.json","weights_only_acceptance.json",
        "anatomical_coupling_evidence.json","movement_coupling_evidence.json","surface_visual_review.json",
        "candidate_comparison_manifest.json",*dec_rel,*exe_rel
      ],
      "next_steps":[
        "fill execution records with actual edited vertices/bones/operations and validate them",
        "run candidate-bound pose scope and build pose capture evidence plan",
        "capture weights-only and corrected motion evidence",
        "complete coupling and movement-coupling records",
        "complete surface visual review",
        "run regression/contact/change audits",
        "run unified candidate comparison; do not infer owner acceptance"
      ]
    }
    write(outdir/"bundle_manifest.json",manifest)
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packages",required=True,help="comma-separated repair package ids")
    ap.add_argument("--candidate",required=True)
    ap.add_argument("--sha256",required=True)
    ap.add_argument("--source-branch",required=True)
    ap.add_argument("--declarations",required=True,help="comma-separated pre-edit declaration paths")
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        package_ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        declaration_paths=[x.strip() for x in a.declarations.split(",") if x.strip()]
        if not package_ids or not declaration_paths: raise ValueError("packages and declarations are required")
        out=build(package_ids,a.candidate,a.sha256,a.source_branch,declaration_paths,Path(a.out_dir))
        print("POST-EDIT EVIDENCE BUNDLE: INITIALIZED")
        print(json.dumps({"candidate_revision":out["candidate_revision"],"packages":out["repair_package_ids"],"regions":out["region_ids"],"files":len(out["files"])},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
