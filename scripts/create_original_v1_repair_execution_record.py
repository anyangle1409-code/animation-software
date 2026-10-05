#!/usr/bin/env python3
"""Create a draft post-edit repair execution record from an immutable declaration."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"ORIGINAL_V1_REPAIR_EXECUTION_RECORD_TEMPLATE.json"
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--declaration",required=True)
    ap.add_argument("--final-sha",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    try:
        dp=Path(args.declaration)
        if not dp.exists(): raise ValueError("declaration not found")
        if not SHA_RE.fullmatch(args.final_sha): raise ValueError("final SHA invalid")
        dec=read(dp); t=read(TEMPLATE)
        pre=str(dec.get("pre_edit_candidate_sha256") or dec.get("candidate_sha256") or "")
        if not SHA_RE.fullmatch(pre): raise ValueError("declaration pre-edit SHA invalid")
        t["status"]="REPAIR_EXECUTION_RECORD_DRAFT"
        t["candidate_revision"]=dec.get("candidate_revision")
        t["source_branch"]=dec.get("source_branch")
        t["repair_package_id"]=dec.get("repair_package_id")
        t["coupling_system_id"]=dec.get("coupling_system_id")
        t["side"]=dec.get("side")
        t["repair_declaration_path"]=str(dp)
        t["repair_declaration_sha256"]=hashlib.sha256(dp.read_bytes()).hexdigest()
        t["pre_edit_candidate_sha256"]=pre
        t["final_candidate_sha256"]=args.final_sha
        out=Path(args.out)
        if out.exists(): raise ValueError(f"refusing to overwrite {out}")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(t,indent=2)+"\n",encoding="utf-8")
        print("REPAIR EXECUTION RECORD DRAFT WRITTEN",out)
        print(json.dumps({
          "candidate_revision":t["candidate_revision"],
          "repair_package_id":t["repair_package_id"],
          "coupling_system_id":t["coupling_system_id"],
          "pre_edit_candidate_sha256":pre,
          "final_candidate_sha256":args.final_sha
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
