"""Record a continuation decision for a numbered candidate in ORIGINAL_V1_PRODUCTION_CONTROL.json (evidence-backed; never an approval).

python scripts/record_original_v1_continuation_decision.py <rN> <parent rM> <classification> <reason-file.txt> <evidence path> [<evidence path> ...]
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rev, parent, cls, reason_file = sys.argv[1:5]
evid = sys.argv[5:]
cp = ROOT / "ORIGINAL_V1_PRODUCTION_CONTROL.json"
raw = cp.read_text(encoding="utf-8-sig")
c = json.loads(raw)
blend = ROOT / f"ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
sha = hashlib.sha256(blend.read_bytes()).hexdigest()
c.setdefault("continuation_decisions", {})[rev] = {
    "candidate_sha256": sha, "chosen_parent": parent, "classification": cls,
    "reason": Path(reason_file).read_text(encoding="utf-8").strip(),
    "comparison_evidence": [{"path": e, "sha256": hashlib.sha256((ROOT / e).read_bytes()).hexdigest()} for e in evid]}
indent_ok = json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n" == raw
if not indent_ok:
    print("WARNING: file does not round-trip with indent=2; diff may include formatting")
cp.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("recorded", rev, sha)
