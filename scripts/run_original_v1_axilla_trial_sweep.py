#!/usr/bin/env python3
"""Run and select deterministic local axilla corrective trials from one prepared arc dump.

No Blender file is created or modified. Each trial invokes the existing first-party optimizer
against the same source dump and pre-edit declaration. The default area weights are a
three-point bracket (0.25x, 1x, 4x) around the established edge-hinge weight. This is
engineering triage only; it never accepts or promotes a candidate.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPT = ROOT / "scripts" / "optimize_original_v1_shoulder_corrective.py"
SPEC = ROOT / "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json"

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def collect(report):
    rows = report["entries"]
    if not rows:
        raise ValueError("trial report has no active entries")
    required = ("edge_max_before","edge_max_after","edge_min_before","edge_min_after",
                "torso_drift_max_before_m","torso_drift_max_after_m",
                "signed_area_min_before","signed_area_min_after",
                "faces_below_area_min_before","faces_below_area_min_after",
                "flipped_faces_before","flipped_faces_after")
    for row in rows:
        miss=[k for k in required if k not in row]
        if miss: raise ValueError("trial report missing: "+", ".join(miss))
    return {
        "min_signed_before": min(float(r["signed_area_min_before"]) for r in rows),
        "min_signed_after": min(float(r["signed_area_min_after"]) for r in rows),
        "max_below_before": max(int(r["faces_below_area_min_before"]) for r in rows),
        "max_below_after": max(int(r["faces_below_area_min_after"]) for r in rows),
        "max_flips_after": max(int(r["flipped_faces_after"]) for r in rows),
        "max_edge_max_rise": max(float(r["edge_max_after"])-float(r["edge_max_before"]) for r in rows),
        "max_edge_min_drop": max(float(r["edge_min_before"])-float(r["edge_min_after"]) for r in rows),
        "max_drift_rise_m": max(float(r["torso_drift_max_after_m"])-float(r["torso_drift_max_before_m"]) for r in rows),
        "max_abs_delta_m": float(report["max_abs_delta_m"]),
        "final_loss": float(report["final_loss"]),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dump",type=Path); ap.add_argument("declaration",type=Path); ap.add_argument("out_dir",type=Path)
    ap.add_argument("--area-min",type=float,default=0.20)
    ap.add_argument("--area-multipliers",default="0.25,1,4")
    ap.add_argument("--hinge-weight",type=float,default=20000.0)
    ap.add_argument("--hold-region-max",type=float,default=None,help="hold family: a region maximum may rise by at most this margin (must stay inside the comparator region-max tolerance)")
    ap.add_argument("--hold-scope",choices=("region","local"),default=None,help="hold family: bound scope (local = the mask edges of each pose, as the trial selection measures them)")
    ap.add_argument("--w-hold",type=float,default=None,help="hold family: separate, stronger hinge weight for the regional guards")
    ap.add_argument("--contact-guard",action="store_true",
                    help="with --hold-region-min: also enable the no-new-contact barrier in the hold trial family (guards against new self-intersections)")
    ap.add_argument("--hold-region-min",type=float,default=None,
                    help="optional extra trial family: also hold each region's current minimum edge ratio (minus this margin) in every pose; selection rules are unchanged")
    ap.add_argument("--canonical-solution",type=Path); ap.add_argument("--canonical-report",type=Path)
    a=ap.parse_args()
    if a.out_dir.exists(): raise SystemExit("refusing to overwrite trial directory: "+str(a.out_dir))
    multipliers=[float(x) for x in a.area_multipliers.split(",") if x.strip()]
    if not multipliers or any(x<=0 for x in multipliers) or len(set(multipliers))!=len(multipliers):
        raise SystemExit("area multipliers must be positive and unique")

    tol=load(SPEC)["comparison_tolerances"]
    edge_max_tol=float(tol["region_max_ratio_rise"]); edge_min_tol=float(tol["region_min_ratio_drop"])
    drift_tol=1e-9
    a.out_dir.mkdir(parents=True)
    trials=[]
    families=[(None,"")]
    if a.hold_region_min is not None:
        if not 0.0 <= a.hold_region_min < 0.02:
            raise SystemExit("--hold-region-min must stay inside the comparator region-min tolerance (0 <= m < 0.02)")
        families.append((a.hold_region_min,"_hold"))
    for hold,suffix in families:
      for mult in multipliers:
        label=("area_%gx"%mult).replace(".","p")+suffix
        sol=a.out_dir/(label+".npz"); report=a.out_dir/(label+".json")
        cmd=[sys.executable,str(OPT),str(a.dump),str(sol),"--mask-file",str(a.declaration),
             "--hi","3.6","--lo","0.30","--w-hinge",str(a.hinge_weight),"--w-trunk","3000000",
             "--w-area",str(a.hinge_weight*mult),"--area-min",str(a.area_min),
             "--w-fold","0","--w-prox","0","--rounds","3","--w-smooth","300","--w-mag","2","--iters","300",
             "--json-out",str(report)]
        if hold is not None:
            cmd += ["--hold-region-min",str(hold)]
            if a.hold_region_max is not None:
                if not 0.0 <= a.hold_region_max < edge_max_tol: raise SystemExit("--hold-region-max must stay inside the comparator region-max tolerance")
                cmd += ["--hold-region-max",str(a.hold_region_max)]
            if a.hold_scope is not None:
                cmd += ["--hold-scope",a.hold_scope]
            if a.w_hold is not None:
                cmd += ["--w-hold",str(a.w_hold)]
            if a.contact_guard:
                # no-new-contact barrier (non-neighbouring mask vertices may not approach closer than in the same-pose base surface)
                i=cmd.index("--w-prox"); cmd[i+1]="3000000"; cmd += ["--prox-d","0.02"]
        p=subprocess.run(cmd,cwd=ROOT)
        if p.returncode: raise SystemExit(f"trial {label} failed with exit code {p.returncode}")
        m=collect(load(report))
        feasible=(m["max_flips_after"]==0 and m["max_below_after"]<=m["max_below_before"]
                  and m["max_edge_max_rise"]<=edge_max_tol+1e-12
                  and m["max_edge_min_drop"]<=edge_min_tol+1e-12
                  and m["max_drift_rise_m"]<=drift_tol
                  and m["min_signed_after"]>=m["min_signed_before"]-1e-12)
        trials.append({"label":label,"area_multiplier":mult,"w_area":a.hinge_weight*mult,
                       "solution":sol.name,"report":report.name,"feasible_for_apply_trial":feasible,**m})

    feasible=[x for x in trials if x["feasible_for_apply_trial"]]
    feasible.sort(key=lambda x:(x["max_flips_after"],x["max_below_after"],-x["min_signed_after"],
                                x["max_abs_delta_m"],x["final_loss"],x["w_area"]))
    selected=feasible[0] if feasible else None
    result={"schema_version":1,"purpose":"numeric pre-apply selection only; no acceptance/promotion",
            "area_reference":"same_pose_uncorrected_lbs",
            "selection_rules":{"max_flipped_faces_after":0,"below_area_faces_may_increase":False,
              "region_max_ratio_rise_tolerance":edge_max_tol,"region_min_ratio_drop_tolerance":edge_min_tol,
              "torso_drift_worsening_tolerance_m":drift_tol,"minimum_signed_area_may_worsen":False},
            "trials":trials,"selected_trial":selected["label"] if selected else None,
            "status":"TRIAL_SELECTED_FOR_APPLY_VALIDATION" if selected else "NO_NUMERICALLY_SAFE_TRIAL",
            "production_approved":False}
    selection=a.out_dir/"selection.json"; selection.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if not selected:
        print("NO NUMERICALLY SAFE AXILLA TRIAL; inspect",selection); return 1
    if a.canonical_solution and a.canonical_report:
        if a.canonical_solution.exists() or a.canonical_report.exists():
            raise SystemExit("canonical solution/report exists; refusing overwrite")
        shutil.copyfile(a.out_dir/selected["solution"],a.canonical_solution)
        shutil.copyfile(a.out_dir/selected["report"],a.canonical_report)
    print("AXILLA TRIAL SELECTED",selected["label"])
    return 0
if __name__=="__main__": raise SystemExit(main())
