# Work autonomous continuation prompt

> Open the latest `codex-high-detail-candidate-v6-knee-review-20260922` branch. Read `HIGH_DETAIL_MESH_WORK/CURRENT_STATE.md`, `RIG_63_FREEZE.md` and `WORK_START_HERE.md` first.
>
> Run `HIGH_DETAIL_MESH_WORK/RESUME_WORK.bat`. It must prepare the isolated `validation_63` tree from current runtime source commit `614033b256d869230ea273522620467401b0bc71` (frozen hierarchy remains `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`). Do not validate new candidates only against the older 53-bone snapshot.
>
> Create each fresh editable candidate with `START_CANDIDATE.bat <version>` so V6 remains untouched.
>
> Continue autonomously in this order unless visual evidence makes a narrower local correction necessary:
> 1. true medial-knee retopology and anatomical knee shaping;
> 2. realistic hand/finger/thumb/palm/wrist geometry while preserving the push-up floor-contact guard;
> 3. skin/material refinement;
> 4. if time remains, shoulder/back/chest/armpit topology/geometry preparation for the confirmed scapula structure.
>
> The canonical hierarchy is structurally frozen at 63 bones. Scapulae remain neutral, rhythm is off, and the current production GLB itself has no newly painted scapula weights. Do not enable scapular rhythm or claim final scapula weighting during this mesh-only pass.
>
> Do not change the frozen canonical hierarchy. Mirrored hand roll is fixed in 614033b. Treat the widened curl finger-wrap gap (36°→66°) as a grip/weight-review item, and production palm-bone placement as asset/binding work.
>
> Save the edited Blend file and export the dressed GLB using the same version suffix. Run `FINISH_CANDIDATE.bat <version> <task>`. Reject failures rather than loosening thresholds or changing accepted exercise mechanics.
>
> Preserve every prior candidate and keep working without asking for routine implementation decisions. Stop only for a genuine structural decision or a regression that would require changing accepted mechanics. Do not merge or promote without explicit approval.
