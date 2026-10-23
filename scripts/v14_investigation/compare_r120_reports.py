#!/usr/bin/env python3
"""Compare a replayed R120's reports with the archived ones (evidence/archive_R120) - plain Python.

usage: python3 compare_r120_reports.py <repo root> <replayed legs-only base dir> <replayed rebuild dir> <out.json>
"""
import json
import sys
from pathlib import Path


def leaves(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def main():
    repo, lb, rb, out = (Path(a) for a in sys.argv[1:5])
    arc = repo / "scripts/v14_investigation/evidence/archive_R120"
    R = {}
    for name, new, old in (("legs_only_base", lb / "legs_v2_report.json", arc / "LB_legs_only_base_report.json"),
                           ("rebuild", rb / "rebuild_report.json", arc / "RB2_rebuild_report.json")):
        a, b = dict(leaves(json.loads(old.read_text()))), dict(leaves(json.loads(new.read_text())))
        R[f"{name}_leaves"] = len(a)
        R[f"{name}_differing"] = [(k, a[k], b.get(k)) for k in a if a[k] != b.get(k)]
    R["R120_vertices"] = json.loads((rb / "rebuild_report.json").read_text())["verts_before_after"]
    R["PASS_reports_identical"] = not R["legs_only_base_differing"] and not R["rebuild_differing"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(R, indent=1)); print(json.dumps(R, indent=1))
    return 0 if R["PASS_reports_identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
