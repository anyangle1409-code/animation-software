# Experimental anatomical muscles — Work checkpoint, 22 October 2026

**PARTIAL FOUNDATION, NOT A MUSCLE-RIGGED BODY. NO PRODUCTION APPROVAL.**
Branch: `work/experimental-anatomical-muscles-20261022`.
Exact output commit: use this handoff's containing commit (`git log -1 --format=%H -- experiments/anatomical_muscles`).

## What exists and what does not

- New isolated Python standard-library authoring package, with no app/runtime imports or dependency changes.
- 120 bilateral seed records; 90 shoulder/axilla/arm/pelvis/thigh pilot records; 22 bilateral research interactions. All 120 bindings unresolved. These counts are semantic records, NOT meshes or anatomically verified coordinates. Serratus and some other entries still need bundle subdivision; do not call this a complete muscle atlas.
- Origin/insertion descriptions, joint crossings, depth, source and confidence preserved from PR123. Neighbor links represent shared research interactions, not measured spatial adjacency or physical contact.
- Explicit bone-local anchors support arbitrary multi-joint paths. Reviewed via points and conservative sphere-envelope clearance checks reject penetrations. No automatic wrap solver, tissue sliding solver, shared-tendon mechanics or bone-surface collision solver yet.
- Equal-volume elliptical-cylinder belly proxy responds to length and independent visual activation. This is a geometry test primitive, not a realistic fusiform/pennate muscle mesh, force model or equilibrium solver. Tendons are fixed-length authoring inputs; real compliant tendons and fibre pennation are not solved.
- Rest-relative normalized skin-delta blending prevents additive double bulges, respects zero region masks and caps displacement. Actual skin masks/cages/deltas are NOT authored, installed or tested on ORIGINAL_v1. Deep/intermediate direct skin weights are blocked.
- Guarded source-copy tool tested on synthetic bytes AND actual hash-pinned R41 bytes. New Blender inventory script syntax-checked only; never executed here.
- NO changed muscle-layer .blend, model renders, native movement validation, mobile export or GLB parity. Copy is byte-identical staging only, not a completed candidate.

## Source reconciliation and protection

Code base: PR123 `b127ff24fed7b2298da6524be0d9da94c5cfc939` (docs and seed), preserving those files verbatim.
Newer model/diagnostic branch inspected and pinned separately:
`codex/r57-local-s7-temporal-study-20261020` at `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
Consolidated branch inspected: `cb4a7ac361c6a8acbe2ca2b9b976e3241352e2a5`.
Latest application branch inspected: `a4f0c100949d25c0975c1aa217ffddfb129a709e` (Body v2 WIP leg-loft revert); this is NOT adopted as an ORIGINAL_v1 source replacement.

Pinned native baseline used by R57:
`ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend`
SHA256: `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`.
Actual Git blob retrieved and hashed here: 5,294,269 bytes; zstd-compressed native file.
Temporary experiment copy: `/tmp/HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT.blend`, same SHA256. Source verified unchanged after copy. Temporary copy is reproducible, unmodified, not committed or claimed transferred to Claude.

R41 alone does NOT contain R52/R57 unsaved increments. Obtain R52 source/solution and any selected later diagnostic explicitly; do not silently promote them. R52 source hash `2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d`; solution hash `b3a6c404a944753facde5a92db8bc4547a1ca756960b6b82df2875f5e4eb804f`. See pinned R57 workflow for artifact run IDs and commands.

Ruling: implementation remains on the PR123-based experimental branch. Later model branches are pinned read-only inputs, avoiding an unrelated branch merge. No original assets, skeletons, production code, version values, weights or existing tests edited. `PT_MODEL_VERSION 1.0` preserved.

## Actual checks

See `test-results.txt` for the final pure test run: **34/34 PASS**. Independent code review found numeric-overflow clearance and empty-registry readiness defects; both reproduced with failing tests and corrected before this checkpoint. Tests cover synthetic geometry only: transforms, segment-interior clearance, authored via routing, equal volume during shortening/lengthening/activation, mask/cap blending, return-to-neutral, binding/source rejection, bilateral completeness, invalid numbers, copy alias/overwrite/hash/LFS protection.
`python -m compileall -q experiments/anatomical_muscles`: PASS (includes native script syntax only).
`npm test -- --reporter=dot`: BLOCKED before execution, `vitest: not found` (exit 127). No existing app suite success claimed.
`command -v blender`: absent. Native Blender version, rig inventory, 3D attachments, anatomy, motion, tissue overlaps, skin deformation, images and mobile parity: **BLOCKED / NOT RUN**.
Historical rig count 67 is reported by PR113, not freshly verified on R41 here. Anatomical side MUST be explicitly mapped: existing F-SIDE-001 indicates anatomical left +X may map to runtime `_r`. Do not infer suffix or mirror local coordinates blindly.

## Design decisions and source checks

Primary sources opened on 22 October 2026:
- Rajagopal et al. 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC5507211/ : lower-limb gait model uses 80 muscle-tendon units and upper-body torque actuators; not shoulder exercise activation ground truth.
- Seth et al. 2019, https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2019.00090/full : shoulder model with independently represented scapular motion; do not impose one fixed scapulohumeral ratio.
Existing seed anatomy references remain coarse sources, not newly certified 3D attachment atlases. No source geometry, images, parameter tables, model files or third-party runtime copied. Reference/model redistribution rights remain unreviewed.
Scientific clarification to PR123: fibre/fascicle contraction type is not necessarily identical to whole muscle-tendon length change when tendon compliance matters. Here outputs are geometric path/belly proxies only; no physiological contraction type or force is inferred.

## Reproduce locally

From experiment branch repository root:

```bash
python -m unittest discover -s experiments/anatomical_muscles/tests -v
python -m experiments.anatomical_muscles.registry --out /tmp/muscles-new.json
```
The output must not already exist. Preserve any locally authored registry; generator never overwrites it.

Extract baseline without checking out or editing another lane:

```bash
git fetch origin codex/r57-local-s7-temporal-study-20261020
git show 025d5f28fa7eba2064fba565b1c9b60119cdd2cb:ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend > /tmp/HGPT_R41_SOURCE.blend
python -m experiments.anatomical_muscles.prepare --source /tmp/HGPT_R41_SOURCE.blend --out /tmp/HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT.blend --sha256 4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e
blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/anatomical_muscles/inspect_blender.py -- /tmp/HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT.blend 4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e /tmp/muscle-native-inventory.json
```
Use fresh output paths; shell redirection of source must also target a fresh scratch name. The native inventory command opens without executing embedded scripts and never saves the model. Run an independently trusted native version matching baseline where possible; R57 specifies Blender 5.2.1, not verified installed here.

## Claude next work — on experimental copy only

1. Execute native inventory; choose actual body and sole runtime driver explicitly. Record real bone IDs, transforms, skin topology, groups, shape keys, modifier order, units, anatomical side mapping and source hash. Preserve separate anatomical guide vs control-rig identities. Recheck live HEADs before any edits.
2. Complete one shoulder side, then verify contralateral mapping independently. Resolve actual anatomical landmarks for three deltoid heads, cuff, trapezius subdivisions, serratus bundles, pec heads, lat, teres major and biceps/triceps long heads. For each binding record `anchors` (`bone`, `local_m`), `source_sha256`, `anatomical_side`, `review` (`reviewer`, `evidence`), `wrap_reviewed`, `direct_skin_weight`, `skin_mask`. Require meaningful evidence; a populated field is not anatomical proof.
3. Author real tendon/belly geometry inside the existing body: broad attachment patches/fan bundles cannot be replaced by one cylinder. Populate actual reviewed `tissue.rest_volume_m3` and two tendon lengths for proxy checks; do not use test fixture values. Create `HGPT_EXPERIMENT_MUSCLES`, `HGPT_EXPERIMENT_TENDONS`, `HGPT_EXPERIMENT_WRAP_GUIDES` collections only in copy. Keep rig rest data fixed.
4. Feed evaluated world bone matrices and authored obstacles into `evaluate.evaluate`; its guards are conservative diagnostics, not contact acceptance. Author dynamic wrapping/sliding and measure path continuity through neutral/45/90/120/150–160° and transition frames. Use known coupled shoulder motion; no new fixed 2:1 rhythm. Evaluate real triangle clearance and tissue intersections separately.
5. Diagnose pelvis/upper-thigh banding by toggling topology/normals/overlapping surfaces/weights/modifiers one at a time before editing. Author gluteals, iliopsoas, TFL and IT tract separately, sartorius ribbon, rectus/vasti and patellar route, hamstrings/adductors. Test hip 0/45/90/110°, abduction, extension and combined knee motion. Preserve genital-neutral outer surface and skeletal anchors.
6. Only after valid rest envelopes, author explicit region masks and rest-relative corrective deltas/cages. `kernel.skin_delta` blends provided deltas; it does not derive a skin response from proximity. Avoid double-counting already sculpted muscle volume. Maintain baseline silhouette at neutral and zero activation. Test activation at fixed pose, eccentric-looking lengthening, mixed-joint paths and neutral return.
7. Save a NEW suffixed experiment, never source or production. Hash both. Compare source rest skeleton, body Basis, weights, topology and non-experimental keys before/after. Show front/side/back/three-quarter, baseline vs candidate, muscle-only/skin-only/overlay, matching cameras, neutral/overhead/hip-flex/squat and transitions. Render from Blender, not generated illustrations.
8. Reuse PR113 nine movement benchmark harness and newest R52/R57 13-benchmark/native checks. Run on source and candidate with identical conditions. Report collapse/stretch, orientation, volume, contacts, temporal pops and isolated mask displacement. Keep failed gates failed. Review full trajectories, not only endpoint screenshots.
9. Publish actual tested hashes, commands, version, output files and PASS/FAIL/BLOCKED matrix. Request independent anatomical/visual review. Defer morph export/runtime contract to engine owner; no GLB replacement, merge, deployment or production promotion.

## Prior failures — do not repeat blindly

- PR107 standalone Preserve Volume: compression improved but stretch 280→566 and excessive bulges; rejected.
- PR113 W4 weights-only shoulder refit: more intersections at 110–145°; rejected.
- PR113 hip-fold corrective: worse everywhere; rejected. Knee band edge, elbow pinch at 120° and over-constrained 140° remain failures even when pair count improves.
- R54 global S5/S7 combinations: no passing pairs. R55 old 26-vertex weight patch misses 1,685 measured high-excess posterior vertices. R56 permission is per angle/control, not global mesh-edit approval.
- R57 is an unsaved local temporal hypothesis, not an accepted model. Preserve original 45 mm cap, native area/contact/orientation checks, unchanged 161-pose motion checks and all 13 newer benchmarks. Native checks not rerun here.

## Phase status

W0 PARTIAL: live branches/PRs reconciled, actual baseline bytes verified; native inventory blocked.
W1 PARTIAL: bilateral semantics and validator implemented; landmark IDs, actual bindings, bundle refinements and layer/contact maps unresolved.
W2/W3 PARTIAL: general authoring kernel and region work instructions; no native shoulder/pelvis muscle geometry.
W4 PARTIAL: tested skin blending primitive; actual body response absent.
W5 BLOCKED: Blender not executed, no new images or anatomy/motion acceptance.
W6 COMPLETE FOR THIS CHECKPOINT: reproducible code/tests/provenance/handoff in experiment branch; final body objective remains incomplete.

## Added reusable exercise-to-muscle contract

Read `EXERCISE_MUSCLE_CONTRACT.md`, `exercise_contracts.json` and the committed curl example before authoring animation behavior. All defined records now have immutable namespaced IDs such as `hgpt.muscle.biceps_brachii_long.L`; their former short IDs are deprecated aliases only. The registry also explicitly carries attachment descriptions, joints, neighbor IDs, contraction semantics and skin-transfer permissions. Actual landmark/rig IDs and masks remain unresolved until native review.

Initial versioned exercise definitions:

- `hgpt.exercise.biceps_curl.bilateral.v1`
- `hgpt.exercise.shoulder_press.bilateral.v1`
- `hgpt.exercise.squat.bodyweight.v1`

Each phase keeps joint targets separate from visual activation estimates and declares muscle role, path-length direction, stabilization, deformation and skin response. The activation range is a qualitative animation prior, never EMG or force. Load/variant-specific rules may scale or replace estimates without moving the skeleton. Run `compile_exercise.py` as documented to generate per-phase instructions. In Blender, verify actual path-length direction against the scene; fail and correct the contract when it disagrees. Do not make object proximity or joint angle silently drive activation.

Current aggregate seed entries are not falsely described as every detailed human muscle. Expand an aggregate into individually sourced permanent head/bundle IDs before detailed modelling when attachments/path/behavior differ. Never create ad-hoc muscle IDs inside one exercise scene.
