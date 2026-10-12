# G4q · Actual ORIGINAL_v1 full-body GLB read-only integration preflight

**Owner:** Chat-owned first-party Lane G. **Source:** Work PR [#81](https://github.com/anyangle1409-code/animation-software/pull/81) head `d04100995ca496fd4e095c748179e08b730bcd6e`, review-only `HomeGymPT_Male_ORIGINAL_v1_REVIEW_ONLY.glb`, SHA-256 `d267dac344affb5d52c7155f8d0254794e818a8eab3ad54f7f263694f36c390d` (1,495,720 bytes).

## New original-source evidence

- One original body mesh / **one primitive**, 17,946 vertices / 35,888 original indexed triangles; 67 unique runtime skin joints.
- Six corrective morph-target **POSITION and NORMAL sparse accessor pairs**, all six mesh source weights exactly zero. Sparse data are part of the real source and must not be silently dropped, misdescribed as animated, or substituted with a mannequin. No animation channels.
- Nested mesh node 67 under **identity** scene node 68, with exporter metadata explicitly marking not production ready. One original double-sided opaque nonmetallic material roughness 0.48; source PBR is metadata only until independently implemented.
- Existing G4 batched importer demands **at least two primitives**, G4 Work pilot requires under **1 MiB**, and strict single importer rejects morph targets, material and nested mesh node. Never relax that inherited gate. A source-SHA-pinned **separate review-only** path is required.
- Independently authenticated local original source: SHA, complete BIN, 67 rest world × inverse-bind palette error below 1e-5, four-weight range and normalization, all six real sparse target index/delta records. First-party JavaScript offline hash implementation checked against NIST empty/abc vectors and Node crypto source hash. **11 local Node regressions PASS** (SHA/tamper, real-source decoder, exact finite rest palette, Y-up camera); source GLB unchanged.
- Actual Chromium GPU proof **NOT verified here**. Local Chromium prohibits WebGL2 contexts and blocked localhost navigation. Renderer and transform-feedback parity harness prepared locally; no screenshots, CI or new production approval claimed for G4q.

## Work coordination / constraints

Work's source 206-bone anatomical skeleton is not yet the controller of the 67-joint body. Work's PR81 attachment audit measured provisional anchor offsets clavicle 12.091 mm, scapula 74.946 mm and humerus 54.789 mm; name-only reattachment is unsafe. Work owns corrective alignment, Blender/CT and actual exercise load/contact validation. No Work source, anatomical geometry, PT-App runtime, 304 videos or rights/release gates changed.

**Next:** publish the reviewed first-party G4q adapter and exact-source tests on this Chat-only branch if connector permits; obtain independent original GPU REST/CPU parity and front/side/rear images in real Chromium; maintain `docs/CHAT_LANE_G_OVERNIGHT_LEDGER_20261011.md` as one morning review log. No approved full-body exercise animation yet.
