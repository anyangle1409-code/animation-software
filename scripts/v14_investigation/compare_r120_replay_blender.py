"""Compare a replayed R120 (L0 replay -> legs-only base at bee05007 -> rebuild at d5141ad3) with the archived R120
(the session's RB2 build) - read-only.

Checks: vertex / triangle counts; positions (same index order) max deviation; triangles identical; vertex-group
weights max deviation; every shape key's max deviation; the two rebuild_report.json and legs-only base reports.

usage: python3.13 compare_r120_replay_blender.py -- <replayed.blend> <archived.blend> <replayed report dir>
                                                   <archive report dir (RB2_rebuild_report.json, LB_legs_only_base_report.json)> <out.json>
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
A, B, RREP, AREP, OUTF = (Path(a) for a in args[:5])


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    ob = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]; me = ob.data
    n = len(me.vertices)
    P = np.empty(n * 3); me.vertices.foreach_get("co", P)
    T = np.array([p.vertices[:] for p in me.polygons])
    G = [g.name for g in ob.vertex_groups]; W = np.zeros((n, len(G)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            W[v.index, g.group] = g.weight
    K = {}
    for kb in (me.shape_keys.key_blocks if me.shape_keys else []):
        c = np.empty(n * 3); kb.data.foreach_get("co", c); K[kb.name] = c.reshape(-1, 3)
    return P.reshape(-1, 3), T, G, W, K


def leaves(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


Pa, Ta, Ga, Wa, Ka = load(A)
Pb, Tb, Gb, Wb, Kb = load(B)
R = {"vertices": [len(Pa), len(Pb)], "triangles": [len(Ta), len(Tb)]}
if len(Pa) == len(Pb):
    R["positions_max_dev_mm"] = float(np.abs(Pa - Pb).max() * 1000)
    R["triangles_identical"] = bool(Ta.shape == Tb.shape and np.array_equal(Ta, Tb))
    R["groups_identical_names"] = Ga == Gb
    R["weights_max_dev"] = float(np.abs(Wa - Wb).max()) if Ga == Gb else None
    R["shape_keys_max_dev_mm"] = max(float(np.abs(Ka[k] - Kb[k]).max() * 1000) for k in Ka) if set(Ka) == set(Kb) else None
for name, ra, rb in (("rebuild_report", RREP / "rebuild_report.json", AREP / "RB2_rebuild_report.json"),
                     ("legs_only_base_report", RREP / "legs_v2_report.json", AREP / "LB_legs_only_base_report.json")):
    if ra.exists() and rb.exists():
        la, lb = dict(leaves(json.loads(ra.read_text()))), dict(leaves(json.loads(rb.read_text())))
        R[f"{name}_leaves"] = len(lb)
        R[f"{name}_differing"] = [(k, lb[k], la.get(k)) for k in lb if la.get(k) != lb[k]]
R["PASS_archived_R120_reproduced"] = bool(R["vertices"][0] == R["vertices"][1] and R.get("triangles_identical")
                                          and R.get("positions_max_dev_mm", 9) < 0.01)
OUTF.parent.mkdir(parents=True, exist_ok=True)
OUTF.write_text(json.dumps(R, indent=1))
print("R120_COMPARE", json.dumps(R)[:3000], flush=True)
