# W8 post-benchmark return-state audit — 24 October 2026

Status: **staged for native cloud execution. Read-only runtime residual measurement; not anatomical neutral or movement approval.**

## Question

After the pinned r57 shoulder-press benchmark completes its nine-sample forward sweep and calls its own final rig reset, does the evaluated W8 runtime state exactly match the benchmark reference captured after the runner's initial reset?

This is narrower than natural return-to-neutral. It tests a software/model-state postcondition on the current authored benchmark. It does not add a reverse trajectory, certify a human neutral pose, establish ISB axes or show physiological tissue recovery.

## Measurement

The existing `pose_state_probe.py` now captures, without saving the source:

- evaluated reference vertex coordinates at the runner's first post-reset evaluation;
- the runtime rig world, pose-matrix and basis-matrix signature at that same point;
- evaluated vertices after the completed forward sweep and the runner's final reset;
- every nonzero non-Basis shape key, including channels outside the already reported S1–S7/C1/K1 families;
- maximum and RMS per-vertex displacement, count above 1 nanometre, skeletal-signature equality and a strict exact-restoration boolean.

Exact restoration means all three are true: maximum vertex displacement is exactly zero, no non-Basis key remains active, and the skeletal pose signature is identical. A nonzero result remains valid evidence and does not abort the diagnostic workflow.

## Guards and interpretation

The pure report contract rejects changed/empty vertex counts, non-3D or nonfinite coordinates, invalid/duplicate active-key records, inconsistent exact-restoration claims, invalid moved counts and any anatomical-neutral claim. Synthetic fixtures cover exact return and independent geometry, key and skeletal residuals.

The output status is permanently `MEASURED_RUNTIME_RETURN_NOT_ANATOMICAL_NEUTRAL`. Even an exact result proves only runtime restoration to the benchmark's own start state. A non-exact result identifies residual authored runtime state but does not by itself identify which driver/key is anatomically wrong or authorize a repair.

## Verification state

Four new test behaviors were observed failing before implementation and passing after. Local focused tests:13/13 PASS. Full diagnostics:256/256 PASS. Frozen snapshot replay guards:7/7 PASS. Python compilation and whitespace checks PASS. Native Blender values and artifact hashes are pending.
