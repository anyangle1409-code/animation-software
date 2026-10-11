# G1d first-party source GLB normals: native strict decoder and batch integration

**11 October 2026 · independent LANE G staged software · source geometry only, NOT production skin-lighting parity**

This branch extends the previously verified native WebGL2/GLB stack through G2 GPU palettes (PRs #41, #42, #43, #46, #49, #51, #53, #55). A prior partial agent created only `src/viewer/firstPartyGlbSourceNormals.mjs` at PR #57 before connector writes stopped; that source is preserved without rewriting it. This checkpoint completes source-level opt-in batch parsing, fixtures, adversarial tests and CI.

## What is implemented

The project-original `readRestrictedGlbNormals` accepts only glTF FLOAT VEC3 per-vertex source normals from an embedded BIN buffer with strict accessor alignment, byte stride/bounds and vertex-count matching, finite values, approximately unit length, no sparse or unknown accessor metadata and no implicit coordinate, handedness or normal correction.

The `parseRestrictedBatchedSkinnedGlb` adapter now accepts explicit `allowSourceNormals:true`. Every mesh and primitive must have source NORMAL and independently pass the source decoder; source normals are returned in each batch's `sourceNormals` typed Float32Array alongside original positions, per-vertex weights and optional source UV0. All geometry and bone data still go through the unchanged original strict GLB parser and retain original order. Legacy default behaviour unchanged: original normal data remains ignored until opting in, and existing CPU triangulated normals continue to be recomputed on deformation.

Project-authored GLB fixtures provide two to four independent primitives with deliberately DIFFERENT +Z and +Y normals, preventing a default constant normal from passing. Unit tests refuse invalid second source normals, zero/nonfinite vectors, wrong normal type/count/normalization, malformed binary pointers, unknown GLB metadata, hidden image/texture/morph content and invalid opt-in. Reproducible browser and full editor typecheck/build CI are committed.

## Not completed

**G1d parses verified source NORMAL attributes ONLY. It does NOT automatically use them for correct GPU normal skinning, tangent transforms, physical lighting, character skin, PBR materials, muscle deformation or actual original model acceptance.** Those are separate G2c tests. No clinical source evidence is edited, and anatomy readiness 0 READY / 9 PARTIAL / 3 BLOCKED remains independent and Work-owned. Normal production editor still depends on Three.js and the PT-App still has temporary clips.

Every new GLB binary fixture is synthetically authored in-repo with no original human source/model, patient CT, image texture or third-party package. The branches remain DRAFT until independently verified.

## Next

Read CI, fix any negative-fixture failure, record actual tested commit, then develop original first-party GPU skin normal transforms with **GPU transform-feedback normals versus independently computed CPU normal palette** and real browser light/pixel tests. Do not claim physically based shading or deformations verified solely by source importer.
