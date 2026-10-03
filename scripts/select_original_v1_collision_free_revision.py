#!/usr/bin/env python3
"""Select the next collision-free numbered ORIGINAL-v1 candidate revision.

Read-only. Scans actual on-disk candidate/evidence paths under ORIGINAL_V1_WORK/candidates
so partial local work reserves its revision too. It never creates, deletes, renames or
promotes a candidate.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/"ORIGINAL_V1_WORK"/"candidates"
REV=re.compile(r"(?<![A-Za-z0-9])r(\d+)(?![A-Za-z0-9])",re.I)


def revision_number(value:str)->int:
    m=re.fullmatch(r"r(\d+)",str(value),re.I)
    if not m:
        raise ValueError("numbered revision required, e.g. r55")
    return int(m.group(1))


def observed_revisions(root:Path)->dict[int,list[str]]:
    base=(root/"ORIGINAL_V1_WORK"/"candidates").resolve()
    rows={}
    if not base.exists():
        return rows
    for path in base.rglob("*"):
        try:
            rel=path.resolve().relative_to(base).as_posix()
        except ValueError:
            continue
        for match in REV.finditer(rel):
            n=int(match.group(1))
            rows.setdefault(n,[]).append(rel)
    return {n:sorted(set(paths)) for n,paths in sorted(rows.items())}


def choose(root:Path,after_revision:str)->dict:
    after=revision_number(after_revision)
    seen=observed_revisions(root)
    highest=max([after,*seen.keys()])
    target=highest+1
    return {
        "schema_version":1,
        "after_revision":f"r{after}",
        "highest_observed_revision":f"r{highest}",
        "selected_revision":f"r{target}",
        "observed_revision_count":len(seen),
        "collision_paths_for_selected_revision":seen.get(target,[]),
        "read_only":True,
        "production_approved":False,
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("after_revision")
    ap.add_argument("--plain",action="store_true")
    args=ap.parse_args()
    try:
        result=choose(ROOT,args.after_revision)
        if result["collision_paths_for_selected_revision"]:
            raise ValueError("internal selector collision")
        print(result["selected_revision"] if args.plain else json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError) as exc:
        print("STOP — "+str(exc), file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
