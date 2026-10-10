# External 3D wrist/tarsus/rib source index — NONCANONICAL (2026-10-10)

This is an independent, source-only follow-on to draft PR #32, **not a replacement anatomical skeleton**, approved mesh, whole-body physical geometry, or production rig change.

## Purpose

The University of Twente/BoneHub *Visible Human Full-Skeleton 3D Bone Models* (DOI 10.57967/hf/10464, CC BY 4.0) provides presegmented male osseous surface STLs derived from aligned NLM Visible Human images, the **same cadaver** already used in our NLM CT audit. Identify candidate carpal, tarsal and individual rib files at an immutable upstream Git commit instead of assuming that four previously verified examples represent full regional coverage.

### Execution

From an isolated project checkout:

    python -m unittest discover -s scripts -p 'test_bonehub_region_source_index.py' -v
    python scripts/anatomy_fit/bonehub_region_source_index.py --network --output /tmp/hgpt-source-region-index.json

The output path must be **outside the repository**. No source files are downloaded by this new metadata-only program, and no personal/medical imaging bytes, screenshots or STL geometry are uploaded. The source SHA from the upstream dataset metadata is read first; only a tree at that **same immutable SHA** is enumerated. A future upstream change must result in a different revision in the report, not a silent alteration of an older report.

Safety rules: exact official HTTPS API host/path, fixed source repository root, controlled pagination and maximum response sizes, only source file candidates in male HAND_LEFT/RIGHT, FOOT_LEFT/RIGHT and THORAX, exact SHA comparison against the four verified original samples when the upstream file metadata supplies SHA256, no inferred missing anatomy, no guessed source units/coordinate system.

### Interpretation

- **Filename candidate** is only a clue: it does not prove named bone geometry or acquisition laterality.
- **LFS SHA256 metadata** is upstream metadata, not an independent local recomputation. Subsequent verified download and raw SHA measurement are separately required for full surface intake.
- **Bounding box** is not a bone centre, joint centre or articular contact patch.
- **The Visible Human donor is 180 cm**, versus the project's ~182 cm target; one cadaver does not establish a population anatomical target.
- A left/right suffix is not enough to resolve the anatomical vs runtime side discrepancy exposed by PRs #27/#29.
- Costal cartilage, carpal and tarsal ligaments, bone surface identity, active physiology, and source-to-HGPT rigid registration are not certified.
- The dataset can support *candidate surface reconstruction* but cannot automatically close CP1, Gate 6, Gate 8, Gate 9 or the 0 READY / 9 PARTIAL / 3 BLOCKED ledger.

### Next safe work following the inventory

1. Read the GitHub Actions metadata report and identify actual coverage/missing files for each body side.
2. Generate a separately SHA-pinned manifest for the truly present individual source bones; do not construct missing ones from guessed names.
3. Reuse PR #32 private bounded binary STL downloader to independently check full raw bytes (no source files in Git).
4. Validate source coordinate units/orientation and same-donor CT registration before comparing spatial relationships.
5. Check mesh watertightness, degeneracy, manifoldness and segmentation boundaries; retain the source defects found in the sample talus and rib.
6. Derive labelled, reviewable articular surface/landmark candidates and compare against independent studies/cohorts.
7. Only then propose anatomy-target updates in separate, reviewed and appropriately regression-tested work.

The resulting source report may reduce data acquisition work, but **does not change any canonical bone position**.
