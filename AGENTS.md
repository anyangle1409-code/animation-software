# Agent project instructions

Keep agentic usage low. Treat repository handoffs/status files as memory instead
of reconstructing history from chat or scanning the entire repository.

For current V15f work, begin with:
- `HIGH_DETAIL_MESH_WORK/AI_USAGE_BUDGET.md`
- `HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md` if present
- `HIGH_DETAIL_MESH_WORK/WORK_RESUME_AFTER_LIMIT.md`
- `HIGH_DETAIL_MESH_WORK/V15F_STATUS.bat`

Use the smallest proving test/audit first. Do not run the full suite for a local
failure until focused checks pass.

Do not spend agent allowance on deterministic work already covered by scripts,
reports, status tools, visual-board generators or the V15f safe runner.

Do not modify/merge `chatgpt/absolute-retarget-imports` from the mesh candidate
workflow.

Reserve expensive reasoning for genuinely ambiguous architecture, difficult
debugging or visual/anatomical decisions. Keep routine command execution concise.

Save/checkpoint and update repo handoff state before a usage/context limit.
