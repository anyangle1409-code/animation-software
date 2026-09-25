# Remaining Blender-only / GPT Work tasks

Purpose: spend GPT Work usage only where direct Blender control is genuinely
required. Everything else should stay in normal Chat/source tooling where
possible.

## 1. Current — V15 deep hand surface rebuild

**Needs Blender:** yes.

Work must physically edit:
- index/middle/ring/little finger shaft topology;
- PIP/DIP transitions;
- cross-section/silhouette;
- inherited unwelded/faceted local patches.

Already automated:
- source selection;
- protected contacts;
- region/joint guide selection;
- checkpoints;
- UV/weight repair for new export vertices;
- triangulation/export;
- validation/renders/diffs/reports;
- next-attempt naming.

Commands:
- start: `START_V15_HAND.bat`
- finish: `RUN_V15_POST_EDIT_ALL.bat`

## 2. Later — shoulder/back/chest/armpit topology

**Needs Blender:** yes.

Work must physically create/revise the deformation-ready mesh around:
- deltoid;
- pec insertion;
- lat/upper back;
- axillary fold;
- scapular region.

Everything should remain a candidate until the Phase E pose pack and latest
source gates pass.

## 3. Later — final source palm/scapula deform controls and weights

**Needs Blender/rigging tool:** yes.

Work must physically:
- repair/add plausible source-side metacarpal deform controls if required;
- repair/add source-side scapula deform controls if required;
- paint/tune palm, wrist, shoulder, scapula, upper-back and axillary weights;
- preserve established source helper/twist structure.

Do **not** rebind the entire surface to the canonical 63-bone rig.

Prepared audits:
- `AUDIT_PHASE_F_SOURCE_RIG.bat`
- `VALIDATE_PHASE_F_RUNTIME.bat`

## Tasks that do NOT inherently need Blender Work

These should be handled source-side/normal Chat unless a visual inspection needs
the desktop:

- grip solve/refit;
- material candidate generation;
- source validation;
- collision/contact/equipment analysis;
- retargeting changes;
- palm/thumb/scapular motion code;
- prompt parser/adapters;
- family certification;
- correction levers;
- test creation;
- generation review orchestration;
- final system acceptance;
- documentation/handoffs.

## Work-usage rule

If a task can be expressed as:
- deterministic code;
- a GLB read/write transform;
- static analysis;
- test/validation;
- report generation;
- source branch work;

do it outside direct Blender Work first.

Use Work for:
- interactive topology;
- rig/bone placement that needs visual 3D judgement;
- weight painting/deformation tuning;
- final visual inspection where a static generated board is insufficient.
