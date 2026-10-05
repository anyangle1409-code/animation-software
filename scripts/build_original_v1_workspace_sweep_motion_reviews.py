#!/usr/bin/env python3
"""Build all per-sweep motion review scaffolds required by a finalized workspace."""
from __future__ import annotations
import argparse,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILDER=ROOT/"scripts/build_original_v1_human_movement_sweep_motion_review.py"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def load_builder():
    sp=importlib.util.spec_from_file_location("sweep_motion_builder",BUILDER)
    if sp is None or sp.loader is None: raise ValueError("unable to load sweep motion builder")
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--workspace",required=True)
    ap.add_argument("--raw-sweep-report",required=True)
    a=ap.parse_args()
    try:
        ws=Path(a.workspace)
        fm=read(ws/"workspace_finalization_manifest.json")
        wm=read(ws/"workspace_manifest.json")
        raw=Path(a.raw_sweep_report)
        if not raw.is_file(): raise ValueError("raw sweep report missing")
        required=list(wm.get("validation_selection",{}).get("sweep_only_movements_requiring_generic_runner",[]) or [])
        builder=load_builder()
        created=[]
        for sid in required:
            out=ws/f"human_movement_sweep_motion_{sid.lower().replace('-','_')}_final.json"
            if out.exists(): raise ValueError(f"motion review already exists: {out}")
            d=builder.build(raw,sid,fm["candidate_revision"])
            if d.get("candidate_sha256")!=fm.get("final_candidate_sha256"):
                raise ValueError(f"{sid}: motion review candidate differs from finalized workspace")
            out.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
            created.append(out.name)
        print("WORKSPACE SWEEP MOTION REVIEWS: BUILT")
        print(json.dumps({"candidate_revision":fm["candidate_revision"],"sweeps":required,"files":created},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP - "+str(exc)); return 2
if __name__=="__main__": raise SystemExit(main())
