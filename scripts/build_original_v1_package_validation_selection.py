#!/usr/bin/env python3
"""Select deterministic validation poses/sweeps for ORIGINAL-v1 repair packages."""
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGES=ROOT/"ORIGINAL_V1_ANATOMICAL_REPAIR_PACKAGES.json"
POSE_MAP=ROOT/"ORIGINAL_V1_POSE_MOVEMENT_FAMILY_MAP.json"
SWEEPS=ROOT/"ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PLAN.json"

def read(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def uniq(xs):
    out=[]; seen=set()
    for x in xs:
        if x not in seen:
            out.append(x); seen.add(x)
    return out

def build(package_ids):
    packages=read(PACKAGES); posemap=read(POSE_MAP); sweeps=read(SWEEPS)
    pby={x["id"]:x for x in packages.get("packages",[])}
    unknown=[x for x in package_ids if x not in pby]
    if unknown: raise ValueError(f"unknown repair packages {unknown}")
    proof=uniq([m for pid in package_ids for m in pby[pid].get("proof_movements",[])])
    pose_mappings=posemap.get("mappings") or {}
    sweep_names=set((sweeps.get("sweeps") or {}).keys())
    poses=["neutral"]
    coverage=[]
    for movement in proof:
        matched=[pose for pose,moves in pose_mappings.items() if movement in moves]
        if matched:
            for pose in matched:
                if pose not in poses: poses.append(pose)
        via_sweep=movement in sweep_names
        mechanisms=[]
        if matched: mechanisms.append("POSE_FIXTURE")
        if via_sweep: mechanisms.append("DETERMINISTIC_SWEEP")
        coverage.append({
          "movement_family":movement,
          "pose_fixtures":matched,
          "deterministic_sweep":movement if via_sweep else None,
          "mechanisms":mechanisms,
          "validation_definition_present":bool(mechanisms),
          "immediately_runnable_via_frozen_pose_harness":bool(matched),
          "requires_generic_sweep_runner":via_sweep and not bool(matched)
        })
    uncovered=[x["movement_family"] for x in coverage if not x["validation_definition_present"]]
    sweep_only=[x["movement_family"] for x in coverage if x["requires_generic_sweep_runner"]]
    return {
      "schema_version":1,
      "status":"PACKAGE_VALIDATION_SELECTION",
      "production_approved":False,
      "repair_package_ids":package_ids,
      "proof_movement_families":proof,
      "pose_names":poses,
      "pose_csv":",".join(poses),
      "deterministic_sweep_names":[x["movement_family"] for x in coverage if x["deterministic_sweep"]],
      "coverage":coverage,
      "uncovered_proof_movements":uncovered,
      "validation_definition_complete":not uncovered,
      "sweep_only_movements_requiring_generic_runner":sweep_only,
      "fully_runnable_via_frozen_pose_harness":not sweep_only,
      "rule":"Every repair-package proof movement must have an existing frozen pose fixture, a deterministic movement-sweep definition, or both. A sweep definition is planning authority only until a separate generic Blender sweep runner executes it; the frozen P3a pose harness must not be modified to manufacture coverage. Neutral is always included as a control pose."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--packages",required=True)
    ap.add_argument("--out")
    ap.add_argument("--poses-out")
    a=ap.parse_args()
    try:
        ids=[x.strip() for x in a.packages.split(",") if x.strip()]
        if not ids: raise ValueError("repair packages required")
        d=build(ids)
        if d["uncovered_proof_movements"]:
            raise ValueError(f"proof movements lack executable validation path: {d['uncovered_proof_movements']}")
        if a.out:
            p=Path(a.out)
            if p.exists(): raise ValueError(f"refusing to overwrite {p}")
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
        if a.poses_out:
            p=Path(a.poses_out)
            if p.exists(): raise ValueError(f"refusing to overwrite {p}")
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(d["pose_csv"]+"\n",encoding="utf-8")
        print("PACKAGE VALIDATION SELECTION: PASS")
        print(json.dumps({
          "packages":ids,
          "poses":d["pose_names"],
          "sweeps":d["deterministic_sweep_names"],
          "proof_movements":len(d["proof_movement_families"])
        },indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("STOP — "+str(exc)); return 2

if __name__=="__main__": raise SystemExit(main())
