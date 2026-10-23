# Home Gym PT — phone review renders and visual evidence protocol

Date: 23 October 2026  
Owner's request: **show actual progress images after major milestones, viewable from an iPhone.**

## Cloud-only capability and provenance

The authoritative source images are already preserved Blender 5.2 render artifacts from the [read-only diagnosis run 39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229):

| Reconstructed model | Original diagnostic artifact | SHA256 of ZIP |
|---|---:|---|
| W8 | [12495910312](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495910312) | `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e` |
| V14 | [12494932817](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12494932817) | `5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0` |
| R120 | [12495970648](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495970648) | `cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f` |

These saved image archives are from **reconstructed, unapproved models**, not proven original Claude-session assets. All model movement, grip, archive-equivalence and muscle-attachment approval gates remain failed or blocked.

## New reusable contact-sheet generator

`scripts/cloud_body_analysis/render_phone_review.py` reads **only** the above archived diagnostic PNGs. It checks exact ZIP SHA256 before opening any contents. A missing, undersized, malformed or incorrectly named screenshot is an error, not silently replaced with another render. It never opens or saves Blender files or invokes geometry operations.

It creates:
- `phone_review_shoulder_press_back_full_body.jpg`: W8 / V14 / R120 × samples 0, 6, 8 (rear view, actual saved diagnostic overlays).
- `phone_review_shoulder_press_back_upper_torso.jpg`: same nine preserved frames with an explicitly labelled upper-torso crop to highlight scapula, posterior shoulder and armpit junction.
- `phone_review_squat_side_full_body.jpg`: W8 / V14 / R120 × samples 0, 7, 8 (side view).
- `phone_review_manifest.json`: authoritative source ZIP digests, individual PNG member names and SHA256, output SHA256, crop warning and **`anatomical_approval: NOT_GRANTED`**.

The `localize-native-movement-failures` cloud job reuses the three verified source ZIPs it already downloads. It installs Pillow, runs six additional synthetic input-validity tests, and uploads a separate `phone-visual-review-<run_id>` GitHub Actions artifact, as well as saving copies within the native failure-localization reports.

Cloud implementation commit: `955efe42a6a0fbbfad1ff484f68d694b32029ebb`. [First expected complete workflow run 40024580927](https://github.com/anyangle1409-code/animation-software/actions/runs/40024580927). **VERIFIED:** run [40024580927](https://github.com/anyangle1409-code/animation-software/actions/runs/40024580927) completed SUCCESS across all five jobs; its [phone visual review artifact 12531993002](https://github.com/anyangle1409-code/animation-software/actions/runs/40024580927/artifacts/12531993002) was downloaded. ZIP SHA256 independently computed = GitHub `c4db0bdb3b5e0d3d916fee57a52c1c272cc8bcd8adda9d38e9acee075ea58a16`. All three JPEGs were checked against manifest-output SHA256. All 18 source render PNGs were also checked against the previously independently verified original Blender diagnostic ZIPs: **0 member-hash mismatches**. The first artifact's manifest names extracted-directory sources UNVERIFIED because it cannot access the original compressed ZIPs in Actions, but its individual source-image SHA256 values were independently checked against the original ZIPs outside the workflow.

**Integrity hardening in progress:** commit `0866b7c48ec358659faa1eebab08fd78a534e789` pins all 18 original source PNG SHA256 directly in the render script, so each source is verified even from extracted GitHub Actions directories. The initial run for this change failed synthetic fixtures (they used synthetic PNG bytes rather than original pinned source); updated test commit `91f6e665f32e9fd011dde7288eeb850b2f75d21d` rebinds only the synthetic fixture's expected checksums and adds an altered-but-valid PNG rejection test. [Corrective run 40025141134](https://github.com/anyangle1409-code/animation-software/actions/runs/40025141134) requires validation; **do not mark its stricter hashing gate verified until PASS**. Original .blend and original stored screenshots were never altered.

## Protocol for future major milestones

1. Always show **unaltered model-source screenshots** and indicate whether the image is an existing diagnostic, baseline, or genuinely new candidate render.
2. Use consistent camera and pose for before/after. Do not present altered zoom, lighting, interpolation, filters, retouching or manual illustration as proof of anatomical improvement.
3. Include rear/front/side views for shoulder/armpit modifications, with 0/50/75/100% exercise poses where an actual Blender pose test is available. A pose that cannot be computed must be clearly marked missing, not invented.
4. Preserve plain renders alongside numeric diagnostic overlays, and state exactly what each overlay measures (collapse, stretch, collisions) instead of treating all yellow pixels as the same defect.
5. Provide exact model SHA256, source revision, movement run, image artifact, original acceptance thresholds, previous failure count and newly tested metrics with clear PASS/FAIL distinction. Raw triangle counts across remeshed models are not a valid quality ranking.
6. Use deterministic model-specific file names and complete source-hash manifests. GitHub Actions artifacts expire under retention policy; copy accepted deliverables to approved storage before expiration.
7. Never save over the three preserved source .blend files. Do not run experimental repair without explicit authorization and separate candidate identity; do not merge, deploy or advance PT_MODEL_VERSION 1.0.

## User experience on phone

Open the latest successful [Phone Blender workbench runs](https://github.com/anyangle1409-code/animation-software/actions/workflows/phone-blender-workbench.yml), choose the `phone-visual-review-<run-id>` artifact, then open the JPEG contact sheets in the downloaded ZIP. An active ChatGPT session with file access can also display the exact verified image. Cloud Blender jobs may run independently of the Windows laptop; new assistant commits/reviews do not continue automatically after the chat ends.

**Status:** visual infrastructure development, not a model correction. The anatomical muscle-layer and production gates remain BLOCKED.
