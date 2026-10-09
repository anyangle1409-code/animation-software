# Mesh-independent hand reconstruction spike — 9 October 2026

**Branch:** `codex/mesh-independent-hand-spike-20261009`  
**Parent:** anatomical audit branch at `2d4b352c`  
**Status:** diagnostic only; no production change, c005 or canonical freeze.

## Problem being isolated

The c003/c004 shoulder reposition moved the forearm and hand while the a003
body mesh stayed fixed. The legacy `skeleton_fit.contain()` stage uses that
unchanged skin to relocate low-confidence bones, so the reconstructed hand no
longer corresponds to the corrected shoulder. The c004 source inputs also
remain 108 points behind their translated endpoints.

Of those 108 points, 98 were exactly the a003 bone endpoints before
containment. Ten distal finger/thumb tails were *pre-containment stations*:
the old mesh later moved them inward 5.28–9.00 mm.

## What this branch actually implements

`scripts/anatomy_fit/mesh_independent_hand_probe.py` runs the existing
`skeleton_fit.build` and `enforce_midline` stages against an in-memory
candidate hand input made by translating the **original** a003 hand input
stations through each side's recorded c004 GH displacement.

No calls to skin clearance or `contain()` are made. Nothing is saved by
default. The only optional output is a *fresh* JSON diagnostic written with
exclusive file creation (an existing output is never overwritten).

It checks each of the 108 reconstructed endpoints against c004 and requires
the discrepancy to be exactly the original a003 input-to-bone offset. This
is a consistency/provenance check, not an anatomy acceptance criterion.

Expected result if the recorded premise still holds:
- 98 reconstructed endpoints coincide with c004 (mesh-independent stage).
- Ten distal phalanx tails retain 5.28–9.00 mm of previously recorded
  skin-containment displacement; their *correct anatomical values are unknown*.
- Any unaccounted discrepancy, changed rigid GH correspondence, or changed
  stale-input premise aborts the probe.

**Do not apply the ten provisional offsets as anatomical targets.** Resolving
these requires independently sourced distal phalanx/toe geometry and a new
skeleton-first coordinate contract.

## Verification

Requires Python, NumPy, and the committed original anatomy records; Blender
is not required for these checks.

```bash
python -m unittest discover -s scripts -p 'test_mesh_independent_hand_probe.py' -v
python scripts/anatomy_fit/mesh_independent_hand_probe.py --out /tmp/hand_probe_fresh.json
```

The GitHub Actions workflow
`.github/workflows/mesh-independent-hand-probe.yml` runs both commands
on pushes to this isolated branch. Inspect its run result before claiming
the checks passed. The branch has no authority to change
`canonical_freeze_readiness_v1.json`.

## Deliberate non-goals

- No new c005, canonical audit revision, or acceptance-gate promotion.
- No change to `skeleton_fit.py`, `contain()`, a003–c004, production
  geometry, Blender files, runtime rig, weights or joint solvers.
- No extrapolation from old skin containment to true finger-bone lengths.
- No approval of proportions or loaded exercise motion.

## Next engineering decision after verified tests

Create a separate canonical-target builder whose input contract consists of
source-backed skeletal landmarks and bone endpoints. Compute the skeleton
without mesh containment; evaluate skin clearance **afterward as a
non-mutating diagnostic**. Keep the legacy character-fit builder available
for reproduction of a003 but never let a production mesh redefine
anatomical master coordinates. Source-backed fingertip targets remain a
separate gate.
