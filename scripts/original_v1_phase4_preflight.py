#!/usr/bin/env python3
"""Read-only Phase 4 development-freeze eligibility preflight for ORIGINAL v1."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from original_v1_production_control import ROOT, CAND, build, digest, read
from original_v1_whole_body_issues import blocking_issues, validate_ledger
from original_v1_anatomy_issue_closure import verify_closed_issues

ISSUE_LEDGER = "ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"


def _load_issue_ledger(root):
    path = root / ISSUE_LEDGER
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assess(state, control, root=ROOT, require_local_blend=False, issue_ledger=None):
    issues=[]
    rev=state.get("current_candidate")
    sha=state.get("last_known_candidate_sha256")
    baseline=(state.get("pinned_baseline") or {}).get("revision")
    if not isinstance(rev,str) or not re.fullmatch(r"r\d+",rev):
        issues.append("numbered current candidate required")
    if not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{64}",sha):
        issues.append("current candidate SHA-256 invalid")
    if state.get("candidate_state")=="rejected":
        issues.append("current candidate is rejected")
    if state.get("incomplete_candidates"):
        issues.append("newer incomplete candidate work remains")
    if state.get("development_failure_count")!=0:
        issues.append("development failures remain")
    if state.get("unresolved_regressions"):
        issues.append("strict severity regressions remain")
    phases=state.get("phases",{})
    for p in ("3A","3B","3C","3D","3E"):
        if phases.get(p,{}).get("state")!="complete":
            issues.append(f"Phase {p} is not complete")
    if phases.get("4",{}).get("state")=="complete":
        issues.append("Phase 4 is already recorded complete for this state")
    decision=(control.get("continuation_decisions") or {}).get(rev,{})
    if decision.get("candidate_sha256")!=sha:
        issues.append("continuation decision is missing/stale for current candidate")
    nxt=(state.get("next_action") or {}).get("action")
    if nxt!="ENTER development freeze validation":
        issues.append("production control does not select ENTER development freeze validation")
    refs={x.get("path") for x in state.get("latest_evidence",[]) if isinstance(x,dict)}
    if rev:
        if f"ORIGINAL_V1_WORK/candidates/repair_checks/full_{rev}_evidence_manifest.json" not in refs:
            issues.append("verified full-evidence receipt missing from current evidence")
        if baseline and f"ORIGINAL_V1_WORK/candidates/repair_checks/full_{rev}_comparison_vs_{baseline}.json" not in refs:
            issues.append("active epoch-baseline comparison missing from current evidence")

    try:
        ledger = issue_ledger if issue_ledger is not None else _load_issue_ledger(root)
        ledger_errors = validate_ledger(ledger, None if issue_ledger is not None else root)
        if ledger_errors:
            issues.append("whole-body issue ledger invalid")
            issues.extend("whole-body issue ledger: " + error for error in ledger_errors)
        else:
            blockers = blocking_issues(ledger)
            if blockers:
                issues.append("Critical/High whole-body anatomy issues remain")
                issues.extend(
                    f"whole-body blocker {row['id']} [{row['severity']}] {row['state']}"
                    for row in blockers
                )
            elif issue_ledger is None:
                human = json.loads(
                    (root / "ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8-sig")
                )
                closure_errors = verify_closed_issues(root, ledger, human)
                if closure_errors:
                    issues.append("Critical/High anatomy closure evidence is invalid")
                    issues.extend("anatomy closure: " + error for error in closure_errors)
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        issues.append("whole-body issue ledger unavailable/invalid: " + str(exc))

    if require_local_blend and rev and sha:
        blend=root/CAND/f"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
        if not blend.is_file():
            issues.append("local candidate Blend is not present")
        elif digest(blend)!=sha:
            issues.append("local candidate Blend hash differs from committed identity")
    return {
        "schema_version":2,
        "candidate":rev,
        "candidate_sha256":sha,
        "active_pinned_baseline":baseline,
        "eligibility":"ELIGIBLE_FOR_PHASE4_VALIDATION" if not issues else "PHASE4_BLOCKED",
        "issues":list(dict.fromkeys(issues)),
        "production_approved":False,
        "note":"Read-only eligibility preflight. Critical/High whole-body anatomy blockers fail closed, and closed Critical/High rows require structured candidate-bound closure receipts; this still does not create a freeze record, execute replay/audits, or approve production.",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--require-local-blend",action="store_true")
    ap.add_argument("--json-out",type=Path)
    a=ap.parse_args()
    try:
        state,_=build(ROOT)
        control=read(ROOT,"ORIGINAL_V1_PRODUCTION_CONTROL.json")
        result=assess(state,control,ROOT,a.require_local_blend)
        if a.json_out:
            if a.json_out.exists():
                raise ValueError("preflight output collision")
            a.json_out.parent.mkdir(parents=True,exist_ok=True)
            a.json_out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))
        return 0 if result["eligibility"]=="ELIGIBLE_FOR_PHASE4_VALIDATION" else 1
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"eligibility":"PHASE4_BLOCKED","issues":[str(exc)],"production_approved":False},indent=2))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
