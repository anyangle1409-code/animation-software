# Phase 6 advanced surface-quality protocol

Prepared only; Phase 6 remains NOT STARTED.

This closes the deterministic tooling gaps left by the raw surface audit:
evaluated-surface normals, evaluated self-intersections and explicit authored
joint-support evidence.

## Inputs

A future Phase 6 execution requires:

- exact latest candidate revision and candidate manifest;
- verified Phase 5 completion;
- the candidate Blend available locally;
- an authored joint-support evidence file derived from
  `ORIGINAL_V1_PHASE6_JOINT_SUPPORT_PLAN.json`.

The joint-support template intentionally contains no vertex IDs. Claude must record
the real final-mesh support-loop/vertex IDs for shoulders, elbows, wrists, hips,
knees and ankles. Do not populate them by nearest-bone or nearest-surface inference.

## One-command capture

After Phase 5 is complete and the joint-support evidence exists:

```bat
RUN_ORIGINAL_V1_PHASE6_SURFACE.bat <rN> <authored-joint-support.json> <fresh-output-dir>
```

The orchestrator checks:

- live model branch and remote HEAD;
- clean working tree;
- Phase 5 complete;
- Blender availability;
- no conflicting Blender/optimiser process;
- sufficient local disk space;
- exact candidate Blend/manifest SHA;
- candidate is latest complete model state;
- joint-support file binds that same candidate.

It then performs, without saving the Blend:

1. raw schema-2 body snapshot;
2. existing raw surface audit;
3. evaluated Blender body capture;
4. combined Phase 6 surface-quality verification.

Outputs are written only to a fresh folder.

## Evaluated normals

`capture_original_v1_surface_quality_blender.py` records evaluated vertex/face
counts, current modifier-stack visibility and transformed vertex/polygon normal
lengths.

It reports exact IDs for invalid/non-finite/zero normals.

It also records Blender's custom-normal state when that API is available. If the
running Blender API cannot expose that state, the combined verifier keeps the
normals domain blocked instead of silently passing it.

A valid normal vector is not the same thing as attractive shading; owner
wire/surface review still remains real evidence.

## Evaluated self-intersection

The capture builds a BVH from the evaluated body surface and records every
non-adjacent intersecting face pair. Face pairs sharing an evaluated vertex are
excluded as ordinary adjacency.

For the final bare body Phase 6 surface, non-adjacent self-intersection remains a
blocking finding. The tool does not automatically repair it or hide it behind an
aggregate count.

## Authored joint support

The joint template declares twelve bilateral support locations:

- shoulders;
- elbows;
- wrists;
- hips;
- knees;
- ankles.

Each real joint-support record must provide:

- non-empty unique raw-mesh vertex IDs within the exact candidate's vertex range;
- exact required loaded poses;
- hashed real evidence for the support-loop record and loaded wire/surface views.

The verifier checks identity/coverage only. It cannot decide that the resulting
loop structure is visually or biomechanically good.

## Combined result

`scripts/original_v1_phase6_surface_quality.py` combines:

- raw manifold/winding/degenerate/symmetry evidence;
- evaluated normal evidence;
- evaluated self-intersection evidence;
- authored joint-support evidence;
- exact candidate identity.

It can report `EVIDENCE_COMPLETE` only when its objective findings are clear and
the joint-support contract is complete.

Even then:

- `phase_complete=false`;
- `production_approved=false`.

Phase 6 still requires the full package's topology/weight change audits,
deformation comparisons and actual wire/surface review before its official phase
exit packet can verify.

## Current boundary

Do not run this on r29 as a Phase 6 claim. The current project is still in Phase 3.
This tooling exists now only to reduce future Claude laptop setup and validation
work once Phases 4 and 5 genuinely pass.
