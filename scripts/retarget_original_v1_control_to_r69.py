"""One-off, auditable textual edit of ORIGINAL_V1_PRODUCTION_CONTROL.json: add the r69 continuation decision (same shape as the r55 entry) and
retarget active_local_repair to r69. Textual (no JSON re-serialisation) so the diff stays minimal. Refuses if the expected anchors are missing.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cp = ROOT / "ORIGINAL_V1_PRODUCTION_CONTROL.json"
raw = cp.read_text(encoding="utf-8")
reason = Path(__import__("sys").argv[1]).read_text(encoding="utf-8").strip()
rc = "ORIGINAL_V1_WORK/candidates/repair_checks"
sha = hashlib.sha256((ROOT / "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r69.blend").read_bytes()).hexdigest()
paths = [f"{rc}/full_r69_comparison_vs_P3B1.json", f"{rc}/full_r69_comparison_vs_r48.json", f"{rc}/full_r69_evidence_manifest.json",
         f"{rc}/remaining_diagnostics_r69/diagnostic_brief.json", f"{rc}/shoulder_corrective_20261002/r69_arc.json",
         f"{rc}/shoulder_corrective_20261002/r69_corrective_audit.json", "ORIGINAL_V1_WORK/shoulder_corrective_r69.json",
         "ORIGINAL_V1_WORK/candidates/repair_preparation/r68_pit_knot_weights_declared/pit_knot_zone_declared_before_solve.json"]
for p in paths:
    if not (ROOT / p).is_file():
        raise SystemExit("missing evidence file " + p)
entry = {"candidate_sha256": sha, "chosen_parent": "r48", "classification": "TRADEOFF_OR_REGRESSION", "reason": reason,
         "comparison_evidence": [{"path": p} for p in paths]}
block = json.dumps(entry, indent=2, ensure_ascii=False)
block = "\n".join(("    " + ln if i else ln) for i, ln in enumerate(block.splitlines()))
anchor = '      ]\n    }\n  },\n  "active_local_repair": {'
if raw.count(anchor) != 1 or '"r69": {' in raw:
    raise SystemExit("anchor missing/ambiguous or r69 already present")
raw = raw.replace(anchor, '      ]\n    },\n    "r69": ' + block + '\n  },\n  "active_local_repair": {')
old_repair = raw[raw.index('  "active_local_repair": {'):raw.index('  "note": "Completion records')]
new_repair = ('  "active_local_repair": {\n'
              '    "candidate_revision": "r69",\n'
              f'    "candidate_sha256": "{sha}",\n'
              '    "action": "RUN local axilla repair",\n'
              '    "reason": "r69 supersedes r55 (local knot weight edit plus re-fitted corrective; 0 development failures, 23 vs 31 strict P3B1 regressions) but real renders still show one small pointed tip at the front pit top; complete the declared local repair before freeze reconciliation",\n'
              '    "command": "RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat r69",\n'
              '    "work_package": "docs/work_packages/PHASE_3A_AXILLA_PIT_LOCAL_REPAIR.md",\n'
              '    "safe_parallel_task": "Read-only review/comparator analysis is safe; do not reopen rev2c rig, P3a poses, thresholds or pinned baselines.",\n'
              '    "production_approved": false\n'
              '  },\n')
raw = raw.replace(old_repair, new_repair)
json.loads(raw)
cp.write_text(raw, encoding="utf-8")
print("control updated: r69 decision + active_local_repair r69", sha)
