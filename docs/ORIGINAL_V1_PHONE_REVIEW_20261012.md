# ORIGINAL_v1 actual full-body phone review — 12 October 2026

Rendered in native Blender 5.2.1 from Work PR80 at full commit
`2af63aedc3ff1c8c5de4974b4e826ec6ce26d81b`, branch
`codex/functional-original-fullbody-bridge-20261011`.
Source: `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend`.
Source SHA256: `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.
Live PR48/26/80 and original Claude branch were checked before work;
Claude head was `540edd4ca97927e04c2966a27f70148678c29464`.

The actual original 17,946-vertex male body is shown, not a legacy V-series
character or replacement mesh. Full-body means head-to-foot coverage; it does
not mean this provisional r95 character is finished or production-ready.
Seven 1600×2400 neutral views use one unchanged orthographic scale;
ten 2000×2000 detail views cover shoulders/axilla, both hands, knees and feet.
Four separate native 206-control guide renders support four registered
body/guide overlays. Control guides are not anatomical bone surface meshes.
Original materials are retained in the separate review GLB; image lighting
uses Workbench neutral clay for shape inspection.

## Open on phone

- [ORIGINAL_v1_FULL_BODY_CONTACT_SHEET.png](https://chatgpt.com/api/library/files/libfile_6af25e18fc688191b7e5784199282b23/download)
- [ORIGINAL_v1_ALL_VIEWS_PHONE_CONTACT_SHEET.png](https://chatgpt.com/api/library/files/libfile_baa8e2f5a16c8191837af96a0f6f92b4/download)
- [ORIGINAL_v1_JOINT_DETAIL_CONTACT_SHEET.png](https://chatgpt.com/api/library/files/libfile_8c71d797f9548191b1fc2e5e2779536b/download)
- [ORIGINAL_v1_SKELETON_OVERLAY_CONTACT_SHEET.png](https://chatgpt.com/api/library/files/libfile_c0b4120716a88191b33162f50d9b24ea/download)
- [ORIGINAL_v1_FULL_BODY_REVIEW.zip](https://chatgpt.com/api/library/files/libfile_7f0a17d27c688191a32ebfa1ce5f5cd4/download)
- [HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb](https://chatgpt.com/api/library/files/libfile_a6ce8fa9bc84819195e37e52afcd455a/download)

All individual images:

- [detail_feet_front.png](https://chatgpt.com/api/library/files/libfile_79c6a978f6f88191950acdca70476190/download)
- [detail_feet_side.png](https://chatgpt.com/api/library/files/libfile_81d00a5140ac819197e42cfbe7f69c70/download)
- [detail_knees_front.png](https://chatgpt.com/api/library/files/libfile_57d6c953c9e081918170855ee55e1df2/download)
- [detail_knees_side.png](https://chatgpt.com/api/library/files/libfile_20cf915f057881918cf6b2fbb4724e6f/download)
- [detail_left_hand.png](https://chatgpt.com/api/library/files/libfile_0fc128f9d8a081918af3c01acb7b57e2/download)
- [detail_left_hand_front.png](https://chatgpt.com/api/library/files/libfile_0eaa4bfc5d188191b3eede894279eee0/download)
- [detail_right_hand.png](https://chatgpt.com/api/library/files/libfile_20186600bbe081919f440ddaa9d450f4/download)
- [detail_right_hand_front.png](https://chatgpt.com/api/library/files/libfile_8be3081f28cc819180eb9432cd1fecf2/download)
- [detail_shoulders_armpits_front.png](https://chatgpt.com/api/library/files/libfile_b3133a8acb048191a1ef639f9107d1c8/download)
- [detail_shoulders_armpits_rear.png](https://chatgpt.com/api/library/files/libfile_3074ac3cbc9481919ea6585f37d99364/download)
- [neutral_front.png](https://chatgpt.com/api/library/files/libfile_cf3690e2eb8481919a39168879c32b56/download)
- [neutral_left_side.png](https://chatgpt.com/api/library/files/libfile_536053dcbe848191a4b3bc7b5e7c93fe/download)
- [neutral_left_three_quarter.png](https://chatgpt.com/api/library/files/libfile_113cb01e81888191b899f2216372c89b/download)
- [neutral_rear.png](https://chatgpt.com/api/library/files/libfile_bc03cf96e43881918a0dfa204db72e4d/download)
- [neutral_rear_three_quarter.png](https://chatgpt.com/api/library/files/libfile_755a110628248191aa99f806bc15afa1/download)
- [neutral_right_side.png](https://chatgpt.com/api/library/files/libfile_deefb450e9d481919f3db2ec60c1c17d/download)
- [neutral_right_three_quarter.png](https://chatgpt.com/api/library/files/libfile_bc34743ae2888191816ff6660967f511/download)
- [skeleton_overlay_front.png](https://chatgpt.com/api/library/files/libfile_3f404b6e3f388191931523a4bdea3eb7/download)
- [skeleton_overlay_left_side.png](https://chatgpt.com/api/library/files/libfile_795aab035f9c8191894a0989aaccaa07/download)
- [skeleton_overlay_rear.png](https://chatgpt.com/api/library/files/libfile_9bd71969597481919a982ba07daae2db/download)
- [skeleton_overlay_right_side.png](https://chatgpt.com/api/library/files/libfile_0e32fbcc62348191bd3cbfa4a010753c/download)

## Verification and limits

- 4 existing pure bridge tests and 4 native Blender bridge tests PASS.
- Source bytes, body vertex coordinates and both skeletons' rest geometry unchanged.
- 30 delivered image/GLB digests independently recomputed: zero mismatches;
  all 29 final PNGs decode and verify, all 32 artifacts saved successfully.
- Separate GLB: 1 mesh, 17,946 vertices, 1 skin, 67 joints, 1,495,720 bytes,
  embedded buffer, no animation or camera; correct source Y-up stature about 1.82m.
  This checks packaging only, not runtime playback or deformation parity.
- Three initially incomplete generated PNG writes were detected by PNG verification,
  regenerated before publication, and excluded from delivered evidence.
  Temporary file + atomic rename protects subsequent generated image publication.
- The 206-bone master remains separate and static; the existing 67-bone rig drives skin.
- Visual issues: angular neck/trapezius and deltoid transitions; simplified tubular
  digits/palm/thumb web; faceted heel/ankle and simplified toes/arch; unfinished face,
  torso and knee detail. These observations are not medical diagnoses or measured
  proportion failures. Reference acceptance, contact and motion remain unverified.
- No new anatomy, clinical, motion, copyright or production approval. Historical
  regional readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.

## Next Work-owned task resumed

PR80 next task is authored thorax/S-curved clavicle/costal-blade integration
and explicit source→runtime attachment/retarget semantics. Start with a read-only
native anchor/rotation comparison: c004-authored shape guides cannot simply be
attached to the r95/a003 runtime without proving centre/frame compatibility.
Never invoke the shoulder builder's destructive `build()` in the original scene:
it deletes the scene before making its separate six-control pilot.


### Executed next-task result

Read-only Blender 5.2.1 comparison of all six newer c004-authored shoulder
controls against the actual r95/a003 full-body runtime completed:

| Pair (both sides) | Pilot head vs runtime head | Axis direction difference |
| --- | ---: | ---: |
| Clavicle | 12.091 mm | 8.018° |
| Scapula (pilot AC-rooted control) | 74.946 mm | 8.175° |
| Humerus | 54.789 mm | 1.229° |

These are model-to-model discrepancies, not distances from medically correct
human anatomy. PR72 intentionally changes the scapula pilot control head to AC;
that control definition differs from the full-body runtime control. All source
skeleton and skin geometry remained unchanged. The detailed read-only native
report is `docs/reviews/ORIGINAL_V1_SHAPE_ATTACHMENT_AUDIT_20261012.json`.
Do not install a bare name-matched six-control adapter. Next: define explicit
joint/contact versus control-origin semantics and bind offsets using the
anatomical source authority, then independently verify placement and motion.
No safe automatic geometry fitting or movement promotion follows from this audit.
