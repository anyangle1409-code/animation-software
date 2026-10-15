#!/usr/bin/env python3
"""ORIGINAL_v1 review candidate R15 (Claude, 15 Oct 2026): R14 rebuilt on press path v4.  The owner looked at R14's lockout
("The shoulder should move with the arm ... I think maybe the shoulder is coming over too far"), then said "In this pose it
should basically end up like a Y shape".  Skeleton diagnosis in docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R14_20261015.md:
  * v3: the clavicle's axial turn is applied first (coupled.clavicle_basis swung the raised clavicle 15 deg forward);
  * v4: plus 15 deg extra scapular upward rotation over 120 -> 172 deg, so that at lockout the humerus is within ~8 deg of the
    scapular spine (Saha's zero position: the arm continues the line of the scapula = the Y from behind).
R14's S5 shapes were baked along v2.  On the v4 skeleton they produce the horizontal shelf and the step at the arm root,
whereas with them off the back forms the Y.  So R15 is the R14 recipe (base from R13, S4 x5 target, delta mush,
S5 bake with the benchmark-path guard) re-run with the v4 flag.  Same steps and arguments as
build_original_review_candidate_r14_blender.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_original_review_candidate_r14_blender as r14  # noqa: E402

r14.PRESS_PATH = "v4"
r14.NAME = "R15"

if __name__ == "__main__":
    if "--base" in r14.args:
        r14.base()
    elif "--make-target" in r14.args:
        r14.r12.make_target()
    elif "--dump" in r14.args:
        r14.r12.dump()
    else:
        r14.bake()
