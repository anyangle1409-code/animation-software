# Phase 5 anatomy execution protocol

Prepared only; Phase 5 remains NOT STARTED until a verified Phase 4 development
freeze exists.

This protocol converts the seven existing region briefs into one deterministic
execution/evidence contract so a future Claude Blender session can focus on
modelling instead of reconstructing workflow.

## Machine plan

Use:

- `ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json`
- `scripts/original_v1_phase5_anatomy.py`
- `RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat`

The execution order is fixed:

`5A torso → 5B shoulders → 5C arms → 5D hands → 5E pelvis/legs → 5F feet → 5G head/neck`.

The order does not mean owner review must block each next region. Routine review
is non-blocking. It means each new region must prove lineage from the previous
verified regional candidate so the chain cannot silently jump between models.

## Before modelling a region

Create an incomplete packet for the region:

```bat
RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat --template 5A ORIGINAL_V1_WORK\phase5\5A_template.json
```

Replace 5A with the required region.

The template records the exact plan-controlled:

- permitted scope;
- protected boundaries;
- focused stress poses;
- required real render views;
- predecessor region;
- required check IDs;
- required evidence/artifact slots.

It intentionally leaves candidate identities, evidence paths and PASS values empty.
A template is never execution evidence.

Before the actual Blender edit, Claude must still follow the corresponding
`docs/work_packages/PHASE_5*.md` brief and record the candidate-bound edit
mask/policy and independent operation intent.

## Required regional evidence

Every completed regional report must bind:

- candidate revision and SHA-256;
- direct parent revision and SHA-256;
- development-freeze candidate SHA-256;
- exact source git commit;
- exact work-package identity;
- unchanged permitted scope;
- exact focused-pose list;
- exact required-view list;
- real source evidence;
- exact required artifacts.

The required artifact inventory is fixed by the machine plan:

1. entry receipt;
2. candidate/source manifest identity;
3. development-freeze report identity;
4. direct-parent identity;
5. declared edit mask/policy;
6. before raw snapshot;
7. after raw snapshot;
8. change audit;
9. mesh/weight audit;
10. full 15-pose merged report and source receipt;
11. active stress-pose epoch baseline comparison;
12. direct-parent comparison;
13. development-freeze comparison;
14. actual required render/capture manifest;
15. regional review manifest;
16. regional execution report.

A missing artifact is not UNKNOWN-but-acceptable; regional evidence verification
is refused until it is present.

## Required regional checks

Every actual report must explicitly carry these nine checks, all backed by hashed
source evidence:

- `scope_bound`
- `provenance_clean`
- `topology_correspondence`
- `mesh_weight_audit`
- `full_deformation_evidence`
- `comparisons_epoch_parent_freeze`
- `contacts_preserved`
- `captures_complete`
- `lineage_complete`

The verifier checks the contract and file identities. It does not manufacture the
truth of these checks; the referenced Blender/audit outputs must actually prove
them.

## Region-order binding

5A has no previous-region receipt.

5B–5G each require the immediately preceding region's
`REGION_EVIDENCE_VERIFIED` receipt. The prior region's candidate SHA must equal
the new region's direct-parent SHA.

This prevents, for example, a 5D hand candidate from being based on an unrelated
5A/Phase-4 model while still appearing to follow the intended sequence.

## Verify completed regional evidence

After the candidate has been modelled and all real evidence exists:

```bat
RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat 5A <actual-region-report.json> <fresh-receipt.json>
```

A valid receipt says:

`REGION_EVIDENCE_VERIFIED`

It still records:

- `phase_complete=false`
- `production_approved=false`

It cannot decide that anatomy looks convincing and cannot mark Phase 5 complete.

The main command also refuses real regional verification while Phase 4 is not
complete and requires the report candidate to be the latest complete candidate.

## Modelling boundaries

The plan preserves the existing anatomy specification and region briefs.

Claude must still:

- author the anatomy in Blender;
- use only ORIGINAL-v1/project-owned geometry and rig;
- preserve frozen dimensions/rest/hierarchy;
- keep R2 untouched;
- preserve frozen stress poses and thresholds;
- use fresh numbered candidates;
- run full evidence after meaningful changes and compare against the active epoch baseline, direct parent and recorded development-freeze candidate;
- publish actual review images;
- retain rejected/trade-off candidates;
- avoid topology changes unless explicitly mapped/audited.

The region verifier is workflow control, not a sculpting system.

## Phase 5 exit

After 5G has a verified regional receipt, execute the existing Phase 5 exit contract
from `docs/ORIGINAL_V1_PHASE_EXIT_EVIDENCE.md`.

Phase 5 still requires the full named exit checks, including all seven anatomy
regions, mesh/weight audits, deformation regression checks and published review
snapshots.

Final owner visual acceptance remains a later explicit requirement for production
promotion. Routine Phase 5 review snapshots remain non-blocking by default.

## Locked rig and baseline identity

Phase 5 is bound to `ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json`: `hgpt_canonical_v4_original` revision `rev2_forearm_twist_only`, 67 bones total / 66 deform bones, with the original 63-bone v4 structure retained as historical base evidence plus four forearm-twist helpers. The machine plan verifies this identity before producing or accepting region packets.

Regional reports must also bind the current active stress-pose epoch baseline revision/SHA and the exact candidate SHA recorded by the verified Phase 4 completion record. A syntactically valid but unrelated freeze SHA or historical R2-only comparison is refused.
