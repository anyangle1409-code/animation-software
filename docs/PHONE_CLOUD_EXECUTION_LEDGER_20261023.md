# Home Gym PT — phone-only cloud Blender execution ledger
Date: 2026-10-23

## Source of truth
- Repository: `anyangle1409-code/animation-software`
- Isolated execution branch: `work/phone-blender-workbench-20261023`
- Prior handover: `ad5b6f012427c2bc378534bb566c72ad37d41776`
- Previously VERIFIED initial cloud run: https://github.com/anyangle1409-code/animation-software/actions/runs/40001879043 (W8, V14, R120 completed successfully).
- Current code updates: `c064ecbd45f5b2ff6bdd2450fca2d65e12157232` (read-only bone/weight/rest coordinates) and `d0446b66bd299b3ceb2b6d0a28b67730402e41f3` (report integrity gates).
- Workflow: `.github/workflows/phone-blender-workbench.yml` (script/workflow changes trigger three cloud Blender inspection jobs **and** one report-comparison job).
- Worker script: `scripts/phone_blender/task.py`.
- Workflow runs page: https://github.com/anyangle1409-code/animation-software/actions/workflows/phone-blender-workbench.yml

## Important status distinction
- VERIFIED: The original cloud smoke test retrieved and opened each reconstruction in Blender 5.2.0 and preserved expected source SHA256.
- VERIFIED: Commit `c064ecb` passed cloud run `40003658521` (3/3); `d0446b6` passed run `40010003731` (3/3). All six model job outputs exist; W8/V14/R120 report ZIP digests were independently matched to GitHub.
- VERIFIED: New four-job workflow at `3f25e57` passed run [40015895314](https://github.com/anyangle1409-code/animation-software/actions/runs/40015895314) (three native models plus cross-model comparison). The combined artifact `12529220072` was downloaded, inspected and matched published ZIP SHA256 `3a8b94c53880b2ee94ec6fffaa0f96150c2c077b5501e5b75787b47feb4e6416`.
- NOT APPROVED: anatomy, archive equivalence, movement/grip deformation, and experimental muscle attachments.

## Immutable reconstruction IDs and hashes
- W8: run 39922636070, artifact 12487119841, SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`
- V14: run 39922636070, artifact 12487932177, SHA256 `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91`
- R120: run 39922636070, artifact 12488550235, SHA256 `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb`
These are *reconstructions*, not verified originals. Artifacts expire under GitHub retention; earlier independent second-drive copies were recorded as verified. Check artifact availability afresh.

## Outstanding existing defects
- V14: 238065 vertices vs archived 238067 (two-vertex discrepancy).
- W8 archive content mismatch (offset difference up to 3.59286 mm against 0.01 mm tolerance); unresolved archived JSON discrepancies.
- Previously reproduced shoulder press/squat collapse/stretch/intersection quality-gate failures and grip solver failures in all three reconstructions.
- Recovered authoring rig 77 bones vs old production bridge 67; movement bridge applicability cannot be presumed.
- Anatomical left/right landmark mapping not independently certified. Weight-group centroids or bone names are only evidence for triage.
- Muscle attachment authorization, validated anchors and source acceptance are not satisfied.

## Latest read-only findings (verified)
- All three reconstructions have 77 bones, 77 named groups, 79 shape keys, zero unweighted vertices, and matching recorded rest-bone positions at six-decimal-metre precision.
- Group weight centroids >10 mm apart: W8→V14 4/77; V14→R120 24/77; W8→R120 30/77. See [digest-verified evidence](PHONE_CLOUD_CROSS_MODEL_EVIDENCE_20261023.md).
- Archive V14 right-leg cut loop 699 vs reconstructed 700; left cut loop 696 in both; feet 26877 vertices each and ring counts unchanged. New reconstructed report stages `back_depth_smooth` and `pec_junction` were absent from archive. **Source of final −2 vertices not proven**.

## Next safe steps (ordered)
1. Use documented V14 cut-loop and extra-stage discrepancies to design isolated read-only native intermediate-topology checks. Do not add/delete two vertices without evidence.
2. Prioritize shoulder press and squat failure localization by reviewing existing exact-frame render/geometry snapshots, especially scapula/clavicle/shoulder and hip/shin; grip failed before the right-hand test.
3. Independently verify anatomical coordinate handedness with landmarks before muscle bindings. Preserve muscle IDs and exercise contracts, but do not attach without approved source and anchors.
4. Maintain cloud test and report artifacts with hashes; no production merge/deploy, no source replacement.

## Guardrails
Laptop OFF is supported for GitHub-hosted scripts; the original-session search and interactive desktop-only Blender tasks remain unavailable until laptop return. No production asset, validated skeleton, `ORIGINAL_v1`, `PT_MODEL_VERSION 1.0`, original reconstructive artifact, Claude branch, merge or deployment should be changed. Do not commit binary .blend files.

The assistant/Work does not run indefinitely after chat termination. GitHub Actions does execute independently once triggered; further code commits require an active authorized cloud session.


## 2026-10-23 native failure-localization extension

Read [PHONE_NATIVE_SHOULDER_SQUAT_GRIP_LOCALIZATION_20261023.md](PHONE_NATIVE_SHOULDER_SQUAT_GRIP_LOCALIZATION_20261023.md) for exact read-only reproducible evidence.

- W8/V14/R120 diagnostic ZIPs from run39937882229 (W8=12495910312, V14=12494932817, R120=12495970648) were independently downloaded and SHA256 matched their recorded digests.
- New script scripts/cloud_body_analysis/localize_failures.py reads immutable triangle flags, geometry snapshots, dominant weight labels and finite-grid grip records. Does not import Blender or write a model.
- Seven new synthetic regression tests + five existing cross-model tests = 12/12 PASS in the native-localization cloud job at run40019611125.
- Native localization job PASSED in run40019611125 and again in corrected run40019877883.
- W8 75% shoulder press: 3,509 stretched, 3,072 newly flagged vs baseline; dominant proxy regions spine_03, shoulder_cap_r/l, scapula. Press flags recorded in all models; no anatomical approval.
- W8 squat sample7: 885 stretched, concentrated hip_crease_r/l, spine_01, pelvis. Pair collisions remain present and are not equivalent to distinct triangles.
- Grip: 263 attempts on runtime suffix l per model; combined acceptance unresolved, suffix r untested.
- Uploaded native ZIP: run40019877883 artifact12530565814, downloaded and SHA256 verified = 595a971897bedce022ca88f57f0cae1d59f2e526d7617484f382f58c5bf660ef. Contains movement_failure_localization.json and .md.
- Initial expanded five-job run40019611125 overall FAILED because older rest-compare job discovered numpy tests without numpy installed. Fixed in commit 78173b749d0e7ff669043847b2fd3d5567fb1517 by restricting rest job to its standard-library tests. **FINAL:** Corrected [run40019877883](https://github.com/anyangle1409-code/animation-software/actions/runs/40019877883) is **SUCCESS / all five jobs passed** (W8, V14, R120, cross-model compare, native localization). The native report artifact 12530565814 SHA256 is `595a971897bedce022ca88f57f0cae1d59f2e526d7617484f382f58c5bf660ef`; cross-model artifact 12530466695 was independently downloaded and its SHA256 verified as `dc69ccf09cc8806bdfea955cc0d418a8a030fa3dc84c7e6235769c2681d489bd`. Run is an infrastructure and read-only diagnostics pass only. Anatomy, archive equivalence, grip, movement safety and muscle attachment remain NOT_GRANTED / FAILED / BLOCKED.
- User may use a separate Claude cloud branch for *read-only V14 topology provenance investigation*. Keep Claude's lane separate. Do not overwrite original reconstruction artifacts or alter source acceptance gates.

Next: verify final five-job workflow; review 5 cm evaluated-coordinate shoulder hotspots at press sample6/8, build a reversible hypothesis checklist for clavicle/scapula/axilla skin deformation; do not edit preserved models, unfreeze anatomy, attach muscles, merge or deploy without explicit authorization. PT_MODEL_VERSION1.0 untouched.


## 2026-10-23 tracked rest-space movement failures — VERIFIED

New read-only native evidence: [shoulder/axilla triage](PHONE_SHOULDER_AXILLA_TRIAGE_20261023.md).

- Code `scripts/cloud_body_analysis/track_rest_hotspots.py` and 8 new synthetic tests `scripts/cloud_body_analysis/tests/test_track_rest_hotspots.py` landed on the isolated cloud branch. The cloud-localization job now outputs `tracked_rest_hotspots.json` and `tracked_rest_hotspots.md` alongside its existing evidence.
- [Cloud run 40021689794](https://github.com/anyangle1409-code/animation-software/actions/runs/40021689794): **SUCCESS, all five jobs**. Native report tests: **20/20 PASS**; W8/V14/R120 Blender inspection and comparison jobs also passed.
- [Native artifact 12531201008](https://github.com/anyangle1409-code/animation-software/actions/runs/40021689794/artifacts/12531201008) independently downloaded. ZIP SHA256 = GitHub digest = `8535f61575f13665bf1a472c33d26e6ca0808d55ad3f2bfdb29a1ce362a17097`. Inspection confirmed both old and new JSON/Markdown reports.
- At sample6, newly stretched (vs sample0), of which still stretched at sample8: W8 3072/491, V14 3550/699, R120 7337/3025. At squat sample7, newly stretched (vs sample0), of which still stretched at sample8: W8 885/862, V14 1238/1210, R120 3363/3345. These are **within-model exact triangle IDs**, not across-model quality ranking.
- W8 newly stretched press rest-space 5cm hotspot centres include (+0.125,+0.175,1.475) metres (363 triangle records) and (-0.125,+0.175,1.475) (325); weight-group proxy leaders spine_03 and shoulder caps/scapulae. These are not anatomical attachments or approved correction coordinates.
- A controlled hypothesis/testing protocol has been committed; no skeleton, model mesh, shape key, muscle attachment, production application or source artifact altered. The V14 two-vertex archival mismatch and all movement acceptance failures remain unresolved.

**Next safe work:** assess baseline/pose shape-key influence and local shoulder-region weight distribution without saving any model; review original evidence for bone-side orientation. Only after explicit scope may independent experimental candidate edits be attempted. Do not merge or deploy.


## 2026-10-23 static shoulder shape-key and skin-weight inventory — CLOUD VALIDATION PENDING

Following the verified rest-space triangle tracking, an additional **read-only** native Blender inspection was committed to the same isolated branch:
- `scripts/phone_blender/rest_roi_audit.py`: inspect six 5cm body-local rest-coordinate cubes around W8 shoulder and clavicle/neck hotspot centres, reporting per-cell influenced vertex counts, total skin weight, top vertex-group mean weights, dominant groups, and stored shape-key absolute differences from Basis.
- `scripts/cloud_body_analysis/tests/test_rest_roi_audit.py`: six pure-Python tests were executed locally and passed (sampling, shape-key delta, absent keys, malformed topology, negative weights, nonfinite vertices, empty regions).
- `scripts/phone_blender/task.py`: outputs a `shoulder_shape_weight_rois.json` inventory per model, with exact source SHA256 guard before/after; does not save/modify any `.blend`.
- Final script commit: `c1985b4a465278d3ce0f3275d490feb736f6de8d`. The new code's [Actions run 40022355554](https://github.com/anyangle1409-code/animation-software/actions/runs/40022355554) was **pending** at the time of this handover update. Do not label the native ROI report verified until its jobs pass and its artifacts have been inspected.

**Important limitations:** A static shape key's stored Basis offset does not establish that the key fires in the shoulder-press pose or causes deformation. Cube centres originated from prior saved native rest-triangle snapshots and must be checked for exact coordinate-frame correspondence with the as-loaded body mesh. No anatomical left/right side accepted by label alone; no muscle attachments or experimental geometry edits authorized. Do not merge or deploy.


## 2026-10-23 phone visual review system — VERIFIED

The owner's iPhone-based visual review requirement now has a tested source-preserving GitHub Actions artifact, without a laptop.

- Implementation: `scripts/cloud_body_analysis/render_phone_review.py` and `scripts/cloud_body_analysis/tests/test_render_phone_review.py`. Workflow: `.github/workflows/phone-blender-workbench.yml` adds Pillow to the pinned native diagnostics job and uploads a separately labelled `phone-visual-review-<runid>` artifact.
- **VERIFIED FINAL:** [run 40025141134](https://github.com/anyangle1409-code/animation-software/actions/runs/40025141134) completed SUCCESS for all five workflow jobs, including three native Blender inspection jobs and failure-localization/visual review and rest comparison. The native job ran **46/46 passing tests**, including 7 image-source and image-manifest guards.
- [Phone review artifact 12532462150](https://github.com/anyangle1409-code/animation-software/actions/runs/40025141134/artifacts/12532462150) downloaded and ZIP SHA256 independently compared with GitHub: `82f66414c46e6a1c4995371d243d1c5bb021e3424905e69e3a9cac1b0c98fd0d` (MATCH). Its `phone_review_manifest.json` verifies SHA256 of all three generated JPEG images and marks per-model source PNGs individually verified.
- **18 source PNG member hashes** were independently pinned against immutable original run39937882229 W8/V14/R120 Blender diagnostic ZIPs, then rechecked inside Actions even though Actions gives extracted directories.
- Three phone JPEGs: `phone_review_shoulder_press_back_full_body.jpg`, `phone_review_shoulder_press_back_upper_torso.jpg` and `phone_review_squat_side_full_body.jpg`. Each contains nine labelled actual model/pose diagnostic panels.
- Initial successful visual artifact: run40024580927 artifact12531993002, digest `c4db0bdb3b5e0d3d916fee57a52c1c272cc8bcd8adda9d38e9acee075ea58a16`, independently verified. The final run's source-PNG-hash hardening supersedes this older version.
- An intermediate hardening run40025085577 was **FAIL** because synthetic fixture images did not match newly pinned original hashes. Tests were corrected by explicitly supplying fixture-specific hashes while production image hashes stayed fixed; the final run 40025141134 is fully SUCCESS. This failure was an audit-test fixture mismatch, not source-model failure.
- [Full picture-review protocol and artifact provenance](PHONE_VISUAL_REVIEW_PROTOCOL_20261023.md). This is baseline read-only evidence, **NOT** an improvement to the shoulder mesh; no new candidate was saved or approved.

**Next safe technical priority:** instrument actual in-memory shoulder-press S7/S5 shape-key activation and cap helper rotations at benchmark samples 0/6/8; compare against observed rear-shoulder flagged triangle geometry, with exact source input guards and no saving. Existing S7 95° start override, cap fraction 0.45 and missing axilla helper are hypotheses, not approved fixes. Do not change original models, weights, production rig, PT_MODEL_VERSION, Claude branches, or acceptance thresholds without new authorized isolated candidate work.


## Human ROM and general movement reference — 2026-10-23

**Owner rule:** human-looking, naturally moving generic body FIRST, then reuse the same rig/deformation foundation for many future exercise templates; preserve correct muscle interactions and overlap. This is a design requirement, not a current anatomy certification.

Research and new versioned machine-readable files committed on isolated cloud branch:
- [Full study/source interpretation, clinical vs skeletal angles, motion gates](HGPT_HUMAN_JOINT_ROM_AND_MOVEMENT_PLAN_20261023.md).
- [Human joint ROM reference V1](anatomy/HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json): 43 named joint coordinates spanning entire body, **44 CDC adult grouped clinical means + CIs**, 12 separately labelled AAOS illustrative clinical-goniometry norms, 12 cervical/lumbar young-adult mean+SD values, seven referenced sources, 19 conceptual isolated/compound movement test scenarios.
- [Exercise movement contract crosswalk](anatomy/HGPT_EXERCISE_ROM_CROSSWALK_V1.json): **16 unique PR124 bilateral exercise coordinate pairs**, 12 semantic coordinate matches and **four unresolved bilateral shoulder coordinate mappings** due ambiguous `elevation` versus `humerothoracic_elevation` and unknown plane/axis. Referenced PR124 `7c820d68de69dcdef7d567e836302123df953446` directly, not merged.
- `scripts/cloud_body_analysis/human_rom_reference.py` and `tests/test_human_rom_reference.py`: pure Python study-source validation, descriptive adult population comparisons **without pose approval or angle clamping**, missing-coordinate/side review guards and test-matrix completeness checks.
- Source examples: CDC adult 20–44 shoulder flexion mean 172.0° (female), 168.8° (male); knee flexion 141.9°/137.7°; ankle dorsiflexion 13.8°/12.7°. **These are study population means, never human maximums or safe exercise endpoints.** Secondary source goniometric values and spinal group means are kept separate and similarly NOT hard stops.
- ISB JCS papers (2002/2005) specify anatomical motion coordinate/reporting standards, not numerical safety limits. 2025 shoulder review rejects universal fixed scapula ratio; forearm and foot multisegment couplings are separately documented.
- All 43 actual Blender joint axes, 19 motion test pose recipes and measured trajectories, source binding, clinical hard limits, and native anatomical approvals remain **NULL / NOT_GRANTED / NOT_MEASURED**.
- Owner has deferred muscle highlighting: preserve stable semantic muscle IDs but no display UI or guessed colours/activation implementation.

VERIFIED STUDY DATA/CROSSWALK REGRESSION: [cloud run 40029040068](https://github.com/anyangle1409-code/animation-software/actions/runs/40029040068) completed SUCCESS across all five existing jobs; the expanded descriptive human-ROM data, secondary AAOS/spine source handling, and exact PR124 exercise-coordinate crosswalk unit tests ran with the read-only cloud suite. This verifies *research data/schema and unchanged old scripts*, not anatomical motion. Native anatomical ranges, axes and acceptance remain NOT_GRANTED. Do not conflate green CI with an anatomically correct human model.

**Next safe action:** establish each actual bone/joint axis on existing W8/V14/R120 rigs with a *read-only* numeric native inventory and independent 3D landmark review, then implement controlled pose-only movement tests with documented frame transforms and return-to-neutral. Continue shoulder and elbow/forearm/joint shape diagnostics, while preserving the original files, 77-bone authoring rig data, production bridge and PT_MODEL_VERSION 1.0. No exercise animation or muscle attachment may be promoted from averages/contract labels alone.

## 2026-10-23 native Blender rig local axes inventory — NATIVE ARTIFACTS VERIFIED

Added `scripts/phone_blender/rig_axes_inventory.py`, `scripts/cloud_body_analysis/tests/test_rig_axes_inventory.py`, and `task.py` integration. This opens the same hash-pinned W8/V14/R120 reconstruction copies and **reads only** bone rest matrix local unit axes (body-local), head/tail coords, rotation modes, constraint/armature modifier metadata and parent hierarchy. Outputs `rig_rest_axes_metadata.json` per model with `actual_anatomical_joint_centres_verified: false`, `model_motion_axes_calibrated_to_ISB: false`, `native_human_ROM_limits_validated: false`, and all other anatomy/side approvals false. It does not pose, edit, or save bones/skin/rig. `Bone.roll` Edit Mode-only access was deliberately avoided to preserve non-mutating inspection. Native three-model job [40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965) has been triggered from `e5cd2c569261c229f82e3819603f5cc378abf15f`; status and output NOT VERIFIED at time of this ledger note. Next session must inspect run/job results and the three JSON artifacts before claiming measured rest axes. Independent anatomical calibration against ISB remains blocked even if job passes.

**Future muscle highlighting:** Owner deferred design; only immutable IDs remain prepared. Avoid implementing display/visualization before requested.


## 2026-10-23 verified native axis + ISB anatomical gap update (supersedes prior pending note)

**FIRST NATIVE RUN:** [40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965) was **overall FAILURE**, despite W8/V14/R120 Blender inspection and old comparison jobs each passing. One of 73 pure Python tests falsely matched the harmless docstring `No bpy.ops` as a forbidden mutation call; **72 pass, 1 false positive**. The test was changed to AST call inspection, without modifying any Blender source. [Corrected run 40030373550](https://github.com/anyangle1409-code/animation-software/actions/runs/40030373550) completed **SUCCESS across five jobs**.

**Independent original artifact verification:** W8 [12534047239](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534047239) ZIP SHA256 `adaba1780dcde12b589f590bc6de7ae2227485471f9ff0817a56dff888188267`; V14 [12534147742](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534147742) `098c34ab14d8e14dbf21735b11808067df4296247dcc7efb7e9420b7b43545a9`; R120 [12534222622](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965/artifacts/12534222622) `17266fbc256cc775ce21c16b556d6a0fbff36499a1f2f78d05a6c058d6e56018`. All three downloaded ZIP SHA256 values match GitHub digests, and each `rig_rest_axes_metadata.json` has 77 bones, source hash guard PASS and all anatomical approvals FALSE. All three have **58 quaternion + 19 XYZ pose bone rotation modes**, no saved pose constraints and one active armature modifier.

**REPRODUCIBLE COMPARATOR:** New `scripts/cloud_body_analysis/compare_rig_axes.py`, synthetic tests, and workflow aggregation verified in [run 40030774310](https://github.com/anyangle1409-code/animation-software/actions/runs/40030774310): **all five jobs SUCCESS**. Downloaded [artifact 12535425648](https://github.com/anyangle1409-code/animation-software/actions/runs/40030774310/artifacts/12535425648) ZIP SHA256 matched GitHub `d3fca1d8303ed65d14402f471e23ae44ef609229c43646d1f8125212eaf931a9`. The report confirms **all 77 rest-bone names, parents, body-local heads/tails, bone-local axes, rotation modes, constraints and armature modifiers are identical in W8/V14/R120 at recorded precision**, fingerprint `b2743dd66a1595aecbd961acc7de3efcec4d57f257577758567591dc649aef1f` each. This rules out a **rest rig metadata difference between the three reconstruction candidates** as the explanation for their different observed shoulder/hip mesh defects; it does NOT prove their movement, weights, shape keys or actual anatomical axes match. There are 35 L/R suffix pairs; X-mirror maximum head residual **2.433 mm** occurs at `muscle_pec_l` vs `muscle_pec_r` authored helper heads, flagged for review, not assumed to be incorrect physical muscle insertions.

**HUMAN JOINT COORDINATE GAP:** Added [46 unbound ISB-inspired anatomical landmarks](anatomy/HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json), a strict source/side/binding validator and tests. Landmarks cover thorax, scapula, clavicle, humerus, forearm, pelvis, hip, knee, ankle and foot, with lower-body/foot proposals explicitly not claimed exact ISB definitions. No model mesh vertices, bones, sides or muscle attachments are bound. [Detailed source and evidence interpretation](HGPT_ISB_NATIVE_RIG_LANDMARK_GAP_20261023.md).

**GENERIC MOTION COVERAGE:** Added [19-scenario execution ledger](anatomy/HGPT_HUMAN_MOTION_TEST_EXECUTION_LEDGER_V1.json): **0/19 isolated generic joint tests executed or approved**; three prior related *failed* shoulder press, squat and grip benchmarks linked to pinned native run39937882229. The source files and tests are committed, and [workflow run 40031004957](https://github.com/anyangle1409-code/animation-software/actions/runs/40031004957) is now **VERIFIED SUCCESS across all five jobs**, including **97/97 passing report-only regression tests** in the native-failure localization job. This validates source/ledger consistency, NOT a single new generic motion or anatomical approval.

**Extra foot control clue:** W8 `foot_l` + `toe_l` rest controls extend roughly **307.7 mm along local forward Y** from foot control head to toe control tail; toe-control segment is about **172.4 mm**. These are **authored bone control spans, NOT anatomical toe or foot mesh lengths**. The values warrant independent mesh/heel/metatarsal/toe inspection given the owner's known excessive-foot concern, not automatic shortening.

**Next safe focus:** actual native ISB landmark/side calibration, in-memory shoulder/scapula/clavicle and elbow/forearm pose-state evidence, joint-chain contact and skin deformation, with original model source SHA checks. No original `.blend` changed, no muscle attached, no clinical hard limits imposed, no production/Claude/PT-App edits or merge/deploy. Muscle highlighting remains deferred.


## Native W8 shoulder pose-state probe — execution pending

At current task milestone, the new isolated first actual movement-state probe is committed:
- `scripts/phone_blender/pose_state_probe.py`: SHA256-pin source W8 `.blend`, pin prior benchmark implementation to r57 commit `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`, use the old `pose_press` / `drives.drive` in Blender **IN MEMORY** through all 9 preserved press samples, and capture **actual measured** driver humerothoracic elevations, individual S1/S2/S3/S4/S5/S6/S7 and C1 shape-key values, shoulder-cap/axilla helper presence and quaternion delta, plus existing native deformation metrics. No blend is written; source/rest bone signatures checked.
- `scripts/cloud_body_analysis/tests/test_pose_state_probe.py`: fail closed on bad source hashes, incomplete samples, nonfinite shape activations, false anatomy approval, and non-human body/sides. Pure-Python tests do NOT substitute for native Blender execution.
- New GitHub Actions `pose-state-w8` job uses pinned source artifact `12487119841` and two independent Git checkouts (current isolated branch + frozen r57 source). It uploads `phone-w8-shoulder-pose-state-<runid>` JSON **only when generated**. Existing 5 proven jobs remain present and independent.
- [First workflow run 40034242376](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376) was QUEUED when inspected. **Do not call native shape-key/cap movement verified until the pose-state-w8 job finishes and its JSON artifact is read.** Intermediate older push runs may be cancelled by concurrency; only verified job conclusions count.

Next: inspect job logs and patch isolated script only if failure; verify all nine frames and native metric continuity, distinguish dynamic measured elevation from authored 90°→160° target, then investigate whether shoulder-cap fraction 0.45 and missing axilla helper actually contribute to posterior crease at sample6/8. No muscle anchors or production changes. High-value later sequel: elbow cross-section silhouette test at neutral/partial/high flexion with radioulnar rotation and restored skin-neutral control.

The overnight hourly cloud continuation automation is configured separately; each run should read current GitHub state and resume safely without duplicating work, reporting verified outcomes only. It is not an always-on persistent session and does not override source-preservation rules.


## W8 measured 9-frame press, native driver validation and elbow taper — late 23 Oct

**Native actual pose evidence VERIFIED:** [six-job run 40034242376](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376) SUCCESS, including W8 dedicated source-preserving nine-frame `pose-state-w8` alongside previous five jobs. W8 [pose artifact 12535648742](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376/artifacts/12535648742) independently downloaded and ZIP SHA256 verified `7f919b5f5562c655a336cc437ab33cf19be4636d47e534d90061721090a06e58`. Source W8 blend SHA256 remained exact. Full numeric evidence: [actual W8 shoulder data](HGPT_W8_MEASURED_SHOULDER_POSE_STATE_20261023.md).

- Actual r57 driver-measured humerothoracic elevation vs authored target: sample0 `87.680° vs 90°`, sample6 `145.726° vs 149.063°`, sample8 `156.103° vs 160°`, L/R almost identical. This is project-authored driver vector measurement, NOT independently calibrated ISB GH elevation. The 2.3–3.9° offset is **not a diagnosed anatomical fault**.
- W8 S7 actual sample6 key values `_145=0.934006`, `_156=0.065994`; sample8 `_156=0.989697`, `_166=0.010303`. Prior static S7 target-based 160° predicted `0.6/0.4`, not actual. Actual cap helper local delta measured ~33.10° at start and ~49.43° at top; axilla helper absent. Saved `hgpt_cap_fraction=0.45`, no ramp.
- Native failing metric reproduced at press sample6: **3509 stretch / 110 collapse / 146 nonadjacent intersection pairs**; final sample8 **1594 /173/441**. This is unchanged known **FAIL** behaviour, not repair.
- Independent static-driver metadata [W8 report ZIP 12535503988](https://github.com/anyangle1409-code/animation-software/actions/runs/40034242376/artifacts/12535503988), ZIP digest `41a5f00bed46842a7b4857d35893a653695ca23d24d237234dedaadaae63a822`. The real model has **FOUR populated S1-S7 families**: S1, S3, S5 and S7; nominal S2/S4/S6 families have zero keys and no installed angles. Across **378 installed shape-key samples** (9 frames × 2 sides × 21 populated keys), independent mathematical hats using **ACTUAL** measured elevation match to max approximately `0.000001`. C1 uses separate shoulder-extension measurement and is not included.
- A new seventh job `verify-actual-shoulder-driver-math` was added. Initial [run 40034863130](https://github.com/anyangle1409-code/animation-software/actions/runs/40034863130) overall FAILED in the new validator only (the six other jobs passed), because its first implementation mistakenly demanded all seven nominal families be populated; it was not a Blender or anatomy regression. Corrected comparator `scripts/cloud_body_analysis/verify_pose_driver_contract.py` at `f18b70e8` and matching tests `test_verify_pose_driver_contract.py` at `f353309f`. [Corrected run 40035351859](https://github.com/anyangle1409-code/animation-software/actions/runs/40035351859) was **PENDING** at time of this entry. **Do not claim the seventh check is CI-verified until it finishes SUCCESS and artifact is inspected.**
- **Elbow problem narrowed numerically:** separate SHA-verified W8 saved source visual artifact `12495910312` has rest-slice distal upper-arm covariance transverse spread-product only **0.407–0.408** of the mid-upper-arm band for suffix l/r. During bent-to-overhead sampled press this ratio remains **0.405–0.428**. This is a deliberately labelled geometric **proxy, not circumference/area or a human normal range**; the narrow distal contour is already present in the rest surface, not newly introduced by the overhead press in this one metric. This supports the owner's concern and refocuses investigation on base shape/anatomical layering AND movement, without presupposing how much taper is normal. Full method: [elbow taper evidence](HGPT_W8_ELBOW_SURFACE_TAPER_READONLY_EVIDENCE_20261023.md).
- A phone-friendly cropped comparison of the three original W8 press front-view images was created for this chat, source-preserving aside from matched crops/labels. It is baseline visual evidence, not a fixed model. Keep derived image source hashes separate from the original artifact.

**Next safe night tasks (ordered):**
1. Check run40035351859 and exact test logs. If any residual comparator error, fix isolated tests/script without relaxing anatomical status; verify the seventh artifact ZIP and report.
2. Add reproducible **source-pinned elbow taper PCA audit** on existing NPZ geometry with explicit covariance/spread-proxy limitations, stable rest vertex bands and per-side comparisons; no false circumference claim.
3. Investigate why target HT differs from project-measured HT and how helper cap+S7 regional *signed displacement vectors* affect shoulder/axilla skin. Use controlled, in-memory only candidate comparison with source hash guards and never apply unapproved repairs or change acceptance criteria.
4. Establish true elbow shaft/joint axes, semantic L/R, skin continuity under flexion and forearm pronation; generic 19 motion suite remains 0/19 approved. Stage 46 ISB-inspired unbound landmarks for human review.
5. Eventually show matched annotated before/after images when an owner-authorized correction is successfully validated. Do not invent new pictures of a fixed model.

**Keep all production and original Blender inputs unchanged**. Muscle highlighting future appearance is owner-DEFERRED. The overnight hourly automation should resume from latest live branch and this ledger.
