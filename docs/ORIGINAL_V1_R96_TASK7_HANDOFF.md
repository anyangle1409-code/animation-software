# ORIGINAL-v1 r96 Task 7 — residual corrective handoff

Status: PREPARED · no model edit performed by this handoff · production approval remains false.

## Starting point

- Branch: `codex/whole-body-deformation-recovery-20261004`
- Frozen comparator: r95 SHA-256 `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`
- r96 topology-only intermediate SHA-256: `6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd`
- Task 6 conclusion: do not add more support loops, broaden arm-follow weights, or use Blender-only Preserve Volume as the delivery solution.
- Task 7 architecture: generic elevation-driven morph-target corrective, applied before ordinary LBS and exportable through the existing glTF/runtime path.

## Required order of work

1. Open and hash-verify the topology-only r96 intermediate. Stop on any identity mismatch.
2. Reproduce the r96 topology-only comparator metrics and review renders before editing.
3. Declare a fresh Task 7 mask **before** solving. Do not reuse the failed r95 displacement field.
4. The declaration must be mirror-closed, corrective-only, and parented to the exact topology-only r96 SHA-256.
5. Fit one residual behaviour at a time. Start with the axillary membrane/trench/pec-transport residual; do not simultaneously sculpt unrelated shoulder anatomy.
6. Use the existing generic humerothoracic-elevation driver. Exercise names must not enter the driver.
7. Run continuous-arc validation, not endpoint-only validation.
8. Compare every candidate to the same r96 topology-only baseline with the existing development-blocker comparison profile.
9. Render through the production deformation path and perform explicit anatomical review against the real-human evidence set.
10. Run the fail-closed Task 7 gate. Promotion is blocked if either numerical or visual evidence is incomplete.

## Mandatory numerical guards

Do not weaken the existing comparator tolerances. A Task 7 candidate is blocked when any tracked baseline pose disappears, failed-check count increases, or the existing comparator reports a material regression.

The solve must continue to guard:

- inward torso/axilla denting;
- local face-area collapse or inversion;
- edge over-stretch and over-compression;
- new penetration / self-intersection;
- abnormal outward lobe/bulge;
- whole-mesh volume loss;
- rough or discontinuous local surface behaviour;
- left/right asymmetry;
- non-local whole-body regressions.

## Mandatory visual/anatomical review

Task 7 is not complete on metrics alone. Production-path renders must explicitly review these open shoulder-complex items:

- `WB-AX-001` membrane-like axillary wall / deep trench
- `WB-PEC-002` excessive lateral pec transport with humerus
- `WB-PEC-003` chest volume collapse / central ballooning
- `WB-AX-004` posterior axillary fold support
- `WB-SHO-005` deltoid regional form
- `WB-SHO-006` shoulder-to-arm junction continuity
- `WB-CLV-007` clavicle/scapula/trapezius surface coupling
- `WB-SYM-008` bilateral shoulder-complex symmetry

Use `ORIGINAL_V1_R96_TASK7_VISUAL_REVIEW_TEMPLATE.json` as the shape only; copy it to a fresh candidate-specific evidence path. Required final review fields include:

- exact `source_candidate_sha256` = the topology-only r96 parent;
- exact candidate SHA-256 and source Git commit;
- real production-path render path/SHA/pose/view rows;
- one explicit PASS row for each of the eight issue IDs above, with committed render paths, human-evidence IDs and a written review note;
- `production_path_rendered: true`;
- `visual_pass: true`;
- `symmetry_pass: true`;
- `arc_continuity_pass: true`;
- `whole_body_regression_pass: true`;
- `real_human_reference_checked: true`;
- `required_issue_failures_remaining: 0` for the eight Task 7 shoulder-complex issues.

## Prepared gates

`scripts/original_v1_r96_task7_arc_gate.py` compares baseline and candidate continuous-arc audits for `press_top`, `press_top_rhythm`, `pullup_hang` and `pullup_hang_rhythm`. It uses only the already-approved repository comparison tolerances for blocking numerical drift; torso-drift and adjacent-sample continuity values without an existing sanctioned threshold are reported as measurements rather than turned into invented pass criteria.

Run it after generating matching baseline/candidate arc JSON:

```text
python scripts/original_v1_r96_task7_arc_gate.py \
  <baseline_arc.json> <candidate_arc.json> \
  --out <task7_arc_gate.json>
```

A green numeric arc result does **not** establish human anatomy; the production-path images still require explicit review.

`scripts/original_v1_r96_task7_gate.py` is Blender-free and intentionally fail-closed. It combines:

1. the existing numerical comparison JSON;
2. the Task 7 solve report JSON;
3. an explicit production-path visual-review JSON.

It will not pass a candidate merely because metrics are green. Even a Task 7 gate pass leaves `production_approved` false until the repository's normal promotion/freeze sequence is completed.

Example after Blender evidence exists:

```text
python scripts/original_v1_r96_task7_gate.py \
  <comparison.json> <solve_report.json> <visual_review.json> \
  --expected-parent 6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd \
  --out <task7_gate.json>
```

## Stop conditions

Stop and preserve evidence instead of promoting if:

- source hash or declaration identity mismatches;
- any numerical comparison regression appears;
- any Critical/High shoulder item remains visibly unresolved;
- the corrective only works for named exercise endpoints rather than the continuous movement envelope;
- Blender and runtime/exported deformation disagree;
- any unrelated body region regresses.

This handoff performs no Blender edit and claims no r96 model improvement by itself. Its purpose is to make the next laptop/Work run deterministic and harder to falsely promote.

## Whole-body continuation after the shoulder candidate

The shoulder fix is not permission to jump to Phase 5. The repository now has:

- `ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json` — explicit evidence coverage for every category in the movement envelope;
- `ORIGINAL_V1_WHOLE_BODY_DEFORMATION_AUDIT_PLAN.json` — 16 anatomical transition zones and start/intermediate/end/reversal sampling requirements;
- `scripts/original_v1_whole_body_audit_readiness.py` — checks audit infrastructure separately from unresolved model blockers;
- a hardened `scripts/original_v1_phase4_preflight.py` that refuses a new development freeze while any Critical/High whole-body anatomy issue remains open/in-progress/pending review.

Therefore, after a shoulder Task 7 candidate passes, continue through the blocking whole-body ledger (including grip/wrist) and the transition-zone audit. Only an empty Critical/High blocker list plus the normal candidate evidence makes Phase 4 re-freeze eligible.
