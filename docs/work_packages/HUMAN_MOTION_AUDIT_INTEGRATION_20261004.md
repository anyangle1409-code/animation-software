# Work handoff — whole-body human-motion realism audit

## Why this exists

The current laptop Work session is investigating chest/armpit deformation on the
ORIGINAL-v1 model. Do not interrupt, reset or overwrite that local Blender work.

A parallel GPT branch now contains an additive audit framework:

`gpt/original-v1-human-motion-audit-20261004`

It was branched from model HEAD
`540edd4ca97927e04c2966a27f70148678c29464` and changes documentation/audit
files only. It does not edit the Blender candidate, rig, weights, pose definitions,
thresholds or historical baselines.

## Files to consume

- `docs/ORIGINAL_V1_WHOLE_BODY_HUMAN_MOTION_AUDIT.md`
- `ORIGINAL_V1_HUMAN_MOTION_AUDIT_PLAN.json`
- `ORIGINAL_V1_HUMAN_MOTION_DEFECT_LEDGER_TEMPLATE.json`
- `scripts/validate_original_v1_human_motion_audit.py`
- `scripts/test_validate_original_v1_human_motion_audit.py`

## Integration rule

First preserve and commit/push the current laptop candidate/evidence on its own
lineage. Then fetch the GPT branch and inspect its audit-only diff. Do not reset
or rebase the current model work onto the GPT branch.

The audit files may be cherry-picked or otherwise integrated only after the live
candidate is safely recorded. If the live model branch advanced after the GPT
branch point, preserve the newer model files exactly and resolve only audit/doc
path collisions.

## Immediate use on the chest/armpit investigation

1. Finish diagnosis of the current candidate without changing existing numerical
   gates.
2. Create a candidate-specific copy of
   `ORIGINAL_V1_HUMAN_MOTION_DEFECT_LEDGER_TEMPLATE.json`.
3. Bind it to the exact candidate revision/SHA.
4. Record external real-human observations as references; observations only,
   never imported geometry/images/weights.
5. Capture both sides of the chest/axilla sweep at approximately
   0/45/90/120/150/170 degrees arm elevation plus a return-transition sample.
6. Inspect anterior axillary fold, pec-deltoid continuity, axillary hollow,
   posterior fold/lat-triceps transition, deltoid cap, chest wall and scapular
   drape.
7. Seed every observed defect with a stable ID and severity.
8. Repair only after declaring the local edit scope and suspected cause.
9. Re-capture the sweep after the repair.
10. Run the existing full deformation/contact evidence against direct parent,
    active epoch baseline and Phase 4 freeze.
11. A HIGH/CRITICAL item is not fixed until the visual sweep and regression
    evidence both pass.

## Broader requirement

Do not stop the audit at chest/armpit. Apply the plan to all mandatory regions
and movement families. In particular, inspect intermediate frames, not merely
neutral and exercise endpoints.

The target is natural human shape change through motion: volume redistribution,
soft-tissue slide, folds appearing/disappearing under compression, coherent
attachment zones and continuous silhouette.

Numerical deformation health remains necessary but is not anatomical proof.

## Verification commands after integration

Plan contract:

```bat
python scripts\validate_original_v1_human_motion_audit.py
```

Candidate ledger during work:

```bat
python scripts\validate_original_v1_human_motion_audit.py --ledger path\to\candidate_human_motion_ledger.json
```

Exit attempt:

```bat
python scripts\validate_original_v1_human_motion_audit.py --ledger path\to\candidate_human_motion_ledger.json --require-exit
```

The exit command must remain blocked while mandatory coverage or open
CRITICAL/HIGH defects remain.

## Production status

This framework must never set `production_approved: true`. It is an additional
evidence layer for anatomy/deformation quality; final production approval remains
the later production-freeze process.
