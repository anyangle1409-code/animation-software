# r102 fold-helper weight sources: declaration before edit

The only change from r101 is where the fold-volume helper takes its weight from. Within a narrow, mirror-exact anterior fold band, a bounded, smoothly tapered share (conservative 0.25, moderate 0.45, hard maximum 0.6) is taken proportionally from the declared torso/girdle, humerus and half-helper weights. The elevation drive, fixed normal and 40 mm cap are kept from r101. Base-motion cost is measured with the offset forced to 0. Prototypes come from fresh copies of r98 only.

## Continuation note

If the session stops:
1. Run `scripts/r102/vol102.py` on a fresh copy of r98 with `screening/v_*.json`.
2. Run `scripts/r102/basecost102.py` (offset 0) against r98.
3. Run the 15-pose subset with `scripts/r97/matrix.py` (MIRROR = `candidates/r98/r98_mirror_idx.npy`).
4. Render close-ups for flexion 170, abduction 150, press_top and pullup_hang against r98 and r101-Acap.

Evidence goes in `repair_checks/r102_fold_weight_source_screening/`. No READY unless a finalist passes.
