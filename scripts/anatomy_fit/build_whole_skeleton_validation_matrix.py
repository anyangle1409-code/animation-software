"""A1: one current whole-skeleton validation matrix for ORIGINAL_v1 (consolidation; no new anatomical judgement).

Joins, per region of canonical_freeze_readiness_v1.json:
  * its readiness, counts of defined anchors/blockers and next action (copied, never upgraded here);
  * the 9 Oct blocker-matrix items that belong to the region;
  * the 13 Oct master-execution work packages touching it (ids only; their live status is in the task ledger);
  * the skeleton-in-skin containment measured by scripts/audit_original_skeleton_containment_blender.py.
A region's readiness can only be changed by its own source review, never by this matrix.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANAT = ROOT / "ORIGINAL_V1_WORK" / "anatomy"
READINESS = ANAT / "canonical_freeze_readiness_v1.json"
BLOCKERS = ANAT / "audit" / "claude_anatomical_development_20261009" / "blocker_matrix_v1.json"
CONTAINMENT = ANAT / "audit" / "claude_a1" / "skeleton_containment_report.json"
LEDGER = ROOT / "docs" / "CLAUDE_MASTER_TASK_LEDGER_20261013.json"
OUT = ANAT / "audit" / "claude_a1" / "whole_skeleton_validation_matrix_v1.json"

BLOCKER_REGION = {
    "U9": ["shoulder_girdle", "ribs"], "H8": ["carpus"], "G3": ["*"], "U3": ["shoulder_girdle"],
    "L3": ["lower_limb_long_bones"], "H6/L4/L7": ["hand", "lower_limb_long_bones"], "U5/U10": ["spine"],
    "Rib slope": ["ribs"], "H1-H3/c005": ["hand", "carpus"], "L5": ["tarsus"], "U7/U8": ["forearm", "humerus"],
}
# bone-name fragments (HGPT_ANATOMICAL_MASTER) per region, for the containment join
REGION_BONES = {
    "shoulder_girdle": ("clavicle", "scapula"), "spine": (),          # spine: exact level names (SPINE_LEVELS)
    "ribs": ("rib", "sternum", "costal"), "forearm": ("radius", "ulna"),
    "carpus": ("scaphoid", "lunate", "triquetrum", "pisiform", "trapezium", "trapezoid", "capitate", "hamate"),
    "hand": ("metacarpal", "digit", "thumb"), "pelvis": ("hip",), "lower_limb_long_bones": ("femur", "tibia", "fibula", "patella"),
    "tarsus": ("talus", "calcaneus", "navicular", "cuboid", "cuneiform"), "forefoot_toes": ("metatarsal", "hallux", "toe"),
    "head_neck_fixed": ("frontal", "parietal", "temporal", "occipital", "sphenoid", "ethmoid", "mandible", "maxilla", "hyoid",
                        "nasal", "zygomatic", "lacrimal", "palatine", "vomer", "concha", "malleus", "incus", "stapes"),
    "humerus": ("humerus",),
}
SPINE_LEVELS = {f"anat_{p}{i}" for p, n in (("c", 7), ("t", 12), ("l", 5)) for i in range(1, n + 1)} | {"anat_sacrum", "anat_coccyx"}
SESSION = {   # 13 Oct master-execution packages -> regions (pointers only; statuses are read from the ledger)
    "F1": ["forefoot_toes", "tarsus"], "F2": ["forefoot_toes"], "F3": ["forefoot_toes", "tarsus"], "F4": ["forefoot_toes"],
    "F5": ["forefoot_toes"], "F6": ["forefoot_toes", "tarsus"], "W1": ["shoulder_girdle", "ribs"], "W2": ["shoulder_girdle"],
    "W3": ["shoulder_girdle"], "W4": ["shoulder_girdle"], "M1": ["*"], "M2": ["*"], "E1": ["*"],
}


def _region_of_bone(name):
    if name in SPINE_LEVELS:
        return "spine"
    for region, frags in REGION_BONES.items():
        if region != "spine" and any(f in name for f in frags):
            return region
    return None


def build():
    ready = json.loads(READINESS.read_text())
    blockers = json.loads(BLOCKERS.read_text())["blockers"]
    cont = json.loads(CONTAINMENT.read_text())
    ledger = {t["id"]: t for t in json.loads(LEDGER.read_text())["tasks"]}
    by_region = {}
    for b in cont["bones_all"]:
        by_region.setdefault(_region_of_bone(b["bone"]), []).append(b)
    rows = {}
    for region, r in ready["regions"].items():
        bones = by_region.get(region, [])
        rows[region] = {
            "readiness": r["readiness"],
            "defined_anchors": len(r.get("ready", [])),
            "open_blockers": len(r.get("blockers", [])),
            "next_action": r.get("next_action"),
            "blocker_matrix_items": [b["id"] for b in blockers if region in BLOCKER_REGION.get(b["id"], []) or "*" in BLOCKER_REGION.get(b["id"], [])],
            "session_packages": [k for k, regs in SESSION.items() if (region in regs or "*" in regs) and k in ledger],
            "containment": {
                "bones": len(bones),
                "outside_skin": sorted(b["bone"] for b in bones if b["min_depth_mm"] <= 0),
                "shallow_lt_3mm": sorted(b["bone"] for b in bones if 0 < b["min_depth_mm"] < 3.0),
                "min_axis_depth_mm": min((b["min_depth_mm"] for b in bones), default=None),
            },
        }
    unassigned = sorted(b["bone"] for b in by_region.get(None, []))
    counts = {s: sum(r["readiness"] == s for r in rows.values()) for s in ("READY", "PARTIAL", "BLOCKED")}
    return {
        "kind": "WHOLE_SKELETON_VALIDATION_MATRIX", "schema_version": 1, "approved": False,
        "rule": "readiness is copied from canonical_freeze_readiness_v1.json; this matrix never upgrades a region",
        "overall_status": ready["overall_status"], "readiness_counts": counts,
        "containment_summary": cont["summary"], "regions": rows,
        "bones_not_mapped_to_a_region": unassigned,
        "session_package_status": "see docs/CLAUDE_MASTER_TASK_LEDGER_20261013.json (live; not copied so this matrix stays current)",
    }


if __name__ == "__main__":
    m = build()
    if "--check" in sys.argv:
        sys.exit(0 if json.loads(OUT.read_text()) == m else 1)
    OUT.write_text(json.dumps(m, indent=1) + "\n")
    print(json.dumps(m["readiness_counts"]), "unmapped bones:", len(m["bones_not_mapped_to_a_region"]))
