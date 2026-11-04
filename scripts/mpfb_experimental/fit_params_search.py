"""Coordinate search of natural MakeHuman settings against the reference silhouettes (fitmeasure.py loss).

Only moderate settings are allowed (targets within +-1.0, muscle 0.5-1.0, weight 0.35-0.75) so the result stays a
natural body instead of inflated geometry.  usage: python3 fit_params_search.py <start params.json> <work dir> <rounds>
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

start, work, rounds = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
RUN = str(work / "run1.sh")
PARAMS = [("macro", "muscle", 0.5, 1.0), ("macro", "weight", 0.35, 0.75),
          ("t", "torso/torso-scale-depth-incr", -1, 1), ("t", "torso/measure-frontchest-dist-incr", -1, 1),
          ("t", "torso/torso-muscle-pectoral-incr", -1, 1), ("t", "torso/measure-shoulder-dist-incr", -1, 1),
          ("t", "torso/torso-scale-vert-incr", -1, 1), ("t", "neck/measure-neck-height-incr", -1, 1),
          ("t", "torso/torso-scale-horiz-incr", -1, 1), ("t", "hip/hip-scale-depth-incr", -1, 1),
          ("t", "buttocks/buttocks-volume-incr", -1, 1), ("t", "legs/upperleg-scale-depth-incr", -1, 1),
          ("t", "legs/measure-thigh-circ-incr", -1, 1), ("t", "legs/upperleg-muscle-incr", -1, 1),
          ("t", "legs/lowerleg-scale-depth-incr", -1, 1), ("t", "legs/measure-calf-circ-incr", -1, 1),
          ("t", "torso/torso-muscle-dorsi-incr", -1, 1), ("t", "arms/upperarm-shoulder-muscle-incr", -1, 1)]
cnt = [0]


def get(P, kind, name):
    return P["macros"][name] if kind == "macro" else P["targets"].get(name, 0.0)


def put(P, kind, name, v):
    if kind == "macro":
        P["macros"][name] = round(v, 3)
    elif abs(v) < 1e-6:
        P["targets"].pop(name, None)
    else:
        P["targets"][name] = round(v, 3)


def loss(P):
    cnt[0] += 1; tag = f"s{cnt[0]:03d}"; pf = work / f"{tag}.json"; pf.write_text(json.dumps(P))
    out = subprocess.run([RUN, str(pf), tag, "--quiet"], capture_output=True, text=True).stdout
    for ln in out.splitlines():
        if ln.startswith("LOSS"):
            subprocess.run(["rm", "-rf", str(work / tag)])
            return float(ln.split()[1])
    return 1e9


P = json.loads(start.read_text()); best = loss(P); log = [{"eval": cnt[0], "loss": best}]
print("START", best, flush=True)
step = 0.4
for rd in range(rounds):
    for kind, name, lo, hi in PARAMS:
        v0 = get(P, kind, name); improved = False
        for d in (step, -step):
            v = min(hi, max(lo, v0 + d))
            if abs(v - v0) < 1e-6:
                continue
            Q = copy.deepcopy(P); put(Q, kind, name, v); L = loss(Q)
            if L < best - 0.5:
                P, best, improved = Q, L, True
                print(f"r{rd} {name} {v0:.2f}->{v:.2f} loss {best:.1f}", flush=True)
                break
        log.append({"round": rd, "param": name, "value": get(P, kind, name), "loss": best})
    (work / "best.json").write_text(json.dumps(P, indent=1)); (work / "search_log.json").write_text(json.dumps(log, indent=1))
    step *= 0.5
print("BEST", best, json.dumps(P), flush=True)
