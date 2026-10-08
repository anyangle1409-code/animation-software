# Laptop / Claude inspection handoff — 8 October 2026, around 20:30 BST

The owner plans to use the laptop around 8:30 pm. This is a prepared inspection and continuation handoff, not a promise that the canonical skeleton will be ready by that time.

Repository: `anyangle1409-code/animation-software`.
Only branch: `codex/whole-body-biomechanics-audit-20261007`.
Last live HEAD checked before this repair: `dbdabf394b2dee92102b3e509c3c2c2f4d884c74`. Fetch the live branch first; read and preserve any newer commits. Never reset, revert, force-push or work from main. Do not discard local laptop work to switch branches; inspect and preserve it first.

## Actual position

CP1 regional numerical closure remains incomplete. Exact shoulder placement needs endpoint-compatible SC articular/manubrial landmarks, stature-aware clavicle chord/curve evidence, neutral thorax/scapula pose and AC/GH contacts. Four further primary shoulder studies were checked; none supplies all of those coordinates. See `canonical_clavicle_shape_source_review_v1.json`, `canonical_SC_contact_semantics_v1.json` and `canonical_clavicle_endpoint_crosscheck_v1.json` in `ORIGINAL_V1_WORK/anatomy/`.

CP2 actual curved-contact acceptance remains incomplete. CP3 is a verified construction/capture rehearsal using a003 data, not a corrected canonical skeleton. CP4 corrected-skeleton visuals remain blocked. Gates 6/8/9 remain open, Phase 10 deferred. Production mesh, weights and runtime drivers remain unchanged.

Blender 5.2.1 LTS through Python 3.13/bpy works in Work. The laptop is useful for independent inspection and local tooling; installing Blender alone does not supply the missing anatomical evidence.

## New independent-review targets

1. **CP3 rejection repair:** the old comparator could accept NaN endpoints, invalid capture vectors and wrong marker frame metadata, or crash on missing bones. All entries now undergo finite numeric/shape/nondegeneracy checks before reductions; identities and source frame-bone fields must match. Failed comparison exits with code 1 and writes a structured rejection report. Review the covariance/geometry thresholds by meaning, not merely by test result.
2. **Capture semantic repair:** `frame_bone` formerly read `hgpt_carrier_bone`, conflating the source reference basis with the physical attachment host. This mislabeled 202 fields in the old rehearsal. New builds preserve `hgpt_frame_bone`; capture stores separate `frame_bone`, `carrier_bone` and actual `parent_bone`. Physical attachment and all 427 marker centres are unchanged in the retained before/after comparison. Do not change parents to force the two references to agree.
3. **Historical limits:** old a003 rehearsal captures and positive round-trip reports remain archived; they did not verify frame-bone metadata. Newly retained files fix metadata only. No new anatomy or Gate 9 acceptance is implied.
4. **Source audit:** Fontana2020 printed pooled height/CL r=.968 conflicts with its subgroup/overall summaries under the same paired-record interpretation; conditional conservative bound is below .692. Do not use it for a 1.82 m prediction or invent a replacement correlation. Qiu's printed mean/SD remain intact; paired bones do not establish a direction of between-person SD change. Languth's AP diameters are not bilateral SC breadth. Lee's pooled tapered-disc thickness is not a uniform joint gap. Suarez Romero's surgical portal distances are not SC-centre coordinates.

## Verified evidence

`ORIGINAL_V1_WORK/anatomy/audit/runs/work_cp3_rejection_repair_20261008_001/` contains failed tests, overflow false-pass, legacy semantic mismatches, fresh .blend files/captures as gzip archives, hashes, fresh round-trip reports and full-suite traces. Both fresh builds retain 206 bones/427 markers; source-frame metadata matches the input and round-trip storage checks pass. CP2 remains FAIL on the inherited anatomy, as expected. No new canonical candidate is present.

26 affected CP2/CP3 tests pass. Full discovery: 805 tests, the same named five failures/four errors as the previous 800-test checkpoint. `baseline_comparison.json` retains the exact names. Earlier 135/135 isolated movement implementation results remain evidence from the preceding run; they were not rerun for a metadata-only repair and do not accept anatomical contacts/followers.

## Safe laptop sequence

1. Fetch/check live HEAD and read every newer commit, the live tracker, findings, skeleton-first policy and checkpoint plan. Preserve local and remote work.
2. Inspect the primary evidence definitions and the validator repair independently. Try omitted bones/markers, NaN in late entries, malformed arrays, wrong frame IDs and unit-axis errors. Check why a valid round-trip can coexist with CP2 FAIL.
3. Run from repository root with a Python environment containing NumPy:

```bash
python -m unittest scripts/test_cp3_roundtrip_compare.py scripts/test_cp2_preflight.py
python scripts/validate_canonical_target_selection.py
python scripts/validate_complete_anatomical_atlas.py
python -m unittest discover -s scripts -p 'test*.py'
```

The full suite is expected to report the retained nine legacy production/recovery failures. Report additional failures explicitly; do not hide or weaken them. Target validation's `freeze_ready=false` is an intentional block, not anatomy acceptance.

4. For visual inspection, decompress `frame_metadata_a003.blend.gz` or `frame_metadata_mirrored.blend.gz` from the repair run into a NEW scratch directory and open a copy in Blender. Compare hashes with `manifest.json`. These are a003 diagnostic skeletons with corrected metadata. Do not present them as the new corrected skeleton.
5. To independently recapture a decompressed rehearsal with desktop Blender, use new paths:

```bash
blender --background --python scripts/anatomy_fit/cp3_rehearsal_blender.py -- capture --blend NEW_SCRATCH/frame_metadata_a003.blend --out NEW_SCRATCH/capture.json
python scripts/anatomy_fit/cp3_roundtrip_compare.py --record ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json --capture NEW_SCRATCH/capture.json --out NEW_SCRATCH/roundtrip.json
```

Replace `NEW_SCRATCH` with the chosen unused directory. Direct Python/bpy can run the same capture script without `blender --background --python ... --`. A zero comparator exit code verifies only the round-trip; inspect `cp2_preflight_on_capture` separately. Do not overwrite retained evidence.

6. Continue CP1a matched articular/source geometry, or independent CP1b–g work while essential shoulder evidence is unavailable. Store precise blockers and source definitions beside each value. Keep a003/production unchanged. Create the next immutable canonical candidate only after accepted target data and CP2 permit it, then produce the owner's required six-view review pack.
7. Append genuinely verified outcomes to both primary tracking files; commit and push coherent progress with a live-head lease. Claude may reopen any conclusion. No routine owner approval is required for the already authorized audit.

The laptop review is independent validation. It cannot turn missing coordinates into numerical evidence or close Gates 6/8/9 by opening Blender.

## Latest owner steering and primary limb review

Owner supplied the Claude 6570e750 handoff again and requested limb proposals first. Live branch was already newer; all intervening work is preserved. The original de Leva paper is now accessible from the primary-paper copy at UFABC; the three recalled values have been rechecked, with the shank endpoint correction recorded above in the current tracker. Read `canonical_de_leva_primary_endpoint_review_v1.json` and `canonical_forearm_endpoint_decision_v1.json` before selecting any radius/ulna targets. Forearm shortness direction is retained, but EJC-WJC, RAD-STYL and bone-articular spans are not interchangeable. Review the new HJC sensitivity; do not declare a003's thigh short. Next continue the other PARTIAL regions, including humerus and sternum. Canonical candidate construction still requires all regional targets and CP2 without FAIL/UNVERIFIED; 23 actual disc surfaces, not plane-only declarations, remain essential. Existing laptop acquisition list in Claude's handoff remains relevant, but verify current availability instead of assuming every cloud route is inaccessible.

Latest forearm review: use `canonical_forearm_landmark_requirements_v1.json` for the radius/ulna inspection points. Keep radial head, radial styloid, sigmoid-notch rims/surface, ulnar head, ulnar styloid and greater sigmoid-notch centre distinct. A three-point sphere fit alone is insufficient. Hong supplement has unresolved sex-ID/units labels and no individual stature field; do not use its mean to resize the skeleton.

Shoulder acquisition update: Seth original archive is now obtained in Work via `https://stacks.stanford.edu/file/br087nj9017/ScapulothoracicModelAnalysisPLOS2015.zip`. Read `canonical_sc_primary_model_reference_v1.json` for hashes, IJ-relative SC and distinct AC/GH records. Download acquisition is resolved; anatomy/182 cm selection and coordinate-frame mapping remain open. SimTK file 4695 still shows a login wall, but the author-advertised Stanford archive is public. C2 source review: Table 2 labels SD; possible SE remains unconfirmed. Usable SD remains null in target/stack/register.

## 8:30 pm London pickup

Latest verified checkpoints before this handoff update: `2c8979f9` and `b3a274b5`; fetch the live branch for the subsequent shoulder/C2 checkpoint and preserve anything newer. Owner input is not needed for routine inspection or audit fixes.

Start with the CP3 rehearsal files and source definitions above. Corrected canonical geometry is still unavailable because CP1 targets/contact surfaces and CP2 remain incomplete. The available Blender files are explicitly a003 diagnostic rehearsals. Latest full suite is 806 tests, with the same nine existing failures; the additional C2 source-register regression check passes.

Shoulder frame pickup: use `map_between_thorax_frames` for a model-body XYZ point. The source body basis differs from its landmark ISB basis by ~7.86°; direct mapping produces a ~1.29 mm SC error. Fresh Blender quaternion-frame math and bilateral signs were checked in a synthetic pose. This does not establish the canonical target thorax pose. Latest suite: 808 tests, unchanged 9 pre-existing failures.
