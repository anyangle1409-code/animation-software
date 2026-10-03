#!/usr/bin/env python3
"""Read-only concise ORIGINAL-v1 progress summary for phone checks.

Derived entirely from generated production-control state plus the orchestration map.
It is not a new source of truth and never estimates completion from subjective scores.
"""
from __future__ import annotations

import argparse
import json

from original_v1_production_control import ROOT,build,digest

ORCHESTRATION="ORIGINAL_V1_EXECUTION_ORCHESTRATION.json"
ROADMAP=[str(n) for n in range(13)]
PHASE3_SUB=["3A","3B","3C","3D","3E"]
PHASE5_SUB=["5A","5B","5C","5D","5E","5F","5G"]


def state_counts(status):
    phases=status["phases"]
    completed=[p for p in ROADMAP if phases[p]["state"]=="complete"]
    started=[p for p in ROADMAP if phases[p]["state"] not in ("complete","not_started")]
    remaining=[p for p in ROADMAP if phases[p]["state"]!="complete"]
    return completed,started,remaining


def milestone(status):
    phases=status["phases"]
    if phases["3"]["state"]!="complete":
        return {
            "name":"Complete Phase 3 deformation foundation",
            "remaining_subphases":[p for p in PHASE3_SUB if phases[p]["state"]!="complete"],
            "then":"Phase 4 development deformation freeze",
        }
    if phases["4"]["state"]!="complete":
        return {"name":"Freeze the development deformation foundation","then":"Phase 5 high-detail anatomy"}
    if phases["5"]["state"]!="complete":
        return {
            "name":"Complete Phase 5 high-detail anatomy",
            "remaining_subphases":[p for p in PHASE5_SUB if phases[p]["state"]!="complete"],
            "then":"Phase 6 final topology/surface",
        }
    for n,label in ((6,"Final topology/surface"),(7,"First-party clothing"),(8,"Materials/presentation"),
                    (9,"Production deformation"),(10,"Runtime integration"),(11,"Automated visual QA"),(12,"Production freeze")):
        if phases[str(n)]["state"]!="complete":
            return {"name":f"Complete Phase {n} {label}","then":f"Phase {n+1}" if n<12 else "controlled owner-authorised release"}
    return {"name":"Controlled owner-authorised release","then":"exact-SHA post-release verification"}


def build_summary(status,orchestration):
    complete,started,remaining=state_counts(status)
    support=orchestration["prepared_support_stages"]
    return {
        "schema_version":1,
        "status":"READ_ONLY_PROGRESS_SUMMARY",
        "production_approved":False,
        "current":{
            "phase":status["current_phase"],
            "subphase":status["current_subphase"],
            "candidate":status["current_candidate"],
            "candidate_state":status["candidate_state"],
            "candidate_classification":status["candidate_classification"],
            "development_failures":status["development_failure_count"],
            "active_epoch_baseline":status.get("pinned_baseline"),
            "strict_active_epoch_regressions":len(status["unresolved_regressions"]),
            "production_failures":status["production_failure_count"],
            "next_action":status["next_action"],
        },
        "roadmap":{
            "complete_phases":complete,
            "active_or_blocked_phases":started,
            "remaining_phases":remaining,
            "phase3_subphases":{p:status["phases"][p]["state"] for p in PHASE3_SUB},
            "phase5_subphases":{p:status["phases"][p]["state"] for p in PHASE5_SUB},
            "next_major_milestone":milestone(status),
        },
        "prepared_infrastructure":{
            "support_stages_prepared":len(support),
            "support_stage_ids":[row["stage"] for row in support],
            "critical_path_nodes":len(orchestration["critical_path"]),
            "note":"Prepared tooling is not actual roadmap completion.",
        },
        "pending_owner_review_count":len(status.get("pending_owner_reviews",[])),
        "incomplete_candidate_revisions":status.get("incomplete_candidates",[]),
        "evidence_timestamp":status.get("evidence_timestamp"),
        "boundaries":[
            "No completion percentage is inferred from unequal roadmap phases.",
            "Prepared tooling does not mark a phase complete.",
            "Routine pending owner review is non-blocking unless an explicit later gate says otherwise.",
            "Production approval remains false until the separate final promotion/freeze workflow."
        ]
    }


def markdown(summary):
    c=summary["current"];r=summary["roadmap"];i=summary["prepared_infrastructure"];m=r["next_major_milestone"]
    lines=[
        "# ORIGINAL v1 concise progress",
        "",
        f"**Current:** Phase {c['phase']} / {c['subphase']} — {c['candidate']} ({c['candidate_classification']}, {c['candidate_state']})",
        f"**Blockers:** {c['development_failures']} development failures; {c['strict_active_epoch_regressions']} strict active-epoch regressions; {c['production_failures']} production-target failures.",
        f"**Active epoch baseline:** {(c.get('active_epoch_baseline') or {}).get('revision')}",
        f"**Next action:** {c['next_action'].get('action')} — {c['next_action'].get('command') or c['next_action'].get('work_package') or c['next_action'].get('reason')}",
        f"**Next major milestone:** {m['name']}",
        f"**After that:** {m['then']}",
        "",
        f"**Roadmap phases complete:** {', '.join(r['complete_phases']) if r['complete_phases'] else 'none'}",
        f"**Roadmap phases remaining:** {', '.join(r['remaining_phases']) if r['remaining_phases'] else 'none'}",
        f"**Prepared support tooling:** {i['support_stages_prepared']}/12 stages; {i['critical_path_nodes']} critical-path nodes.",
        "",
        "**Phase 3:** "+", ".join(f"{k}={v}" for k,v in r["phase3_subphases"].items()),
        "**Phase 5 regions:** "+", ".join(f"{k}={v}" for k,v in r["phase5_subphases"].items()),
        "",
        "Prepared tooling is not model completion. Production approved: **NO**.",
        "Evidence timestamp: "+str(summary["evidence_timestamp"]),
        ""
    ]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json",action="store_true")
    ap.add_argument("--markdown",action="store_true")
    args=ap.parse_args()
    try:
        status,_=build(ROOT)
        path=ROOT/ORCHESTRATION
        orchestration=json.loads(path.read_text(encoding="utf-8"))
        summary=build_summary(status,orchestration)
        summary["orchestration_plan"]={"path":ORCHESTRATION,"sha256":digest(path)}
        if args.json:print(json.dumps(summary,indent=2))
        else:print(markdown(summary))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc));return 2

if __name__=="__main__":
    raise SystemExit(main())
