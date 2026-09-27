# Final first-party release audit

After building the final production output:

```bat
npm run audit:release
```

This requires all of the following automated gates:
1. standalone source/provenance audit;
2. production-output third-party audit;
3. deny-by-default production allowlist audit.

The release allowlist is intentionally empty during migration, so the final
release gate cannot accidentally pass early.

Before release, populate `RELEASE_ASSET_ALLOWLIST.json` only with production
paths that have first-party provenance.

Example shape only (do not add until verified):
- `index.html`
- `assets/**`
- `characters/HomeGymPT_Male_ORIGINAL_v1.glb`

Even an allowlisted file must still pass the production-output third-party scan.

The automated audit is followed by the separate offline acceptance in:
`docs/OFFLINE_STANDALONE_ACCEPTANCE.md`.
