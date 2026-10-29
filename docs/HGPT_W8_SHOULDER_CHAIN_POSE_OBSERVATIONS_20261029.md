# W8 authored shoulder-chain pose observations — 2026-10-29

## Purpose

The existing nine-frame W8 shoulder-press probe measured project-driver humerothoracic elevation and shoulder-cap state, but did not record the authored clavicle, scapula and upperarm controls. This extension captures those three controls for each runtime suffix after the pinned r57 pose and driver have evaluated each frame.

This is a read-only observation task. It does not construct ISB coordinate systems, identify anatomical side, calculate signed component rotations, prescribe scapulohumeral rhythm, or approve the failed shoulder press.

## Method

- At each of the exact nine existing samples, require `clavicle_{suffix}`, `scapula_{suffix}` and `upperarm_{suffix}` for authored suffixes `l/r`.
- Read each pose bone's `matrix_basis`, convert its rotation component to a normalized quaternion and report the unsigned rotation magnitude in degrees.
- Record the original Blender pose rotation mode separately. The measurement does not change the mode, bone transform, driver, key, model or source file.
- Fail closed on missing controls, nonfinite/out-of-range magnitudes, empty rotation-mode metadata, wrong source identity or any existing report-integrity failure.
- Publish `w8_shoulder_chain_pose_observations.md` alongside the existing pose JSON and corrective evidence in the pose artifact.

The matrix-basis magnitude is an authored-control local delta from its rest basis. It is **not** an anatomical clavicle elevation, scapular upward rotation/posterior tilt, glenohumeral angle, humerothoracic component sequence or clinical ROM value. Unsigned magnitudes cannot establish direction or coordination quality.

## Verification state

Four initial focused behaviors were observed RED before implementation and GREEN after: exact three-control presence, finite delta/mode validation, rotation-mode-independent non-mutating extraction, and phone report nonclaims. Fresh-context review found two Important evidence-integrity gaps: arbitrary nonempty rotation-mode strings passed, and quaternion sign-equivalent rotations were not explicitly canonicalized to the shortest `0..180°` magnitude. Two expanded regressions reproduced both RED. The one fix pass requires the pinned modes (clavicle/scapula `QUATERNION`, upperarm `XYZ`) and canonicalizes the quaternion angle with `min(angle, 360-angle)`. Focused `29/29` pose-probe tests pass locally with no deferred review finding. Full repository and native Blender verification are pending.

No original `.blend`, skeleton, weights, drivers, shape keys, permanent muscle IDs, attachment/highlighting, PT-App, production asset, version, merge or deployment changed. Anatomical landmarks remain unbound and generic movement approval remains `0/19`.
