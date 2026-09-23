Read CURRENT_STATE.md and WORK_START_HERE.md first when resuming on the Blender laptop.

V6 knee seam is the latest reviewed geometry baseline. Read REVIEW_V6_KNEE_SEAM.md, REVIEW_V5_HANDS.md and REVIEW_V4B.md as supporting history.

Next autonomous modelling order:
1. retopologize the still-open medial-knee strips into connected anatomical loops and reshape the pointed overhang;
2. model realistic finger/thumb/palm/wrist forms on V5/V6's contact-safe topology;
3. refine skin materials.

Use START_CANDIDATE.bat <version> to create a fresh candidate working file. After editing and exporting the dressed GLB, use FINISH_CANDIDATE.bat <version> <task> so the bare variant, guards, task-specific audit, visual review pack and checkpoint are handled automatically.

Final shoulder/chest/back/armpit weighting must wait for the separately audited scapula-capable canonical rig to be confirmed. Keep the existing rig/exercises/grip/contact behavior and all production assets untouched. Do not merge or promote.
