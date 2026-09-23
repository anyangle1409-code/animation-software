"""Audit the preparation/automation workspace before handing back to Work."""

from __future__ import annotations
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"CANDIDATE_BASELINE_MANIFEST.json"
REQUIRED=[
 "CURRENT_STATE.md","RIG_63_FREEZE.md","WORK_START_HERE.md","LAPTOP_CONTINUATION_HANDOFF.md",
 "FINAL_RIG_INTAKE.md","CANDIDATE_OUTPUT_CONTRACT.md","WORK_AUTONOMOUS_PROMPT.md",
 "RESUME_WORK.bat","START_CANDIDATE.bat","FINISH_CANDIDATE.bat",
 "scripts/preflight_resume.py","scripts/prepare_rig63_validation.py","scripts/start_candidate.py",
 "scripts/finish_candidate.py","scripts/candidate_quick_check.py","scripts/run_candidate_gates.py",
 "scripts/prepare_review_pack.py","scripts/render_candidate_review.py","scripts/checkpoint_candidate.py",
 "scripts/guard_hand_floor_vertices.py","scripts/audit_knee_topology_candidate.py",
 "scripts/compare_rig_compatibility.py","scripts/tag_v6_review_regions.py",
]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
errors=[]
for rel in REQUIRED:
    if not (ROOT/rel).is_file():errors.append(f"missing {rel}")
if not MANIFEST.is_file():
    errors.append("missing CANDIDATE_BASELINE_MANIFEST.json")
else:
    m=json.loads(MANIFEST.read_text())
    base=m.get("geometry_baseline",m.get("baseline",{}))
    for key in ("dressed_glb","bare_glb","blend"):
        path=ROOT/base.get(key,"")
        expected=base.get("sha256",{}).get(key)
        if not path.is_file():errors.append(f"missing baseline artifact {path.name}")
        elif not expected or sha(path)!=expected:errors.append(f"baseline hash mismatch {path.name}")
    rig=m.get("rig_baseline",{})
    if rig.get("freeze_commit")!="19ca602ca2f2a821237dcf5b1b50c7906d86b0fe":errors.append("manifest rig baseline is not 19ca602")
    if rig.get("canonical_bones")!=63:errors.append("manifest canonical bone count is not 63")

print("PREPARATION WORKSPACE AUDIT")
print("="*27)
print("required files:",len(REQUIRED))
if errors:
    print("FAIL")
    for e in errors:print("-",e)
    raise SystemExit(1)
print("PASS")
print("Geometry baseline:",base.get("version","unknown"))
print("Rig baseline: 19ca602 / hgpt_canonical_v3 / 63 bones")
print("Laptop flow: RESUME_WORK.bat -> START_CANDIDATE.bat -> edit/export -> FINISH_CANDIDATE.bat")
