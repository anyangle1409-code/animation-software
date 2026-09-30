"""Priority-1 shoulder/upper-torso weight repair for the ORIGINAL v1 O4 CANDIDATE.

blender --background --factory-startup <source candidate.blend> \
        --python scripts/repair_original_v1_o4_shoulder_weights_blender.py -- <new candidate.blend> [preset]

Project-authored, deterministic edits of the candidate's OWN weights (no data
from any other character). The source candidate is never overwritten: the
result is saved as a new numbered candidate and a JSON record of every
parameter is written next to it.

Evidence (shoulder_weights_r2_before_repair.json + a spatial probe):
  * upper back z 1.24-1.40 is 70-99 % scapula; the v4 scapula pivots at the
    glenoid, so rhythm poses swing the whole ribcage (volume ~1.13);
  * deltoid cap front/back stays 40-87 % clavicle/scapula, so the cap does not
    follow the arm overhead and single edges stretch ~9x;
  * the arm/torso transition is concentrated over a few rings.

Operations (left side authored, right side mirrored; region-limited):
  A  deltoid cap -> upperarm share rising with lateral distance from the neck;
  B  most scapula ownership on the back/lats moved to spine_03/spine_02,
     leaving a reduced scapula share over the blade itself;
  C  wider, permission-bounded smoothing band around the glenohumeral joint;
then max 4 influences and normalisation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("Usage: ... -- <new candidate.blend> [preset]")
OUT = Path(args[0]).resolve()
PRESET = args[1] if len(args) > 1 else "r3"
SRC = Path(bpy.data.filepath).resolve()
if OUT == SRC or OUT.exists():
    raise SystemExit("Refusing to overwrite: choose a new, numbered candidate path.")
scene = bpy.context.scene
if not scene.get("hgpt_not_production"):
    raise SystemExit("Candidate files only.")

PRESETS = {
    # r3: rejected (shoulder_r3) - fixed press_top collapse but regressed rhythm poses.
    "r3": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
               scap_keep=0.40, scap_zmax=1.50, band_radius=0.20, band_iters=10, band_rate=0.5,
               axilla_radius=0.0, axilla_iters=0),
    # r4: stretch probe put every 5-9.7x edge in the axilla vault -> harmonic
    # (Laplace) weight interpolation across the axilla zone; milder back rebalance.
    "r4": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
               scap_keep=0.60, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
               axilla_radius=0.085, axilla_iters=120),
    # r5: r4 cut the axilla peak (press_top 9.09 -> 5.79) but the arm absorbed
    # stretch (arm max ~3.7 -> 4.2). Keep arm vertices as the fixed boundary.
    "r5": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
               scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
               axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    # ablations of r5 (which op causes the remaining small regressions?)
    "r6": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.0,          # no deltoid-cap raise
               scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
               axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    "r7": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
               scap_keep=1.0, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,  # no back rebalance
               axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    # ablation result: B is harmless/helpful; the 8 small r5 regressions come
    # from A (cap raise too strong -> cap pushes into trapezius/neck overhead).
    "r8": dict(cap_lx0=0.180, cap_lx1=0.250, cap_zmin=1.37, cap_max=0.55,
               scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
               axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    "r9": dict(cap_lx0=0.175, cap_lx1=0.250, cap_zmin=1.37, cap_max=0.65,
               scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
               axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    # r8/r9 (weaker cap) re-open the collapse; r5's residual compression sits on
    # the acromion (z 1.52-1.54) where the cap raise leaves a 0.66/0.51 step.
    # The acromion is scapula anatomy: taper the cap raise with height.
    "r10": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
                cap_ztaper0=1.47, cap_ztaper1=1.545, cap_top_factor=0.55,
                scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
                axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    # r10 taper too strong (pull-up hang top collapse 0.107): milder, higher taper.
    # r13/r14: r10 / r5 plus a harmonic acromion patch (operation E).
    "r13": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
                cap_ztaper0=1.47, cap_ztaper1=1.545, cap_top_factor=0.55,
                scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
                axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso"),
                acro_radius=0.05, acro_iters=80),
    "r14": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
                scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
                axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso"),
                acro_radius=0.05, acro_iters=80),
    "r11": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.82,
                cap_ztaper0=1.49, cap_ztaper1=1.55, cap_top_factor=0.75,
                scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
                axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
    "r12": dict(cap_lx0=0.165, cap_lx1=0.245, cap_zmin=1.37, cap_max=0.76,
                cap_ztaper0=1.49, cap_ztaper1=1.55, cap_top_factor=0.75,
                scap_keep=0.50, scap_zmax=1.50, band_radius=0.20, band_iters=4, band_rate=0.5,
                axilla_radius=0.085, axilla_iters=120, axilla_regions=("shoulder", "torso")),
}
P = PRESETS[PRESET]

rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
names = json.loads(scene["hgpt_region_names"])
reg = np.array([names[d.value] for d in body.data.attributes["hgpt_region"].data])
V = np.array([v.co[:] for v in body.data.vertices])
deform = [b.name for b in rig.data.bones if b.use_deform]
bidx = {n: i for i, n in enumerate(deform)}
gname = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(V), len(deform)))
for v in body.data.vertices:
    for g in v.groups:
        n = gname[g.group]
        if n in bidx:
            W[v.index, bidx[n]] = g.weight
before = W.copy()


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def set_share(i, bone, share):
    """Give `bone` the given share of vertex i, scaling the others to fill the rest."""
    j = bidx[bone]
    rest = W[i].sum() - W[i, j]
    W[i, j] = share
    if rest > 1e-9:
        others = [k for k in range(len(deform)) if k != j]
        W[i, others] *= (1.0 - share) / rest
    elif share < 1.0:
        W[i, j] = 1.0


nbrs = [[] for _ in range(len(V))]
for e in body.data.edges:
    a, b = e.vertices
    nbrs[a].append(b)
    nbrs[b].append(a)

stats = {}
for s, sx in (("l", -1.0), ("r", 1.0)):
    side = (V[:, 0] * sx) > 1e-6
    lx = V[:, 0] * sx                      # lateral distance from the midline
    H = np.array(rig.data.bones[f"upperarm_{s}"].head_local[:])
    ua, clav, scap = f"upperarm_{s}", f"clavicle_{s}", f"scapula_{s}"

    # A: deltoid cap follows the humerus, rising with lateral distance
    capA = np.nonzero(side & np.isin(reg, ["shoulder"]) & (V[:, 2] > P["cap_zmin"]))[0]
    changedA = 0
    for i in capA:
        target = P["cap_max"] * smoothstep((lx[i] - P["cap_lx0"]) / (P["cap_lx1"] - P["cap_lx0"]))
        if "cap_ztaper0" in P:  # acromion (top) stays with the shoulder girdle
            t = smoothstep((V[i, 2] - P["cap_ztaper0"]) / (P["cap_ztaper1"] - P["cap_ztaper0"]))
            target *= 1.0 - (1.0 - P["cap_top_factor"]) * t
        if target > W[i, bidx[ua]] + 1e-6:
            set_share(i, ua, target)
            changedA += 1

    # B: back / lat skin: keep only part of the scapula share; move the rest to the spine
    back = (V[:, 1] > H[1] + 0.02)          # behind the shoulder joint (Blender +Y = back)
    zoneB = np.nonzero(side & np.isin(reg, ["torso", "shoulder"]) & back & (V[:, 2] < P["scap_zmax"]))[0]
    changedB = 0
    for i in zoneB:
        w = W[i, bidx[scap]]
        if w <= 1e-6:
            continue
        # over the blade itself (medial border to glenoid, upper back) keep more
        over_blade = smoothstep((V[i, 2] - 1.28) / 0.12) * smoothstep((0.19 - lx[i]) / 0.08)
        keep = P["scap_keep"] + (1.0 - P["scap_keep"]) * 0.35 * over_blade
        moved = w * (1.0 - keep)
        W[i, bidx[scap]] = w * keep
        spine = "spine_03" if V[i, 2] > 1.32 else "spine_02"
        W[i, bidx[spine]] += moved
        changedB += 1

    allowed = W > 1e-6
    for b in (ua, clav, scap, "spine_03", "spine_02", "neck"):
        allowed[:, bidx[b]] |= side & np.isin(reg, ["shoulder", "torso", "arm"])

    # D: harmonic weights across the axilla vault. Vertices inside the zone are
    # relaxed to the average of their neighbours (Jacobi iterations) while the
    # zone border stays fixed, so the arm-to-torso transition spreads over the
    # whole armpit instead of a few short vault edges.
    axilla_n = 0
    if P["axilla_radius"] > 0:
        C = np.array([sx * 0.176, H[1] + 0.02, H[2] - 0.105])   # axilla vault (Blender +Y = back)
        zone_regions = list(P.get("axilla_regions", ("shoulder", "torso", "arm")))
        inside = side & np.isin(reg, zone_regions) & (np.linalg.norm(V - C, axis=1) < P["axilla_radius"])
        zoneD = np.nonzero(inside)[0]
        axilla_n = int(len(zoneD))
        for _ in range(P["axilla_iters"]):
            avg = np.array([W[nbrs[i]].mean(axis=0) for i in zoneD])
            W[zoneD] = np.where(allowed[zoneD], avg, 0.0)
            W[zoneD] /= np.maximum(W[zoneD].sum(axis=1, keepdims=True), 1e-9)

    # E: harmonic weights across the acromion/deltoid-top patch. The min-edge
    # probe put every overhead compression (r10 pull-up hang 0.107, r12 rhythm
    # 0.07) on short edges here where the A-cap share jumps between neighbours.
    acro_n = 0
    if P.get("acro_radius", 0) > 0:
        CE = np.array([sx * 0.230, 0.045, 1.525])
        zoneE = np.nonzero(side & (reg == "shoulder") & (np.linalg.norm(V - CE, axis=1) < P["acro_radius"]))[0]
        acro_n = int(len(zoneE))
        for _ in range(P["acro_iters"]):
            avg = np.array([W[nbrs[i]].mean(axis=0) for i in zoneE])
            W[zoneE] = np.where(allowed[zoneE], avg, 0.0)
            W[zoneE] /= np.maximum(W[zoneE].sum(axis=1, keepdims=True), 1e-9)

    # C: wider, permission-bounded smoothing band around the glenohumeral joint
    dist = np.linalg.norm(V - H, axis=1)
    zoneC = np.nonzero(side & np.isin(reg, ["shoulder", "torso", "arm"]) & (dist < P["band_radius"]))[0]
    fall = (1.0 - dist[zoneC] / P["band_radius"])[:, None]
    for _ in range(P["band_iters"]):
        avg = np.array([W[nbrs[i]].mean(axis=0) for i in zoneC])
        W[zoneC] = np.where(allowed[zoneC], (1 - P["band_rate"] * fall) * W[zoneC] + P["band_rate"] * fall * avg, 0.0)
    stats[s] = {"cap_vertices_raised": changedA, "back_vertices_rebalanced": changedB,
                "axilla_harmonic_vertices": axilla_n, "acromion_harmonic_vertices": acro_n, "band_vertices_smoothed": int(len(zoneC))}

# max 4 influences, normalise
order = np.argsort(-W, axis=1)
keep = np.zeros_like(W, dtype=bool)
keep[np.arange(len(W))[:, None], order[:, :4]] = True
W = np.where(keep, W, 0.0)
W /= W.sum(axis=1, keepdims=True)

changed = np.nonzero(np.abs(W - before).sum(axis=1) > 1e-6)[0]
for n in deform:
    vg = body.vertex_groups.get(n)
    j = bidx[n]
    vg.remove([int(i) for i in changed])
    for i in changed:
        if W[i, j] > 1e-5:
            vg.add([int(i)], float(W[i, j]), "REPLACE")

scene["hgpt_candidate"] = f"O4_bind_shoulder_{PRESET}"
scene["hgpt_candidate_parent_sha256"] = hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
record = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "stage": "O4 candidate shoulder weight repair (not production)",
    "preset": PRESET, "parameters": P,
    "source_candidate": SRC.name,
    "source_sha256": scene["hgpt_candidate_parent_sha256"],
    "candidate": OUT.name,
    "candidate_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    "vertices_changed": int(len(changed)), "per_side": stats,
    "max_influences": int((W > 1e-5).sum(axis=1).max()),
    "weight_sum_error": float(np.abs(W.sum(axis=1) - 1).max()),
    "inputs": "this candidate's own ORIGINAL v1 mesh/weights and the v4 rig only",
}
OUT.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print("SHOULDER REPAIR", json.dumps(record))
