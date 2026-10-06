# Shoulder/Axilla Foundation Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace r95's compensating shoulder/axilla corrective stack with an evidence-backed anatomical support foundation and fail-closed visual validation.

**Architecture:** Preserve r95 as an immutable comparator. Add evidence and issue-ledger controls first, then instrument the existing deformation layers through the elevation arc. Declare and audit one local shoulder-yoke topology/weight repair before creating a new candidate; refit generic correctives only after the weights-only surface is visually plausible.

**Tech Stack:** Python 3, Blender 5.2 Python API, NumPy, JSON evidence/control records, `unittest`, Git/GitHub.

**Spec:** `docs/superpowers/specs/2026-10-04-whole-body-human-deformation-recovery-design.md`

## Global Constraints

- Preserve r95 unchanged with SHA-256 `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`.
- Preserve P3B1 and all numerical thresholds unchanged.
- Preserve the first-party clean-room boundary; external evidence is development-only.
- Do not modify the 67-bone rig in this package.
- Do not use exercise-name-driven correctives.
- Commit the declared repair scope before any model edit.
- Numerical pass plus visual anatomical pass plus regression pass are all required.
- Use the exact production deformation path for validation renders.

## Review Focus

- Missing or unreachable real-human evidence must fail validation, not silently become optional.
- A historical freeze with a later Critical/High visual rejection must not remain selectable as current quality approval.
- A diagnostic run with a missing corrective configuration must identify the omitted layer explicitly.
- A topology or weight edit outside the declared shoulder-yoke scope must fail the change audit.
- A locally improved overhead pose must be rejected if another primitive or transition gains a Critical/High defect.

---

### Task 1: Record the owner visual rejection in production control

**Files:**
- Modify: `ORIGINAL_V1_PRODUCTION_CONTROL.json`
- Modify: `scripts/original_v1_production_control.py`
- Modify: `scripts/test_original_v1_production_control.py`
- Modify: `ORIGINAL_V1_CANDIDATE_STATUS.json`

**Interfaces:**
- Consumes: immutable r95 Phase 4 record and the recovery spec.
- Produces: `visual_rejections[]` records and a fail-closed next action of `REOPEN shoulder/axilla foundation`.

- [ ] **Step 1: Write failing tests for a candidate-bound visual rejection**

Add tests asserting that an open Critical/High `visual_rejections` record bound to the active candidate SHA prevents Phase 5 selection and returns the recovery action, while a rejection for a different candidate SHA does not mutate historical records.

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `C:/Users/Mark/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -m unittest scripts.test_original_v1_production_control -v`

Expected: FAIL because production control has no visual-rejection state.

- [ ] **Step 3: Implement fail-closed visual-rejection handling**

Add parsing/validation for `visual_rejections` with exact candidate revision, candidate SHA, severity, issue IDs, evidence paths, decision date and status. Preserve the historical Phase 4 packet unchanged.

- [ ] **Step 4: Record the r95 rejection and regenerate status**

Record WB-AX-001, WB-PEC-002, WB-PEC-003 and WB-QA-011 as open blockers. Regenerate status through the existing production-control path.

- [ ] **Step 5: Run focused and production-control safety tests**

Expected: PASS; Phase 5 is no longer selected while the r95 rejection is open.

- [ ] **Step 6: Commit and push**

Commit message: `Reopen r95 after owner anatomical visual rejection`

### Task 2: Add the real-human evidence manifest

**Files:**
- Create: `ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json`
- Create: `scripts/validate_original_v1_human_evidence.py`
- Create: `scripts/test_original_v1_human_evidence.py`
- Modify: `DOCUMENTATION_MANIFEST.json`

**Interfaces:**
- Consumes: source URLs/capture IDs, movement primitive, view, subject-diversity and permissible-conclusion fields.
- Produces: `validate_manifest(path: Path) -> list[str]` and a non-zero CLI exit on any missing required evidence.

- [ ] **Step 1: Write failing manifest validation tests**

Cover valid primary-study/photo/video entries; missing URL/capture ID; missing licence/use note; missing movement phase; empty diversity notes; unsupported conclusion; and a movement primitive with no visual source.

- [ ] **Step 2: Run tests and confirm failure**

Expected: FAIL because the validator does not exist.

- [ ] **Step 3: Implement the validator and schema-bearing manifest**

Require `id`, `region`, `movement_primitive`, `source_type`, `source`, `movement_phase`, `view`, `diversity`, `observable_landmarks`, `permissible_conclusions`, `uncertainty`, `development_only` and `review_status`.

- [ ] **Step 4: Populate the initial shoulder evidence set**

Include the direct-bone shoulder-complex study, unconstrained overhead-reaching study, axillary anatomy source and multiple real-human visual sources spanning flexion, abduction and rotation. Do not encode a fixed universal scapulohumeral ratio.

- [ ] **Step 5: Validate and commit**

Commit message: `Add real-human evidence gate for deformation work`

### Task 3: Add the master anatomical issue ledger

**Files:**
- Create: `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`
- Create: `scripts/original_v1_whole_body_issues.py`
- Create: `scripts/test_original_v1_whole_body_issues.py`
- Modify: `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`

**Interfaces:**
- Consumes: stable issue records and committed evidence paths.
- Produces: `blocking_issues(ledger: dict) -> list[dict]` and a CLI summary/exit status.

- [ ] **Step 1: Write failing ledger tests**

Assert stable unique IDs, permitted severities/states, required reproduction/evidence/candidate fields, and failure while any Critical/High issue is Open, In Progress or Pending Review.

- [ ] **Step 2: Run tests and confirm failure**

- [ ] **Step 3: Implement the ledger validator and blocker selector**

- [ ] **Step 4: Enter WB-AX-001 through WB-QA-011**

Use the recovery record as the source of truth. Do not mark any issue fixed from numerical evidence alone.

- [ ] **Step 5: Bind orchestration to the ledger and commit**

Commit message: `Add fail-closed whole-body anatomical issue ledger`

### Task 4: Add deterministic deformation-layer diagnostics

**Files:**
- Create: `scripts/original_v1_deformation_layers.py`
- Create: `scripts/diagnose_original_v1_deformation_layers_blender.py`
- Create: `scripts/test_original_v1_deformation_layers.py`
- Create: `RUN_ORIGINAL_V1_DEFORMATION_LAYERS.bat`

**Interfaces:**
- Produces: `activation_snapshot(scene, body, rig) -> dict`, `summarize_zone_displacement(states: dict, zones: dict) -> dict`, and a JSON report containing skeleton, weights-only, each corrective, combined, per-zone displacements and arc continuity.

- [ ] **Step 1: Write failing pure-Python tests for activation/displacement summaries**

Test missing configuration, zero activation, one active layer, combined layers, left/right symmetry and non-monotone arc detection.

- [ ] **Step 2: Run tests and confirm failure**

- [ ] **Step 3: Implement pure diagnostic functions**

Keep Blender-independent calculations in `original_v1_deformation_layers.py`.

- [ ] **Step 4: Implement the read-only Blender capture**

Sample shoulder elevation at 0°, 30°, 60°, 90°, 120°, 150° and maximum for flexion and abduction with rotation variants. Save no Blend and make no persistent scene changes.

- [ ] **Step 5: Run against exact r95 and hash-bind the report**

Expected: reproduce the weights-only wing and quantify which layer trades it for the scoop/trench.

- [ ] **Step 6: Commit and push**

Commit message: `Instrument shoulder deformation layers through elevation arc`

### Task 5: Declare the anatomical shoulder-yoke repair scope

**Files:**
- Create: `scripts/declare_original_v1_shoulder_yoke_repair_blender.py`
- Create: `scripts/test_original_v1_shoulder_yoke_declaration.py`
- Create: `ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/shoulder_yoke_declared_before_edit.json`
- Create: `ORIGINAL_V1_WORK/candidates/repair_preparation/r96_shoulder_yoke_declared/DECLARATION.md`

**Interfaces:**
- Consumes: exact r95 candidate, layer diagnostic and anatomical issue IDs.
- Produces: mirror-closed vertex/face zone, permitted existing bones, proposed support topology, invariants and stop conditions.

- [ ] **Step 1: Read the existing support-loop and declaration implementations completely**

Read `scripts/add_original_v1_o4_shoulder_support_loop_blender.py` and the r22-r24/r80-r95 declaration records before designing the new zone.

- [ ] **Step 2: Write failing declaration validation tests**

Require exact parent hash, mirror closure, issue/evidence links, permitted bones, topology intent, maximum scope, protected-zone exclusions and stop conditions.

- [ ] **Step 3: Implement read-only declaration capture**

- [ ] **Step 4: Generate, inspect, commit and push the declaration before any model edit**

Commit message: `Declare r96 anatomical shoulder-yoke repair scope`

### Task 6: Build the weights-first r96 candidate

**Files:**
- Create: `scripts/author_original_v1_shoulder_yoke_blender.py`
- Modify: `scripts/optimize_original_v1_o4_shoulder_weights.py`
- Test: relevant optimiser/declaration tests plus Blender audit tools.
- Create locally: `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r96.blend`
- Create: `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r96.json`

**Interfaces:**
- Consumes: r95 plus the committed r96 declaration.
- Produces: r96 with declared topology/weights only; r95 corrective keys retained but disabled for the weights-only gate.

- [ ] **Step 1: Write failing audit tests for out-of-scope topology/weights**

- [ ] **Step 2: Implement the declared support topology**

Represent continuous anterior and posterior folds and provide rest length across the axillary vault without copying third-party coordinates.

- [ ] **Step 3: Solve only declared local weights using existing permitted bones**

- [ ] **Step 4: Run the weights-only movement matrix**

Stop unless the large wing, pointed flap and knife-edge membrane are absent before correctives.

- [ ] **Step 5: Audit exact changes and commit evidence**

Commit message: `Build r96 weights-first anatomical shoulder foundation`

### Task 6A: Apply owner-confirmed overhead rejection gate

**Status:** mandatory before any r96 promotion.

- [ ] Treat existing r96 support-rest-length and weights-only screening renders as diagnostic evidence, not acceptance evidence.
- [ ] Add explicit fail-closed checks for deltoid volume collapse/elongation, axillary trench or membrane, pec drag, scapular deformation grooves and loss of the continuous neck-to-shoulder-to-arm silhouette.
- [ ] Require matched elevation poses with humeral internal/neutral/external rotation to produce anatomically meaningful surface differences.
- [ ] Require the weights-only foundation to pass the overhead visual gate before fitting any residual corrective.
- [ ] If the foundation cannot pass without a large corrective, stop r96 iteration and revise topology/weight transfer rather than stacking another patch.
- [ ] Preserve all rejected renders and measurements with candidate/hash identity so later candidates can prove improvement.

### Task 7: Fit minimal generic correctives and validate r96

**Files:**
- Modify: `scripts/optimize_original_v1_shoulder_corrective.py`
- Create: r96 corrective declaration/solution/runtime records under `ORIGINAL_V1_WORK/candidates/repair_preparation/`.
- Create: full r96 evidence under `ORIGINAL_V1_WORK/candidates/repair_checks/` and `review/`.
- Modify: `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`

**Interfaces:**
- Consumes: weights-first r96 and the real-human evidence manifest.
- Produces: minimal motion-driven residual correctives and complete r96 review evidence.

- [ ] **Step 1: Add failing tests for activation continuity and zone protection**

- [ ] **Step 2: Declare corrective masks/drivers before solving**

- [ ] **Step 3: Fit one residual behaviour at a time**

Do not combine causes in one solve. Stop after three failed trials and revisit the foundation.

- [ ] **Step 4: Run full evidence and comparisons**

Run every existing 15-pose gate plus the expanded shoulder primitive matrix, layer diagnostics, visual board, arc, symmetry, contact, collision, grip and whole-body regression checks.

- [ ] **Step 5: Perform the real-human visual review**

Record observable agreements/disagreements against each relevant evidence item. Do not use “looks acceptable” without evidence.

- [ ] **Step 6: Update issue states only from committed evidence**

WB-AX-001, WB-PEC-002, WB-PEC-003, WB-AX-004, WB-SHO-005, WB-SHO-006, WB-CLV-007 and WB-SYM-008 may close only if no Critical/High defect remains in any sampled frame/view.

- [ ] **Step 7: Run verification and commit/push**

Commit message: `Validate r96 shoulder and axilla foundation against human evidence`

### Task 8: Whole-package verification and handoff

**Files:**
- Modify: `docs/ORIGINAL_V1_WHOLE_BODY_RECOVERY_20261004.md`
- Modify: `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`
- Create: package verification receipt under `ORIGINAL_V1_WORK/candidates/repair_checks/`.

- [ ] **Step 1: Run all focused Python tests and the complete ORIGINAL v1 suite**

- [ ] **Step 2: Run Blender smoke, production-path replay and hash checks**

- [ ] **Step 3: Run the phase selector and prove it remains fail-closed**

Shoulder completion does not close grip/wrist or other whole-body issues.

- [ ] **Step 4: Inspect the complete visual evidence**

- [ ] **Step 5: Record exact HEAD, model hashes, open issues and next package**

- [ ] **Step 6: Commit and push the recoverable handoff**

Commit message: `Handoff evidence-backed shoulder foundation recovery`
