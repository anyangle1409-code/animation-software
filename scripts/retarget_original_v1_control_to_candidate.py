"""Auditable TEXTUAL edit of ORIGINAL_V1_PRODUCTION_CONTROL.json (no JSON re-serialisation, LF endings, minimal diff):
adds a TRADEOFF_OR_REGRESSION continuation decision for <rev> (same shape as the existing r55/r69 entries) and retargets active_local_repair to <rev>.

python scripts/retarget_original_v1_control_to_candidate.py <rev> <parent> <reason.txt> <repair-reason.txt> <repair-command> <evidence path> [<evidence path> ...]

Refuses if an anchor is missing, the decision already exists, an evidence file is missing, or the candidate Blend is not present locally.
Never accepts anatomy, enters Phase 4 or approves production; the entry only records evidence-bound lineage.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rev, parent, reason_file, repair_reason_file, repair_command = sys.argv[1:6]
paths = sys.argv[6:]
cp = ROOT / "ORIGINAL_V1_PRODUCTION_CONTROL.json"
raw = cp.read_bytes().decode("utf-8").replace("\r\n", "\n")
blend = ROOT / f"ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
sha = hashlib.sha256(blend.read_bytes()).hexdigest()
for p in paths:
    if not (ROOT / p).is_file():
        raise SystemExit("missing evidence file " + p)
entry = {"candidate_sha256": sha, "chosen_parent": parent, "classification": "TRADEOFF_OR_REGRESSION",
         "reason": Path(reason_file).read_text(encoding="utf-8").strip(), "comparison_evidence": [{"path": p} for p in paths]}
block = json.dumps(entry, indent=2, ensure_ascii=False)
block = "\n".join(("    " + ln if i else ln) for i, ln in enumerate(block.splitlines()))
data = json.loads(raw)
if rev in data["continuation_decisions"]:
    raise SystemExit(rev + " decision already present")
anchor = '      ]\n    }\n  },\n  "active_local_repair": {'
if raw.count(anchor) != 1:
    raise SystemExit("anchor missing/ambiguous")
raw = raw.replace(anchor, '      ]\n    },\n    "' + rev + '": ' + block + '\n  },\n  "active_local_repair": {')
start, end = raw.index('  "active_local_repair": {'), raw.index('  "note": "Completion records')
old = json.loads("{" + raw[start:end].rstrip().rstrip(",") + "}")["active_local_repair"]
new = dict(old, candidate_revision=rev, candidate_sha256=sha, reason=Path(repair_reason_file).read_text(encoding="utf-8").strip(), command=repair_command)
rep = json.dumps({"active_local_repair": new}, indent=2, ensure_ascii=False)
rep = "\n".join(rep.splitlines()[1:-1]) + ",\n"
raw = raw[:start] + rep + raw[end:]
json.loads(raw)
cp.write_bytes(raw.encode("utf-8"))
print("control updated:", rev, "parent", parent, sha)
