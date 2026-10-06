# Animation Software → PT App export bridge

Status: prepared, fail-closed, no production character or exercise promoted.

The PT App already owns the consumer side: schema-v2 bundle validation, stable exercise-ID mapping, SHA verification, dry-run promotion, rollback and readiness reporting. This branch prepares the missing upstream producer boundary without changing the model branch or PT App runtime.

## Production bundle

Animation Software will emit a directory containing:

- `animation-export.manifest.json`
- one validated `.webm` or `.mp4` per exported exercise

The manifest contract is mirrored in `contracts/pt-app-animation-export-v2.schema.json`.

The builder refuses output unless `ORIGINAL_V1_PROMOTION_CONTRACT.json` is explicitly `approved_for_promotion`, pins an approved source commit and contains exact production character hashes. Therefore today's candidate model cannot accidentally enter PT App.

## Prepared command

`node scripts/build-pt-app-export-manifest.mjs <bundle-dir> <input.json>`

The input is renderer evidence. The builder computes the final media SHA itself; callers cannot supply/trust that hash.

## Still intentionally blocked

The deterministic video-render stage is not implemented here because it must be bound to the final approved ORIGINAL-v1 character, its deformation path, equipment, camera and render profile. Building that stage against the rejected candidate would risk encoding the wrong model assumptions.

Once ORIGINAL-v1 is approved, the shortest production path is:

validated exercise motion → approved character/equipment scene → deterministic first-party frame render → browser-playable video encode → manifest builder → PT-App validator/readiness → one-exercise dry-run promotion → PT regression/playback acceptance → deliberate apply.

Do not add a real-time 3D engine to PT App for this integration. The existing PT architecture consumes deterministic demonstration media and should remain unchanged unless a separately approved product decision changes it.
