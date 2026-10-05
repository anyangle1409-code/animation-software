#!/usr/bin/env python3
"""Return whether a finalized repair workspace requires a package-specific diagnostic.

Exit codes:
  0 = diagnostic required
  3 = diagnostic not required
  2 = invalid workspace/diagnostic
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

PROFILES={
  "shoulder_layer":{
    "packages":{"RP-NECK-TRAP-001","RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004"}
  }
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--diagnostic",required=True,choices=sorted(PROFILES))
    a=ap.parse_args()
    try:
        ws=Path(a.workspace)
        p=ws/"workspace_manifest.json"
        if not p.is_file(): raise ValueError("workspace_manifest.json missing")
        d=json.loads(p.read_text(encoding="utf-8"))
        if d.get("status")!="PRE_EDIT_REPAIR_WORKSPACE": raise ValueError("unexpected workspace status")
        selected=set(d.get("repair_package_ids") or [])
        if not selected: raise ValueError("workspace repair_package_ids missing")
        required=bool(selected & PROFILES[a.diagnostic]["packages"])
        print(json.dumps({"diagnostic":a.diagnostic,"required":required,"selected_packages":sorted(selected)},indent=2))
        return 0 if required else 3
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__":
    raise SystemExit(main())
