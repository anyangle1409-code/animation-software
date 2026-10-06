#!/usr/bin/env python3
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/"coordination"
HEX40=re.compile(r"^[0-9a-f]{40}$",re.I); HEX64=re.compile(r"^[0-9a-f]{64}$",re.I)
def load(p):
    try:return json.loads(p.read_text())
    except Exception as e: raise SystemExit(f"FAIL — cannot read {p}: {e}")
def valid_identity(x):
    for k in ("candidate_id","candidate_commit","candidate_sha256"):
        if not x.get(k): raise SystemExit("FAIL — missing "+k)
    if not HEX40.match(x["candidate_commit"]):raise SystemExit("FAIL — invalid candidate_commit")
    if not HEX64.match(x["candidate_sha256"]):raise SystemExit("FAIL — invalid candidate_sha256")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--ready",action="store_true");ap.add_argument("--response",choices=["fail","pass"]);ap.add_argument("--candidate-file");a=ap.parse_args()
    ready_path=C/"MODEL_CANDIDATE_READY.json"
    if not ready_path.exists():raise SystemExit("BLOCKED — no MODEL_CANDIDATE_READY.json")
    r=load(ready_path);valid_identity(r)
    if r.get("state")!="candidate_ready" or r.get("author")!="claude_blender":raise SystemExit("FAIL — ready record state/author invalid")
    if a.candidate_file:
        p=(ROOT/a.candidate_file).resolve()
        if not p.is_file() or ROOT not in p.parents:raise SystemExit("FAIL — candidate file missing/outside repo")
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h.lower()!=r["candidate_sha256"].lower():raise SystemExit("FAIL — candidate file SHA does not match ready record")
    if a.response:
        p=C/("MODEL_CANDIDATE_FAILURES.json" if a.response=="fail" else "MODEL_CANDIDATE_PASS.json")
        if not p.exists():raise SystemExit("BLOCKED — response file missing")
        x=load(p);valid_identity(x)
        for k in ("candidate_id","candidate_commit","candidate_sha256"):
            if x[k].lower()!=r[k].lower():raise SystemExit("FAIL — stale/mismatched response "+k)
        expected="failed" if a.response=="fail" else "passed"
        if x.get("state")!=expected or x.get("validator")!="gpt_work":raise SystemExit("FAIL — response state/validator invalid")
        if x.get("production_approved") is not False:raise SystemExit("FAIL — agent response may not production-approve")
    print("PASS — model handoff identity is coherent and fail-closed.")
if __name__=="__main__":main()
