# ORIGINAL-v1 non-Blender exhaustion checkpoint — 2026-10-06

Status: PREPARED AND PUSHED · production approval false · no claim of visible model repair.

## Trigger

Owner rejected the latest r96 overhead shoulder screening renders. The visible failure is structural and connected across deltoid, axilla, pectoral transition, scapular/back surface and shoulder-girdle motion. The previous direct residual-corrective next action was therefore unsafe.

## Completed without Blender

- Added `ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json`.
- Added `ORIGINAL_V1_SHOULDER_ANATOMICAL_REVIEW_TEMPLATE.json`.
- Added `scripts/original_v1_shoulder_acceptance.py` and its safety tests.
- Redirected `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json` from corrective-first r96 Task 7 to weights-first shoulder-foundation rearchitecture.
- Marked `docs/ORIGINAL_V1_R96_TASK7_HANDOFF.md` superseded for execution.
- Added `docs/ORIGINAL_V1_SHOULDER_FOUNDATION_REBUILD_HANDOFF.md`.
- Added fresh-descendant declaration template/validator:
  - `ORIGINAL_V1_SHOULDER_FOUNDATION_DECLARATION_TEMPLATE.json`
  - `scripts/original_v1_shoulder_foundation_declaration.py`
  - `scripts/test_original_v1_shoulder_foundation_declaration.py`
- Added pre-edit readiness gate:
  - `scripts/original_v1_shoulder_foundation_readiness.py`
  - `scripts/test_original_v1_shoulder_foundation_readiness.py`
- Bound whole-body audit readiness to the shoulder acceptance contract.
- Hardened Phase 4 preflight to require a candidate-bound passing shoulder acceptance receipt with weights-only foundation pass, complete movement matrix and human anatomical review.
- Updated the whole-body recovery document, audit plan and high-detail status recovery override.

## Enforced architecture

`skeleton mechanics -> support topology -> weights-first transfer -> rotation-aware anatomical deformation -> minimal residual correctives`

A later layer cannot be used to hide failure of an earlier layer.

## Current candidate dispositions

- r95: immutable rejected comparator.
- existing r96 screening: diagnostic evidence; rejected for promotion.
- next model candidate: must be a fresh numbered descendant declared before edit. This checkpoint intentionally does not invent the revision or parent hash; resolve them from the live Blender/repository state at execution time.

## Next Blender execution

1. Re-read live HEAD and this checkpoint.
2. Copy/fill the fresh shoulder-foundation declaration template with the exact parent candidate/hash and exact repair scope.
3. Run the declaration validator.
4. Run the shoulder-foundation readiness gate; require `BLENDER_FOUNDATION_EDIT_ALLOWED`.
5. Verify shoulder-girdle mechanics through elevation and axial rotation.
6. Repair the first failed causal layer on the fresh candidate.
7. Render/measure the weights-only movement matrix with correctives disabled.
8. Stop if any mandatory overhead visual failure remains.
9. Only after a weights-only pass, fit minimal generic residual deformation if still required.
10. Populate the candidate-specific shoulder review, run the acceptance evaluator, whole-body regressions and issue closure evidence.
11. Do not enter Phase 4/5 while any Critical/High blocker remains.

## Verification boundary

The GitHub-connected chat environment can create/read repository files but does not execute the repository's Python or Blender test suite. The safety tests and validators above are committed/prepared, but this checkpoint does **not** falsely report them as executed green. The next execution-capable environment must run the focused Python tests before Blender authoring, then run the Blender/candidate evidence gates.

## Stop point

Further meaningful progress on the visible shoulder defect now requires an execution environment with the actual candidate Blend and Blender. Additional prose/specification work would not improve the model and risks duplicating already committed authority.

Production approval remains false.
