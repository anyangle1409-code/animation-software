# Work autonomous continuation prompt

> Open the latest `codex-high-detail-candidate-v6-knee-review-20260922` branch. Read `HIGH_DETAIL_MESH_WORK/CURRENT_STATE.md`, `RIG_55_BASELINE.md` and `WORK_START_HERE.md` first.
>
> Run `HIGH_DETAIL_MESH_WORK/RESUME_WORK.bat`. It must prepare the isolated `validation_55` tree from exact source commit `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`. Do not validate new candidates only against the older 53-bone snapshot.
>
> Create each fresh editable candidate with `START_CANDIDATE.bat <version>` so V6 remains untouched.
>
> Continue autonomously in this order unless visual evidence makes a narrower local correction necessary:
> 1. true medial-knee retopology and anatomical knee shaping;
> 2. realistic hand/finger/thumb/palm/wrist geometry while preserving the push-up floor-contact guard;
> 3. skin/material refinement;
> 4. if time remains, shoulder/back/chest/armpit topology/geometry preparation for the confirmed scapula structure.
>
> The canonical shoulder girdle is now settled at 55 bones. Scapulae remain neutral, rhythm is off, and the current production GLB itself has no newly painted scapula weights. Do not enable scapular rhythm or claim final scapula weighting during this mesh-only pass.
>
> Do not finalise hand weights until the palm-arch/thumb-twist decision is settled. Do not assume forearm twist distribution or carrying angle were settled by the scapula commit.
>
> Save the edited Blend file and export the dressed GLB using the same version suffix. Run `FINISH_CANDIDATE.bat <version> <task>`. Reject failures rather than loosening thresholds or changing accepted exercise mechanics.
>
> Preserve every prior candidate and keep working without asking for routine implementation decisions. Stop only for a genuine structural decision or a regression that would require changing accepted mechanics. Do not merge or promote without explicit approval.
