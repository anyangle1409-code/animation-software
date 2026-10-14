#!/usr/bin/env python3
"""Add K1-type hinge contact keys for one more hinge to an ORIGINAL_v1 review candidate, saved as a NEW review blend (bpy).

Used for R3 = R2 + K1 wrist-extension keys (dorsal crease): soft contact (softplus 3 mm, gap 2 mm), keys at 60/80/100 deg
extension from 30 deg, count-based fold/collision guard over 30-100 deg
(scripts/build_original_knee_contact_corrective_blender.py HINGES["wrist"]).  The parent's basis, weights, bones and
existing keys are unchanged; the helper bones are only installed in memory and removed before saving (67-bone file).
Measured: pure-hinge sweep before/after.  Review only; nothing is approved.

  python3.13 build_original_review_candidate_hinge_keys_blender.py -- --blend R2.blend --hinge wrist --name R3 \
      --out R3.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_knee_contact_corrective_blender as k1  # noqa: E402
import build_original_movement_benchmarks_blender as bench  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    parent, hinge, name, out, report = get("--blend"), get("--hinge"), get("--name"), Path(get("--out")), Path(get("--report"))
    if out.exists():
        raise FileExistsError(out)
    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    import build_functional_shoulder_correction_blender as correction
    import build_functional_original_attachment_blender as attachment
    result = correction.build_corrected_scene()
    body, rig = result["body"], result["runtime"]
    if any(kb.name.startswith(k1.HINGES[hinge]["prefix"]) for kb in body.data.shape_keys.key_blocks):
        raise RuntimeError(f"{hinge} keys already present")
    drives.install_helpers(rig)
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    signs_ok = all(k1.HINGES[hinge].get("side_sign", {s: None for s in k1.SIDES})[s] in
                   (None, -bench._palmar_sign(rig, rig.pose.bones[f"hand_{s}"])) for s in k1.SIDES)
    before = k1.hinge_sweep(result, False, hinge)
    log = k1.build(result, hinge)
    after = k1.hinge_sweep(result, True, hinge)
    attachment._remove_previous()
    view = bpy.context.view_layer
    for ob in view.objects:
        ob.select_set(False)
    view.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for s in k1.SIDES:
        rig.data.edit_bones.remove(rig.data.edit_bones[f"deltoid_helper_{s}"])
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    view.update()
    if sum(b.use_deform for b in rig.data.bones) != 67:
        raise RuntimeError("the review blend must stay a 67-bone file")
    scene = bpy.context.scene
    scene["hgpt_review_candidate"] = f"ORIGINAL_V1_CONSOLIDATED_REVIEW_{name}_CLAUDE"
    scene["hgpt_review_candidate_approved"] = False
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out.resolve()), copy=True)
    h = k1.HINGES[hinge]
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE_HINGE_KEYS", "candidate": name, "approved": False, "hinge": hinge,
           "params": {k: (list(v) if isinstance(v, (tuple, range)) else v) for k, v in h.items() if k != "benchmarks"},
           "gap_m": k1.GAP_M, "side_sign_matches_palmar": signs_ok,
           "parent": {"path": Path(parent).name, "sha256": sha(parent)}, "output": {"path": out.name, "sha256": sha(out)},
           "keys": sorted(kb.name for kb in body.data.shape_keys.key_blocks if kb.name.startswith(h["prefix"])),
           "solve": log, "sweep_before": before, "sweep_after": after}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")
    for a in before:
        x, y = before[a], after[a]
        print("HK", a, (x["collapse_lt_0_1"], x["stretch_gt_2"], x["self_intersecting_pairs"]), "->",
              (y["collapse_lt_0_1"], y["stretch_gt_2"], y["self_intersecting_pairs"]))
    if not signs_ok:
        raise SystemExit("side signs do not match the measured palmar sign")


if __name__ == "__main__":
    main()
