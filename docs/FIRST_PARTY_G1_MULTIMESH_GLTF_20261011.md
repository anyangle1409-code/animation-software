# G1 — First-party bounded GLB multi-mesh and multi-primitive diagnostic

**11 October 2026 · Independent Lane G software work · DRAFT · Not a finished human body renderer**

## Scope and ownership

Stacked onto independently tested [PR #46](https://github.com/anyangle1409-code/animation-software/pull/46) and preceding first-party GLB/skin GPU stages (#43/#42/#41). This branch only modifies original first-party GPU renderer, compatible first-party GLB batch adapter, project-owned synthetic fixtures, and CI. It does **not** edit Work PR #26, private CT records, Blender, canonical proportions, c001–c004, a003, skeleton owner policy, original body, exercise definitions, existing PT-App shell or third-party temporary videos.

### Implemented

1. `src/viewer/firstPartyGlbSkinnedBatches.mjs`: multi-mesh/multi-primitive GLB compatibility **data adapter**. Allows 1–4 meshes, 2–8 total indexed TRIANGLES parts, one shared explicit skin, one source scene, one direct identity mesh-root node per mesh, no implicit scene transforms/instancing. Each part reuses the **original strict one-primitive GLB loader** by internally constructing a bounded, temporary in-memory GLB with the unchanged BIN and selected original primitive. This ensures original bounds/attributes/inverse binds/normalized weights and extension/material/UV/morph/image refusals are actually exercised on **EVERY** part. Refuses skipped parts, unassociated source nodes, hierarchy-embedded mesh transforms and mismatched joint palettes. Aggregates <=250,000 source vertices. Current adapter copies the embedded binary per part and is **not** a production-efficient general GLB parser.
2. `src/viewer/firstPartyIndexedSkinnedMesh.mjs`: adds `renderBatches(meshes, {eye,target,colors})` to the existing independently verified WebGL2 indexed triangle GPU port. Checks **all** supplied geometry/indices/material colours before any framebuffer mutation; one `gl.clear` per frame, then multiple `gl.drawElements` submissions under a common camera/depth buffer. Preserves existing `render(geometry)` method semantics, adds `drawCallCount` diagnostics. No additional npm runtime dependency, GLSL library, Three.js, WebGL wrapper or external mesh.
3. `tests/support/buildSyntheticBatchedGlb.mjs` constructs source-created embedded GLB geometry with **physically separate position buffers** for different source meshes/parts. No actual human or medical source asset ever embedded in CI.
4. `tests/firstPartyGlbSkinnedBatches.test.mjs` covers two meshes, multiple primitives within one mesh, combined meshes+primitives, exact original GLB source bone identifiers/rest-bind contract, separate CPU four-weight LBS, malformed second-part refusal, scene instance/skin/hierarchy rejections, 1–8 GPU batch bounds, atomic no-partial-draw errors and context-loss recovery.
5. `scripts/verify-first-party-batched-glb-browser.mjs`: real Chromium software WebGL2 proves 2 original GLB meshes each independently parsed, numerically rig-bound, CPU-skinned and submitted in **one framebuffer frame**. Checks exact draw-call count and actual left-red/right-green GPU framebuffer pixel readback to catch accidental last-mesh-only render behaviour. A diagnostic screenshot is non-anatomical evidence only.
6. `.github/workflows/first_party_batched_glb_webgl.yml` runs zero-dependency new+inherited Node tests, strict editor TypeScript and production build parity, and actual browser WebGL2 framebuffer colour validation.

### Deliberately unsupported

- UV0, materials, textures, tangents, shading models, transparent sorting, shadows, morph targets or sculpted corrective shapes;
- nonidentity scene mesh node transforms, mesh instances, multiple skins, sophisticated joint node hierarchies, source→canonical physical registration and embedded animations;
- GPU matrix-palette vertex skinning (CPU four-weight reference only); >8 triangles groups; optimised shared buffer streaming; large body asset performance;
- ORIGINAL-v1 first-party human asset or scientifically verified body anatomy, muscle/axilla/shoulder realism or physically validated exercise clips;
- `three` removal from the **existing editor**, unchanged during the test. No original third-party temporary video replacements, final source redistribution rights or customer product release clearance.

A successful unit test, GPU framebuffer screenshot or a restricted synthetic GLB demonstration does not verify the full human model, legal provenance or first-party release. All human skeleton regions remain subject to Work's independent anatomical review; latest historical programme gate **0 READY / 9 PARTIAL / 3 BLOCKED** until verified otherwise.

### Next safely parallel work

Move to source-authored UV coordinates/materials only with defined finite/fail-closed typed contracts and actual shader/browser tests; separately develop multi-bone GPU palette parity from the already verified numerical bind contract. Work will supply only source-owned original model schema, bone names, inverse binds and provenance once accepted. Keep this PR draft, isolated and stacked for review; do not modify the normal studio renderer or freeze the anatomical skeleton based on this prototype.
