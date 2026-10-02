"""Author the rev2 twist-helper rig revision into a NEW numbered O4 candidate (first-party; declare, then apply).

Declare (read-only, writes JSON only):
  blender --background --factory-startup <source.blend> --python-exit-code 1 ^
    --python scripts/author_original_v1_twist_helpers_blender.py -- declare <declaration.json>
Apply (writes a new candidate; refuses to overwrite; refuses unless the derived edit set equals the declaration):
  blender --background --factory-startup <source.blend> --python-exit-code 1 ^
    --python scripts/author_original_v1_twist_helpers_blender.py -- apply <declaration.json> <new.blend>

What it does (see scripts/original_v1_twist_helpers.py for the model): adds 8 deform helper bones (upperarm/forearm x tw0/tw1 x
l/r, children of the segment bones, same rest orientation) and moves part of each affected vertex's existing weight on the
upperarm/forearm bones onto the helpers by a partition of unity along the segment's rest axis. No geometry, topology, UV,
material, other bone or other weight changes. Vertices that would exceed four influences keep their four largest weights
(renormalised to the original sum); the number and size of those prunes is recorded. Records rig revision and helper spec on the
scene so later tools can tell the revisions apart.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import original_v1_twist_helpers as th  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0]
if mode not in ("declare", "apply"):
    raise SystemExit("mode must be declare or apply")
scene = bpy.context.scene
if not scene.get("hgpt_not_production") or scene.get("hgpt_candidate") != "O4_bind":
    raise SystemExit("O4_bind candidate files only.")
src_path = Path(bpy.data.filepath)
rig = bpy.data.objects["HGPT_CANONICAL_V4_ORIGINAL"]
if len(rig.data.bones) != 63:
    raise SystemExit("Expected the 63-bone v4 rig as the source (apply the helper revision once).")
body = bpy.data.objects["HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"]
me = body.data
group_names = {vg.index: vg.name for vg in body.vertex_groups}
segment_groups = [f"{seg}_{s}" for seg in th.SEGMENTS for s in th.SIDES]


def segment_geometry(name):
    b = rig.data.bones[name]
    h, t = Vector(b.head_local), Vector(b.tail_local)
    return h, t


DEBUG = []


def plan():
    """For every vertex weighted on a segment bone: new weight dict (after split and <=4-influence prune)."""
    rest = np.array([v.co[:] for v in me.vertices])
    geo = {}
    for name in segment_groups:
        h, t = segment_geometry(name)
        ax = (t - h)
        L = ax.length
        geo[name] = (np.array(h[:]), np.array((ax / L)[:]), L)
    changed, prunes, edits = {}, [], {}
    for v in me.vertices:
        w = {group_names[g.group]: g.weight for g in v.groups if g.weight > 0.0}
        hit = [n for n in segment_groups if n in w]
        if not hit:
            continue
        total = sum(w.values())
        new = dict(w)
        for name in hit:
            h, ax, L = geo[name]
            t = float((rest[v.index] - h) @ ax / L)
            a0, a1, a2 = th.partition(t)
            seg, side = name.split("_")
            wv = new.pop(name)
            # Keep within four influences WITHOUT discarding weight where possible: the 50 % station's share can be folded half
            # into the 0 % and half into the 100 % station, which preserves the swing and the mean twist fraction exactly.
            if len(new) + sum(1 for a in (a0, a1, a2) if a * wv > 1e-7) > 4:
                a0, a2, a1 = a0 + 0.5 * a1, a2 + 0.5 * a1, 0.0
            if len(new) + sum(1 for a in (a0, a1, a2) if a * wv > 1e-7) > 4:
                # the vertex already carries three other influences (chest-side axilla / shoulder-cap vertices): give the whole
                # share to the nearest station so no other weight is touched
                a0, a1, a2 = (1.0, 0.0, 0.0) if a0 >= a2 else (0.0, 0.0, 1.0)
            for nm, a in ((f"{seg}_tw0_{side}", a0), (f"{seg}_tw1_{side}", a1), (name, a2)):
                if a * wv > 1e-7:
                    new[nm] = new.get(nm, 0.0) + a * wv
        if len(new) > 4:
            keep = dict(sorted(new.items(), key=lambda kv: -kv[1])[:4])
            lost = 1.0 - sum(keep.values()) / sum(new.values())
            prunes.append(lost)
            DEBUG.append((v.index, hit[0], round(t, 3), sorted(w.items(), key=lambda kv: -kv[1]), round(lost, 4)))
            new = keep
        s = sum(new.values())
        new = {k: x * total / s for k, x in new.items()}
        changed[v.index] = new
        edits[v.index] = w
    return changed, edits, prunes


changed, before, prunes = plan()
ids = sorted(changed)
ids_hash = hashlib.sha256(np.asarray(ids, dtype="<i8").tobytes()).hexdigest()

if mode == "declare" and "--debug" in args:
    big = [d for d in DEBUG if d[4] > 0.02][:12]
    for d in big:
        print("DBG", d)
    print("DBG count>2%", len([d for d in DEBUG if d[4] > 0.02]), "of", len(DEBUG))
if mode == "declare":
    out = Path(args[1])
    if "--debug" in args:
        raise SystemExit(0)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite {out}")
    rec = {"declared_utc": datetime.now(timezone.utc).isoformat(), "phase": "skeleton-motion rev2", "declared_before_edit": True,
           "source_candidate": src_path.name, "source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
           "rig_revision": th.REVISION, "new_bones": th.helper_spec(), "new_bone_count": len(th.helper_names()),
           "weight_rule": "partition of unity along each segment's rest axis: tw0 (1-2t)+, tw1 triangle at t=0.5, segment (2t-1)+; "
                          "vertices over four influences keep their four largest (renormalised to the original sum)",
           "source_bones_changed": segment_groups, "allowed_vertex_ids": ids, "vertex_count": len(ids),
           "allowed_vertex_ids_sha256": ids_hash,
           "planned": {"vertices_pruned_to_4_influences": len(prunes),
                       "max_pruned_weight_fraction": round(max(prunes), 6) if prunes else 0.0,
                       "mean_pruned_weight_fraction": round(float(np.mean(prunes)), 6) if prunes else 0.0},
           "geometry_changed": False, "topology_changed": False, "other_bones_changed": False,
           "frozen_untouched": ["R2", "thresholds and tolerances", "all existing bone rest transforms and hierarchy", "mesh geometry"],
           "inputs": "this candidate's own ORIGINAL v1 mesh and rig only"}
    out.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("TWIST HELPER DECLARATION", out, "vertices", len(ids), "pruned", len(prunes))
    raise SystemExit(0)

# ---------------------------------------------------------------- apply
decl_path, new_path = Path(args[1]), Path(args[2])
if new_path.exists():
    raise SystemExit(f"Refusing to overwrite {new_path}")
decl = json.loads(decl_path.read_text(encoding="utf-8"))
if not decl.get("declared_before_edit") or decl["allowed_vertex_ids"] != ids or decl["allowed_vertex_ids_sha256"] != ids_hash:
    raise SystemExit("derived vertex set differs from the declaration: refusing to edit")
if decl["source_sha256"] != hashlib.sha256(src_path.read_bytes()).hexdigest():
    raise SystemExit("declaration was made for a different source candidate")
rest_before = np.array([v.co[:] for v in me.vertices])
other_before = {v.index: {group_names[g.group]: g.weight for g in v.groups}
                for v in me.vertices if v.index not in changed}
bones_before = {b.name: (tuple(b.head_local), tuple(b.tail_local), b.parent.name if b.parent else None) for b in rig.data.bones}

# --- bones
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = rig.data.edit_bones
for h in th.helper_spec():
    seg = eb[h["parent"]]
    head, tail = seg.head.copy(), seg.tail.copy()
    ax = (tail - head).normalized()
    L = (tail - head).length
    station = 0.0 if h["twist_fraction"] == 0.0 else 0.5
    nb = eb.new(h["name"])
    nb.head = head + ax * (L * station)
    nb.tail = head + ax * (L * (station + 0.25))
    nb.roll = seg.roll
    nb.parent = seg
    nb.use_connect = False
    nb.use_deform = True
bpy.ops.object.mode_set(mode="OBJECT")

# --- weights
for h in th.helper_spec():
    if h["name"] not in body.vertex_groups:
        body.vertex_groups.new(name=h["name"])
for vi, new in changed.items():
    old = before[vi]
    for name in set(old) | set(new):
        vg = body.vertex_groups[name]
        if name in new:
            vg.add([vi], new[name], "REPLACE")
        else:
            vg.remove([vi])
me.update()

# --- verification: nothing outside the declaration moved
rest_after = np.array([v.co[:] for v in me.vertices])
if np.abs(rest_after - rest_before).max() > 1e-12:
    raise SystemExit("geometry changed")
for vi, w in other_before.items():
    now = {group_names.get(g.group, body.vertex_groups[g.group].name): g.weight for g in me.vertices[vi].groups}
    if any(abs(now.get(k, 0.0) - x) > 1e-9 for k, x in w.items()) or any(k not in w and x > 1e-9 for k, x in now.items()):
        raise SystemExit(f"vertex {vi} outside the declaration changed")
for name, (h, t, p) in bones_before.items():
    b = rig.data.bones[name]
    if max(abs(a - c) for a, c in zip(tuple(b.head_local) + tuple(b.tail_local), h + t)) > 1e-9 or (b.parent.name if b.parent else None) != p:
        raise SystemExit(f"existing bone {name} changed")
if len(rig.data.bones) != 63 + len(th.helper_names()):
    raise SystemExit("unexpected bone count")
over = [v.index for v in me.vertices if sum(1 for g in v.groups if g.weight > 1e-6) > 4]
if over:
    raise SystemExit(f"{len(over)} vertices exceed four influences")

scene["hgpt_rig_revision"] = th.REVISION
scene["hgpt_twist_helpers"] = json.dumps(th.helper_spec())
scene["hgpt_candidate_revision"] = new_path.stem
scene["hgpt_candidate_parent_sha256"] = decl["source_sha256"]
bpy.ops.wm.save_as_mainfile(filepath=str(new_path), copy=True)
rec = {"generated_utc": datetime.now(timezone.utc).isoformat(),
       "stage": "O4 candidate first-party rig revision: axial twist helpers (not production)",
       "source_candidate": src_path.name, "source_sha256": decl["source_sha256"], "candidate": new_path.name,
       "candidate_sha256": hashlib.sha256(new_path.read_bytes()).hexdigest(), "declaration": decl_path.name,
       "declaration_sha256": hashlib.sha256(decl_path.read_bytes()).hexdigest(), "rig_revision": th.REVISION,
       "bone_count": len(rig.data.bones), "new_bones": th.helper_names(), "weights_rewritten_vertices": len(ids),
       "pruned_vertices": len(prunes), "max_pruned_weight_fraction": round(max(prunes), 6) if prunes else 0.0,
       "topology_changed": False, "geometry_changed": False}
new_path.with_suffix(".json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
print("TWIST HELPERS APPLIED", json.dumps({k: rec[k] for k in ("candidate", "candidate_sha256", "bone_count", "weights_rewritten_vertices", "pruned_vertices")}))
