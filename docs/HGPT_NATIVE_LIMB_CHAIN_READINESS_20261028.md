# Native shoulder and lower-limb chain readiness — 2026-10-28

## Purpose

Record the existing pinned authored control hierarchy for the shoulder complex and lower limb before attempting generic coupled movement. This is a rest-skeleton readiness audit, not an ISB coordinate calibration, anatomical side binding, movement test, or model repair.

## Actual pinned evidence

The independently downloaded W8/V14/R120 inspection artifacts from historical run `40029398965` remain usable successful-job evidence even though that run remains **FAILED overall** for its documented read-only docstring false positive. Their exact artifact and rig-member hashes are recorded in [native forearm chain readiness](HGPT_NATIVE_FOREARM_CHAIN_READINESS_20261028.md).

All three 77-bone inventories contain the same selected authored hierarchy for each suffix:

- Shoulder: `spine_03 -> clavicle -> scapula -> upperarm`; the authored `shoulder_cap` control is separately parented to `scapula`.
- Lower limb: `pelvis -> thigh -> shin -> foot -> toe`; the authored `hip_crease` control is separately parented to `pelvis`.
- No separately named `patella`, `talus`, `calcaneus`, `hindfoot`, `midfoot`, or `forefoot` skeletal control is recorded.

The selected hierarchy/coordinates/rotation-mode/deform/constraint subset is identical across W8/V14/R120, SHA256 fingerprint `6b2fbbe17a4ab18a2c054755138d682ba0115ff1b43080582f6ef7efbc304519`.

## Ruling

Status: `AUTHORED_LIMB_CHAINS_PRESENT_ANATOMICAL_FRAMES_AND_COUPLING_BLOCKED`.

The named clavicle/scapula/upperarm controls are evidence of an authored hierarchy, not verified thorax/clavicle/scapula/humerus frames, glenohumeral centre, scapulohumeral rhythm, or anatomical laterality. Likewise a single authored foot plus toe chain is not a verified talocrural/subtalar/midtarsal/forefoot model. Absence of separately named controls does not prove the mesh lacks those anatomical forms.

Seven initial synthetic regressions were observed RED before implementation and GREEN after. Fresh-context review found three Important wording/gating gaps: a broad multisegment-foot field conflicted with the observed foot/toe chain, concatenated segment names could bypass the absence gate, and shoulder-cap/hip-crease were called helpers without role metadata. Expanded regressions reproduced the first two RED. The hardened report narrowly states no separately named patella/internal-foot controls, matches segment tokens as case-insensitive substrings, and calls both items authored controls only. Focused `7/7` and actual replay PASS; final JSON SHA256 `3aba6e8a484de9afd6745166986ab61f796a74674a9dc581d4b4b642ab9cd5a7`, Markdown `fb09b41638d99d03790c2682c680af9ffe13c416ef80f6e41cf2ff5ed23fb3d1`. No review finding remains deferred.

Cloud execution is pending. No shoulder rhythm, squat, gait, ground contact, toe loading, balance, skin deformation or return trajectory was run. No original model, skeleton, weights, corrective key, permanent muscle ID, attachment/highlighting, PT-App, production asset, version, merge or deployment changed. Population ROM means are not hard limits.

## Cloud verification

- Published commit `bf6a83f4b0c5cb5a8932182c299435d1b3906d48`; [run 40758837170](https://github.com/anyangle1409-code/animation-software/actions/runs/40758837170) completed **SUCCESS 7/7**. Job IDs: pose `123064928473`, R120 `123064928707`, V14 `123064928733`, localization `123064928737`, W8 `123064928778`, comparison `123065544026`, driver `123068429094`.
- Cloud logs confirm localization `314/314`; comparison suites `5/5 + 12/12 + 9/9 + 7/7 + 12/12 + 15/15 + 13/13`; pose `24/24 + 19/19 + 6/6 + 10/10`; and driver `10/10 + 20/20 + 8/8` tests passed.
- Comparison artifact `12847173728` was independently downloaded, CRC-checked and SHA256-matched GitHub at `21a11414c1bb985586cb4931f792bbcb14378f38519e41f5b6a21ce6dc3968f9`. Its embedded limb JSON and Markdown exactly match the pinned replay hashes above.
- All nine artifact digests are recorded in `docs/recovery_20261023/cloud_verification_20261029_run40758837170.json`; the other eight are GitHub metadata hashes and are not claimed as independently downloaded here.
- Cloud reproduction verifies only the authored rest hierarchy and fail-closed nonclaims. Anatomical frames, joint centres, movement coupling, contact, balance and deformation approval remain blocked.
