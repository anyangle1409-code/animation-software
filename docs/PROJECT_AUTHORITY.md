# Project authority

## Purpose

This file defines which project information is authoritative for all AI agents and human work on the Home Gym PT standalone transition. The repository is the authority; no model-specific memory, chat transcript, historical branch, or old handoff overrides it.

## Current active branch

`work/standalone-first-party-audit-20260927`

Development for the first-party standalone transition must continue on this branch unless `docs/CURRENT_HANDOFF.md` explicitly changes the branch.

## Required read order

For a fresh GPT, Claude, Codex, or human session, read only these first:

1. `docs/CURRENT_HANDOFF.md`
2. `docs/AI_OPERATING_CONTRACT.md`
3. `docs/DECISION_LOG.md`
4. `FIRST_PARTY_COMPONENT_MANIFEST.json`

Then read only the task-specific document named by `CURRENT_HANDOFF.md`.

Do not reconstruct project state by reading historical documents or branches.

## Authority precedence

When information conflicts, use this order:

1. current source code plus executable tests/guards;
2. `docs/CURRENT_HANDOFF.md`;
3. `docs/DECISION_LOG.md`;
4. `docs/AI_OPERATING_CONTRACT.md`;
5. current task-specific technical handoff explicitly named by `CURRENT_HANDOFF.md`;
6. `FIRST_PARTY_COMPONENT_MANIFEST.json` and current machine-generated audit reports;
7. supporting progress/plan documents;
8. historical branches, old handoffs, legacy assets, review renders, and chat history.

A lower item must never silently override a higher item.

## Current task-specific authorities

- Runtime migration: `docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`
- Physical browser/device parity: `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`
- ORIGINAL v1 Blender O2 work: `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`
- Clean-room character requirements: `docs/ORIGINAL_V1_CLEAN_ROOM_CHARACTER_BRIEF.md`
- Canonical v4 rig: `docs/CANONICAL_V4_ORIGINAL_RIG_PLAN.md` and `docs/CANONICAL_V4_ORIGINAL_DIMENSIONS.md`
- Provenance: `docs/FIRST_PARTY_PROVENANCE_FINDINGS_2026-09-27.md` and `docs/THIRD_PARTY_REFERENCE_ONLY.md`
- Release gate: `RELEASE_ASSET_ALLOWLIST.json`, `FIRST_PARTY_COMPONENT_MANIFEST.json`, and `npm run audit:release`

## Historical material rule

Historical documents may contain useful measurements and reasoning, but they are not instructions unless the current handoff explicitly names them.

Legacy V5-V15f/CORNER_FINAL, old MakeHuman-derived body data, rejected candidate branches, old renders, and removed review bundles are reference-only. They may not become production inputs.

## Branch rule

Only the active standalone branch is a development authority. `main`, `chatgpt/absolute-retarget-imports`, the V15f branch, Codex candidate branches, prompt-generation branches, self-review branches, and internal-reference branches are non-authoritative unless `CURRENT_HANDOFF.md` explicitly opens one for a named comparison.

Do not inspect another branch "just in case".

## Verification rule

A written claim is not a pass condition. Where an executable gate exists, the executable result is authoritative.

Start every laptop session with:

```bat
STANDALONE_STATUS.bat
```

Do not weaken or bypass a failing gate to make the dependency or provenance counts look cleaner.
