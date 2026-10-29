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

## Native cloud result — verified

- Published commit `35b75861c63c0054be5e0e67b369aabed904282f`; [run 40855460996](https://github.com/anyangle1409-code/animation-software/actions/runs/40855460996) completed **SUCCESS 7/7**. Job IDs: pose `123385171697`, R120 `123385172051`, V14 `123385172065`, W8 `123385172088`, localization `123385172159`, comparison `123385658405`, driver `123387019122`.
- Cloud logs confirm localization `319/319`; pose `29/29 + 19/19 + 6/6 + 10/10`; comparison `5/5 + 12/12 + 9/9 + 7/7 + 12/12 + 15/15 + 13/13`; driver `10/10 + 20/20 + 8/8` tests passed.
- Pose artifact `12888194458` was independently downloaded, CRC-checked and SHA256-matched GitHub at `2471ef5da07b93f657f0d702d4b24175f4ddd8fb6f4c83fdd8b4140b5b31f2fd`. Pose JSON SHA256 is `53800d2a74b816510097ecaea6031512fde0103148b68af36162c0d236a37d7b`; phone Markdown is `b43ff8e825cd1881d2a3dca8fc839dc5c1c3e2f7815711efc5e9fac8123a295f`.
- All six authored controls were present in all nine frames. From sample 0 to 8, unsigned local magnitudes changed: clavicle `19.51463→36.04909°` (`l`) / `19.51455→36.04982°` (`r`); scapula `39.34783→78.21723°` / `39.34769→78.22840°`; upperarm `73.55633→109.84473°` / `73.55610→109.85365°`. Maximum l/r magnitude differences across the trajectory were `0.00320°`, `0.01117°`, and `0.01150°` respectively.
- Each magnitude series is monotone across these nine increasing press samples. This describes the authored control state only: differences of unsigned magnitudes are not signed relative rotations, contribution ratios or proof of natural coordination.
- Removing only the nine new fields per side and the new limitation makes the new pose report exactly equal to the previously verified report. Existing return, corrective-key, skin-edge and deformation evidence is therefore preserved rather than reinterpreted.
- All artifact metadata is recorded in `docs/recovery_20261023/cloud_verification_20261029_run40855460996.json`. Anatomical/quality approval remains `NOT_GRANTED`; the shoulder press remains failed for its existing visual/deformation reasons.
