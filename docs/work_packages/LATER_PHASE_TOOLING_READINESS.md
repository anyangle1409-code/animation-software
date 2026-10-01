# Phase 6–11 tooling readiness

This is preparation scope, not phase completion. Scripts were inspected at model
source HEAD `61689f5119aab4ee619940ddfabe9176201f03b5`. Check live code again at
execution. Do not call an early O-stage checkpoint a later production gate.

| Phase | Ready tooling | Missing work before its exit checks can pass |
|---|---|---|
| 6 | Raw schema-2 snapshots; mesh/weight deltas; full bare stress evidence; source-bound review capture | Candidate-bound surface audit for manifold components, winding/normals, degenerate faces, joint-support landmarks and symmetry coverage |
| 7 | Original authoring boundary rules; body snapshot/change audits; bare stress controls | Garment-local geometry/weight audit, dressed pose/contact capture with source receipts, body/garment clearance measurements and dressed review protocol |
| 8 | Repeatable bare-body milestone cameras and actual-image comparison boards | Candidate-bound scene/material inventory, numeric material/presentation state capture, dressed/application-distance capture and readability review |
| 9 | Unchanged production_target evaluator for all 15 static stress poses; grip/floor metrics | Continuous range sampler, per-frame garment/body/contact checks, explicit legitimate-contact classification and final export identity binding |
| 10 | Candidate GLB structural auditor accepts an explicit manifest; standalone source/release/browser audits exist on this branch | Revision-isolated candidate exporter, ORIGINAL-owned measured runtime grip metadata, real standalone-engine exercise/contact/continuity and export round-trip evidence on its live integration commit |
| 11 | Review source/image hashes; matched boards; coverage plan; stable bare capture protocol | Runtime-bound frame capture and actual visual defect tests with coverage/limits, reproducibility checks and a first-party reference inventory |

Queue missing deterministic tooling as GPT repo-side work before the corresponding
Blender session. The packages define required inputs/outputs below; Claude should
execute prepared tools, not invent a success marker. Safe modelling/diagnostics in
earlier eligible phases can continue while these tools are prepared. A future
domain tool must bind exact candidate/asset hashes, runtime commit where relevant,
its source script/version, actual command, source git commit and timestamp. Save
raw measurements and coverage/limits; do not give it promotion authority.

## Existing tools with limited or unsafe later-phase scope

- `scripts/audit_original_v1_blender.py` is a fixed clean-scaffold checkpoint with
  historical reference-rig/count expectations. It is not the final topology audit.
- `scripts/add_original_v1_candidate_shorts_blender.py` replaces existing shorts,
  uses early fixed dimensions and nearest-body weight assignment. Do not rerun it
  as Phase 7 production construction. Prepare independently authored garment
  operations with explicit source correspondence under the current boundary.
- `scripts/export_original_v1_candidate_glb_blender.py` writes shared GLB filenames
  and CANDIDATE_GLB_EXPORT.json beside its input, without revision isolation or
  final candidate-SHA binding. Do not run it over historical exports. A future
  replacement/opt-in mode needs fresh output paths, collision refusal, exact
  candidate identity, export settings and raw export hashes; preserve old outputs.
- `scripts/audit_original_v1_candidate_glbs.py --manifest <new manifest.json>` is a
  structural/self-contained packaging check. It does not establish anatomy,
  dressed deformation, final lineage or runtime motion. The default manifest is
  the historical export checkpoint; always identify the new manifest explicitly.
- Authoring-boundary and standalone audit wrappers use fixed report locations.
  Run later audits only in a controlled isolated checkout/output context and
  preserve each raw result before another run. Never overwrite committed history.
- `scripts/browser-first-party-viewport-smoke.mjs` explicitly reports supplementary
  coverage. A successful viewport smoke test is not motion, offline-device or final
  character acceptance. Report the additional gates still open.

No missing tool is claimed implemented by these documents. Earlier shorts/GLBs
remain candidate history and cannot be relabelled as exports of r29 or later models.
