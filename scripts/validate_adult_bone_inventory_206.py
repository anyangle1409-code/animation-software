#!/usr/bin/env python3
"""Validate the conventional adult 206-bone anatomical inventory."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "ORIGINAL_V1_WORK/anatomy/adult_bone_inventory_206.json"
d = json.loads(P.read_text(encoding="utf-8"))
bones = d["bones"]

errors = []

def req(cond, msg):
    if not cond:
        errors.append(msg)

req(len(bones) == 206, f"Expected 206 bones, got {len(bones)}")
ids = [b["id"] for b in bones]
req(len(set(ids)) == len(ids), "Duplicate bone IDs detected")

div = Counter(b["division"] for b in bones)
req(div["axial"] == 80, f"Expected 80 axial bones, got {div['axial']}")
req(div["appendicular"] == 126, f"Expected 126 appendicular bones, got {div['appendicular']}")

expected_regions = {
    "skull": 8,
    "facial_skeleton": 14,
    "auditory_ossicles": 6,
    "neck": 1,
    "vertebral_column": 26,
    "thoracic_cage": 25,
    "pectoral_girdle": 4,
    "upper_limb": 6,
    "wrist": 16,
    "hand": 38,
    "pelvic_girdle": 2,
    "lower_limb": 8,
    "foot": 52,
}
regions = Counter(b["region"] for b in bones)
for k,v in expected_regions.items():
    req(regions[k] == v, f"Region {k}: expected {v}, got {regions[k]}")
req(set(regions) == set(expected_regions), f"Unexpected/missing regions: {sorted(set(regions)^set(expected_regions))}")

# Every explicitly paired bone should have a left/right mate with the same base ID.
paired = [b for b in bones if b.get("paired")]
groups = defaultdict(set)
for b in paired:
    if b["id"].endswith("_left"):
        base = b["id"][:-5]
    elif b["id"].endswith("_right"):
        base = b["id"][:-6]
    else:
        # Indexed hand/foot IDs carry side as final token.
        parts = b["id"].rsplit("_",1)
        base = parts[0]
    groups[base].add(b["side"])
for base,sides in groups.items():
    req(sides == {"left","right"}, f"Paired bone {base} lacks left/right mate: {sorted(sides)}")

# Required conventional adult fused structures.
byid = {b["id"]: b for b in bones}
for x in ("sacrum","coccyx","hip_bone_left","hip_bone_right"):
    req(byid.get(x,{}).get("adult_fused") is True, f"{x} must be marked adult_fused")

summary = {
    "total": len(bones),
    "axial": div["axial"],
    "appendicular": div["appendicular"],
    "regions": dict(sorted(regions.items())),
    "unique_ids": len(set(ids)),
    "errors": errors,
}
print(json.dumps(summary, indent=2))
raise SystemExit(1 if errors else 0)
