# Laptop Work handoff — whole-body human deformation recovery — 2026-10-05

## Purpose

Resume the ORIGINAL-v1 body recovery without losing any newer local Blender work.

The governing requirement is now explicit:

> The model must move and deform like a real human body. When any joint or body
> segment moves, every anatomically connected skin/muscle/tendon chain that should
> respond must respond coherently, while tissue that should remain rooted must
> remain rooted.

Do not treat this as a cosmetic preference. It is a blocking engineering contract.

## Branches

Current Work recovery branch last known remote checkpoint:
`codex/whole-body-deformation-recovery-20261004`

Parallel GPT authority/tooling branch:
`gpt/shoulder-layer-diagnostic-20261004`

Do NOT reset, rebase, force-push, or overwrite local Work changes.

## Safe pickup order

1. Inspect current local branch, working tree and untracked files.
2. Fetch the remote.
3. Re-read the live remote HEAD for both branches.
4. If local Work changes exist, commit them on the current Work lineage first with
   a clear checkpoint message. Preserve all local candidate/evidence files.
5. Only after the Work state is safely committed, integrate the GPT branch using a
   normal merge/cherry-pick strategy that preserves both histories. Do not rebase
   the Work branch onto GPT.
6. Resolve only documentation/tooling conflicts. Preserve newer model/Blend/evidence
   files from Work.
7. Run:
   `RUN_ORIGINAL_V1_HUMAN_BODY_READINESS_CHECK.bat`
8. Do not continue if that control layer is inconsistent.

## Read first

- `docs/ORIGINAL_V1_HUMAN_BODY_MASTER_PLAN.md`
- `docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md`
- `ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json`
- `ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json`
- `ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json`
- `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`
- `ORIGINAL_V1_HUMAN_BODY_STATUS.json`

Historical Phase 4/r95 remains immutable comparator evidence. It is NOT current
anatomical sign-off. Historical "Phase 5A next" text is subordinate to the master
human-body plan.

## Current master state

**Master Stage 1 — Human movement foundation**

Current blocker:
shoulder/chest/anterior-axilla/posterior-axilla foundation recovery.

The current shoulder/chest defect is known to be foundational:

- weights-only surface already contains incorrect torso/axilla ownership/support;
- existing correctives reduce the external wing but trade it for membrane/trench/
  chest-volume defects;
- another cosmetic r95 patch is not the selected path.

## Immediate shoulder recovery sequence

### A. Read-only diagnostics first

First record the exact saved Blender skinning mode:

`RUN_ORIGINAL_V1_SKINNING_MODE_AUDIT.bat <candidate.blend> <fresh-label>`

Do not change LBS/Preserve Volume/DQ at this point. This establishes what r95
actually uses so any later A/B test can keep every other variable identical.

Then run the shoulder deformation layer diagnostic on the exact comparator/current
candidate using a fresh label:

`RUN_ORIGINAL_V1_SHOULDER_LAYER_DIAGNOSTIC.bat <candidate.blend> <fresh-label> press_top,pullup_hang 13`

Review:

- weights-only surface;
- abduction corrective contribution;
- flexion corrective contribution;
- scapular corrective contribution;
- combined corrective contribution;
- anterior/posterior axilla zones;
- lateral chest-root zone;
- left/right symmetry.

Also run, using fresh labels:

`RUN_ORIGINAL_V1_MOTION_REVERSIBILITY_AUDIT.bat <candidate.blend> <fresh-label>`

`RUN_ORIGINAL_V1_MOTION_CONTINUITY_AUDIT.bat <candidate.blend> <fresh-label>`

These are read-only and must not save the Blend.

### B. Declare the repair before editing

Create a fresh candidate-specific copy of:

`ORIGINAL_V1_COUPLING_ZONE_DECLARATION_TEMPLATE.json`

For the affected coupling systems, especially:

- `CP-PEC-AX-002`
- `CP-POSTAX-003`
- `CP-DELTOID-004`
- `CP-NECK-TRAP-001`

Declare exact:

- proximal attachment vertices;
- bridge-tissue vertices;
- distal attachment vertices;
- protected-neighbour vertices;
- allowed edit vertex set;
- allowed bone groups;
- expected human behaviour;
- forbidden visual failures;
- source/hash identities.

Validate the declaration before any edit.

### C. Create a NEW candidate

Never overwrite r95.

The new candidate must first repair the weights/support foundation.

Do not add/refit correctives yet.

### D. Prove weights-only anatomy first

The shoulder/chest/axilla evidence must include both sides through approximately:

`0° -> 45° -> 90° -> 120° -> 150° -> 170° -> return`

At each useful checkpoint inspect:

- pectoral chest root;
- humeral pectoral insertion side;
- anterior axillary fold;
- posterior axillary fold;
- lat/teres/triceps transition;
- deltoid yoke;
- clavicle/acromion/scapular surface;
- lateral chest wall;
- neck/trapezius drape;
- whole-body silhouette.

The weights-only surface must be anatomically plausible before a corrective layer
may be fitted.

### E. Fit correctives only if the foundation is already plausible

A corrective may refine:

- volume redistribution;
- fold quality;
- secondary surface transition;
- app-distance silhouette.

A corrective may NOT conceal:

- wrong bone/tissue ownership;
- detached attachment sides;
- a large wing/flap;
- a chest/axilla membrane;
- a deep artificial trench/pit;
- a rigid spherical deltoid;
- a single-bone ownership seam.

### F. Candidate-bound coupling proof

Create a candidate-specific copy of:

`ORIGINAL_V1_ANATOMICAL_COUPLING_EVIDENCE_TEMPLATE.json`

Every required coupling system must prove:

- exact candidate SHA;
- weights-only evidence;
- corrected evidence;
- intermediate samples;
- return samples;
- whole-body renders;
- close regional renders;
- numerical regression;
- contact/load evidence where applicable;
- bilateral consistency;
- attachment continuity;
- volume/fold logic.

Use:

`ORIGINAL_V1_ANATOMICAL_COUPLING_CAPTURE_PLAN.json`

for the required movement/camera matrix.

### G. Automatic moved-joint coverage

For each pose/sample, record the materially moved production bones.

The authoritative:

`ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json`

determines every tissue chain that becomes required review scope.

Use candidate evidence based on:

`ORIGINAL_V1_MOVEMENT_COUPLING_EVIDENCE_TEMPLATE.json`

A sample is incomplete if a moved joint triggers a connected tissue system that
is absent from the evidence.

Example: humeral motion requires review of the pec/anterior axilla, posterior
axilla, deltoid, upper-arm and neck/trapezius chains. It is not enough to inspect
the arm alone.

## Whole-body continuation after shoulder recovery

Do not assume the rest of the body is accepted.

Continue Master Stage 1 through every coupling system:

1. cervical -> trapezius -> shoulder girdle;
2. pec -> anterior axilla -> humerus;
3. lat/teres -> posterior axilla -> humerus;
4. deltoid shoulder yoke;
5. upper arm -> elbow -> forearm;
6. forearm -> wrist -> hand load chain;
7. palm/flexor tendon -> fingers/thumb;
8. ribcage -> abdomen/obliques/lumbar -> pelvis;
9. pelvis/glute -> femur/lateral thigh;
10. pelvis/adductor/groin -> medial thigh;
11. quadriceps/rectus -> patella/tibia;
12. hamstrings -> posterior thigh/popliteal region;
13. gastrocnemius/soleus -> Achilles/calcaneus;
14. ankle/hindfoot -> arch/forefoot/toes.

All 12 body regions and all 27 master movement families now have evidence
scaffolding, but evidence scaffolding is NOT candidate acceptance.

## Exterior human appearance

The repo now separately tracks real-human exterior surface evidence at:

`ORIGINAL_V1_SURFACE_VISUAL_EVIDENCE_REQUIREMENTS.json`

All body regions require:

- neutral;
- lengthened/elevated;
- compressed/loaded;
- intermediate;
- return;

plus whole-body context and close regional views.

Biomechanics/anatomy/numerical metrics cannot by themselves close exterior
skin/muscle appearance.

## Blocking rule

Do not enter high-detail anatomy while any Critical/High whole-body defect remains
open or while required coupling systems are not candidate-proven.

Do not weaken thresholds, re-pin baselines, modify frozen pose definitions, or
hide body errors with clothing/material/lighting/crop.

## Definition of success

This recovery is not complete when the chest/armpit alone looks better.

It is complete only when the exact candidate proves that all anatomically connected
surface chains respond correctly to their driving joints through complete movement
and return, with no unresolved Critical/High whole-body defect, preserved contact,
and no material regression elsewhere.

Only after the human body foundation, regional proof, movement-family proof and
human-evidence closure are complete may high-detail anatomy resume.
