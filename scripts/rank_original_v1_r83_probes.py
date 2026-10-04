"""Rank r83 focused probe comparison JSONs against retained r81 with hard rejection rules.

Inputs are comparator JSONs produced by the existing project comparison tooling. Filenames should contain alpha
(e.g. cmp_r83_a0p20_P3B1.json). This script does no Blender work and changes no acceptance rule.

python scripts/rank_original_v1_r83_probes.py --r81 full_r81_comparison_vs_P3B1.json --out ranking.json probe*.json

Hard reject when a probe has development_failures > 0 (if supplied in its JSON/sidecar summary) or has more
strict regressions than r81. Shoulder-intersection preservation is reported from named shoulder poses and must be
confirmed before promotion. Ranking favours fewer regressions, then lower aggregate normalized severity.
"""
import argparse,json,re
from pathlib import Path

ap=argparse.ArgumentParser(); ap.add_argument("--r81",required=True); ap.add_argument("--out",required=True); ap.add_argument("probes",nargs="+"); a=ap.parse_args()
base=json.loads(Path(a.r81).read_text(encoding="utf-8-sig"))
bn=len(base.get("regressions",[]))
shoulder={"press_top","press_top_rhythm","pullup_hang","pullup_hang_rhythm"}

def alpha(p):
    m=re.search(r"a(?:lpha)?[_-]?(\d+)[p._](\d+)",Path(p).name,re.I)
    return float(m.group(1)+"."+m.group(2)) if m else None

def sev(rows):
    s=0.0
    for r in rows:
        b=float(r.get("baseline",0)); c=float(r.get("candidate",0)); d=abs(c-b)
        s += d/max(abs(b),1e-9)
    return s

rows=[]
for p in a.probes:
    j=json.loads(Path(p).read_text(encoding="utf-8-sig")); regs=j.get("regressions",[])
    dev=int(j.get("development_failures",j.get("summary",{}).get("development_failures",0)) or 0)
    ints=[r for r in regs if r.get("name") in shoulder and r.get("metric")=="self_intersecting_face_pairs"]
    hard=[]
    if dev: hard.append(f"development_failures={dev}")
    if len(regs)>bn: hard.append(f"strict_regressions={len(regs)}>{bn}")
    rows.append({"file":str(p),"alpha":alpha(p),"strict_regressions":len(regs),"normalized_severity":sev(regs),
                 "development_failures":dev,"shoulder_intersection_regressions":len(ints),
                 "shoulder_intersection_rows":ints,"decision":"REJECT" if hard else "REVIEW","reasons":hard})
eligible=[r for r in rows if r["decision"]!="REJECT"]
eligible.sort(key=lambda r:(r["shoulder_intersection_regressions"]>0,r["strict_regressions"],r["normalized_severity"],r["alpha"] if r["alpha"] is not None else 99))
best=eligible[0] if eligible else None
for r in rows:
    if best is r and r["shoulder_intersection_regressions"]==0 and r["strict_regressions"]<bn: r["decision"]="BEST_FOCUSED_CANDIDATE"
rec={"schema_version":1,"retained_r81_strict_regressions":bn,"ranking_rule":"hard reject development failure or >r81 strict count; prefer no shoulder-intersection regression, fewer strict regressions, lower normalized severity","probes":rows,
     "best":best,"boundary":"Focused ranking only. BEST_FOCUSED_CANDIDATE is not 3A clearance and does not authorize Phase 4; full project evidence remains mandatory."}
Path(a.out).write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8"); print(json.dumps(rec,indent=2))
