"""Copy a VERIFIED continuation-decision fragment into ORIGINAL_V1_PRODUCTION_CONTROL.json (textual, minimal diff, LF) and retarget active_local_repair.

python scripts/apply_original_v1_continuation_fragment.py <receipt.json> <repair-reason.txt> <repair-command>

The receipt must be a CONTINUATION_DECISION_VERIFIED receipt written by scripts/verify_original_v1_continuation_decision.py; its
production_control_fragment is inserted unchanged under continuation_decisions[<revision>]. Refuses an existing entry, a receipt with issues,
or a candidate Blend whose SHA-256 differs from the fragment. Never promotes a baseline, enters Phase 4 or approves production.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
receipt_path, repair_reason_file, repair_command = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
if receipt.get("kind") != "EXPERIMENTAL_CONTINUATION_DECISION_RECEIPT" or receipt.get("contract_status") != "CONTINUATION_DECISION_VERIFIED" or receipt.get("issues"):
    raise SystemExit("receipt is not a clear verified continuation decision")
if receipt.get("production_approved") is not False or receipt.get("baseline_promotion") is not False or receipt.get("phase4_authorized") is not False:
    raise SystemExit("receipt claims promotion/authorisation")
rev, frag = receipt["candidate_revision"], receipt["production_control_fragment"]
blend = ROOT / f"ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_{rev}.blend"
if hashlib.sha256(blend.read_bytes()).hexdigest() != frag["candidate_sha256"]:
    raise SystemExit("local Blend differs from the verified fragment")
cp = ROOT / "ORIGINAL_V1_PRODUCTION_CONTROL.json"
raw = cp.read_bytes().decode("utf-8").replace("\r\n", "\n")
data = json.loads(raw)
if rev in data["continuation_decisions"]:
    raise SystemExit(rev + " decision already present")
block = json.dumps(frag, indent=2, ensure_ascii=False)
block = "\n".join(("    " + ln if i else ln) for i, ln in enumerate(block.splitlines()))
anchor = '      ]\n    }\n  },\n  "active_local_repair": {'
if raw.count(anchor) != 1:
    raise SystemExit("anchor missing/ambiguous")
raw = raw.replace(anchor, '      ]\n    },\n    "' + rev + '": ' + block + '\n  },\n  "active_local_repair": {')
start, end = raw.index('  "active_local_repair": {'), raw.index('  "note": "Completion records')
old = json.loads("{" + raw[start:end].rstrip().rstrip(",") + "}")["active_local_repair"]
new = dict(old, candidate_revision=rev, candidate_sha256=frag["candidate_sha256"], reason=Path(repair_reason_file).read_text(encoding="utf-8").strip(), command=repair_command)
rep = json.dumps({"active_local_repair": new}, indent=2, ensure_ascii=False)
rep = "\n".join(rep.splitlines()[1:-1]) + ",\n"
raw = raw[:start] + rep + raw[end:]
json.loads(raw)
cp.write_bytes(raw.encode("utf-8"))
print("control updated from verified fragment:", rev, frag["candidate_sha256"])
