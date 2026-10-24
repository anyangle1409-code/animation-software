# W8 individual active S5/S7 key isolation — 24 October 2026

Status: **staged for native cloud execution. Not a repair, anatomical calibration or movement approval.**

## Purpose

The verified family-level diagnostic showed mixed effects: muting all active S5 keys at press sample 0 moved the eight distal neighboring edge ratios closer to their benchmark-rest values but moved all eight middle neighbors farther; at sample 6, muting the S7 family moved three of four neighboring edges per middle seed closer and one farther. A family mute cannot distinguish the two interpolated keys that are simultaneously active around a driver interval.

This extension keeps the same pinned W8 source, frozen r57 nine-frame shoulder-press trajectory, four ranked seed edges and sixteen topology-selected neighboring controls. At each fixed native pose it adds one temporary condition for every **active, originally unmuted S5 or S7 key**, muting exactly that key while retaining all other key, rig, constraint, weight and modifier state. Zero-valued and originally muted keys are excluded. Conditions are deterministic and retain the exact key name and observed activation value.

## Safety and evidence contract

- Duplicate key names or nonfinite key values fail before isolation.
- Every condition reuses the frozen evaluated topology and finite endpoint checks.
- Full skeletal pose, every key value/mute flag and evaluated endpoints must return to the observed baseline; callback or evaluation failures restore the original state.
- The phone JSON and Markdown count ranked seeds separately from adjacent topology controls as moving closer to, farther from, or unchanged relative to a unit edge-length ratio.
- A ratio nearer one is **not** an anatomical target, physiological tissue strain, safe limit or proof that a corrective is beneficial. Individual muting is still a conditional nonlinear modifier-stack comparison, not additive causal attribution.
- No `.blend` is saved and no source geometry, skeleton, weights, driver, muscle attachment, permanent muscle ID, app, production asset or version is changed.

## Verification state

The individual-condition and summary tests were written first and observed failing against the family-only implementation. Local execution passes 18 corrective-isolation tests and the full247-test diagnostic suite; Python compilation and whitespace checks also pass. Native cloud results are not recorded as successful until separately executed and inspected.

All 46 anatomical landmarks remain unbound and 0/19 generic motion scenarios remain approved. Shoulder/scapula/clavicle, elbow/radius-ulna, lower-body joint/contact, balance and grip validation remain open. Population ROM statistics remain descriptive and are never converted to hard limits. Muscle highlighting remains deferred.
