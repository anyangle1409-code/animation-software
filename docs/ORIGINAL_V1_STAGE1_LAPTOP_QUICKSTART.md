# ORIGINAL v1 Stage 1 — laptop quick-start

This is the preferred operator path for the Home Gym PT ORIGINAL-v1 human-body
foundation. It does not replace the master plan; it removes ambiguity at laptop
pickup.

## Non-negotiable target

The character must deform like a plausible human body through complete motion.
When a joint/segment moves, every anatomically connected tissue chain that should
respond must respond coherently, while rooted tissue stays rooted. Passing
numerical deformation checks is not anatomical acceptance.

## 1. Preserve local Work before integrating tooling

Before using any command below:

1. inspect the live Work branch, working tree and untracked files;
2. commit any newer local Work/Blender/evidence state on the Work lineage;
3. fetch both live branches;
4. integrate the GPT tooling branch without reset/rebase/force-push;
5. preserve newer Work model/evidence files during conflict resolution.

Tooling branch:
`gpt/shoulder-layer-diagnostic-20261004`

Recovery branch:
`codex/whole-body-deformation-recovery-20261004`

## 2. Optional: reuse a previously calibrated generic sweep runner

Runner calibration is reusable **only while its runner/spec/frozen-pose hashes
remain unchanged**.

If a validated CALIBRATED record already exists:

`set HGPT_SWEEP_CALIBRATION_RECORD=<path-to-calibrated-record.json>`

The pickup planner validates it before reuse.

**Calibration reuse rule:** reuse is allowed only while the generic runner,
execution spec and frozen pose-source hashes still match the calibrated record.
A repaired body candidate does **not** require recalibrating the runner when those
authorities are unchanged; the candidate still requires its own selected sweep,
visual, contact and acceptance evidence.

If no calibrated record exists, leave the variable unset. The pickup sequence
will generate an IN_REVIEW record and stop at a review gate before model editing.

## 3. Generate the Stage 1 pickup packet

Current active wave:
`shoulder_yoke_foundation`

Current repair cluster:
- `RP-PEC-AX-002`
- `RP-POSTAX-003`
- `RP-DELTOID-004`
- `RP-NECK-TRAP-001`

Run:

`RUN_ORIGINAL_V1_STAGE1_LAPTOP_PICKUP_PLAN.bat <candidate.blend> <current-revision> <new-revision> <source-branch> bilateral <fresh-label> <fresh-repair-workspace-dir> <fresh-pickup-plan-dir>`

The packet calculates the exact pre-edit SHA and produces a paste-ready command
sequence.

## 4. Execute the generated commands in order

The generated sequence is fail-closed:

1. human-body contract/test gates;
2. Stage-1 wave work package;
3. package-aware pre-repair diagnostic bundle;
4. package-aware generic human-movement sweep pipeline where required;
5. sweep-runner calibration review/finalization when no reusable calibrated
   record exists;
6. PRE-EDIT repair workspace creation;
7. immutable repair-declaration review;
8. coupling-weight audit;
9. model-edit boundary.

Do not start the Blender repair if any earlier step fails.

### Generic human-movement sweep pipeline

The pickup plan uses:

`RUN_ORIGINAL_V1_HUMAN_MOVEMENT_SWEEP_PIPELINE.bat <candidate.blend> <revision> <RP-ID[,RP-ID...]> <fresh-label> [calibrated-runner-record]`

Without a reusable calibrated record it:
- runs one all-11 raw sweep report for calibration;
- creates a candidate-bound IN_REVIEW calibration record;
- captures only the sweep visuals needed by the selected repair packages;
- captures raw contact/load evidence only where applicable;
- creates per-sweep motion/contact/acceptance review workspaces.

With a reusable CALIBRATED record it skips authority-wide recalibration and runs
only the candidate-specific sweep subset.

Runner binding or raw sweep execution is **never** human-motion acceptance.

## 5. Calibration review

For first-time calibration, every one of the 11 adapters must have:
- automatic source/sample/identity checks true;
- per-adapter engineering review PASS;
- per-adapter human-evidence review PASS;
- every required human-evidence ID reviewed;
- calibration notes.

Then finalize with:

`RUN_ORIGINAL_V1_FINALIZE_HUMAN_MOVEMENT_SWEEP_CALIBRATION.bat <reviewed-IN_REVIEW-record.json> <fresh-CALIBRATED-record.json>`

Owner review remains separate.

## 6. Model repair

For the current shoulder wave, repair the **weights/support foundation first**.

Do not add/refit correctives until the weights-only shoulder/chest/axilla/back
surface is anatomically plausible through outbound, intermediate and return
motion.

Never overwrite r95 or the direct parent. Save a new numbered candidate.

## 7. Immediately after saving the repaired candidate

Use the paste-ready command emitted by the pickup packet:

`RUN_ORIGINAL_V1_STAGE1_POST_EDIT_CONTINUATION_PLAN.bat ...`

That continuation:
- binds the repair workspace to the exact final Blend SHA;
- generates the post-repair validation command order;
- carries the calibrated sweep record forward where required.

Then run the generated post-repair validation bundle.

## 8. Human-movement sweep acceptance

Each sweep-only movement needed by the repair packages requires:
- exact-candidate raw sweep evidence;
- validated CALIBRATED runner;
- full required visual capture set;
- reviewed motion continuity;
- reviewed return/reversibility;
- contact/load evidence for contact-bearing sweeps;
- all required human-evidence refs.

After those referenced reviews are PASS, finalize each acceptance record with:

`RUN_ORIGINAL_V1_FINALIZE_HUMAN_MOVEMENT_SWEEP_ACCEPTANCE.bat <reviewed-acceptance.json> <fresh-final-acceptance.json>`

The unified candidate comparison rejects raw sweep reports as substitutes for
accepted sweep evidence.

## 9. Candidate clearance

The new candidate may become engineering-clear eligible only after:
- scoped weights-only regions are CLEAR;
- scoped anatomical coupling systems are CLEAR;
- all repair-package proof movement families are present in COMPLETE
  movement-coupling evidence;
- all required sweep-only movements have accepted candidate-bound records;
- surface visual review is PASS;
- contact/regression/change audits pass;
- repair execution stayed inside immutable declarations;
- no new Critical/High issue exists;
- scoped Critical/High defects have closure evidence.

Engineering clearance never implies owner acceptance or production approval.

## Stop conditions

Stop before editing/promotion if any of these occurs:
- newer local Work state has not been preserved;
- candidate SHA differs;
- human-body contract gate fails;
- required sweep adapter/calibration/acceptance is incomplete;
- repair declaration is incomplete;
- edit exceeds declared vertices/bones/operations;
- weights-only anatomy remains implausible;
- a Critical/High whole-body defect remains open;
- candidate comparison is not engineering-clear eligible.

High-detail anatomy remains blocked until Stage 1 whole-body integration is
complete.
