#!/usr/bin/env python3
"""Non-Blender pre-edit readiness gate for a fresh shoulder-foundation candidate."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from original_v1_shoulder_acceptance import validate_contract
from original_v1_shoulder_foundation_declaration import validate_declaration,ISSUES
from original_v1_whole_body_issues import validate_ledger
from validate_original_v1_human_evidence import validate_manifest
ROOT=Path(__file__).resolve().parents[1]
def assess(contract,declaration,ledger,human):
 e=[]
 e += ["contract: "+x for x in validate_contract(contract)]
 e += ["declaration: "+x for x in validate_declaration(declaration)]
 e += ["ledger: "+x for x in validate_ledger(ledger)]
 e += ["human evidence: "+x for x in validate_manifest(human)]
 rows={x.get("id"):x for x in ledger.get("issues",[]) if isinstance(x,dict)}
 for issue in sorted(ISSUES):
  if issue not in rows:e.append("linked issue missing from ledger: "+issue)
  elif rows[issue].get("state") not in ("Open","In Progress","Pending Review"):e.append("pre-edit linked issue unexpectedly closed: "+issue)
 ids={x.get("id") for x in human.get("entries",[]) if isinstance(x,dict)}
 for issue in sorted(ISSUES):
  row=rows.get(issue,{})
  for eid in row.get("human_evidence_ids",[]):
   if eid not in ids:e.append("linked human evidence missing: "+issue+" -> "+str(eid))
 return {"schema_version":1,"ready":not e,"production_approved":False,"errors":list(dict.fromkeys(e)),
 "target_revision":declaration.get("target_revision"),"parent":declaration.get("parent"),
 "next":"BLENDER_FOUNDATION_EDIT_ALLOWED" if not e else "STOP"}
def load(p):return json.loads(p.read_text(encoding="utf-8-sig"))
def main():
 ap=argparse.ArgumentParser();ap.add_argument("declaration",type=Path);ap.add_argument("--out",type=Path);a=ap.parse_args()
 try:r=assess(load(ROOT/"ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json"),load(a.declaration),load(ROOT/"ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"),load(ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"))
 except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:r={"schema_version":1,"ready":False,"production_approved":False,"errors":[str(exc)],"next":"STOP"}
 payload=json.dumps(r,indent=2)+"\n"
 if a.out:
  if a.out.exists():raise SystemExit("STOP — output collision")
  a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(payload,encoding="utf-8")
 print(payload,end="");return 0 if r["ready"] else 1
if __name__=="__main__":raise SystemExit(main())
