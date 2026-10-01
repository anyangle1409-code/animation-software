# ORIGINAL v1 shared GPT / Claude pickup

Work only on `claude/original-v1-blender-o2-20260929`. Before edits read LIVE branch
HEAD and preserve newer commits. This page is execution navigation; the master
plan is the authoritative roadmap and O4 handoff supplies the repair evidence.

Read in order:
1. `docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md`
2. `ORIGINAL_V1_HIGH_DETAIL_STATUS.json` / `docs/ORIGINAL_V1_DAILY_STATUS.md`
3. `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`
4. The work package selected by `scripts/select_original_v1_next_action.py`.

## Current exact laptop sequence

```bat
RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
RUN_ORIGINAL_V1_NEXT.bat
RUN_ORIGINAL_V1_R30.bat
```

Preflight/NEXT are read-only and print the task; NEXT does not silently launch
Blender. Run r30 only if preflight says SAFE TO START and selector says RUN r30.
If files already exist, inspect partial/new work; never delete it to obtain green.
Connect AC for the long solve/evidence run. Battery/runtime information may be
unknown; preflight never invents availability or completion time.

After r30 completes:
- Read full_r30 trial summary and R2/r29/r28 comparisons; trade-off is experimental.
- Run `RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r30` read-only if r30 is the
  verified diagnostic candidate. If rejected, diagnose the previous valid candidate.
- Collect real review images using source manifests. Record owner_review pending;
  publish and continue safe work. Do not wait for routine visual approval.
- Commit/push candidate manifests, reports, comparison/solution evidence and
  review folders. Re-read live branch before publishing; no force push.
- Run `python scripts/build_original_v1_daily_status.py`, then `--check`.
  Update O4 handoff and the ledger/dashboard in the same checkpoint.
- Record chosen experimental continuation under
  `ORIGINAL_V1_PRODUCTION_CONTROL.json:continuation_decisions`, keyed by revision
  with candidate_sha256, reason, comparison evidence references and chosen parent.
  This records worker execution lineage, not owner acceptance or baseline promotion.
- Run selector again: wrist → grip/thumb → lunge. If frozen rig/pose change is
  needed, record the defect and continue independent safe diagnostics/doc tasks.

## State and historical evidence

Production control recomputes full required coverage, grip and comparator results,
checks frozen input hashes, retains rejected candidates and refuses contradictory
or newer incomplete state. Foundation phases derive from the existing verified
R2/export status gates. Its 54/133 failures describe R2, not the 7-failure r29 state.
Earlier r20 has historical 14-pose coverage; it remains in the ledger but cannot
be selected as the latest complete 15-pose state. Intermediate r29a has geometry
metadata, not a completed full-evidence candidate. Missing metrics are null.

A future phase exit record is keyed by phase in phase_completion_records and
contains candidate_sha256 plus an evidence path/SHA reference. The exit report
must say PASS for that same candidate and document the master plan's exit checks.
Records are never inferred from a candidate's name or optimisation score. Phase 4
requires zero failures and resolved strict regressions. Phase 12 is deliberately
reserved for the separate final promotion workflow, never this generator.

## Known validation boundaries

The cloud prepares/tests Python tooling and checks committed reports/GLBs. It
cannot validate the local Windows battery/process APIs, render Blender candidates,
inspect unavailable local .blend files, or run real animation integration here.
Blender-facing additions are capture/source metadata and read-only snapshot tools;
no rest pose, stress pose, candidate geometry/weights or threshold is changed.

Full milestone rear/anatomy views remain a later capture requirement; the existing
17-view repair set is a compact snapshot only. Earlier renders without capture
manifests remain historical; regenerate verified evidence into a fresh label rather
than relabelling them. The project requires zero third-party shipped runtime/assets;
existing stock Blender/Python authoring tools are development tools, not content.
