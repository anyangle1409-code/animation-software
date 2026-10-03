"""Deterministic, evidence-led classification of a candidate's strict regressions versus the active epoch baseline (read-only).

python scripts/classify_original_v1_p3b1_regressions.py <rN> <pre-corrective rM> <out.json> <out.md>

Every regression listed in repair_checks/full_<rN>_comparison_vs_P3B1.json is placed next to: the baseline value, the value of the
pre-corrective weights-only candidate <rM> (so the cause can be attributed to the anchored weights or to the corrective), the candidate value,
the development-blocker gate, the margin to that gate, the production-target limit and whether the pose belongs to the 3A shoulder pose set.

Attribution rules (mechanical, no judgement):
  INHERITED_FROM_WEIGHTS  the pre-corrective candidate already regressed by more than the comparison tolerance and the corrective did not
                          add more than the tolerance on top;
  ADDED_BY_CORRECTIVE     the pre-corrective candidate was within tolerance and the candidate is not;
  OUTSIDE_3A_POSES        the pose is not one of the shoulder-owned poses (the shoulder zone still moves in it);
Each row also states GATE_MARGIN_OK when the value stays inside the development-blocker gate and PRODUCTION_TARGET_OK when it also meets the
stricter production-target limit. Nothing here accepts a regression: it only attributes and measures it.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rev, pre, out_json, out_md = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
RC = ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks"
spec = json.loads((ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json").read_text(encoding="utf-8-sig"))
tol = spec["comparison_tolerances"]
dev, prod = spec["profiles"]["development_blocker"], spec["profiles"]["production_target"]
shoulder_poses = set(spec["repair_priority"][0]["poses"])


def load_rows(path):
    return {r["pose"]: r for r in json.loads(Path(path).read_text(encoding="utf-8-sig"))}


rows_c = load_rows(RC / f"full_{rev}_merged_pose_report.json")
rows_p = load_rows(RC / f"full_{pre}_merged_pose_report.json")
cmp_ = json.loads((RC / f"full_{rev}_comparison_vs_P3B1.json").read_text(encoding="utf-8"))
tol_key = {"region_min_ratio": "region_min_ratio_drop", "region_max_ratio": "region_max_ratio_rise", "self_intersecting_face_pairs": "self_intersecting_face_pairs_rise",
           "edge_ratio_p99": "edge_ratio_p99_rise", "edge_ratio_p01": "edge_ratio_p01_drop"}
limit_key = {"region_min_ratio": ("region_min_ratio_min", "min"), "region_max_ratio": ("region_max_ratio_max", "max"),
             "self_intersecting_face_pairs": ("self_intersecting_face_pairs_max", "max"), "edge_ratio_p99": ("edge_ratio_p99_max", "max"),
             "edge_ratio_p01": ("edge_ratio_p01_min", "min")}


def value(row, region, metric):
    if row is None:
        return None
    if region:
        key = {"region_min_ratio": "min_ratio", "region_max_ratio": "max_ratio"}[metric]
        return row.get("by_region", {}).get(region, {}).get(key)
    return row.get(metric)


def worse(metric, base, cand):
    """signed amount by which cand is WORSE than base (positive = worse)."""
    return (base - cand) if limit_key[metric][1] == "min" else (cand - base)


result = []
for x in cmp_["regressions"]:
    metric, region, pose = x["metric"], x["region"], x["name"]
    base, cand = float(x["baseline"]), float(x["candidate"])
    prev = value(rows_p.get(pose), region, metric)
    tolerance = float(tol[tol_key[metric]])
    gate_name, kind = limit_key[metric]
    gate, ptarget = float(dev[gate_name]), float(prod[gate_name])
    margin = (cand - gate) if kind == "min" else (gate - cand)
    pmargin = (cand - ptarget) if kind == "min" else (ptarget - cand)
    pre_worse = None if prev is None else worse(metric, base, float(prev))
    added = None if prev is None else worse(metric, float(prev), cand)
    if pose not in shoulder_poses:
        cause = "OUTSIDE_3A_POSES"
    elif pre_worse is not None and pre_worse > tolerance and (added is None or added <= tolerance):
        cause = "INHERITED_FROM_WEIGHTS"
    elif pre_worse is not None and pre_worse <= tolerance:
        cause = "ADDED_BY_CORRECTIVE"
    else:
        cause = "INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE"
    reg_si = None
    if metric == "self_intersecting_face_pairs":
        reg_si = {"candidate_by_region": rows_c[pose].get("self_intersection_by_region"), "baseline_by_region": None}
    result.append({"pose": pose, "region": region, "metric": metric, "baseline_P3B1": base, "pre_corrective_" + pre: prev, "candidate_" + rev: cand,
                   "tolerance": tolerance, "worse_than_baseline_by": round(worse(metric, base, cand), 4),
                   "pre_corrective_worse_than_baseline_by": None if pre_worse is None else round(pre_worse, 4),
                   "corrective_added": None if added is None else round(added, 4), "attribution": cause,
                   "development_gate": gate, "gate_margin": round(margin, 4), "GATE_MARGIN_OK": margin > 0,
                   "production_target_limit": ptarget, "production_margin": round(pmargin, 4), "PRODUCTION_TARGET_OK": pmargin > 0, "si_detail": reg_si})
summary = {}
for r in result:
    summary[r["attribution"]] = summary.get(r["attribution"], 0) + 1
rec = {"schema_version": 1, "candidate": rev, "pre_corrective_candidate": pre, "baseline": "P3B1", "regression_count": len(result),
       "attribution_counts": summary, "all_inside_development_gate": all(r["GATE_MARGIN_OK"] for r in result),
       "all_inside_production_target": all(r["PRODUCTION_TARGET_OK"] for r in result),
       "min_gate_margin": min(r["gate_margin"] for r in result), "rows": result,
       "note": "Attribution only. It accepts nothing, changes no tolerance and does not enter Phase 4."}
out_json.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
lines = [f"# {rev} strict regressions vs P3B1 - attribution", "", f"Pre-corrective reference: {pre}. Attribution counts: {json.dumps(summary)}. "
         f"All inside the development gate: {rec['all_inside_development_gate']}. All inside the production target: {rec['all_inside_production_target']}.", "",
         "| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in result:
    lines.append(f"| {r['pose']} | {r['region'] or 'mesh'} | {r['metric']} | {r['baseline_P3B1']} | {r['pre_corrective_' + pre]} | {r['candidate_' + rev]} | {r['worse_than_baseline_by']} | {r['tolerance']} | {r['attribution']} | {r['gate_margin']} | {r['production_margin']} |")
out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("CLASSIFIED", len(result), summary, "inside gate:", rec["all_inside_development_gate"], "inside production target:", rec["all_inside_production_target"], "min gate margin", rec["min_gate_margin"])
