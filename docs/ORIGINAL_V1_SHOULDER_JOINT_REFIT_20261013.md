# ORIGINAL_v1 shoulder source-joint trial — 13 October 2026

## Actual phone review

[Six-view full-body phone sheet](https://chatgpt.com/api/library/files/libfile_6b371aed35208191944bd8bedd05e2f2/download).

| Pose | Front | Three-quarter |
| --- | --- | --- |
| Neutral | [PNG](https://chatgpt.com/api/library/files/libfile_a6a3a06d173c8191a20baca7d787800d/download) | [PNG](https://chatgpt.com/api/library/files/libfile_aab894bfd21c8191b071001a3f8533dc/download) |
| 90° authored reach | [PNG](https://chatgpt.com/api/library/files/libfile_737b1019a8848191892b50d545528539/download) | [PNG](https://chatgpt.com/api/library/files/libfile_817429e5c09c819188b5dd920d84ce0c/download) |
| 160° authored reach | [PNG](https://chatgpt.com/api/library/files/libfile_47956a3178b88191875b0e3e0851b93c/download) | [PNG](https://chatgpt.com/api/library/files/libfile_6acd601cfa1c8191a50e848ce5b64cac/download) |

[Separate native full-body candidate](https://chatgpt.com/api/library/files/libfile_66b2bc9a12b4819197fb0e2bcd7a1a2a/download). [Native measurements](https://chatgpt.com/api/library/files/libfile_33dca9cc690481919fa1e9226a125516/download). Downloads require the owner's signed-in session. These are actual Blender5.2.1 renders, 1200×1800, fixed orthographic scale2.65m. No generated substitute. Skin distortion is visible and NOT accepted.

## Source and explicit joint semantics

Implementation input PR105 branch `codex/original-toe-articulation-trial-20261013`, full commit `8e050c2dc9798030df584f9a71644945568c3a48`. Authored-context source PR84 full commit `27e2dbf4424b878d8312cf346624e495720bba0a`, `HomeGymPT_Male_ORIGINAL_v1_AUTHORED_THORAX_REVIEW_ONLY.blend`, SHA256 `ca8e6824ae54e5778a04409e00d32ae13ac23d9fce95e1f6d8207abbef265ca7`. Original r95/a003 source SHA256 `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56` remains untouched.

The existing c004 `joint_markers` provide six fitted SC/AC/GH centres and marker frames. All are **FITTED_UNVERIFIED_OPERATION**. The contract checks SC against clavicle head, AC against clavicle tail, GH against humerus head, validates proper rigid marker frames, and explicitly transposes XYZ column vectors into row-major matrices. AC is NOT the scapular glenoid head. Native guide-origin gaps are below0.000015mm. Marker axes are distinct from authored bone control axes; recorded offsets do not authorize clinical axes or an installed production retarget.

## Separate functional runtime trial

Copied67-control runtime `HGPT_SHOULDER_JOINT_REFIT_TRIAL` refits six shoulder control rest frames: six heads use the provisional centres and four tails change. Bilateral clavicle tails become AC, scapular control tails become GH. Control lengths and rest directions consequently change; upper-arm tails retain inherited elbow stations and edit-bone roll scalars are inherited. Original67runtime,206reference and actual17,946vertex body are retained separately. Anatomical left+X maps suffix_r; right−X maps_l.

Copied body `HGPT_BODY_SHOULDER_REFIT_TRIAL` retains mesh coordinates, inherited weights and correctives. It binds to the copied runtime only. **Skin/weights have not been refitted.** Neutral evaluated maximum displacement is0.000141mm. No native source saved over; original vertex/weights/all corrective coordinates/rig world-rest matrices/parent names/poses fingerprint matches before/after. This enumerated fingerprint omits topology, group names, explicit bone endpoints/lengths and the authored guide armature; it is not an exhaustive in-memory scene-invariance proof. The exact unchanged source-file hash independently preserves all original file bytes. Candidate SHA256 `a48ee389a064927f740b5ea294b7afed3ef1616cbe8ac6c121867b86581680c2`.

Eleven stages REST/0/45/90/135/160/135/90/45/0/REST executed, all finite, returning within2µm of neutral. The inherited artist-authored shoulder coupling and shortest-arc humeral direction are implementation probes, not human movement validation. At160° minimum/maximum triangle area ratios are0.009709/3.950244: major compression/stretch is unresolved. World normal-dot sign changes also include legitimate rigid turning and must NOT be described as proved triangle inversions.

Visual review finds severe chest-to-armpit stretching and shoulder volume distortion at90°/160°. Original long/tubular feet remain present; the separate PR104/105 toe candidates are not installed into this shoulder trial. Foot shape, shortening, individual-toe regression, elbow station/axes, realistic shoulder muscles/skin, loaded exercise, contact and production acceptance remain open.

## Verification and restart

Eleven pure shoulder contract/bind tests PASS; two native candidate reopen tests PASS after failing on the original input. These check source-centre alignment and retained original body/sole trial driver, not deformation acceptance. Six rendered PNG hashes, phone sheet, candidate and measurement hashes are recorded in `docs/reviews/ORIGINAL_V1_SHOULDER_REFIT_EXPORT_HASHES_20261013.json`. Native authority frames and sampled measurements accompany this checkpoint. Inherited broad suite remains red; not rerun. CI checks pure contracts/syntax only, native tests were executed separately against saved candidate.

Next W2/W4: deliberately refit chest/deltoid/axilla skin influences and corrective shapes around these unchanged provisional source centres; compare actual neutral/90°/160° skin, preserve original geometry and failing deformation evidence. Resolve elbow/functional-axis authority separately. Do not merge, promote anatomy, export as accepted67schema or replace production. Regional readiness remains0READY/9PARTIAL/3BLOCKED. Existing hourly task was re-enabled on13October; no exposed quota/reset telemetry or exact restart-time promise.
