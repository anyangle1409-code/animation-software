# Phase C Work handoff — dormant until V15 visual acceptance

Do not execute this handoff unless V15 has passed the visual anatomy gate.

Read `PHASE_C_GRIP_REFIT_PLAN.md`.

When activated:

1. Fetch the newest `chatgpt/absolute-retarget-imports` and record its HEAD.
2. Work in an isolated source candidate/worktree. Do not merge it into the mesh branch.
3. Use the accepted V15 dressed GLB as the real character.
4. Preserve the existing `homeGymPTMale` solved grip as a baseline.
5. Create a temporary versioned solution such as `homeGymPTMaleV15Candidate`.
6. Re-solve the **dumbbell** family against the accepted V15 hand:
   - per-digit MCP/PIP/DIP;
   - thumb opposition;
   - bounded handle-centre correction.
7. Hold wrist pose, exercise motion, equipment transforms, sockets, retargeting
   and the frozen hierarchy fixed.
8. Reject any solve that introduces a new body/equipment/technique/contact gate
   regression anywhere in the current exercise library.
9. Generate matched high-zoom baseline/candidate grip boards.
10. Stop for acceptance. Do not overwrite the old solution or promote automatically.

The current source's historical `-9 mm` handle-centre correction is evidence,
not a target. Re-measure it against V15 and the current library.
