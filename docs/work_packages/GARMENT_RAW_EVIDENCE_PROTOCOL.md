# Candidate-bound raw garment evidence

Stage 6 GPT preparation, not Phase 7 execution/completion. This prepares the raw
foundation for dressed evidence. Posed clearance, intersections, motion and dressed
review capture remain future tooling. Current next deformation action remains RUN r30.
Early existing shorts are EXPERIMENTAL evidence, not final clothing acceptance.

## Inputs and capture on the laptop

Check LIVE branch, read the master/status/handoff and preserve newer work first.
Use a clean reconciled checkout and the exact local candidate Blend/JSON bytes.
Run `python scripts/original_v1_session_preflight.py --evidence-only` before capture.
Set BLENDER_EXE to the actual verified executable path. Use a fresh repository
folder and substitute the actual eligible revision for rN in these commands:

```bat
"%BLENDER_EXE%" --background --factory-startup "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_rN.blend" --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- "ORIGINAL_V1_WORK/candidates/garment_evidence/rN_trial1/body_snapshot.json"
"%BLENDER_EXE%" --background --factory-startup "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_rN.blend" --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- "ORIGINAL_V1_WORK/candidates/garment_evidence/rN_trial1/garment_snapshot.json" --garment
python scripts/original_v1_garment_evidence.py "ORIGINAL_V1_WORK/candidates/garment_evidence/rN_trial1/body_snapshot.json" "ORIGINAL_V1_WORK/candidates/garment_evidence/rN_trial1/garment_snapshot.json" --candidate-manifest "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_rN.json" --json-out "ORIGINAL_V1_WORK/candidates/garment_evidence/rN_trial1/raw_pair_evidence.json"
```

The existing snapshot tool still defaults to the body. Its optional --garment mode
selects exactly the owned shorts bound to the canonical 63-bone rig; it never falls
back to a body mesh. Capture verifies source manifest filename/hash and preserves
raw coordinates, faces, region labels, weights, matrices and rest bones. Body
region labels remain anatomical; garment rows use the coarse label `garment`,
which grants no edit permission. No nearest-body correspondence/weight transfer,
normalisation, modifier evaluation or Blend save is performed.

New schema-2 metadata includes mesh/scope identity, capture script/helper hashes,
actual Blender version, source git commit, command/time and source-manifest hash.
Non-deform group weights are recorded separately, including raw body coverage
weights. Ordered modifier receipts include viewport/render state and MASK/ARMATURE
settings. Other modifier types have only name/type/state inventory; their full
settings, shape keys and normals remain unresolved. Do not call this a complete
scene/material/garment construction receipt.

Outputs refuse existing files. Keep partial captures after failure, reconcile and
use fresh names; never relabel old snapshots or overwrite historical evidence.
After capture check LIVE HEAD again. If it advanced, stop stale work and reconcile
before publishing evidence. Use the recorded source checkout for later verification
if scripts changed; do not rewrite source hashes. Exact Python bytes are preserved
by Git attributes; follow the safe checkout guidance in CANDIDATE_EXPORT_PROTOCOL.

## Raw pair verification and existing audits

The pair verifier can run without Blender. It checks snapshot structure, candidate,
mesh/scope, capture version, rig/rest/frame and exact source-manifest/script hashes.
Local Blend bytes are VERIFIED when available and matching; absent local Blend is
honestly UNAVAILABLE. Record the source-operation history as well: receipt hashes
alone do not independently authenticate authorship.

The JSON is always EVIDENCE_ONLY, phase_complete=false, production_approved=false.
It includes counts, raw weight normalisation/influence/symmetry diagnostics, both
object matrices and complete captured mask/group rows. Cross-side diagnostics use
raw rig-aligned X coordinates; differing garment/rig matrices give UNRESOLVED_COORDINATE_FRAME,
not a contamination-free result. Centre crossing/intentional garment construction
still needs classification. Diagnostic influence defaults are inherited from the
existing audit (four influences, 1e-6 normalisation tolerance), not new promotion gates.
Exit 0 means a valid evidence report was written; 2 means input/identity/collision failure.

For garment surface findings, reuse the prepared surface audit on garment_snapshot:

```bat
python scripts/audit_original_v1_surface.py <garment_snapshot.json> --candidate-manifest <candidate.json> --json-out <fresh garment_surface.json> --markdown-out <fresh garment_surface.md>
python scripts/audit_original_v1_changes.py <before_garment.json> <after_garment.json> --policy <explicit garment_policy.json> --json-out <fresh garment_change.json>
python scripts/audit_original_v1_changes.py <before_body.json> <after_body.json> --policy <frozen_body_policy.json> --json-out <fresh body_preservation.json>
```

Read `SURFACE_AUDIT_PROTOCOL.md` and the model change audit contract. Declare exact
before/after candidate SHAs, allowed vertex IDs/regions/bones and genuine index
correspondence from authoring history. Garment topology changes invalidate automatic
index comparisons; supply a separately recorded authored correspondence instead of
assuming one. For frozen-body raw comparisons permit no edits and use zero change
epsilon; source history must confirm correspondence. These raw audits do not prove
unchanged shape keys, evaluated modifiers or bare/dressed motion. Those checks stay open.

## Execution and review boundaries

This stage was tested with controlled numeric fixtures and mocked Blender capture,
not an actual candidate Blender session. Actual source snapshots and modifier API
compatibility still require laptop execution. Do not use test fixtures as evidence.
No geometry repair, clipping exemption, rest/pose/gate change or phase PASS is authorised
by a report. In particular, a visibility mask does not remove underlying body failures.

Commit/push real snapshots, raw receipts, policies and audits where appropriate.
Images must come from actual candidate renders/runtime. REVIEW SNAPSHOTS ARE
NON-BLOCKING BY DEFAULT: record OWNER REVIEW pending and continue safe work under
the master's pause exceptions. Next repo-side preparation: evaluated dressed pose,
clearance/contact evidence and matched dressed review capture using frozen pose
functions without changing their definitions. Phase 7 remains NOT STARTED.
