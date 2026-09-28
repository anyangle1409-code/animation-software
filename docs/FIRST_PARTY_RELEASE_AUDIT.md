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

The release matcher interprets `**/` as zero or more directories, so a denial such as `**/*.blend` catches both `old.blend` at package root and `nested/old.blend`. A fixture test pins this behavior.

The release gate also rejects symbolic links (including links to files outside the package) and refuses a policy whose mode is not exactly `deny_by_default`, even when its approved paths otherwise match. Focused fixtures pin both cases.
