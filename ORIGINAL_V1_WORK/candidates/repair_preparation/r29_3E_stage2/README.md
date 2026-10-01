# Phase 3E repair preparation — r29

Parent SHA-256: `d9b24e75fa6f2eb4c8999787fd925d5986f236691e00c9d251be3f0f061d7574`. PREPARATION ONLY; no edit is authorised by these drafts.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md` and run the next-action selector first. Hand recovery
precedes these repairs. If a newer continuation candidate exists, regenerate into
a NEW folder for that candidate; do not relabel this parent-bound packet.

## Before editing

1. Check LIVE branch, preflight and the latest complete candidate. Preserve newer work.
2. Run remaining diagnostics on the appropriate continuation candidate; read the
   brief and raw points/weights. This packet's diagnostic state is
   **AWAITING_PROBES**. Missing probes are not a diagnosis.
3. Export the parent's raw schema-2 snapshot using the existing snapshot exporter.
   Inspect the measured defect in Blender. Inspection IDs are not permission lists;
   select the minimal local scope and verify actual region membership and symmetry.
   Region envelope: pelvis, torso, leg. This does not permit a
   whole-region edit. No shoulders, arms/hands/feet, shorts, frozen rig rest, lunge/squat definitions or threshold changes.
4. Copy `edit_intent_template.json` to a fresh operation-record path. Record explicit
   vertex IDs, regions, bones, mask evidence, intended operation and symmetry plan.
   Keep the original template unchanged. Freeze this intent before editing.
5. Work only on a NEW experimental candidate. Do not modify the source Blend.

## After the local experiment

Record child revision/hash and actual operations in a new operation record linked
to the pre-edit intent. Export a fresh child snapshot. Copy the audit policy to a
NEW file and bind both actual candidate hashes and the SAME intended scope.
Confirm index correspondence from operation history, never equal counts alone.
If topology/order changed, preserve that evidence; numerical deltas cannot be
claimed without separately authored correspondence. Do not widen permissions after
seeing unexpected changes; reject or diagnose the experiment instead.

Use the existing commands, with fresh snapshot/policy/output paths:

```bat
blender --background --factory-startup <verified parent.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <new before.json>
blender --background --factory-startup <verified child.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <new after.json>
python scripts/audit_original_v1_changes.py <before.json> <after.json> --policy <completed policy.json> --json-out <new audit.json>
```

An audit being written is not a gate PASS. Inspect unexpected vertices/bones,
normalisation, influences, cross-side weights, symmetry and topology/correspondence.
Run focused groups **hip**, then full 15-pose
evidence and R2/direct-parent/r28/r29 comparisons. Follow the package's exact gates
and renders. Publish actual review images and record pending NON-BLOCKING review;
continue safe work. Preserve rejected experiments and all their evidence.

The preparation manifest hashes the original templates and source context. It is
not a model candidate manifest or an approval record. No Blender work was run.
