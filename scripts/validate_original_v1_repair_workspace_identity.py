#!/usr/bin/env python3
"""Verify a finalized repair workspace against the exact repaired Blend on disk."""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
SHA_RE=re.compile(r"^[0-9a-f]{64}$")

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workspace",required=True); ap.add_argument("--candidate",required=True)
    a=ap.parse_args()
    try:
        ws=Path(a.workspace); candidate=Path(a.candidate)
        fm=json.loads((ws/"workspace_finalization_manifest.json").read_text(encoding="utf-8"))
        if fm.get("status")!="POST_EDIT_WORKSPACE_FINALIZED": raise ValueError("workspace is not finalized")
        expected=str(fm.get("final_candidate_sha256",""))
        if not SHA_RE.fullmatch(expected): raise ValueError("workspace final SHA invalid")
        if not candidate.exists(): raise ValueError("candidate missing")
        got=digest(candidate)
        if got!=expected: raise ValueError(f"candidate/workspace SHA mismatch: expected {expected}; got {got}")
        print("REPAIR WORKSPACE FINAL CANDIDATE IDENTITY: PASS")
        print(json.dumps({"candidate_revision":fm.get("candidate_revision"),"final_candidate_sha256":got},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
