# Work autonomous continuation prompt

Use this text when handing the mesh candidate back to Work on the Blender laptop.

> Open the latest `codex-high-detail-candidate-v6-knee-review-20260922` branch. Read `HIGH_DETAIL_MESH_WORK/CURRENT_STATE.md` and `WORK_START_HERE.md` first, then follow their instruction precedence.
>
> Run `HIGH_DETAIL_MESH_WORK/RESUME_WORK.bat`. Create each fresh editable candidate with `START_CANDIDATE.bat <version>` so V6 remains untouched and the AUDIT selection groups are available.
>
> Continue autonomously in this order while the final canonical rig is being completed separately:
> 1. true medial-knee retopology into connected anatomical joint loops, including patella/tendon/medial-knee shape;
> 2. realistic finger/thumb/palm/wrist anatomy while preserving the push-up floor-contact guard;
> 3. skin/material refinement.
>
> Do not finalise shoulder/chest/back/armpit weights or scapular deformation against the old hierarchy. Do not change the frozen rig, exercises, IK, grips, contacts, equipment transforms, production assets or `bundled.ts`.
>
> Save the edited Blend file and export the dressed GLB using the same version suffix. Then run `FINISH_CANDIDATE.bat <version> <task>`, where task is `knee`, `hand` or `material`. Let that workflow create the bare GLB if needed, run the structural/runtime gates, perform the task-specific audit, render the review pack and write the checkpoint/review scaffold.
>
> Reject a failed candidate rather than loosening thresholds or altering accepted mechanics. Preserve every prior candidate. Keep working without asking me for routine implementation decisions. Stop only for a genuine structural decision, an unsatisfied guard that would require changing accepted mechanics, or arrival of the final canonical rig.
>
> For an accepted checkpoint, complete the generated review note with exact modelling changes, validation totals, hashes and remaining limitations. Do not merge or promote without explicit approval.
