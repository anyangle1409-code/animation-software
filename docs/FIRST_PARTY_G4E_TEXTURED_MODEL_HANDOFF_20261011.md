# G4e — one original SHA-bound model path for PNG materials, source skin and moving GPU

**Home Gym PT, 11 October 2026 • Chat-owned first-party Lane G.** This solves a real integration gap between the early Work→Chat GLB/rig preflight (G4 PR #59) and the already-tested original source PNG/GPU materials renderer (G1e/G2e PRs #61–#64). The renderer could read and display embedded PNG textures but G4's hashed GLB model handoff refused these exact same material declarations. That would have blocked Work's first textured provisional human GLB.

## Implemented

The original `validateProvisionalModelHandoff(originalGLBArrayBuffer, manifest)` now accepts a backward-compatible **fourth optional** source feature:

~~~json
{
  "glb": {
    "sha256": "EXACT_64_CHARACTER_LOWERCASE_SHA256_OF_GLb_BYTES",
    "layout": "batched",
    "sourceFeatures": {
      "flatColors": true,
      "uv0": true,
      "normals": false,
      "embeddedPngBaseColor": true
    }
  }
}
~~~

The complete manifest still needs the **unchanged** existing `kind/candidateId/status/frame/rights/rig/releaseApproved` fields, source joint names, explicit runtime name mapping, source-generated 4×4 world rest matrices, and *UNVERIFIED* anatomical/rights flags. See [original G4 Work handoff instructions](https://github.com/anyangle1409-code/animation-software/blob/codex/first-party-prototype-handoff-20261011/docs/FIRST_PARTY_G4_PROTOTYPE_HANDOFF_20261011.md).

- Prior manifests with exactly `flatColors`, `uv0`, `normals` remain accepted. The optional `embeddedPngBaseColor` feature is a **strict boolean**, never an arbitrary URI or URL. Unknown source features, non-boolean opt-ins and undeclared capabilities are rejected.
- Textured source requires the **existing supported batched source GLB subset**, flat opaque material validation and source UV0. Single-primitive original GLB format is unchanged and cannot smuggle source textures under an incorrect layout claim.
- Exact source SHA-256 verification is performed on copied GLB bytes *before* any source structures are decoded. The original G1e independent PNG/UV/material/sampler validator checks every declared image and primitive; source image data must be embedded in the GLB BIN, never a network request. The G4 rig validator checks every part's source joint palette, source inverse binds and declared rest-world matrices in the same unit/frame. There is no adjustment to any original bone or skin geometry.
- A successful G4e result now includes `scene.batches[].sourceBaseColorPng`, `sourceUV0`, source materials and original parsed skin/mesh, which can be passed **unchanged by identity** into the G2d/G2e native GPU skeleton/texture renderer. Its audit includes `sourceEmbeddedPngBaseColorValidated`; **no** medical/real human/rights/release acceptance is implied.
- The first-party renderer accepts this G4-validated source material via `setSourcePngBatches(scene.batches,{colorSpace:'gltf-srgb'})` and uses separate original source image texture, validated UV and existing skinned matrix palette in one shader. No extra vendor dependency or URI fetch.

## Test evidence

A new fixture builds a real glTF 2.0 **two-mesh, two-joint** binary GLB, with two *test-authored* 2×2 PNGs generated independently using Node's built-in `zlib` and CRC32, embedded with their own GLB bufferViews, UV0, material, image, texture and sampler relationships. It tests both the full source GLB parser and SHA-bound Work handoff, all original rest and source joint names, and that original moving posed-skin matrices preserve both source PNG references.

Adversarial tests include stale source digest after modifying a source image, injected external image URL, invalid source sampler, broken PNG CRC, deliberately omitted UV0, unsupported material link, falsified source declaration, changed second primitive, wrong first-party layout and a forged extra manifest feature. The original THREE-field untextured G4 manifest tests and original G4b pose/bind tests remain in the targeted CI suite.

An actual Chromium + SwiftShader WebGL2 test executes the **entire path together**: original GLB SHA → G4 independent rig binds → embedded source PNG/UV/material checks → two source textures → original GPU four-weight palette → indexed triangle draw, producing a full-size real browser PNG and GPU pixel/pose report. It verifies both original red and green source material regions stay attached as the GPU skinned joints move; no vendor network requests or browser/WebGL errors. It also reruns G2e material colour parity and untouched original studio TypeScript/build.

**Mark software VERIFIED only after exact-head CI passes; never promote synthetic image/mesh fixtures to a production human model.**

## Constraints and next integration

This remains a strict early subset: 2–8 triangle primitives over 1–4 identity-root skinned meshes sharing one skin; up to 128 GPU palette joints, original four-influence weights, ≤32 MiB source GLB, supported embedded PNG RGB/RGBA non-interlaced images, linear clamp-to-edge sampler, opaque unlit sRGB material, no imported CT/anatomy scans. Blender's eventual first-party character may legitimately export unsupported glTF features such as nonidentity mesh transform, morph targets, extension materials, more joints or multiple skins; **report those to Chat** and extend the decoder when justified. **Never distort, simplify or reposition the human skeleton solely to force importer compatibility.** Human proportions, correct S-curved clavicle and moving 3D scapula, realistic exercise contact/loads/skin deformation, rights review and mobile rendering remain Work/Joint Release acceptance tasks.

Actual Work-owned original GLB, images and pose sequences are NOT available in this branch; synthetic correctness is not human anatomical approval. This is a draft integration compatibility change, not a production asset or a finished PT App.

Coordination: [owner-updated master plan v1.1 PR #48](https://github.com/anyangle1409-code/animation-software/pull/48), original Work handoff [PR #26](https://github.com/anyangle1409-code/animation-software/pull/26).
