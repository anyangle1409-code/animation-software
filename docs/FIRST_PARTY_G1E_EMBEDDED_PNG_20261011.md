# G1e — bounded first-party embedded PNG source intake (data-only)
**11 October 2026; owner v1.1 Lane G software; no original character/model/anatomical edits.**

This stage extends the restricted GLB batched loader (G1b flat base colours, G1c UV0, G1d source normals) with **explicit opt-in extraction of PNG bytes embedded in GLB BIN**, including referenced texture and sampler. External URLs, data URIs, arbitrary glTF extensions and unused source images/textures/samplers are forbidden. Each source primitive still passes the original strict geometry/skin decoder after source image declarations are independently screened and stripped from an in-memory validation copy. The GLB input is not mutated.

### Supported subset

- Source GLB: 2–8 triangle primitives across 1–4 identity-root skinned meshes with a single shared skin; source maximum 32 MiB, 250,000 aggregate vertices, inherited 128-joint/four-weight bounds.
- One to four embedded PNG images, image bufferView wholly within source BIN; one to four referenced textures and explicitly declared samplers.
- PNG size <= 8 MiB, width and height <= 4096, pixel count <= 4,194,304. Checks source signature, IHDR, all recognized chunk CRC32s, contiguous IDAT, end marker, and no trailing data.
- Only 8-bit RGB/RGBA PNG, noninterlaced, without palette, ancillary metadata, unknown chunks or compression extensions.
- Each texture has linear clamp-to-edge, no mipmaps; only material baseColorTexture with texCoord zero and existing source TEXCOORD_0 is accepted. Material is opaque, matte, one-sided, bounded baseColorFactor.
- Strict explicit opt-in on parseRestrictedBatchedSkinnedGlb: options allowSourceFlatColors, allowSourceUV0 and allowEmbeddedPngBaseColor all true. Default source reader remains fail-closed.
- Returned per-primitive sourceBaseColorPng contains copied source PNG bytes and original image/texture index, measured dimensions and sampler. Source buffer and bone weights remain unchanged.

### Not yet implemented

**This is data-only**. No PNG raster decompression, browser ImageBitmap decode, texture GPU upload or sampling, PBR material, real ORIGINAL-v1 human skin appearance or verified ownership of a production mesh. It never fetches source images. Existing Three.js editor and the 304 temporary videos are intentionally unchanged.

Synthetic first-party regression fixtures independently generate valid tiny PNGs using Node built-in zlib and CRC32, and test opt-in, source preservation, source skin weights, multi-mesh, invalid URLs, malformed image views, broken CRC, unsupported sampler, missing UV, excessive dimensions and invalid second primitives. GitHub CI also runs inherited source GLB/UV/normal/pose tests and editor typecheck/build. Passing synthetic tests does **not** prove human movement realism or full source asset compatibility.

### Next Chat step

Add original native browser ImageBitmap decoding and direct WebGL2 texture upload/sampling with an independently generated nonuniform PNG and actual pixel readback, including UV orientation and colour-space checks. Preserve no-network source-only provenance. Work continues independently on shape, mechanics and the real human character.

See the [owner-shared master plan v1.1](https://github.com/anyangle1409-code/animation-software/blob/codex/shared-autonomous-master-plan-20261011/docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md).
