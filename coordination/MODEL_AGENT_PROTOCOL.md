# ORIGINAL-v1 Claude ↔ GPT model protocol

## Ownership
- **Claude/Blender is the sole model author while a candidate is active.** It owns the .blend, topology, weights, armature mechanics and deformation authoring.
- **GPT/Work is the independent validator.** It may run/read tests, movement sweeps, renders and measurements and may change validation/integration code, but MUST NOT modify Claude's active candidate geometry, weights or armature.
- Never edit the same .blend concurrently. Never work from main. Re-read live branch HEAD before every handoff.

## State machine
`idle -> candidate_ready -> validating -> failed|passed -> repairing|freeze_ready`.

Claude publishes `coordination/MODEL_CANDIDATE_READY.json` only after saving and committing a candidate and its evidence. GPT validates exactly that commit/candidate and publishes exactly one of:
- `coordination/MODEL_CANDIDATE_FAILURES.json`
- `coordination/MODEL_CANDIDATE_PASS.json`

Every response must echo candidate_id, candidate_commit and candidate_sha256. A mismatch is stale and MUST fail closed.

## Current priority
Phase 3A shoulder foundation rearchitecture. r96 is rejected evidence, not a production candidate. Fix causal layers in this order: skeleton mechanics -> topology -> weights -> connected anatomical deformation -> minimal residual correctives. Numerical success cannot override visible anatomical failure.

## Claude loop
1. Pull/read live branch and latest validator response.
2. If FAIL, repair the stated causal layer in Blender; do not patch around it with unrelated correctives.
3. Commit candidate + evidence.
4. Write candidate-ready record last, bound to that commit/hash.
5. Continue only model-author work; do not mark PASS yourself.

## GPT loop
1. Pull/read live branch and candidate-ready record.
2. Verify identity/hash/commit before testing.
3. Run the movement matrix and machine/visual gates available in repo.
4. Write PASS only when all required gates pass. Otherwise write ranked failures with evidence and required next causal layer.
5. Never promote/freeze the model itself.

## Human authority
Production freeze remains a deliberate release decision. Neither agent may infer approval from silence, a green numeric score, or a single good render.
