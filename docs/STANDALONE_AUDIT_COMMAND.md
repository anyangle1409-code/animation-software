# Standalone audit — one command

Run from repository root:

```bat
node scripts\run-standalone-audit.mjs
```

This executes the prepared first-party audits and writes:

- `reports/third_party_dependency_audit.json`
- `reports/third_party_runtime_usage.json`
- `reports/first_party_marker_audit.json`
- `reports/legacy_character_coupling.json`
- `reports/external_runtime_resources.json`
- `reports/first_party_release_readiness.json`
- `reports/standalone_audit_summary.json`

The overall gate is **expected to fail during migration**. Preserve each report so blocker counts can be compared after every dependency/model migration stage.

After a production build, also run:

```bat
node scripts\audit-production-output.mjs dist
```

That scans the actual operational output for known third-party runtime/library fingerprints, remote URLs, package artefacts and prohibited legacy-character names.

A final standalone release requires both:
1. source/provenance release gates PASS;
2. production-output audit PASS.

Development-only tools/packages are outside the operational-product gate as long as they are absent from and unnecessary for the finished runtime.
