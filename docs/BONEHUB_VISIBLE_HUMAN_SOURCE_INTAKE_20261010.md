# 2026-10-10 — Source-pinned 3D anatomical bone-surface intake (NONCANONICAL)

## Why this adds useful evidence

Alavi and Asseln's [Visible Human Full-Skeleton 3D Bone Models](https://huggingface.co/datasets/BoneHub/visible-human-3d-models), DOI [10.57967/hf/10464](https://doi.org/10.57967/hf/10464), supplies individual male 3D segmented STL surfaces for both eight-carpal wrists, the separate tarsal bones, all 24 ribs, and vertebrae. University of Twente [dataset listing](https://research.utwente.nl/en/datasets/visible-human-full-skeleton-3d-bone-models/). The data derive from aligned NLM Visible Human CT redistributed by Andreassen et al., [Scientific Data 2023](https://doi.org/10.1038/s41597-022-01905-2). This is **a different segmentation of the same Visible Human subject**, not an independent anatomical subject.

The upstream dataset card reports 142 male individually *labelled structures*, 180 cm/90 kg/39 years, **not** 206 separate conventional bones or a 182 cm male population mean. Licence: **CC BY 4.0**; both Alavi/Asseln (2026) and Andreassen et al. (2023) require attribution if used. Read the upstream dataset card and original-source licence before any downstream release.

## New source material (hashes pinned, source files not included in Git)

Machine-readable file: ORIGINAL_V1_WORK/anatomy/bonehub_reference_sources_20261010.json

Four small, **individually confirmed** upstream male file links and SHA256 fingerprints, spanning the project's three BLOCKED regions:

| Region | Upstream bone STL | SHA256 |
|---|---|---|
| Carpus | HAND_LEFT/SCAPHOID_LEFT.stl | 362d0d42bf1b4475e705846d8c7c48965bb052f875a93355c8e302937ddef762 |
| Tarsus | FOOT_LEFT/TALUS_LEFT.stl | b79dcb8037223d2652e300cb42124c9d4e16dfedcc49ff36b4d44ed3fc24602e |
| Tarsus | FOOT_LEFT/CUBOID_LEFT.stl | 7ed61043826f269aecee108a1d1298e59dc2cf2da29b0083a297f548d48d0353 |
| Ribs | THORAX/RIB_1_LEFT.stl | 5b5216f2df8cac598aa94b1fe89039ce6734a15e520b9f1f788ddae3a6070295 |

The names and digests were transcribed from their *individual source pages*, not guessed from generic URLs. The downloader refuses any file with a different SHA256 and has a per-file size cap. It never downloads the 5.33 GB whole dataset.

## Read-only first-party workflow

No Python packages, Blender, HF client, UI package, CT data or third-party runtime are required. On a networked workstation, run from the repository root (replace the external output path as appropriate):

    python scripts/anatomy_fit/bonehub_surface_intake.py --list
    python scripts/anatomy_fit/bonehub_surface_intake.py --all --download --private-dir /tmp/hgpt-bonehub-source
    python -m unittest discover -s scripts -p 'test_bonehub_surface_intake.py' -v

**Output must be outside the Git checkout**. Each verified STL stays in that external directory. The script emits a JSON diagnostic with independently recomputed SHA256, triangle count, nondegenerate-triangle count and axis-aligned bounds **in the STL's unspecified source units**. It does NOT infer millimetres, physical bone centres, the imaging LPS/RAS axis frame, HGPT X/Y/Z mapping, cartilage, joint contacts, segment length or true physiological motion. Binary STL parse safety and provenance/approval guards have adversarial tests. No source file is altered.

A focused GitHub Actions workflow exercises the offline checks and makes one SHA-pinned external acquisition of the four small reference meshes, with a diagnostics-only report. That is **engineering source intake**, not anatomy acceptance. Failed external downloads or a source hash change fail closed; neither warrants weakening a hash pin.

## Verified live source execution (GitHub Actions, 2026-10-10)

[Successful focused Actions run 38066130130](https://github.com/anyangle1409-code/animation-software/actions/runs/38066130130) at commit c0d2faeac78ce34af726e20166b972d9b5574602:
**16/16 offline adversarial tests PASS**; all four real upstream binary STLs downloaded (source SHA256 rechecked before any cache write), read and measured; numeric-only JSON artifact \`bonehub-four-reference-bbox-provenance-only\` uploaded. Original STL/CT files were **not** uploaded or committed.

| Source | Actual triangle records | Nonzero cross-product triangle records | Axis-aligned bounding extents in *unspecified STL source units* |
|---|---:|---:|---|
| Left scaphoid | 4,156 | 4,156 | 28.259 × 19.918 × 16.781 |
| Left talus | 24,812 | 24,774 | 47.770 × 55.246 × 48.046 |
| Left cuboid | 11,000 | 11,000 | 27.265 × 34.295 × 37.012 |
| Left first rib | 15,360 | 15,354 | See source report artifact |

The talus contains **38** and first rib **6** triangles with zero geometric cross product in the source data interpreted as float32 coordinates. This flags triangle-level QA only; no conclusion is drawn about full mesh manifoldness, anatomical surface integrity or joint contacts. No units were silently assigned to the native STL vertices. Only after verifying source frame/scale and true articular geometry should these vertices be registered to HGPT. None of these metrics changes CP1 readiness.

## Hard limitations and required follow-on

- Upstream human annotators used model-assisted segmentation and published no inter-rater reproducibility result. STL mesh smoothing factor is 0.5. This cannot be accepted as perfect human bone ground truth.
- The Visible Human elbow region is truncated; distal humerus and proximal radius/ulna geometry are incomplete. **Do not use for unresolved arm length or DRUJ/PRUJ target approval.**
- Phalanges are grouped by finger/toe, craniofacial bones and sternum are not individually separated, sacrum includes coccyx, hyoid and costal cartilages are missing.
- The normal reading of an STL filename suffix is not proof of scanner laterality; validate against acquisition source and HGPT side conventions before registration. Nor is a bounding-box midpoint an anatomical joint centre.
- **For CP1 carpus:** independently orient/register all eight carpal surfaces, verify centroids and contact patches including pisiform, then cross-check a separate cohort before selecting canonical values.
- **For CP1 tarsus:** reconstruct all seven bones in a common frame, derive talocalcaneal/navicular/cuboid/cuneiform contact layout, and compare against independently sourced stature-specific foot morphology.
- **For CP1 ribs:** use all 24 curved bone surfaces for geometric hypotheses, identify head/tubercle and anterior ends; costal cartilage and sternocostal connections must come from independent anatomy and CT registration. Single-donor rib shapes are not population movement/ROM.
- **For CP1 spine/shoulder/pelvis:** later inspect full source surfaces with an independently checked scanner-to-HGPT rigid transform, shape/endplate/cavity QA and matched landmarks. **No old mesh fitting as anatomical authority.**
- Source acquisition and data comparison must be kept separate from release decisions. Only owner-approved evidence converged with independent datasets may change the master. This branch does not edit a003/c001-c004, c005, production geometry, muscles, skin, runtime rig or source motion limits.

**Status: still 0 READY / 9 PARTIAL / 3 BLOCKED; Gate 6/CP1 open.** This contribution resolves a *previously missing candidate geometry source*, not final positions, contact surfaces or correct biomechanics.
