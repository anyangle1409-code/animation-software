# Repository instructions for Claude

Before changing code, read `README.md`, `docs/ARCHITECTURE.md`, and
`AI_CHANGELOG.md`.

- Keep this project isolated from the live Home Gym PT repository until the
  owner explicitly approves integration.
- Preserve the canonical bone names and the character-independent pose model.
- Use the standing dumbbell bicep curl as the first quality gate for character,
  hands, equipment, animation, and export changes.
- Work on a separate branch unless the owner explicitly requests `main`.
- Add or update tests for behavioural changes.
- Run `npm test`, `npm run typecheck`, and `npm run build` before handoff.
- Add a dated **Claude** entry to `AI_CHANGELOG.md` for every material change.
- Do not edit or remove Codex's log entries.
