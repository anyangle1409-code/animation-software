# r101 rotation-driven axillary fold-volume helpers: declaration before edit

Fresh copies of r98 only. The fold-volume helpers are children of the glenohumeral half-swing helper and start from its rest frame, so each one reproduces the half helper exactly until it moves. Each is translated along its fold band's outward normal by `a_max * smoothstep(d0, d1, d)`, where `d` is a swing-only glenohumeral elevation measure taken from two on-axis probe bones. The response is exactly zero at rest and at low elevation.

Band vertices hand part of their half-helper weight to the fold helper, so base motion is unchanged and only the declared offset is added. No shape keys, re-rig, bind-pose change or global solve. See the JSON for the details.

## Continuation note (if the session ends mid-stage)

State: the declaration is committed; the prototypes are in `scripts/r101/` once pushed, and the evidence is under `repair_checks/r101_fold_volume_screening/`.

To continue:
1. Run `scripts/r101/vol101.py` on a fresh copy of r98 for each variant (anterior / posterior / both, at 0.015 and 0.03 m).
2. Run `scripts/r101/resp101.py` to check the driver response through 0–170°.
3. Compare the 15-pose subset with r98 using `scripts/r97/matrix.py` (`MIRROR=candidates/r98/r98_mirror_idx.npy`), plus `scripts/r98/cmp.py`.
4. Render the close-ups.
5. Run the repository pose test on any promising variant.

Publish READY only for a defensible finalist.
