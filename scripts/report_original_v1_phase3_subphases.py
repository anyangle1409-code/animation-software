"""Read-only per-sub-phase evidence report (3A-3E) for a candidate from its committed full-evidence merged pose report.

python scripts/report_original_v1_phase3_subphases.py <rN> <pre-corrective rM> <out.json> <out.md>

For every sub-phase it lists, per owned pose/region, the candidate value, the active-epoch baseline (P3B1), the pre-corrective candidate, the
development gate and the margin, plus the strict comparator verdict (regression versus P3B1 beyond the unchanged tolerances). Grip rows use the
bilateral penetration/contact numbers. Nothing is accepted here: this is the measured evidence a sub-phase closure is built from.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rev, pre, out_json, out_md = sys.argv[1], sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
RC = ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks"
spec = json.loads((ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json").read_text(encoding="utf-8-sig"))
dev, tol = spec["profiles"]["development_blocker"], spec["comparison_tolerances"]


def rows(p):
    return {r["pose"]: r for r in json.loads(Path(p).read_text(encoding="utf-8-sig"))}


C = rows(RC / f"full_{rev}_merged_pose_report.json")
P = rows(RC / f"full_{pre}_merged_pose_report.json")
B = rows(ROOT / "ORIGINAL_V1_WORK/candidates/pose_test_report_p3b1.json")
rp = spec["repair_priority"]
GROUPS = {
    "3A shoulder/axilla": [(p, r) for p in rp[0]["poses"] for r in rp[0]["regions"]],
    "3B hands/fingers": [(p, r) for p in rp[1]["poses"] for r in ("hand", "finger", "thumb")],
    "3D wrist (push-up hand/arm chain)": [("pushup_bottom", r) for r in ("hand", "arm")],
    "3E hip/pelvis/legs": [(p, r) for p in rp[2]["poses"] for r in rp[2]["regions"]],
}
out = {"candidate": rev, "baseline": "P3B1", "pre_corrective": pre, "groups": {}, "grip": []}
md = [f"# {rev} Phase 3 sub-phase evidence (read-only, measured)", "", "Gate = development_blocker profile (unchanged). Verdict = strict comparator versus P3B1 with the unchanged tolerances.", ""]
for name, items in GROUPS.items():
    table = []
    for pose, region in items:
        rc, rb, rpv = C.get(pose), B.get(pose), P.get(pose)
        if not rc or region not in rc["by_region"]:
            continue
        cmin, cmax = rc["by_region"][region]["min_ratio"], rc["by_region"][region]["max_ratio"]
        bmin = rb["by_region"][region]["min_ratio"] if rb and region in rb["by_region"] else None
        bmax = rb["by_region"][region]["max_ratio"] if rb and region in rb["by_region"] else None
        si = (rc.get("self_intersection_by_region") or {}).get(region, 0)
        bsi = ((rb or {}).get("self_intersection_by_region") or {}).get(region, 0)
        reg_min = bmin is not None and (bmin - cmin) > tol["region_min_ratio_drop"]
        reg_max = bmax is not None and (cmax - bmax) > tol["region_max_ratio_rise"]
        reg_si = (si - bsi) > tol["self_intersecting_face_pairs_rise"]
        table.append({"pose": pose, "region": region, "min": cmin, "max": cmax, "P3B1_min": bmin, "P3B1_max": bmax,
                      "min_gate": dev["region_min_ratio_min"], "max_gate": dev["region_max_ratio_max"],
                      "min_margin": round(cmin - dev["region_min_ratio_min"], 3), "max_margin": round(dev["region_max_ratio_max"] - cmax, 3),
                      "self_intersections": si, "P3B1_self_intersections": bsi,
                      "regression_vs_P3B1": {"min": bool(reg_min), "max": bool(reg_max), "self_intersections": bool(reg_si)}})
    out["groups"][name] = table
    bad = [t for t in table if any(t["regression_vs_P3B1"].values())]
    gate_bad = [t for t in table if t["min_margin"] <= 0 or t["max_margin"] <= 0]
    md += [f"## {name}", "", f"rows {len(table)}; gate failures {len(gate_bad)}; strict regressions vs P3B1 {len(bad)}", "",
           "| pose | region | min | P3B1 min | max | P3B1 max | SI | P3B1 SI | min margin | max margin | regression |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in table:
        flag = ",".join(k for k, v in t["regression_vs_P3B1"].items() if v) or "-"
        md.append(f"| {t['pose']} | {t['region']} | {t['min']} | {t['P3B1_min']} | {t['max']} | {t['P3B1_max']} | {t['self_intersections']} | {t['P3B1_self_intersections']} | {t['min_margin']} | {t['max_margin']} | {flag} |")
    md.append("")
md += ["## 3C grip / equipment contact (bilateral)", "", f"Gate: penetration <= {dev['grip_max_penetration_mm']} mm, contact vertices within 2 mm >= {dev['grip_min_contact_vertices_within_2mm']}.", "",
       "| pose | side | max penetration mm | P3B1 | contact vertices | P3B1 | ok |", "|---|---|---|---|---|---|---|"]
for pose, rc in C.items():
    for side in ("grip_l", "grip_r"):
        if side in rc:
            g, bg = rc[side], (B.get(pose) or {}).get(side, {})
            ok = g["max_penetration_mm"] <= dev["grip_max_penetration_mm"] and g["contact_vertices_within_2mm"] >= dev["grip_min_contact_vertices_within_2mm"]
            out["grip"].append({"pose": pose, "side": side, "penetration_mm": g["max_penetration_mm"], "contact": g["contact_vertices_within_2mm"], "ok": ok})
            md.append(f"| {pose} | {side[-1]} | {g['max_penetration_mm']} | {bg.get('max_penetration_mm')} | {g['contact_vertices_within_2mm']} | {bg.get('contact_vertices_within_2mm')} | {ok} |")
tot_regs = {k: sum(1 for t in v if any(t["regression_vs_P3B1"].values())) for k, v in out["groups"].items()}
out["strict_regressions_by_group"] = tot_regs
out["grip_all_ok"] = all(g["ok"] for g in out["grip"])
md += ["", f"Strict regressions by group: {json.dumps(tot_regs)}. Grip all inside gate: {out['grip_all_ok']}."]
out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
print("SUBPHASES", tot_regs, "grip ok", out["grip_all_ok"])
