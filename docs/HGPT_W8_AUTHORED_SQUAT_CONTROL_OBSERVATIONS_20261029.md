# W8 authored squat-control observations — 2026-10-29

## Scope

This is a read-only observation of the immutable W8 reconstruction (`2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`) under the frozen r57 benchmark code (`025d5f28fa7eba2064fba565b1c9b60119cdd2cb`). The probe opens the source with script auto-execution disabled, runs the existing nine authored squat samples in memory, records controls after the same runtime driver call used by the preserved diagnostic, and never saves a `.blend`.

The values below are authored-control observations. They are **not** ISB joint-coordinate angles, independently verified anatomical joint centres, pressure/force measurements, balance evidence, clinical limits or movement approval.

## Verified cloud execution

- Implementation commit: `30a2eaa5c0d661adb6ea5367aec91fcdcd23a09f`.
- GitHub Actions run [40857162884](https://github.com/anyangle1409-code/animation-software/actions/runs/40857162884): **SUCCESS 7/7**.
- Pose job `123390906355` executed all nine native samples. Its new focused suite passed 11/11; the localization job passed the complete 330/330 suite.
- Squat artifact `12890610821` independently downloaded, ZIP CRC clean, and SHA256 matched GitHub: `4a90f5bfb042140fc2136d9d1a91f455aa1f076c05ffb8679db2e225a54f3043`.
- Embedded JSON SHA256: `79331c557fe8ced962f154ed5dab7dba1693b50404fdec5da62af6f418a68f05`.
- Embedded Markdown SHA256: `c10cc5eb8019c23f142522a45be85f8a026164b5ff0d37f756dbbcee6bba4383`.

## Native observations

The authored targets use the frozen smoothstep path from rest to 25° pelvis forward tilt, 10° spine extension, 110° hip flexion and 110° knee flexion. Those targets describe the project path, not measured anatomical angles. The measured authored ankle value and foot-head world trajectories are:

| Sample | Authored ankle DF° (not ISB) | l foot-head X mm | r foot-head X mm | foot-head separation mm | lowest evaluated body Z mm (not contact) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000002 | -91.999993 | 91.999993 | 183.999985 | -1.423313 |
| 1 | 1.076256 | -90.573147 | 90.573147 | 181.146294 | -1.309167 |
| 2 | 3.913890 | -86.879946 | 86.879946 | 173.759893 | -0.970709 |
| 3 | 7.924802 | -82.101278 | 82.101278 | 164.202556 | -0.609452 |
| 4 | 12.518321 | -77.777497 | 77.777497 | 155.554995 | -0.609488 |
| 5 | 17.104715 | -75.190105 | 75.190105 | 150.380209 | -0.609461 |
| 6 | 21.099769 | -74.605525 | 74.605525 | 149.211049 | -0.609467 |
| 7 | 23.923236 | -75.173870 | 75.173877 | 150.347747 | -0.609518 |
| 8 | 24.993933 | -75.598121 | 75.598128 | 151.196249 | -0.609549 |

- Bilateral thigh, shin, foot and toe unsigned local-delta magnitudes match exactly at the artifact's serialized precision for all nine samples. This is authored symmetry, not anatomical side certification.
- Terminal unsigned local magnitudes are thigh `109.999992°`, shin `109.999992°`, foot `25.167521°`, toe `0°`; the measured authored ankle value is `24.993933°`. Matrix-basis magnitudes are not signed joint-coordinate components.
- Fore–aft and vertical foot-head positions stay within `0.000071 mm` of sample 0, but each foot head moves inward by as much as `17.394468 mm` at sample 6. Their separation narrows by `34.788936 mm` at sample 6 and remains `32.803737 mm` narrower at sample 8.
- The frozen benchmark's root translation therefore preserves the observed sagittal/vertical ankle-head placement to numerical precision but does **not** preserve mediolateral foot-head placement. A literal claim that both ankle heads remain at their complete rest positions is not supported by the runtime evidence.
- The evaluated body's lowest world Z rises by `0.813764 mm` from sample 0 to sample 8. This is a lower-envelope observation only; it does not establish floor location, pressure, force, slip or verified ground contact.
- The single `foot` plus `toe` control chain cannot establish talus/calcaneus or hindfoot/midfoot/forefoot coordination. No corresponding separately named controls were present in the prior three-model rest inventory.

## Ruling and next test

Status remains `READ_ONLY_AUTHORED_SQUAT_CONTROL_STATE_ANATOMY_NOT_APPROVED`. The newly measured mediolateral foot-head drift is a reusable full-body coordination defect to investigate before claiming planted feet, balance or ground contact. It does not authorize a rig, weight, shape-key or source-model edit.

The foot-plant decomposition requested here has now been completed and is recorded below. No corrective deformation is authorized.

No original `.blend`, mesh, skeleton, weights, driver, shape key, permanent muscle ID, attachment, highlighting, PT-App, production asset, PT_MODEL_VERSION 1.0, Claude-owned branch, merge or deployment changed. Muscle attachment/highlighting remain deferred; 46 landmarks remain unbound and 0/19 generic motions approved.


## Foot-plant solve decomposition — corrected native verification

The follow-up probe wraps the unchanged frozen \`_plant_feet\` call and observes evaluated control state immediately before and after it. Implementation commit \`aac74b36d40098756c4c2a82aef496fc436b572d\` added the decomposition. Run [40858906795](https://github.com/anyangle1409-code/animation-software/actions/runs/40858906795) completed SUCCESS 7/7, but independent artifact review found that its pre-solve observation preceded Blender's dependency-graph update and therefore contained stale rest-state heads. That run remains a successful CI execution, but its pre-solve evidence is superseded and must not be used.

Corrective commit \`b268375790150a30745de9c88a3d4c92728e7691\` requires an evaluated dependency-graph update before both observations. Replacement run [40919982094](https://github.com/anyangle1409-code/animation-software/actions/runs/40919982094) completed **SUCCESS 7/7**. Job IDs: localization \`123610262859\`, pose \`123610263090\`, V14 \`123610263160\`, R120 \`123610263190\`, W8 \`123610263334\`, comparison \`123610905509\`, driver \`123613572401\`. Cloud logs confirm 333/333 localization tests and pose suites 29/29 + 14/14 + 19/19 + 6/6 + 10/10.

Corrected squat artifact \`12917508191\` was independently downloaded, CRC-checked and SHA256-matched GitHub: \`718eee9b5ea8b5fedc76e091a5f58cd59389ba44a7b9ca14467d9262c402de2f\`. Embedded JSON SHA256 is \`998c3db075317a4549d7130c965bf38e08d3ad147fe3669214465d5303c47b69\`; Markdown SHA256 is \`e97810311ff7b4b9e6b9e5e843889e2b0d0b3d7e36e4dedd6d04eb1fa1da83bd\`.

At sample 6, immediately before the solve, authored foot-head residuals from captured rest targets are:

- suffix \`l\`: \`(+17.394640, -229.035827, +292.100161) mm\` in world X/Y/Z;
- suffix \`r\`: \`(-17.394312, -229.035840, +292.100161) mm\`.

After the unchanged solve they are:

- suffix \`l\`: \`(+17.394468, +0.000001, +0.000052) mm\`;
- suffix \`r\`: \`(-17.394468, +0.000024, +0.000030) mm\`.

Across all nine samples, the magnitude of the mean bilateral post-solve residual is at most \`0.000058 mm\`. The shared fore-aft and vertical residual is therefore removed to numerical precision, while the equal-and-opposite mediolateral residual cancels in the bilateral average and remains on each side. This directly localizes the inward foot-head drift to a limitation of using one averaged root correction for two opposing lateral residuals. It does not prove an anatomical ankle error, because the authored foot heads are still not independently verified joint centres.

The recorded root matrix-basis translation is expressed in the root control's local basis and must not be compared component-for-component with world-space foot residuals. No contact, balance, pressure, force, friction or movement approval follows from the near-zero bilateral mean.

Next safe work is to measure the evaluated foot/toe-dominant skin support envelope at the same nine in-memory samples and compare it with these control residuals. This should remain descriptive and must not invent a contact or balance threshold.


## Evaluated foot/toe-dominant skin lower envelope — native verification

Implementation commit `925106926653eaf002acc4a63b6ba1490fe65c08` extends the same source-preserving nine-frame probe with evaluated skin geometry. [Run 40921817758](https://github.com/anyangle1409-code/animation-software/actions/runs/40921817758) completed **SUCCESS 7/7**. Job IDs: pose `123616797572`, V14 `123616798041`, W8 `123616798153`, R120 `123616798155`, localization `123616798186`, comparison `123617575108`, driver `123620651993`. Cloud logs confirm 336/336 localization tests, 17/17 focused squat-probe tests, and the other pose suites at 29/29 + 19/19 + 6/6 + 10/10.

Artifact `12919471465` (`phone-w8-squat-pose-state-40921817758`) was independently downloaded and CRC-checked. Its ZIP SHA256 exactly matches GitHub at `e6aa66566ca220b224acb9157212ef6545f2b4a9f56b726f7d4864b4813ad4d7`. Member SHA256 values are JSON `dca20d29a49d65113c61fa7ce54d9b6bde9e55fb4bcc6b127bba7cae6e77e53a` and Markdown `f212fb7f217de68e770ce55c2fefdd60b3e73beb6a58e98063d5e2f8f82d9843`.

At each sample the probe evaluates the 219,974-vertex body mesh, selects vertices whose single dominant weight-group token is exactly `foot` or `toe` with the matching runtime suffix, and then reports the lowest 1% by world Z with vertex-ID tie-breaking. This produces 6,865 selected vertices and 69 lower-envelope vertices per side. The full selected-ID fingerprints remain constant across all nine samples:

- `l`: `e364be8f7e6735b11492afe3fd26f1d1a39c9954fa8988a7d8df463393a0c6df`, groups `foot_l` and `toe_l`;
- `r`: `8b066cf0408f3a0701d057908d0bb5c968f1d5f1bcd9af599823e12dcb60b858`, groups `foot_r` and `toe_r`.

The lowest-69 membership is not fixed: it occupies seven distinct vertex-ID sets per side over nine samples. This is evidence of a moving evaluated lower envelope, not a persistent anatomical or physical contact patch.

Across the trajectory, lower-centroid spans are approximately `7.86098 mm` mediolateral, `65.91125 mm` fore-aft and `0.34611 mm` vertical per side. Minimum Z spans `0.81388 mm` left and `0.81386 mm` right. Bilateral mirrored centroid disagreement is at most `0.000069 mm`. The world-space distance between each authored foot-control head and its skin lower centroid ranges from `103.47847 mm` to `151.10239 mm`; these different observables must not be treated as interchangeable joint/contact coordinates.

Status is `DESCRIPTIVE_EVALUATED_FOOT_SKIN_LOWER_ENVELOPE_NOT_CONTACT` with `contact_claimed=false`. No floor plane, support polygon, pressure, force, friction, slip, balance or tissue-safety threshold is measured or inferred. The selected groups are rig labels, not independently verified foot segments, and the authored foot controls remain unverified anatomical centres. Anatomy and ground-contact approval remain NOT_GRANTED; 46 landmarks remain unbound and 0/19 generic motions approved.

Machine record: `recovery_20261023/cloud_verification_20261029_run40921817758.json`. Historical run `40029398965` remains FAILED overall for its documented read-only docstring false positive; its separately verified W8/V14/R120/cross rig evidence remains valid. Run `40858906795` remains superseded for pre-solve causality despite successful CI. No protected source, model, rig, weights, shape keys, muscles, app, version, merge or deployment changed.


## Foot-control to evaluated-skin relative motion — native verification

Implementation commit `a1b1cf8acaa9272c9d3fa1bb6e0defc54ed3da17` adds an arithmetic-verified cross-reference between each authored foot-control head and the previously verified foot/toe-dominant skin lower centroid. [Run 40923708948](https://github.com/anyangle1409-code/animation-software/actions/runs/40923708948) completed **SUCCESS 7/7**. Job IDs: V14 `123623474520`, localization `123623474675`, W8 `123623474793`, pose `123623474843`, R120 `123623474954`, comparison `123624237260`, driver `123627194483`. Logs confirm 339/339 localization tests, 20/20 focused squat-probe tests, pose suites 29/29 + 19/19 + 6/6 + 10/10, and driver suites 10/10 + 20/20 + 8/8.

Artifact `12920285983` was independently downloaded and CRC-checked. ZIP SHA256 exactly matches GitHub at `7693ae61b4016ed65e0b83aa463514b775e07f2f3f401adb25d04cdec6f5cec2`; JSON SHA256 is `a8c52b51fe9c96f3be25c7bc46b4d0f6cda8ec0c8b275b8097815ec5aed2c561`; Markdown SHA256 is `12b6d26fe0cc9592fe520ffb92e7a33f8b4819c2c9416503b2a161d2473ff7cc`.

The report stores authored foot-control head minus evaluated skin lower centroid in world space, plus the change from sample 0. By sample 6 the changes are:

- suffix `l`: `(+9.533495, +65.911215, -0.346059) mm`;
- suffix `r`: `(-9.533493, +65.911244, -0.346046) mm`.

At sample 8 they remain approximately `(±9.53349, +65.91122, -0.34604) mm`. The maximum three-dimensional change-vector magnitude is `66.598047 mm`. The authored-control-head to lower-centroid distance rises from about `103.47847 mm` at sample 0 to `151.10238 mm` at samples 6–8.

This decomposition distinguishes two motions that a single planted-foot label would conceal. At sample 6 the authored foot head moved inward `17.394468 mm`, while the skin lower centroid moved inward only `7.860973 mm`; their mediolateral gap therefore increased by `9.533495 mm` on the left and the mirrored amount on the right. The approximately `65.9112 mm` fore-aft vector change is dominated by lower-centroid motion while the post-solve authored foot head stays near its captured rest Y coordinate. The approximately `-0.3461 mm` vertical change reflects the evaluated lower centroid rising relative to the authored foot head.

Status is `DESCRIPTIVE_FOOT_CONTROL_TO_SKIN_LOWER_CENTROID_RELATIVE_MOTION_NOT_CONTACT` with `contact_claimed=false`. These are not slip distances because no floor plane or persistent material contact point exists; the lowest-69 membership itself changes across seven sets. They do not establish support, pressure, force, friction, balance, tissue safety, multisegment foot anatomy or anatomical joint centres.

Machine record: `recovery_20261023/cloud_verification_20261029_run40923708948.json`. Historical run `40029398965` remains FAILED overall for the documented read-only docstring false positive; separately verified rig evidence remains valid. Run `40858906795` remains superseded for pre-solve causality. Anatomy/contact/movement approval remains NOT_GRANTED; 46 landmarks remain unbound and 0/19 generic motions approved. No protected source/model/rig/weights/keys/muscles/app/version/merge/deploy change.


## Corrective return-to-neutral lifecycle — 2026-10-30

The frozen benchmark calls its skeletal reset after the ninth sample but does not call the optional corrective driver again. Commit `b4e4aaf69f2ff9dcb8a6fc0519616955279cf4cf` measures both stages without changing the frozen r57 source:

1. after benchmark skeletal reset, before neutral driver refresh; and
2. after one call to the unchanged driver at neutral.

[Run 41048610295](https://github.com/anyangle1409-code/animation-software/actions/runs/41048610295) completed **SUCCESS 7/7**. The first stage has an exact identity matrix basis across all 77 pose bones, but retains eight active terminal squat correctives: bilateral H1 hip keys at 110/135 and bilateral K1 knee keys at 90/110. Relative to sample 0, `206166/219974` evaluated vertices differ above `0.000001mm`, with maximum displacement `65.193636mm` and RMS `8.395539mm`.

One unchanged neutral driver call clears all 79 shape-key values to the exact sample-0 fingerprint. The evaluated geometry then differs from sample 0 by at most `0.000478mm` (RMS `0.0000975mm`). However, the driver call introduces a maximum matrix-basis translation of `0.000223mm`, so the result is not reported as exact skeletal identity. The responsible control has not yet been localized.

Artifact `12974051212` was independently downloaded and CRC-checked. ZIP SHA256 `8d055ad877948109b09e7679979db7ee197f0c0a9616e83ba3d86c915ec08340`; JSON `877733264ff0ea2b4fb0845aa820fbc035c653d34ee6372cdb5298440b78606e`; Markdown `f8eb7143c586d698cdf29801b792ebe553e49d239c8c84b126c381ff50c25004`. Machine record: `recovery_20261023/cloud_verification_20261030_run41048610295.json`.

This is corrective lifecycle evidence, not anatomical neutral, deformation quality, contact, balance or tissue safety. No source model was modified or saved; no movement is approved.


### Residual control localization

Commit `b99eeae01bd16e1d76d48eac609a0249e60260e6` adds strict control-name inventory fingerprints and per-control matrix-basis residuals. [Run41049928430](https://github.com/anyangle1409-code/animation-software/actions/runs/41049928430) completed SUCCESS7/7. Before neutral driver refresh all77 controls are identity. After refresh, only six existing frozen muscle-line helpers exceed `0.000001mm`: `muscle_lat_l/r`, `muscle_pec_l/r`, and `muscle_trap_l/r`. The maximum is `muscle_lat_l = 0.000223020mm`; all six rotation residuals are zero.

Frozen r57 blob `c629f45ddb0bd48ece9f34be992a9ef168e66e38` (`scripts/original_v1_muscle_line_helpers.py`) recomputes each helper pose matrix from carried origin/insertion points, a rotation difference and length-dependent scale. This localizes the matrix recomposition source, but repeat-refresh idempotence remains unmeasured.

Artifact `12974836027`: ZIP `019b4a71664dea6a420d2f01d3bdd1d90e52383137daa117487bf4ebadb54b56`; JSON `f1b99eb109a5ce99cfb9cb5b7596834f1a9a39a18c50a491231ec7a52fcdc849`; Markdown `aeb3ff7ac01974472da7b2be556d833432b968cad6ed18e0390a81bf395845af`. These pre-existing authored review helpers are not verified anatomical muscle IDs, origins, insertions, side mappings or approved attachments.


### Repeated neutral driver idempotence

Commit `5d5c7c2d829fa65eb8f3b574c288c11bb590f150` captures a second unchanged driver call at the same neutral pose and directly compares its evaluated geometry with the first refresh. [Run41051228187](https://github.com/anyangle1409-code/animation-software/actions/runs/41051228187) completed SUCCESS7/7.

The complete77-control skeletal fingerprint is identical after refresh counts1 and2 (`489a8183964f9337a1cf0c267ae1a04c9cce2df6b832d80f9bf5378d805db9b1`). The79-key value fingerprint is also identical (`910743d8c37ed133e3ddf43eed2c4cf27dae553052ccc123147c0c142606c547`). Direct first-to-second evaluated geometry comparison finds0/219974 vertices above `0.000001mm`, max `0.0mm`, RMS `0.0mm`.

Therefore the six sub-micron muscle-line helper translations are stable one-time matrix recomposition, not iterative drift across the two measured refreshes. This is runtime idempotence evidence only, not anatomical validation of helper names, origins, insertions, side mapping or attachments.

Artifact12975276249 independently downloaded/CRC-checked: ZIP `138972401995e9b8096421d3fdec2fdf2daf0adcb45030cc6f6c5104c8405f4a`; JSON `420f107f1c8b76e64c6d79cb992038a9b146b011fa51a9bc5c5f81bb125a1ce7`; Markdown `d17bed5fcb9be88a96e6ba7ccd265e4bc64502898b49c55d8871b2084aa35ef6`.
