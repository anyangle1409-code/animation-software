"""Build an O4 *CANDIDATE* (not production): ORIGINAL v1 bound to hgpt_canonical_v4_original.

blender --background --factory-startup ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend \
        --python scripts/disable_addons_for_guarded_session.py \
        --python scripts/build_original_v1_o4_candidate_blender.py

The production O2 Blend is opened read-only and immediately saved under
ORIGINAL_V1_WORK/candidates/ (it is never written). O2 rules forbid binding in
the production Blend until the owner's neutral-anatomy review; the O2 handoff
allows deformation experiments in a separate file made from a passing
checkpoint. Nothing here may be merged back into the production Blend.

Weights are computed on this ORIGINAL mesh only:
  1. Blender's built-in bone-heat solve (stock algorithm, this mesh + v4 rig);
  2. project rules restrict each vertex to anatomically plausible bones
     (own side, own body part, own finger), with nearest-allowed-bone fallback;
  3. neighbour smoothing, max 4 influences, normalised.
No weights, bind data or geometry from any other character are read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_o2_body as generator  # noqa: E402

PROD = (ROOT / "ORIGINAL_V1_WORK" / "HomeGymPT_Male_ORIGINAL_v1.blend").resolve()
LOG = ROOT / "ORIGINAL_V1_WORK" / "O2_AUTHORING_LOG.jsonl"
OUT_DIR = ROOT / "ORIGINAL_V1_WORK" / "candidates"
CANDIDATE = OUT_DIR / "HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend"
REPORT = ROOT / "ORIGINAL_V1_WORK" / "candidates" / "O4_CANDIDATE_BUILD.json"
MAX_INFLUENCES = 4

if Path(bpy.data.filepath).resolve() != PROD:
    raise SystemExit("Open the production O2 Blend (read-only source) to build the candidate.")
source_sha = hashlib.sha256(PROD.read_bytes()).hexdigest()
entries = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
if not entries or entries[-1]["blend_sha256"] != source_sha:
    raise SystemExit("Production Blend does not match the latest passing O2 checkpoint.")
if bpy.context.preferences.addons:
    raise SystemExit("Disable all add-ons first (scripts/disable_addons_for_guarded_session.py).")

OUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(CANDIDATE))  # from here on, only the candidate is written
scene = bpy.context.scene
scene["hgpt_candidate"] = "O4_bind"
scene["hgpt_candidate_source_sha256"] = source_sha
scene["hgpt_not_production"] = True

body = bpy.data.objects["HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD"]
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
body.name = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"

# --- region labels from the (deterministic) generator; verify identity ---
gen = generator.build()
Vg = gen["vertices"]
Vm = np.array([v.co[:] for v in body.data.vertices])
if Vm.shape != Vg.shape or float(np.abs(Vm - Vg).max()) > 1e-5:
    raise SystemExit("Body mesh differs from the committed generator output; rebuild the O2 checkpoint first.")
vregion = np.empty(len(Vm), dtype=object)
for name, ids in gen["regions"].items():
    for i in ids:
        vregion[i] = name

# --- bind with the stock bone-heat solve ---
rig.data.bones["root"].use_deform = False
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")

bones = [b.name for b in rig.data.bones if b.use_deform]
bidx = {n: i for i, n in enumerate(bones)}
W = np.zeros((len(Vm), len(bones)))
for vg in body.vertex_groups:
    if vg.name not in bidx:
        continue
for v in body.data.vertices:
    for g in v.groups:
        name = body.vertex_groups[g.group].name
        if name in bidx:
            W[v.index, bidx[name]] = g.weight
heat_empty = int((W.sum(axis=1) < 1e-6).sum())

# --- anatomical permission rules ---
FINGERS = ("index", "middle", "ring", "pinky")
CENTRE = ["pelvis", "spine_01", "spine_02", "spine_03", "neck", "head"]


def side_bones(s):
    return {
        "arm": [f"clavicle_{s}", f"scapula_{s}", f"upperarm_{s}", f"forearm_{s}", f"hand_{s}"],
        "shoulder": [f"clavicle_{s}", f"scapula_{s}", f"upperarm_{s}"],
        "hand": [f"forearm_{s}", f"hand_{s}", f"thumb_01_{s}"] + [f"metacarpal_{f}_{s}" for f in FINGERS] + [f"{f}_01_{s}" for f in FINGERS],
        "thumb": [f"hand_{s}", f"thumb_01_{s}", f"thumb_02_{s}", f"thumb_03_{s}"],
        "leg": [f"thigh_{s}", f"shin_{s}", f"foot_{s}"],
        "foot": [f"shin_{s}", f"foot_{s}", f"toe_{s}"],
        "torso": [f"clavicle_{s}", f"scapula_{s}", f"upperarm_{s}", f"thigh_{s}"],
        "pelvis": [f"thigh_{s}"],
        "neck": [f"clavicle_{s}"],
    }


def rest_seg(name):
    b = rig.data.bones[name]
    return np.array(b.head_local[:]), np.array(b.tail_local[:])


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


allowed = np.zeros_like(W, dtype=bool)
region_centre = {
    "head": ["neck", "head"], "neck": ["spine_03", "neck", "head"],
    "shoulder": ["spine_02", "spine_03", "neck"], "torso": CENTRE[:5], "pelvis": ["pelvis", "spine_01"],
    "arm": [], "hand": [], "finger": [], "thumb": [], "leg": ["pelvis"], "foot": [],
}
for i, (p, reg) in enumerate(zip(Vm, vregion)):
    names = list(region_centre.get(reg, CENTRE))
    sides = ["l"] if p[0] < -1e-6 else ["r"] if p[0] > 1e-6 else ["l", "r"]
    for s in sides:
        if reg == "finger":
            best = None
            for f in FINGERS:
                d = min(float(seg_dist(p[None], *rest_seg(f"{f}_0{k}_{s}"))[0]) for k in (1, 2, 3))
                if best is None or d < best[0]:
                    best = (d, f)
            f = best[1]
            names += [f"hand_{s}", f"metacarpal_{f}_{s}", f"{f}_01_{s}", f"{f}_02_{s}", f"{f}_03_{s}"]
        else:
            names += side_bones(s).get(reg, [])
    for n in names:
        if n in bidx:
            allowed[i, bidx[n]] = True

W = np.where(allowed, W, 0.0)
# nearest-allowed-bone fallback for vertices left without weight
empty = np.where(W.sum(axis=1) < 1e-6)[0]
segs = {n: rest_seg(n) for n in bones}
for i in empty:
    cand = [n for n in bones if allowed[i, bidx[n]]]
    d = [float(seg_dist(Vm[i][None], *segs[n])[0]) for n in cand]
    W[i, bidx[cand[int(np.argmin(d))]]] = 1.0

# --- neighbour smoothing (within permissions), then max influences + normalise ---
mesh = body.data
nbrs = [[] for _ in range(len(Vm))]
for e in mesh.edges:
    a, b = e.vertices
    nbrs[a].append(b)
    nbrs[b].append(a)
for _ in range(3):
    Wn = np.array([W[n].mean(axis=0) if n else W[i] for i, n in enumerate(nbrs)])
    W = np.where(allowed, 0.5 * W + 0.5 * Wn, 0.0)

# Extra smoothing where joints fold hardest (pose tests showed knife-edge creases):
# axilla, hip crease, elbow and knee. Radius (m) around the joint centre, iterations.
joint_zones = []
for s in "lr":
    joint_zones += [(rig.data.bones[f"upperarm_{s}"].head_local, 0.16, 14),
                    (rig.data.bones[f"thigh_{s}"].head_local, 0.15, 10),
                    (rig.data.bones[f"forearm_{s}"].head_local, 0.07, 5),
                    (rig.data.bones[f"shin_{s}"].head_local, 0.08, 5)]
for centre, radius, iterations in joint_zones:
    c = np.array(centre[:])
    zone = np.nonzero(np.linalg.norm(Vm - c, axis=1) < radius)[0]
    falloff = np.clip(1 - np.linalg.norm(Vm[zone] - c, axis=1) / radius, 0, 1)[:, None]
    for _ in range(iterations):
        Wz = np.array([W[nbrs[i]].mean(axis=0) for i in zone])
        W[zone] = np.where(allowed[zone], (1 - 0.5 * falloff) * W[zone] + 0.5 * falloff * Wz, 0.0)
order = np.argsort(-W, axis=1)
keep = np.zeros_like(W, dtype=bool)
rows = np.arange(len(W))[:, None]
keep[rows, order[:, :MAX_INFLUENCES]] = True
W = np.where(keep, W, 0.0)
W /= W.sum(axis=1, keepdims=True)

for vg in list(body.vertex_groups):
    body.vertex_groups.remove(vg)
groups = {n: body.vertex_groups.new(name=n) for n in bones}
for j, n in enumerate(bones):
    ids = np.nonzero(W[:, j] > 1e-5)[0]
    for i in ids:
        groups[n].add([int(i)], float(W[i, j]), "REPLACE")

# per-vertex region attribute for later diagnostics (candidate only)
attr = mesh.attributes.new("hgpt_region", "INT", "POINT")
names = sorted(gen["regions"])
for i, reg in enumerate(vregion):
    attr.data[i].value = names.index(reg)
scene["hgpt_region_names"] = json.dumps(names)

bpy.ops.wm.save_mainfile()
report = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "stage": "O4 candidate (not production)",
    "source_o2_blend_sha256": source_sha,
    "candidate": str(CANDIDATE.relative_to(ROOT)).replace("\\", "/"),
    "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
    "weights": "stock bone-heat on this mesh + project permission rules + smoothing; max 4 influences",
    "deform_bones": len(bones),
    "heat_solve_empty_vertices": heat_empty,
    "fallback_vertices": int(len(empty)),
    "max_influences": int((W > 1e-5).sum(axis=1).max()),
    "weight_sum_error": float(np.abs(W.sum(axis=1) - 1).max()),
    "not_used": ["legacy/third-party weights", "data transfer from other meshes", "imported bind matrices"],
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("O4 CANDIDATE", json.dumps(report, indent=2))
