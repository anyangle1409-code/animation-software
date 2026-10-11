# G4f — small, 18-mesh Blender shoulder PILOT diagnostic intake (not a release importer)

11 October 2026. Chat/G lane; stacked ONLY on G4e SHA-bound textured handoff PR #67.

Work's separate authored W1 shoulder draft PR #68 exports a diagnostic GLB with 18 meshes/18 primitives/6 skin joints (reported ~281 kB), whereas the standard first-party importer explicitly limits 1–4 meshes and 2–8 primitives. **Do not change the source skeleton or collapse anatomical shapes to satisfy that historical renderer budget.**

This patch adds manifest `glb.layout: "pilot"` with exact existing G4 SHA/rig/rest/laterality/rights declaration. It opts into `allowProvisionalPilot:true` on the batched parser, which accepts up to 24 meshes/24 primitives/200 nodes and **at most 1 MiB** of complete source GLB, with the same total 250,000 vertices, strict single-skin, identity-root mesh nodes and exact per-primitive importer/bind checks. PNG textures are intentionally unsupported in pilot mode. The old `single` and `batched` layouts, GLB size/type checks, and their ordinary mesh/primitive limits remain unchanged.

The diagnostic test supplies an actual complete *synthetic* 18-mesh/two-joint GLB, asserts all mesh identities and numerical rest binds survive, asserts byte immutability and false production/anatomical/source-frame gates, and verifies legacy rejection plus malicious source rejection. This **does not** claim that Work's privately generated W1 GLB is accepted: a real Work file still requires direct exact-asset SHA/bind testing, and Work's separate Z-up/row-major native pose records must be explicitly converted/verified against Y-up/column-major glTF world transforms. No bone positions, joint curves, model geometry or medical sources are changed. The general GPU renderer may still enforce an 8-draw limit; this is an isolated `GLB decode + rig preflight` step, not an 18-mesh human animation preview.

Run:
```
node --test tests/firstPartyProvisionalPilotIntake.test.mjs tests/firstPartyGlbSkinnedBatches.test.mjs tests/firstPartyPrototypeModelHandoff.test.mjs tests/firstPartyTexturedOriginalModelHandoff.test.mjs
```
