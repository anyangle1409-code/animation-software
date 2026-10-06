# ORIGINAL-v1 shoulder foundation rebuild handoff

Status: PREPARED · fail-closed · no Blender/model edit performed by this document · production approval false.

## Why this supersedes the old r96 Task 7 next action

Owner review of the committed r96 overhead screening renders found structural deformation failure: deltoid elongation/collapse, deep axillary trench/membrane, pectoral transport, scapular/upper-back grooves, lost tissue continuity and a shoulder complex that behaves too much like an arm rotating inside a comparatively static torso.

The previous prepared Task 7 residual-corrective route is therefore not the next execution step. It remains historical evidence only.

## Immutable evidence

- r95 remains the rejected comparator and must never be overwritten.
- Existing r96 support-rest-length and weights-only screening renders remain diagnostic evidence.
- r96 topology-only intermediate SHA-256 remains `6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd` where referenced by historical evidence.
- Existing thresholds, first-party provenance rules, contacts and unrelated-body regression gates remain protected.
- Do not copy third-party geometry, weights, morphs or coordinates.

## Active acceptance authority

Read before any edit:

1. `ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json`
2. `ORIGINAL_V1_SHOULDER_ANATOMICAL_REVIEW_TEMPLATE.json`
3. `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`
4. `ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json`
5. `docs/superpowers/specs/2026-10-04-whole-body-human-deformation-recovery-design.md`
6. `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`

## Mandatory causal order

Do not skip a layer:

1. **Shoulder-girdle mechanics** — verify humerus, clavicle and scapula state through elevation and axial rotation. Do not impose a universal fixed scapulohumeral ratio.
2. **Support topology** — ensure the mesh can represent anterior/posterior axillary folds, deltoid transition, chest root and scapular/back continuity without membranes or trenches.
3. **Weights-first transfer** — solve only declared local influences and prove the surface with shoulder correctives disabled.
4. **Rotation-aware anatomical deformation** — only after the weights-only foundation passes, allow generic motion-driven deformation that distinguishes axial-rotation states.
5. **Minimal residual correctives** — only for remaining soft-tissue behaviour. Never use a large morph to conceal failure of layers 1–3.

## Fresh-candidate rule

Do not overwrite r96. Before editing, create a fresh numbered descendant candidate and a declaration that binds:

- exact parent SHA-256;
- exact source Git commit;
- vertex/face repair scope;
- permitted bones/influences;
- protected regions;
- topology intent;
- maximum edit scope;
- linked issue IDs;
- stop conditions.

Start from `ORIGINAL_V1_SHOULDER_FOUNDATION_DECLARATION_TEMPLATE.json`, copy it to a fresh candidate-specific evidence path, fill the exact parent/hash and scope, then validate it with `scripts/original_v1_shoulder_foundation_declaration.py` before Blender edits. The repository template is intentionally incomplete/fail-closed.

Before Blender editing, run `python scripts/original_v1_shoulder_foundation_readiness.py <candidate-declaration.json> --out <readiness.json>`. Blender foundation editing is allowed only when it returns `ready: true` / `BLENDER_FOUNDATION_EDIT_ALLOWED`.

If declaration identity or parent identity does not match, stop.

## Required movement proof

Capture flexion and abduction at:

`0°, 30°, 60°, 90°, 120°, 150°, maximum valid elevation`

For anatomically valid samples, capture:

`internal rotation · neutral rotation · external rotation`

Required views:

`front · front three-quarter · side · rear three-quarter · rear · shoulder/axilla close-up`

Capture enough intermediate/reversal frames to expose onset, maximum and release of deformation. Endpoint-only evidence is insufficient.

## Weights-only hard gate

Before any residual corrective fitting, reject the candidate if any required view/frame shows:

- deltoid collapse or implausible elongation;
- deep axillary trench, knife edge, membrane or pointed flap;
- pectoral tissue dragged vertically with the arm;
- broken neck → elevated shoulder → upper-arm continuity;
- deformation-generated scapular/back groove;
- disappearing shoulder/axilla/chest volume;
- torso motion substituting for shoulder-girdle mechanics;
- implausible anterior/posterior axillary-fold migration;
- surface pinch/stretch discontinuity;
- effectively identical surface response across axial-rotation variants where anatomy should differ.

## Machine evidence

Populate all SH-M01..SH-M09 rows in a candidate-specific copy of `ORIGINAL_V1_SHOULDER_ANATOMICAL_REVIEW_TEMPLATE.json`.

Run:

`python scripts/original_v1_shoulder_acceptance.py <candidate_review.json> --out <shoulder_acceptance_result.json>`

The evaluator is fail-closed. Missing rows, missing visual evidence, an open linked Critical/High issue, incomplete movement matrix, or a corrective fitted before weights-only acceptance blocks progression.

## Visual evidence

Every SH-V01..SH-V10 row requires committed production-path render paths and a written review note. A green numerical report cannot override a visible anatomical failure.

The shoulder-linked blockers remain:

`WB-AX-001, WB-PEC-002, WB-PEC-003, WB-AX-004, WB-SHO-005, WB-SHO-006, WB-CLV-007, WB-SYM-008`.

Do not close them from a single pose or a single view.

## Stop conditions

Stop the current candidate and preserve evidence when:

- a foundation layer cannot pass without a large corrective;
- three controlled trials move the defect rather than remove it;
- axial-rotation variants remain effectively indistinguishable;
- a new Critical/High defect appears;
- unrelated body regions regress;
- Blender and exported/runtime deformation disagree;
- evidence is incomplete or identity binding is stale.

A stopped candidate is useful evidence. Do not rescue it by relaxing thresholds.

## Exit

Shoulder foundation recovery is complete only when:

- the weights-only foundation passes;
- the full movement matrix is candidate-bound;
- all SH-M and SH-V gates pass;
- linked shoulder Critical/High issues have valid committed closure evidence;
- whole-body regressions pass;
- `shoulder_acceptance_result.json` says `pass: true`;
- `production_approved` remains false.

Then continue to the next whole-body blocker. Do not jump directly to Phase 5.
