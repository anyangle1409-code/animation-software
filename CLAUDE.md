# Claude Code project instructions

Keep token/usage consumption low. The repository is the project memory.

Before work:
1. Read `HIGH_DETAIL_MESH_WORK/AI_USAGE_BUDGET.md`.
2. Read `HIGH_DETAIL_MESH_WORK/CLAUDE_LOW_USAGE_HANDOFF.md`.
3. For current V15f state, read `HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md`
   if present; otherwise run/read `HIGH_DETAIL_MESH_WORK/V15F_STATUS.bat`.

Do not scan historical hand documents or the whole repository unless a current
failure explicitly requires them.

Use bare file paths when asking/read-targeting files rather than injecting large
files unnecessarily.

Use focused tests first. Run the full suite only after focused checks pass.

Prefer direct work over subagents for simple/single-file tasks. Do not use web
search or unrelated tools unless the task requires them.

Model/effort:
- routine implementation/mechanical work: use a cost-efficient available model;
- hard architecture/debugging only: use the strongest model;
- lower effort/extended thinking for routine work.

Do not duplicate GPT Work's Blender GUI task. Claude's role is narrow source-code
work, one-report analysis, or independent second opinions.

Never modify or merge `chatgpt/absolute-retarget-imports` while working on the
mesh-prep branch unless the user explicitly changes that rule.

At task completion, verify with the smallest relevant test, write durable state
to the repo, and stop. Do not invent extra work just to consume the session.
