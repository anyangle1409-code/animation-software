# Source-bound pelvic CT candidate review (2026-10-09)

This directory records the noncanonical result of a live-source review. It does not contain downloaded CT pixels, scanner headers, anatomical cross-section images, patient data, or a Blender file.

## Verified source material

Six pinned NLM Visible Human CT images and matching scanner headers were downloaded privately and checked byte-for-byte against the repository manifest: `1749`, `1752`, `1755`, `1797`, `1800`, and `1803`. The lower three slices support only a tentative central sacrum-region observation. The available sparse windows do not establish a complete pelvis, verified bone surfaces, a defensible S1 landmark, or a patient-to-HGPT registration.

Same-number full-colour anatomical cross-sections were reviewed only as cross-modality context from the same donor. Their SHA-256 values were:

- `1749`: `b5f737c409c1df1a61fa0b1079f3f93e428575e6e48f9fa6c62b1c8c5d6888bd`
- `1752`: `bace8e3b0799b60471eabf912aa3cf99d40f42c62d3c4858fcc39146f0181f15`
- `1755`: `2b3435708398aa587af606d4edf98bd4b40b6a82d4e8fa9982ec3d527d31b8a7`
- `1797`: `34ceb21c5932078caf82111429a969ea4282b4fd0475ea7bbcfb35f5e3580e1c`
- `1800`: `7f2ca8a75ca9244a027316e26fc08a88b6df2c27c7cf39537eb1a2d02eb46859`
- `1803`: `3e321a484789f7a69a07503dfe98b13cdc09227b65139dddff59b146c3e4dcd6`

These cross-sections are not independent population evidence and do not unlock canonical promotion.

## Blender verification

The six CT slices were loaded into a real Blender 5.2.1 scene as source-bound review planes. The saved private scene preserved pre-existing objects, did not pack the source images, made no anatomical or landmark claim, did not modify the source skeleton, and did not create a canonical asset. Its SHA-256 was `9991cb047b2ad4b5ff13d9a5e1c2176bdc0fd6d226af2b1b110d7a9c4627d728`.

## Result

`candidate_sacrum_report.json` is the sanitized deterministic workflow output. It records three pinned observations, a 27-voxel connectivity probe, zero accepted landmarks, zero canonical promotions, and every unmet validation gate. The source skeleton remains the geometry authority.

Sources: [NLM Visible Human data access](https://www.nlm.nih.gov/research/visible/getting_data.html), [NCBI bony pelvis anatomy](https://www.ncbi.nlm.nih.gov/books/NBK545204/), and [sacroiliac CT morphometry study](https://pubmed.ncbi.nlm.nih.gov/27324173/).
