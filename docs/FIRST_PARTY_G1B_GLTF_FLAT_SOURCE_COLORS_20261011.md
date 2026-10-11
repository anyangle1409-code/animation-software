# Lane G1b — first-party GLB source-authored flat opaque material colours

**11 October 2026 · isolated, stacked draft · no human-model or PBR approval**

Building on [PR #49](https://github.com/anyangle1409-code/animation-software/pull/49), this extends the original GLB multi-mesh source parser with an **explicit opt-in** `allowSourceFlatColors:true`. The old no-material, vendor-free GLB behavior remains unchanged by default.

### New source subset

- Permit only glTF 2.0 `materials[n].pbrMetallicRoughness.baseColorFactor = [r,g,b,1]`, all finite and within [0,1], **explicit `metallicFactor:0`**, `roughnessFactor` omitted or equal to 1, `alphaMode:'OPAQUE'` or absent, `doubleSided:false` or absent.
- Every material index must be an integer in range, referenced by a parsed primitive, and every source material must be used. Maximum 8 source materials in the existing 32-MiB bounded source GLB.
- Unknown material extension, texture references, alpha blending/masking, two-sided material, transparency, metallic/rough, extra opaque fields, normals/UV/tangents textures and externally fetched images remain **strictly refused**, never ignored.
- After explicitly validating a single permitted source material, remove only its material reference from the **temporary in-memory copy** passed to the *unchanged one-primitive GLB validator*; the original GLB bytes remain untouched and all existing position/index/weight/skin/rig compatibility gates still apply.
- Per-primitive `materialColor` (frozen RGB) is passed to the existing project's first-party `renderBatches()` shader. We are **not** interpreting glTF physically-based shaders, textures, UVs, HDR, tone mapping or cloth/skin scattering. No actual original-v1 human mesh has been loaded.
- New project-authored deterministic two-mesh synthetic GLB source material tests and real headless Chromium WebGL2 browser render verify both red and green colour source arrays using the **actual GPU framebuffer pixel readback**, not just parser metadata.
- No `three`, React, third-party material/shader loader, paid character or purchased exercise animation introduced; no files on Work's anatomical/Blender CT branch modified.

### Acceptance boundary

Project-owned flat-matte RGB is only a basic source→GPU material plumbing proof. GLB materials with texture/UV, physically based metal/roughness, transparency, shadows, mesh normals/tangents, morph deformations and accepted human skin are next independent tasks. Work retains the exclusive skeleton-first validation track, Phase 6 CP1 / Gate 6 OPEN with historically 0 READY/9 PARTIAL/3 BLOCKED. The default production editor still uses its existing single Three.js gateway until complete character material, interaction and movement parity is verified. PT-App unchanged and 304 placeholder exercise videos not deleted.


## Actual CI and browser proof — 11 October 2026

At source tested head `14f7fa925dda0d2c419b4c8e7ea5d393ba5a951b`, [GitHub Actions run 38134182774](https://github.com/anyangle1409-code/animation-software/actions/runs/38134182774) **PASSED all 3 jobs**:

- **84/84** original zero-npm-install Node tests passed: **12 new** flat RGBA source/material refusal tests, plus 14 mesh batching, 18 explicit GLB-to-rig binding, 12 source GLB parsing, 16 CPU LBS/indexed GPU and 12 original skeletal WebGL2 tests.
- Full existing animation studio strict TypeScript check + production build both PASS. Existing legacy Three.js remains the normal editor renderer; no customer product migration claimed.
- Real Chromium decoded one project-authored two-mesh GLB containing source-assigned **material RGB [.94,.28,.21] and [.16,.86,.30]**, verified opaque matte-only constraints and both explicit named joint bindings, and drew **20 GPU frames / 40 indexed drawElements** without network-loading the Three/React vendor runtime. Actual GPU pixel readback: **8,182 red pixels + 8,016 green pixels simultaneously**, proving the GLB-specified colours reached visible geometry. Observed source-probe mesh deformation 0.125 synthetic units (not a physiological distance); browser errors 0, vendor module requests 0.
- [Diagnostic browser PNG and JSON artifact](https://github.com/anyangle1409-code/animation-software/actions/runs/38134182774/artifacts/11700481151). These display project-authored geometric **test triangles**, never actual original human skin or an anatomy approval.

No final character GLB/texture/UV or medical subject image was imported or redistributed, no deletion of the remaining Three.js studio dependency, no Blender/CT candidate modified and no app release gate promoted.
