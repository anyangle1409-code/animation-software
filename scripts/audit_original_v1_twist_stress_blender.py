"""Read-only axial-twist (candy-wrapper) stress test for the bone-sufficiency audit (never saves the .blend).

blender --background --factory-startup <candidate.blend> --python-exit-code 1 ^
  --python scripts/audit_original_v1_twist_stress_blender.py -- <out.json> [segment,segment,...]

For each long segment (forearm, upperarm, thigh, shin; both sides tested, left reported) the neutral rest pose is twisted ABOUT
THE SEGMENT'S OWN AXIS by increasing angles with nothing else moved (the child chain follows rigidly, as in a pronating
forearm). The skinned mesh is evaluated and the limb is sliced along the segment axis: for every slice the mean distance of the
slice vertices from the posed axis is compared with the rest value. A twist concentrated at one end (no distribution of
the axial rotation along the segment) pinches the slice nearest the joint where the weights hand over to the next bone:
this is the 'candy-wrapper' signature. Also reported: worst per-region edge min ratio, volume ratio.

Interpretation (project policy docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md): a twist helper is justified only
if the slice radius collapses at physiologically required twist angles even though joint motion and weights are otherwise correct.
Physiological axial range used for the test: forearm pronation/supination 0..90 each way (test to 150 as a stress margin),
humeral rotation +-90, femoral rotation +-45, tibial rotation +-30 (stress margin 60).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <out.json> [segment,...]")
OUT = Path(args[0]).resolve()
ONLY = set(args[1].split(",")) if len(args) > 1 and args[1] else None

pose_script = Path(__file__).with_name("pose_test_original_v1_o4_candidate_blender.py")
src = pose_script.read_text(encoding="utf-8")
src_defs = src[:src.index("# ---------------------------------------------------------------- metrics")]
saved_argv = sys.argv
sys.argv = ["blender", "--", tempfile.mkdtemp(), ""]
ns = {"__name__": "pose_defs", "__file__": pose_script.name}
exec(compile(src_defs, "pose_test_defs", "exec"), ns)
sys.argv = saved_argv
rig, body, pb, reset, upd, rot, bdir = ns["rig"], ns["body"], ns["pb"], ns["reset"], ns["upd"], ns["rot"], ns["bdir"]
_mask = body.modifiers.get("HGPT_DRESSED_MASK")
if _mask is not None:
    _mask.show_viewport = False
    _mask.show_render = False
region_names = json.loads(bpy.context.scene["hgpt_region_names"])
group_names = {vg.index: vg.name for vg in body.vertex_groups}
vreg = np.array([d.value for d in body.data.attributes["hgpt_region"].data])
rest_V = np.array([v.co[:] for v in body.data.vertices])
edges = np.array([e.vertices[:] for e in body.data.edges])
rest_len = np.linalg.norm(rest_V[edges[:, 0]] - rest_V[edges[:, 1]], axis=1)
all_ids = list(range(len(rest_V)))

SEGMENTS = {          # segment bone, region name that owns its flesh, angles tested (deg, applied one side only)
    "forearm": ("forearm_l", "arm", [45, 90, 150]),
    "upperarm": ("upperarm_l", "arm", [45, 90, 135]),
    "thigh": ("thigh_l", "leg", [30, 45, 90]),
    "shin": ("shin_l", "leg", [20, 30, 60]),
}
NBIN = 12


def evaluated():
    return ns["evaluated_positions"](all_ids)


def slices(bone, pos, rest_pos=None):
    """Mean distance of the segment's vertices from the (posed) axis, per bin along the axis."""
    b = rig.data.bones[bone]
    h0, t0 = np.array(b.head_local[:]), np.array(b.tail_local[:])
    ax0 = (t0 - h0) / np.linalg.norm(t0 - h0)
    L = np.linalg.norm(t0 - h0)
    rel = rest_V - h0
    t = rel @ ax0 / L
    rad = np.linalg.norm(rel - np.outer(t * L, ax0), axis=1)
    return t, rad


def axis_radius(bone, P, t, sel):
    p = pb(bone)
    h, tl = np.array(p.head[:]), np.array(p.tail[:])
    ax = (tl - h) / np.linalg.norm(tl - h)
    rel = P - h
    return np.linalg.norm(rel - np.outer(rel @ ax, ax), axis=1)


results = {}
for seg, (bone, region, angles) in SEGMENTS.items():
    if ONLY and seg not in ONLY:
        continue
    reset()
    rig.location = (0, 0, 0)
    rest_P = evaluated()
    t, rad0 = slices(bone, rest_V)
    side_x = rest_V[:, 0] < 0                              # the left limb (character's left is -X)
    sel = (np.abs(t - 0.5) <= 0.5) & (vreg == region_names.index(region)) & side_x & (rad0 > 1e-4)
    rest_axis_rad = axis_radius(bone, rest_P, t, sel)
    edges_sel = sel[edges[:, 0]] & sel[edges[:, 1]]
    bins = np.clip((t * NBIN).astype(int), 0, NBIN - 1)
    rows = []
    for ang in angles:
        for sign in (1, -1):
            reset()
            rig.location = (0, 0, 0)
            rot(bone, bdir(bone), sign * ang)
            P = evaluated()
            ar = axis_radius(bone, P, t, sel)
            prof = []
            for k in range(NBIN):
                m = sel & (bins == k)
                prof.append(round(float(ar[m].mean() / rest_axis_rad[m].mean()), 4) if m.sum() >= 6 else None)
            el = np.linalg.norm(P[edges[:, 0]] - P[edges[:, 1]], axis=1) / rest_len
            ratios = el[edges_sel]
            vals = [x for x in prof if x is not None]
            worst = []
            if sign > 0:
                idx = np.nonzero(edges_sel)[0]
                for k in idx[np.argsort(el[idx])[:3]].tolist() + idx[np.argsort(-el[idx])[:3]].tolist():
                    a, b = edges[k]
                    worst.append({"ratio": round(float(el[k]), 3), "rest_mid": [round(float(x), 3) for x in (rest_V[a] + rest_V[b]) / 2],
                                  "weights_a": {group_names[g.group]: round(g.weight, 3) for g in body.data.vertices[a].groups if g.weight > 0.01},
                                  "weights_b": {group_names[g.group]: round(g.weight, 3) for g in body.data.vertices[b].groups if g.weight > 0.01}})
            rows.append({"worst_edges": worst, "twist_deg": sign * ang, "slice_radius_ratio_profile": prof,
                         "min_slice_radius_ratio": round(min(vals), 4), "max_slice_radius_ratio": round(max(vals), 4),
                         "segment_edge_min_ratio": round(float(ratios.min()), 4),
                         "segment_edge_max_ratio": round(float(ratios.max()), 4)})
    results[seg] = {"bone": bone, "region": region, "vertices": int(sel.sum()), "tests": rows}
    worst = min(r["min_slice_radius_ratio"] for r in rows)
    print("TWIST", seg, "worst slice radius ratio", worst)
reset()
source = Path(bpy.data.filepath)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
                           "purpose": "axial twist / candy-wrapper stress test (read-only)", "source_candidate": source.name,
                           "source_candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                           "pose_definition_script_sha256": hashlib.sha256(pose_script.read_bytes()).hexdigest(),
                           "results": results}, indent=1) + "\n", encoding="utf-8")
print("TWIST STRESS", OUT)
