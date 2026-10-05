#!/usr/bin/env python3
"""Resolve required generic sweep evidence from a finalized repair workspace."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTACT=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_CONTACT_REQUIREMENTS.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workspace",required=True); ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    try:
        ws=Path(a.workspace); wm=read(ws/"workspace_manifest.json")
        if wm.get("status")!="PRE_EDIT_REPAIR_WORKSPACE": raise ValueError("workspace manifest identity invalid")
        if not (ws/"workspace_finalization_manifest.json").is_file(): raise ValueError("workspace is not finalized")
        sweeps=list(wm.get("validation_selection",{}).get("sweep_only_movements_requiring_generic_runner",[]) or [])
        contact_ids=set(read(CONTACT).get("sweeps",{}))
        contacts=[x for x in sweeps if x in contact_ids]
        out=Path(a.out_dir)
        if out.exists() and any(out.iterdir()): raise ValueError("output directory is not empty")
        out.mkdir(parents=True,exist_ok=True)
        (out/"required_sweeps.txt").write_text(",".join(sweeps)+"\n",encoding="utf-8")
        (out/"contact_sweeps.txt").write_text(",".join(contacts)+"\n",encoding="utf-8")
        result={"schema_version":1,"status":"WORKSPACE_SWEEP_REQUIREMENTS","repair_package_ids":wm.get("repair_package_ids",[]),"required_sweeps":sweeps,"contact_sweeps":contacts}
        (out/"workspace_sweep_requirements.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print("WORKSPACE SWEEP REQUIREMENTS: PASS"); print(json.dumps(result,indent=2)); return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
