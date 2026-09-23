"""Audit the preparation/automation workspace before handing back to Work."""

from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"CANDIDATE_BASELINE_MANIFEST.json"

REQUIRED=[
 "CURRENT_STATE.md","WORK_START_HERE.md","LAPTOP_CONTINUATION_HANDOFF.md",
 "FINAL_RIG_INTAKE.md","CANDIDATE_OUTPUT_CONTRACT.md","WORK_AUTONOMOUS_PROMPT.md",
 "RESUME_WORK.bat","START_CANDIDATE.bat","FINISH_CANDIDATE.bat",
 "RUN_CANDIDATE_GATES.bat","RUN_REVIEW_PACK.bat",
 "scripts/preflight_resume.py","scripts/start_candidate.py","scripts/finish_candidate.py",
 "scripts/candidate_quick_check.py","scripts/run_candidate_gates.py",
 "scripts/prepare_review_pack.py","scripts/render_candidate_review.py",
 "scripts/checkpoint_candidate.py","scripts/guard_hand_floor_vertices.py",
 "scripts/audit_knee_topology_candidate.py","scripts/compare_rig_compatibility.py",
 "scripts/tag_v6_review_regions.py",
]

def sha(path):
    h=hashlib.sha256(path.read_bytes()).hexdigest();return h

errors=[]
for rel in REQUIRED:
    if not (ROOT/rel).is_file():errors.append(f"missing {rel}")

if not MANIFEST.is_file():
    errors.append("missing CANDIDATE_BASELINE_MANIFEST.json")
else:
    m=json.loads(MANIFEST.read_text())
    base=m["baseline"]
    checks=[
      ("dressed_glb","sha256" in base and "dressed_glb" in base["sha256"]),
      ("bare_glb","sha256" in base and "bare_glb" in base["sha256"]),
      ("blend","sha256" in base and "blend" in base["sha256"]),
    ]
    for key,ok in checks:
        if not ok:errors.append(f"manifest missing hash for {key}")
    if not errors:
        mapping={
          "dressed_glb":base["dressed_glb"],
          "bare_glb":base["bare_glb"],
          "blend":base["blend"],
        }
        for key,name in mapping.items():
            path=ROOT/name
            if not path.is_file():
                errors.append(f"missing baseline artifact {name}")
            else:
                actual=sha(path);expected=base["sha256"][key]
                if actual!=expected:errors.append(f"baseline hash mismatch {name}")

print("PREPARATION WORKSPACE AUDIT")
print("="*27)
print("required files:",len(REQUIRED))
if errors:
    print("FAIL")
    for e in errors:print("-",e)
    raise SystemExit(1)
print("PASS")
print("Authoritative entry: CURRENT_STATE.md")
print("Laptop flow: RESUME_WORK.bat -> START_CANDIDATE.bat -> edit/export -> FINISH_CANDIDATE.bat")
