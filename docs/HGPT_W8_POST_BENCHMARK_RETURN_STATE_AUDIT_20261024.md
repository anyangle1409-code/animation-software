# W8 post-benchmark return-state audit — 24 October 2026

Status: **native cloud verified — runtime return FAIL. Read-only residual measurement; not anatomical neutral or movement approval.**

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

Four new test behaviors were observed failing before implementation and passing after. Local focused tests:13/13 PASS. Full diagnostics:256/256 PASS. Frozen snapshot replay guards:7/7 PASS. Python compilation and whitespace checks PASS.

Native run [40116799535](https://github.com/anyangle1409-code/animation-software/actions/runs/40116799535) at `ed90d3bb8e1d8473809fff3f968ff1a77577ad75` completed SUCCESS7/7: the diagnostic executed correctly, while the measured runtime return gate itself is **FAIL**.

- skeletal pose signature restored exactly: `true`;
- active non-Basis shape keys after reset:14;
- evaluated vertices:219,974; moved more than1 nm:102,253 (46.484130%);
- maximum residual: `0.06231378350054487 m` (62.313784 mm);
- RMS residual: `0.012929646292009458 m` (12.929646 mm).

The14 residual key names exactly match the14 nonzero sample8 terminal channels; values match within `4.90e-7`, explained by the existing sample report's six-decimal rounding. They comprise bilateral S1 145/160, S3 125, S5 145/160 and S7 156/166 channels. This establishes terminal corrective-state retention after skeletal reset; it does **not** show that any individual shape is anatomically incorrect.

Pose artifact `12569756252` was independently downloaded: ZIP SHA256 `7efe9f7a1686e1439a4315eac59bbce3a19f5b811b987800637b89bb4f9045e7`, CRC clean,71 members, no `.blend`; pose JSON SHA256 `9b831723b9f438152d9b9fd9495c4afb79173bd79a24751aab770e3a5f265b3e`. Existing individual-isolation JSON/Markdown and fixed-edge Markdown remain byte-identical to the prior verified run, confirming the new field did not change forward-pose conclusions.
