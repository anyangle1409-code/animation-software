"""Print where a study's new self-contacts are (Claude, 20 Oct 2026).  Reads the gate's native_final.json and the source rest mesh;
labels each contact vertex as trapezius region (R62), upper arm, or other, so the cause can be fixed rather than guessed.
  python3 print_contacts.py source.npz native_final.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

here = Path(__file__).resolve().parent
src = np.load(sys.argv[1]); rest = src["rest"]
rep = json.loads(Path(sys.argv[2]).read_text())
trap = set(np.load(here / "r62_upper_trap_region.npz")["vertex_ids"].tolist())
armw = np.load(here / "r63_arm_weights.npz")["upperarm_weight"].astype(float).max(axis=0)


def label(v):
    if v in trap:
        return "trapezius"
    if armw[v] >= 0.5:
        return "upper_arm"
    x, y, zz = rest[v]
    if zz > 1.6:
        return "neck_head"
    return "torso_other"


c = rep.get("contacts", [])
print("CONTACTS_TOTAL", len(c))
kinds = Counter(tuple(sorted((label(e["a"]), label(e["b"])))) for e in c)
print("CONTACTS_BY_REGION", json.dumps({f"{a}+{b}": n for (a, b), n in kinds.most_common()}))
samples = Counter(e["sample"] for e in c)
print("CONTACTS_BY_SAMPLE", json.dumps(dict(sorted(samples.items()))))
seen = set()
for e in c:
    key = (min(e["a"], e["b"]), max(e["a"], e["b"]))
    if key in seen:
        continue
    seen.add(key)
    if len(seen) > 25:
        break
    print("CONTACT", e["sample"], e["a"], label(e["a"]), np.round(rest[e["a"]], 3).tolist(), "|", e["b"], label(e["b"]), np.round(rest[e["b"]], 3).tolist())
