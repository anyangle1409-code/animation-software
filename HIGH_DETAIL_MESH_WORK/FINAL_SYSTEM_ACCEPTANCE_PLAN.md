# Final system acceptance — self-sufficient exercise studio

## Gate

Run only after:
- final character geometry/appearance/source-rig mapping is accepted;
- Phase G movement activation is accepted;
- Phase H prompt-family certification is complete for the intended release scope;
- the final character GLB and source branch are explicitly identified.

This gate does not fix anything. It only proves the integrated system or stops.

## Required release state

For full current-library autonomy:
- all 16 existing family builders are prompt-certified;
- all 28 current library exercises remain valid;
- canonical prompts reproduce the family/library behaviour;
- unsupported variants are refused rather than approximated;
- final character is the one used by character-dependent checks;
- source suite, typecheck and production build are clean;
- frozen canonical hierarchy remains `hgpt_canonical_v3`;
- source character keeps its reviewed rig/helpers/weights and maps cleanly through
  the retarget path;
- final grip solutions are certified;
- palm/thumb/scapula activation has no unintended zero-state regression;
- generated candidates still require explicit review/promotion.

## One isolated acceptance run

Use:

`RUN_FINAL_SYSTEM_ACCEPTANCE.bat final_character.glb`

The prepared runner:
1. hashes the supplied final character;
2. fetches the newest `chatgpt/absolute-retarget-imports`;
3. creates a detached disposable worktree;
4. installs/reuses dependencies without touching the mesh branch;
5. runs the source suite in its normal reference configuration;
6. runs typecheck;
7. runs the production build;
8. runs the full suite again with `REAL_CHARACTER_GLB` pointed at the final character;
9. runs the generator parse/generate tests separately for readable logs;
10. runs the focused real-character collision/contact/retarget gate set;
11. runs the prompt-family coverage audit against that exact source checkout;
12. requires every family in the certification manifest to be CERTIFIED unless
    `--allow-blocked` is deliberately supplied;
13. writes one JSON + Markdown acceptance report with exact source HEAD/commit,
    suite counts, character hash and failing stage;
14. removes the disposable worktree.

It never merges or promotes anything.

## Failure rule

A final acceptance failure is not fixed by loosening a check.

Route it back to the owning phase:
- geometry/contact -> V15/Phase E;
- grip -> Phase C;
- material-only invariant -> Phase D;
- source-rig mapping/weights -> Phase F;
- palm/thumb/scapula motion -> Phase G;
- parser/adapter/correction/review generation -> Phase H;
- build/typecheck/general source regression -> source engineering.

## Release record

Keep the final acceptance report beside:
- final dressed/bare character hashes;
- source commit/revert point;
- prompt certification manifest;
- final generated review corpus;
- any explicitly blocked family if a deliberately partial release is made.

A passing final gate means the current system is internally verified. It does not
mean every conceivable exercise outside the certified family/equipment model can
be generated.
