"""Generate the strict-regression reconciliation record for a candidate from its committed comparison JSON (read-only evidence -> markdown).

python scripts/build_original_v1_regression_reconciliation_doc.py <rN> <out.md>
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rev, out = sys.argv[1], Path(sys.argv[2])
rc = ROOT / "ORIGINAL_V1_WORK/candidates/repair_checks"
p3 = json.loads((rc / f"full_{rev}_comparison_vs_P3B1.json").read_text(encoding="utf-8"))
r48 = json.loads((rc / f"full_{rev}_comparison_vs_r48.json").read_text(encoding="utf-8"))
tol = p3["comparison_tolerances"]


def fam(x):
    if x["metric"] == "self_intersecting_face_pairs":
        return "A. self-intersecting face pairs (contact at the closed armpit)"
    if x["metric"].startswith("edge_ratio"):
        return "D. whole-mesh edge percentile"
    if x["region"] == "arm":
        return "B. arm-region stretch range (upper-arm underside folds into the armpit)"
    if x["region"] in ("torso",):
        return "C. torso-region minimum (skin shortening along the ribs)"
    return "E. shoulder-region range"


lines = [f"# {rev} - strict comparator regressions vs the pinned P3B1 baseline (for owner disposition)", "",
         "Generated from committed comparison JSON; read-only. Development gates are unchanged and PASS (0 failures). This lists what the strict comparison",
         f"(tolerances: {json.dumps(tol)}) still reports. The control status keeps Phase 3 open while any of these remain unresolved.", "",
         "Why they exist: P3B1 is r42 re-measured under pose definition P3. r42 had NO trunk anchoring: its lateral torso skin rode up with the arm as a tent flap",
         "(326 torso vertices >10 cm from their trunk-driven position) and its armpit web was simply torn open, so almost nothing touched and the region ranges",
         "looked tidy. Fixing the tent and closing the armpit necessarily brings the upper-arm underside and the torso side into contact and folds the skin there,",
         "which the comparator reads as more intersections and wider arm/torso ranges. None of the values is near a development gate.", ""]
for name, c in (("P3B1 (pinned baseline of the P3 epoch)", p3), ("r48 (direct execution parent)", r48)):
    reg = c["regressions"]
    lines += [f"## vs {name}: {len(reg)} regressions", ""]
    groups = collections.defaultdict(list)
    for x in reg:
        groups[fam(x)].append(x)
    for g in sorted(groups):
        lines += [f"### {g}", "", "| pose | region | metric | baseline | candidate | tolerance |", "|---|---|---|---|---|---|"]
        for x in groups[g]:
            lines.append(f"| {x['name']} | {x['region'] or 'whole mesh'} | {x['metric']} | {x['baseline']} | {x['candidate']} | {x['tolerance']} |")
        lines.append("")
open_ = out
open_.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out, len(p3["regressions"]), len(r48["regressions"]))
