# AI Change Log

This file is the shared record of changes made by Codex and Claude. Both
assistants must add an entry in the **Unreleased** section whenever they change
code, tests, documentation, assets, exercise definitions, or repository
configuration.

Do not rewrite another assistant's entry. When work is merged, move its entry
under a dated release heading and add the commit or pull-request link.

## Unreleased

### Codex — 2026-09-08 — `codex/character-pipeline-foundation`

Purpose: make the imported-character path usable without changing the live Home
Gym PT application.

- Added export of the selected imported GLB character with the exercise clip
  baked onto its mapped bones.
- Made exported and preview equipment follow the retargeted character's hand
  positions and anatomical hand frames.
- Moved imported-character root translation and rotation to the character scene
  root, avoiding world/local hip-transform errors.
- Restored imported scene-root transforms when resetting a character.
- Reused a saved mapping automatically when the same character file is imported
  again, while discarding references to bones no longer present.
- Added manual mapping controls for every optional bone and all 30 finger bones.
- Prevented imported-character export until every required body bone is mapped.
- Added regression tests for root motion, retargeted equipment placement, and
  imported-character GLB export.

Verification: all 80 tests passed; `npm run typecheck` and `npm run build`
completed successfully.

## Baseline history

### Claude Opus 5 — 2026-09-08 — commit `287f72c6`

Created the initial Home Gym PT Animation Studio: canonical 53-bone rig,
forward kinematics, analytic IK, contact locks, equipment library, exercise
definitions, deterministic animation generation, technique validation, muscle
display, character retargeting, editor UI, and GLB/JSON export. Added the bicep
curl, push-up and bodyweight-squat proofs plus the original 77-test suite.

The repository commit explicitly records Claude as co-author and includes its
Claude session reference.

### Repository owner — 2026-09-07 — commit `df07dced`

Created the repository with the initial commit.

## Required entry format

```markdown
### Codex|Claude — YYYY-MM-DD — branch or commit

Purpose: one sentence.

- Concrete change and affected area.
- Concrete change and affected area.

Verification: commands run, or `not run` with the reason.
```
