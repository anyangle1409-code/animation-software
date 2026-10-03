# Phase 3A — local axilla-pit repair after r55

Status: PREPARED · 2026-10-03

## Purpose

Remove the remaining visible armpit/axilla sliver tearing and lateral-torso crumple from the current r55 experimental candidate without reopening the locked skeleton, changing the P3a stress-pose definition, relaxing any gate, or broadening the edit into unrelated anatomy.

r55 is an execution parent only. It is **not** production-approved and must not be frozen as-is merely because the development-blocker count is zero.

Current identity:

- candidate: `r55`
- SHA-256: `ccaef8ba1fdde161b9e5769175b7576eeb88d96f4c99e41cdd0147041a93bbd7`
- development failures: 0
- strict severity regressions versus P3B1: 31
- corrective solution: `corr_v8.npz`
- locked rig: `hgpt_canonical_v4_original_rev2c` / 67 bones
- frozen stress-pose definition: P3a

## Evidence-led diagnosis

The remaining defect is local, not a general rig failure.

- The broad r45-r48 tent-flap problem was reduced by the generic elevation-driven corrective.
- r55 continuous-arc evidence keeps volume approximately 0.998-1.043, has no left/right mismatch, and reduces maximum lateral-torso drift relative to r48.
- The worst press-top edges are <= about 3.65 rather than an extreme stretch spike.
- The visible residual is a thin triangular sliver/fold at the axilla pit plus local crumpling.
- Self-intersection severity remains materially higher than P3B1 in several overhead/pull-up poses, so zero development blockers is not sufficient for a strict freeze.

Primary evidence:

- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r55_comparison_vs_P3B1.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r55_comparison_vs_r48.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/shoulder_corrective_20261002/r55_arc.json`
- `ORIGINAL_V1_WORK/candidates/repair_checks/shoulder_corrective_20261002/r55_press_top_worst_edges.json`
- `ORIGINAL_V1_WORK/candidates/review_images/shoulder_corrective_20261002/`

## Hard locks

Do not change:

1. rev2c skeleton structure, bind matrices or bone placement.
2. P3a stress-pose construction.
3. deformation thresholds or comparison tolerances.
4. P3B1 or any historical pinned baseline.
5. unrelated hand, wrist, hip, knee, foot or face geometry/weights.
6. first-party boundary: no copied third-party/legacy vertices, topology, weights or implementation data.

## Candidate numbering

Before authoring, check the live branch. Use the next collision-free revision after the highest complete/partial manifest. If r56 does not exist, use r56; otherwise advance monotonically. Never replace an existing revision.

## Step A — declare the pit mask before editing

The repository now has a read-only deterministic preflight. From a clean checkout with the verified source candidate present, run:

```bat
RUN_ORIGINAL_V1_AXILLA_PIT_PREP.bat r55 r56
```

Use the next collision-free target revision if `r56` already exists. The runner never saves the Blend. It samples the full shoulder arcs, ranks signed face-area collapse/orientation reversal, mirror-closes the worst local faces, expands one topological ring, and writes both the audit and the declaration before any edit. It aborts if the default declaration exceeds 180 left-owned vertices so a local repair cannot silently become another broad shoulder edit.

It creates:

`ORIGINAL_V1_WORK/candidates/repair_preparation/<rev>_axilla_pit_declared/`

including `face_collapse_audit.json`, `face_collapse_audit.md`, and `axilla_pit_mask_declared_before_edit.json`.

The declaration must include:

- exact candidate parent + SHA-256;
- explicit left-side vertex IDs;
- exact mirrored right-side IDs;
- rest-space bounding box;
- connected triangle IDs / one-ring adjacency;
- region labels and top bone weights;
- a hash of the ordered ID set;
- allowed mutation type.

Start from the actual triangles that form the visible r55 sliver/crumple. Expand only one topological ring at a time until a stable local solve is possible. The expected order of magnitude is tens of vertices per side, not the full 1491-vertex shoulder-corrective mask.

## Step B — first attempt: local weight/corrective repair only

Prefer a local first-party weight/corrective edit before changing topology.

The source Blend already contains the r55 corrective, so the next solve is an **incremental delta from zero** on top of r55. Do **not** pass `corr_v8.npz` as `--init`: corr_v8 was solved against r48 and that would double-apply the correction. Cross-source `--init` is now rejected.

The optimizer now supports `--mask-file <declaration.json>` to restrict the solve to the committed local vertices. It also supports:

- `--w-fold`: dihedral fold barrier;
- `--w-area`: signed face-area/orientation barrier;
- `--area-min`: minimum projected area ratio versus the uncorrected pose;
- `--w-prox`: no-new-contact barrier.

The face-area barrier is disabled by default, so historical results remain reproducible. For the new experiment, enable it explicitly and record every parameter in the solution manifest.

The signed-area term must stop a triangle from becoming a near-zero-area sliver or flipping orientation even when all individual edge lengths remain inside the existing edge gates. Its reference is the same-pose **uncorrected LBS surface**, not r55's already-corrected surface, so it can actively reopen an existing r55 sliver rather than only prevent further collapse.

Do not choose parameter values merely to make the aggregate development gate pass; r55 already passes that gate. Choose them to remove the visible fold while avoiding new severity regressions.

### Deterministic local solve/apply

After Step A:

```bat
RUN_ORIGINAL_V1_AXILLA_PIT_SOLVE.bat r55 r56 <w-area> [area-min] [w-fold] [w-prox]
```

The area weight is explicit rather than silently tuned. This writes an incremental solution only and does not save a Blend. It also writes `incremental_corrective_solution_report.json` with per-pose before/after edge, torso-drift, signed-area, below-threshold-face and flipped-face metrics, so a parameter trial can be rejected before creating a new Blend.

After inspecting that solve:

```bat
RUN_ORIGINAL_V1_AXILLA_PIT_APPLY.bat r55 r56
```

The apply step verifies source SHA, declaration, mirror mapping and parent runtime spec; changes only the existing shoulder corrective keys at declared vertices; preserves Basis, weights, topology and bones; and emits a full updated runtime corrective spec.

## Step C — topology only if the local weight/corrective attempt is insufficient

A topology edit is permitted only after a committed result shows that the declared local weight/corrective solve cannot remove the fold without a new regression.

If required:

- remain inside a separately declared axilla-pit topology mask;
- preserve the outer boundary loop exactly;
- use only independently authored local geometry;
- rebuild/revalidate shape-key correspondence deterministically;
- emit before/after vertex/face counts and a change audit;
- prove no unrelated topology moved.

Do not use a broad remesh.

## Required acceptance evidence for each new candidate

Run the normal full evidence suite plus:

1. comparison versus P3B1;
2. comparison versus r55;
3. full remaining diagnostics;
4. continuous shoulder arc audit with shape keys active;
5. face-area/orientation audit for all triangles touching the declared pit mask;
6. self-intersection counts for press_top, press_top_rhythm, pullup_hang, pullup_hang_rhythm, pullup_bar and pullup_top;
7. left/right symmetry;
8. real Blender review renders from front, side and three-quarter for press_top, press_top_rhythm, pullup_hang and pullup_hang_rhythm.

## Promotion rule

A candidate may replace r55 as the experimental continuation only when:

- development failures remain 0;
- the visible axilla sliver/crumple is removed or materially reduced in the real renders;
- there is no new strict severity regression versus r55;
- continuous-arc behaviour remains smooth with no face inversion;
- the declared-mask audit proves the edit stayed local.

Phase 4 is still blocked while unresolved strict regressions remain. A zero-blocker candidate is not automatically a freeze candidate.
