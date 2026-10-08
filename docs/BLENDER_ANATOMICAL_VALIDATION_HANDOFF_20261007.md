
## OWNER DECISION 2026-10-08 — SKELETON FIRST

The anatomical skeleton is now the production source of truth for proportions. The current r95/a003 mesh-driven short forearm/hand and long feet are **not** accepted as intended final styling. Keep a003 unchanged as the audit baseline. Do not move corroborated joint centres merely to stay inside the current mesh and do not reshape production geometry yet. First define/freeze canonical skeletal proportions independently of the mesh, then refit the mesh/skin around the validated skeleton after Gates 6–9 permit downstream production work.

Machine-readable target record: `ORIGINAL_V1_WORK/anatomy/canonical_skeleton_proportion_targets_v1.json`.
Policy: `docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md`.
Regression checks: `scripts/test_skeleton_first_proportions.py`.

# Local Blender validation tools — 7 October 2026

These tools prepare the next validation session. They do not fit the skeleton, create poses, approve movement or complete any Blender gate. Production files are unchanged.

## What is ready

- `scripts/capture_anatomical_validation_blender.py`: reads an explicitly selected armature, its evaluated poses, fitted joint-frame empties and tagged landmarks. It never creates bones/poses or saves the `.blend`. Animation frame/subframe is restored even if a measurement fails.
- `scripts/anatomical_blender_validation.py`: generates the source-bound test plan and analyses captures outside Blender. It checks numerical integrity and records lengths, bilateral differences, centres, relative transforms, principal rotation changes and trajectory speed/acceleration.
- `ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json`: all 206 reference names, 427 joint marker requests, 30 landmark recipes, 44 profile test specifications and all 12 functional tasks. Animation requests are intentionally empty until local poses and solvers are authored.
- `scripts/test_blender_anatomical_validation.py`: synthetic regression tests. These verify the numerical/report logic and frame restoration through a small scene-state test double. They do not execute Blender.

## What the results mean

**PASS** means the specific supplied numerical/identity check succeeded. For example, all expected anatomical IDs are present once, or a provided matrix has a proper rotation basis. It does not mean those bones are correctly fitted to the body.

**FAIL** means a detected contract or numerical error, such as missing required reference bones, duplicate identities, zero-length segments, unknown parents, cycles, stale evidence, reflected/sheared frames or an exact AC/GH centre collision.

**UNVERIFIED** means the required evidence or anatomical judgement is absent. The report always leaves character acceptance, joint operation and anatomical placement unverified. It never checks off tracker gates.

A capture of the current simplified production rig will fail complete-master bone coverage because its 67 controls are not the 206 anatomical reference bones. That is an expected reference gap, not a claim that all existing animation is unusable.

## Start with an isolated audit copy

1. Open an isolated copy of the exact character to be fitted. Record the file revision. Do not save audit edits into the production/recovery candidate.
2. Fit/create the anatomical master under the existing Phase6/7 instructions. Each conventional reference bone must use the stable `anat_<anatomical_id>` name from the aliases file. A `hgpt_anatomical_id` custom property may identify a reference, but it does not replace the naming contract. Untagged runtime helpers do not count as anatomical bones.
3. Fit joint-frame EMPTY objects using the exact `HGPT_JOINT_<articulation_id>` names in the plan. Orient them from the referenced landmark recipes. Their translation is the explicitly fitted reference centre. The script never guesses a centre from an armature bone head. Functional/fixed contacts use their specified reference locator, not a fictional free hinge.
4. Landmark objects can carry a string custom property `hgpt_landmark_id`, for example `femur_left/femoral_head_centre`. The label and position are exported; anatomical suitability still requires review against the atlas recipe and character.
5. Identify the armature by its exact Blender object name. Confirm how many physical metres one Blender world unit represents from the character's scale; do not infer it from a plausible height.

## Static smoke capture

Run from the repository root with your installed Blender executable. Replace the paths, armature name and measured scale:

```bash
blender --background /absolute/path/character_audit_copy.blend \
  --python scripts/capture_anatomical_validation_blender.py -- \
  --armature HGPT_ANATOMICAL_MASTER \
  --metres-per-unit 1 \
  --plan ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json \
  --out-directory /absolute/path/audit_runs/static_001
```

`1` is an example, not an approved scale. The tool refuses to overwrite `capture.json`, `report.json` or `report.md`; use a fresh run directory. With an empty `samples` list it captures the current frame/subframe as `unassigned_current_pose`, not as a completed motion test.

The exporter samples the evaluated dependency graph: pose-bone matrices are in armature object space, then transformed to world space. Translation/point values use the explicit metres conversion; rotation axes are retained. Source `.blend` hashes before/after, initial/restored frame, dirty state, scene FPS, scene units and Blender version are recorded. Failed automatic Python execution leaves motion provenance unverified. Unsaved edits leave the saved-file identity insufficient; save the isolated audit copy before its final evidentiary run.

## Add locally prepared movement samples

Generate an editable copy of the plan; the generator refuses overwrites:

```bash
python scripts/anatomical_blender_validation.py plan --out /absolute/path/audit_runs/local_plan.json
```

Only fill `samples`; the reference contract must stay equal to the source atlas. The profile cases give source context, sides, stages, return/reversal requirements, tests and acceptance criteria. The frame numbers below are examples of an already-authored local animation, not instructions to drive the production skeleton:

```json
{
  "test_id": "isolated_hip",
  "frame": 20,
  "subframe": 0,
  "side": "left",
  "plane": "sagittal",
  "direction": "outbound",
  "posture": "locally documented test posture",
  "load": "unloaded",
  "measurement_mode": "active",
  "evidence_images": ["/absolute/path/audit_runs/hip_left_frame20.png"]
}
```

Place a list of such entries in `samples`. The exporter does not render screenshots: existing operator-prepared images can be attached by absolute path and content hash. Image-to-scene correspondence remains a review task.

Prepare both sides where applicable, neutral/intermediate/near-context-range samples, return and reversal, and every relevant movement plane. Keep each task, side, posture, load and mode distinct. Use functional test IDs from `functional_cases`, such as `functional_squat`, after isolated mechanics pass. A frame label is not proof that a test's full requirements were executed.

Times are `(frame + subframe) / scene_fps`. Trajectory metrics are computed within each named task/side/plane/direction/posture/load/mode context, preserving sample order. Duplicate or decreasing times within a trajectory fail. Principal rotation change is a descriptive 0–180 degree orientation difference, not a signed anatomical axis angle, cumulative turn or clinical ROM. Relative bone matrices are parent-relative raw transforms; character-specific anatomical/JCS conversion and contact-surface mechanics remain separate work.

## Reanalyse a capture outside Blender

```bash
python scripts/anatomical_blender_validation.py analyze \
  /absolute/path/audit_runs/static_001/capture.json \
  --plan /absolute/path/audit_runs/local_plan.json \
  --out /absolute/path/audit_runs/static_001/reanalysis.json \
  --markdown /absolute/path/audit_runs/static_001/reanalysis.md
```

The analyser verifies the atlas hashes and full reference contract rather than trusting a modified list of expected bones. Existing output files are preserved. Exit1 means a detected failure; exit0 can still mean UNVERIFIED, so always read `overall_status` and the individual checks.

## Verification and remaining local checks

The automated tests cover missing geometry, false acceptance from naming alone, nonfinite/zero-length bones, hierarchy errors, duplicate identities, stale/altered contracts, unresolved/dirty provenance, missing marker evidence, coincident centres, proper-frame relative transformations, real-time trajectory calculations, absent-sample status, frame/subframe restoration on failure, exclusive output creation and landmark identity/coordinate errors. The exporter has an additional static scan for forbidden save/pose-driver calls. That scan does not replace a Blender execution test.

Blender is not installed in this environment. Before relying on local output:

- Run the static smoke capture and verify point positions against Blender's UI with the same unit conversion.
- Verify an intentionally offset joint marker and a simple 90-degree test rotation produce expected raw measurements.
- Confirm the original frame/subframe and source file hash are preserved.
- Confirm constraints/drivers evaluated correctly and the expected armature was selected.
- Inspect bone-only screenshots and measured centres against fitted landmarks; do not accept placement based on segment lengths alone.
- Review anatomical coupling, contact surfaces, translations, source-specific active/passive behaviour and continuity in the existing tracker order.

No universal bilateral tolerance, acceleration limit or physiological angle limit is invented by these tools. Anatomical operation, fitting, deformation and performance remain unaccepted until the local evidence passes review.

Final tool verification: 21 synthetic tool tests and 16 atlas tests pass. The full repository runs 571 tests: 562 pass, with the same five failures and four errors recorded before this extension; no additional failures. Protected production input hashes match the prior baseline. Independent review found and verified fixes for incomplete/contradictory provenance reporting and absent geometry reporting. Machine-readable evidence: `ORIGINAL_V1_WORK/anatomy/blender_validation_tools_verification.json`. These results do not execute Blender or accept any character fitting/motion gate.

## Live execution update (7 October 2026) and resume instructions

Blender was available in the cloud session as Blender 5.2.1 LTS, imported as the `bpy` module (`PYTHONPATH=<bpy dir> python3.13 …`). On the laptop, run the same scripts with `blender --background --python <script> -- <args>`; every script accepts the `--` argument separator.

### What now exists

| Step | Command (repo root) | Output |
|---|---|---|
| Toolchain smoke | `python3 scripts/blender_smoke_anatomical_capture.py --out <new dir>` | 22 analytic checks (`audit/runs/blender_smoke_001`, re-run `blender_smoke_002` after the scale check) |
| Audit copy | `python3 scripts/anatomy_fit/build_audit_copy.py --glb <r95 BARE> --sha256 c4b8e388… --out-blend <new> --receipt <new>` | `audit/HGPT_ANATOMICAL_AUDIT_r95_a001.blend` |
| Fit and master (Phases 6–7) | `python3 scripts/anatomy_fit/build_anatomical_master_blender.py --source-blend audit/…a001.blend --out-blend <new> --record <new>.json` | a003 + `character_fit_r95_a003.json` (a002 superseded) |
| Independent capture | `python3 scripts/capture_anatomical_validation_blender.py --blend <a003> --armature HGPT_ANATOMICAL_MASTER --metres-per-unit 1 --plan ORIGINAL_V1_WORK/anatomy/blender_validation_plan.json --out-directory <new>` | `audit/runs/master_static_003` (adds `bone_scale`) |
| Isolated sweeps (Phase 9) | `python3 scripts/anatomy_fit/run_isolated_tests_blender.py --source-blend <a003> --record character_fit_r95_a003.json --out-blend <new> --out-dir <new>` | `audit/runs/isolated_bone_only_014` (current, 135 tests; earlier runs retained) |
| Review images / clips | `scripts/anatomy_fit/render_master_review.py`, `render_test_clips.py` | `audit/review/…` (clips: `isolated_clips_005` for the original 70 tests, `isolated_clips_007` for the newly sourced tests from the run-012 file) |
| Review addendum | `python3 scripts/anatomy_fit/recheck_fit_record.py --record character_fit_r95_a003.json --out <new>` | corrected Trotter–Gleser, pre-snap midline, parallel-segment check |
| Proportion evidence (F-PROP/F-GH/F-HJC) | `python3 scripts/anatomy_fit/proportion_audit.py measure --blend <a003> --record <fit> --out <new>` then `compare --surface <that> --record <fit> --addendum <addendum> --ansur ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv --out <new>` | `audit/proportion_audit_001` |
| Tests | `python -m unittest scripts/test_blender_anatomical_validation.py scripts/test_anatomy_fit.py` | 28 + 23 (absolute world-direction tests for every spec and follower, source binding, proportion evidence) |

All outputs are new files; every script refuses to overwrite. The meaning of PASS is unchanged: it records numerical integrity only.

### Resume order

1. Fetch the live branch head and read the tracker and findings report (sections “Phase 6–7” and “Phase 8–9”).
2. F-PROP-001 / F-GH-001 / F-HJC-001 were investigated (findings section “investigation”). Femur and humerus stature-equation failures are method bias, and HJC, KJC, elbow and GH are corroborated, so no a004 was made. Ask the owner one question: is the short forearm/hand (z −2.2) and long foot (z +2.8) of the authored body intended styling? Any body change is a production change; if it happens, refit as a new audit revision and repeat Phases 6–9.
3. Obtain full-text magnitudes for what is still unresolved (`phase9_supplementary_observations.json` → `unresolved`): L1/L2, C2/C3, C7/T1, ribs 8–12 and proper rib-neck axes (F-RIB-001), SC elevation, midfoot/TMT/lesser toes, wrist stage split, thumb pronation and opposition flexion, patellar translation path, fibular rotation, and rhythm plane dependence. Patellar flexion and distal fibular translation are now sourced followers. This session's egress policy blocked journal hosts. Add each to `FOLLOWER_COUPLINGS` with its source and a regression test, then extend `isolated_tests.specs`.
4. As those values arrive, extend `isolated_tests.specs` (every new spec needs an absolute direction assertion and a source-binding check). Phase 10 then uses the project's authored exercise definitions, once Gates 6 and 9 allow it.
5. Production assets are untouched. Do not promote any audit file.
