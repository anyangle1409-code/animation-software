#!/usr/bin/env python3
"""Return whether selected repair packages require a package-specific diagnostic.

Supply either --workspace or --packages.

Exit codes:
  0 = diagnostic required
  3 = diagnostic not required
  2 = invalid input/diagnostic
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

PROFILES={
  "shoulder_layer":{
    "packages":{"RP-NECK-TRAP-001","RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004"}
  }
}

def selected_packages(workspace=None,packages=None):
    if bool(workspace)==bool(packages):
        raise ValueError("supply exactly one of --workspace or --packages")
    if workspace:
        p=Path(workspace)/"workspace_manifest.json"
        if not p.is_file(): raise ValueError("workspace_manifest.json missing")
        d=json.loads(p.read_text(encoding="utf-8"))
        if d.get("status")!="PRE_EDIT_REPAIR_WORKSPACE": raise ValueError("unexpected workspace status")
        selected=set(d.get("repair_package_ids") or [])
    else:
        selected={x.strip() for x in packages.split(",") if x.strip()}
    if not selected: raise ValueError("repair package selection missing")
    return selected

def main():
    ap=argparse.ArgumentParser()
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--workspace")
    group.add_argument("--packages")
    ap.add_argument("--diagnostic",required=True,choices=sorted(PROFILES))
    a=ap.parse_args()
    try:
        selected=selected_packages(a.workspace,a.packages)
        required=bool(selected & PROFILES[a.diagnostic]["packages"])
        print(json.dumps({"diagnostic":a.diagnostic,"required":required,"selected_packages":sorted(selected)},indent=2))
        return 0 if required else 3
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__":
    raise SystemExit(main())
