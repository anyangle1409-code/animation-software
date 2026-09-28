# Branch hygiene

## Authority

Only `work/standalone-first-party-audit-20260927` is the active first-party standalone development branch.

Branch existence does not make a branch authoritative. Follow `docs/PROJECT_AUTHORITY.md`.

## Deliberate keep set

- `main` — repository default/baseline; contained in the active branch.
- `work/standalone-first-party-audit-20260927` — active development branch.
- `archive/pre-makehuman-removal-20260928` — immutable recovery checkpoint for the exact pre-removal state at `502adedc9fd5c7ddbee1b74cd0472879de6fb047`; reference/recovery only, never a development source.
- `work/v15-deep-hand-rebuild-prep-20260925` — legacy V15f reference benchmark only; divergent and never a production source.

## Verified contained retirement set

On 2026-09-28 these branch tips were verified as ancestors of the active standalone branch, with zero commits missing from the active branch:

- `chatgpt/absolute-retarget-imports`
- `claude/home-gym-pt-animation-txux66`
- `codex/anatomical-reference-character`
- `codex/fix-dumbbell-grip-position`
- `work/self-sufficient-engine-integration-20260925`

They can be deleted without losing unique commits. Use the guarded cleanup script rather than deleting by hand:

```bat
CLEANUP_CONTAINED_BRANCHES.bat --apply
```

The script rechecks ancestry immediately before deletion and refuses any target that is no longer contained.

## Diverged historical branches

The remaining `codex-high-detail-candidate-*`, `work/current-source-self-review-*`, `work/generator-*`, `work/internal-reference-*`, `work/prompt-generation-*`, `work/reference-rebased-*`, and related September 25 branches currently contain unique commits relative to the active branch.

Do not delete them merely for tidiness until their unique endpoints have been intentionally archived or declared disposable.

They are nevertheless **non-authoritative** and should not be inspected during normal continuation work.

## Rule for future branches

Create a new branch only when isolation is genuinely required. At completion, record one of:

- merged/contained -> delete;
- reference benchmark -> retain and label;
- divergent experiment -> archive or explicitly discard.

Do not accumulate unnamed temporary branches as project state.
