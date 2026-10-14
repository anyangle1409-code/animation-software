#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R9 (Claude, 14 Oct 2026): R8 + S3 mid-range shape keys (owner: "Go ahead yes", on fixing
what R8 left).  docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R9_20261014.md.

R8's shoulder-cap helper leaves the skin above the shoulder pivot up to 45 mm proud of R5's surface at 45-100 deg (a
"shoulder pad"; body volume +1.4 % at 90 deg).  S3 keys (scripts/build_original_shape_target_corrective_blender.py) pull it
back to R5's posed surface at 45/75/100 deg and fade out by 125 deg, so 125-160 deg is exactly R8.

  python3.13 build_original_shape_target_corrective_blender.py -- --reference R5.blend --out refs.npz
  python3.13 build_original_review_candidate_r9_blender.py -- --blend R8.blend --reference R5.blend --refs refs.npz \
      --out R9.blend --report JSON
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_shape_target_corrective_blender as s3  # noqa: E402
import build_original_shoulder_relax_corrective_blender as s1  # noqa: E402
import original_v1_review_candidate_drives as drives  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k: args[args.index(k) + 1]
    parent, ref, out, report = get("--blend"), get("--reference"), Path(get("--out")), Path(get("--report"))
    z = np.load(get("--refs"))
    refs = {int(k): z[k] for k in z.files}
    if sorted(refs) != sorted(s3.KEYS_HT):
        raise SystemExit("reference surfaces do not match the S3 key elevations")
    if out.exists():
        raise FileExistsError(out)
    import build_functional_shoulder_correction_blender as correction
    bpy.ops.wm.open_mainfile(filepath=str(Path(parent).resolve()))
    res = correction.build_corrected_scene()
    body, rig = res["body"], res["runtime"]
    for kb in body.data.shape_keys.key_blocks[1:]:
        kb.value = 0.0
    drives.setup(res)
    before = s1.sweep(res, True)                          # R8
    log = s3.build(res, refs)
    after = s1.sweep(res, True)
    for a, b in zip(before, after):
        print("R9SW", a["ht"], (a["collapse"], a["stretch"], a["pairs"], round(a["volume_pct"], 2)), "->",
              (b["collapse"], b["stretch"], b["pairs"], round(b["volume_pct"], 2)))
    output = s1.save(res, out, parent, "R9")
    rep = {"kind": "ORIGINAL_V1_REVIEW_CANDIDATE", "candidate": "R9", "status": "REVIEW_CANDIDATE_NOT_ACCEPTED", "approved": False,
           "reference": {"path": Path(ref).name, "sha256": sha(ref)},
           "s3_params": {"keys_ht": s3.KEYS_HT, "close_ht": s3.CLOSE_HT, "start_deg": s3.START_DEG, "radius_m": s3.RADIUS,
                         "z_below_m": s3.Z_BELOW, "min_mm": s3.MIN_MM, "taper_rings": s3.TAPER_RINGS, "cap_m": s3.CAP_M},
           "s3": log, "sweep_r8": before, "sweep_r9": after, "output": output}
    report.write_text(json.dumps(rep, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
