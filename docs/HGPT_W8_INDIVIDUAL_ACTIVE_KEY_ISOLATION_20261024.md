# W8 individual active S5/S7 key isolation — 24 October 2026

Status: **native cloud diagnostic verified. Not a repair, anatomical calibration or movement approval.**

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

## Native result

[Run40095096697](https://github.com/anyangle1409-code/animation-software/actions/runs/40095096697) passed all seven jobs at commit `c41708896a05ca10a58aec2310d7b8ec24def0e9`. Cloud logs show247/247 diagnostic tests, including18/18 focused isolation tests. The nine native poses produced60 active S5/S7 conditions and0m maximum endpoint restoration error.

At sample0, muting the low-weight S5 110 key on either suffix moved one of four ranked seeds closer to a unit ratio, but four of16 adjacent controls farther; muting the dominant S5 85 key produced mixed one-closer/one-farther seed behavior and four-closer/four-farther adjacent behavior. At sample6, muting either S5 145/160 key on one suffix moved one ranked seed and four controls farther from a unit ratio. Muting dominant S7 145 moved two seeds closer, while adjacent controls remained mixed; muting S7 156 moved one seed closer and one farther, again with mixed adjacent controls. The unchanged counts include geometry outside the key suffix's local effect. These counts do not certify suffixes as anatomical left/right.

Pose artifact12560597148 independently matches GitHub SHA256 `5ccf5e78d1bb815584708456096bceb342add8beb8eff0a3fda9cd58282a801c`; driver artifact12560327616 matches `ed3ca5d7e56d5dce563a26c03c9436533f79dbe08426c2d6ada2bb948db571a4`. The new individual JSON member is `270205a6963efad9c6ea3eeedf4ba4a94035b7786d9aa21b1fd8200c8e999dc2`. The previous pose artifact was re-downloaded and reverified; after removing only new individual fields, all existing pose data is equal, and camera plans plus all eight snapshot/vertex hashes match. Full record: `recovery_20261023/cloud_verification_20261024_run40095096697.json`.

**Conclusion:** neither S5 nor S7, nor either interpolated endpoint key, has a uniform local geometric effect across the selected seeds and adjacent controls. No blanket disable or repair is justified.

## Authored-suffix neighborhood refinement — staged

The first verified summary counts all four seeds and all16 controls per key, so unchanged counts include the opposite suffix. The report now also selects the two ranked seed neighborhoods associated with the key's authored `l` or `r` suffix and emits those local counts separately, while retaining the all-edge counts in JSON. The Markdown leads with the local counts and labels the suffix as **NOT independently reviewed anatomical laterality**. This changes reporting only; it adds no shape-key evaluation and does not alter the source, snapshots, cameras or existing geometry measurements.

The refinement test was observed failing before implementation, then the focused18-test suite and full247-test local suite passed; compilation and whitespace checks passed. Native cloud output remains pending until a new run completes and the artifact is inspected.
