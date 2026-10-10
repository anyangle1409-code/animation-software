# CP1 foot/pelvis independence: 30-subject VSD evidence candidate and licensing quarantine

Date: 2026-10-10
Programme: Home Gym PT — canonical skeleton-first regional target closure.
**Status: SOURCE DISCOVERY ONLY; NOT A GEOMETRY TARGET, NOT A DATA IMPORT AND NOT COMMERCIAL CLEARANCE.**

## Independent-donor opportunity

University of Twente's BoneHub [vsd-lower-extremities-seg](https://huggingface.co/datasets/BoneHub/vsd-lower-extremities-seg) is derived from the original Fischer 2023 Virtual Skeleton Database (VSD), DOI [10.1038/s41597-023-02669-z](https://doi.org/10.1038/s41597-023-02669-z). The BoneHub release describes **30 distinct cadaver CT cases**, with **16 male, 14 female subjects** aged 19–95, each with lower-extremity labelling of up to **63 bone labels** (sacrum to feet), individual bone STL meshes, and subject demographics. The underlying original cadaver scans were contributed by forensic institutions in Bern/Zurich, **not the NLM Visible Human male**.

Compared with our source-confirmed BoneHub Visible Human male 180 cm donor (PR32–34), this could be a genuinely independent *donor cohort* suitable for population-level checks of pelvis, hip, femur, tibia, patella, tarsal and forefoot dimensions after permissions and measurement endpoint definitions are resolved.

**DO NOT DOUBLE COUNT**:
- BoneHub \`vsd-feet-seg\` is the exact same 30 VSD donor cases as \`vsd-lower-extremities-seg\`, cropped around feet, not another 30 independent individuals.
- Fischer's original Zenodo meshes and BoneHub-derived STL meshes likewise refer to the same VSD donor subjects, not separate independent evidence.
- The 16 male subjects must be screened for stature, missing structures, anatomical definition, methodological uncertainty and body-size conditioning before claiming any specific adult-182cm target or cohort mean.
- BoneHub release notes case 026 missing three right distal toe phalanges; case 030 all phalanges absent. Do not interpret missing data as true anatomical variants.

## Binding use/licensing barrier

**BoneHub dataset explicitly specifies CC BY-NC-SA 4.0**, reflecting the licence of the original VSD cadaver CT sources. This contains a **non-commercial** restriction. The eventual Home Gym PT App Store publication may be commercial. Consequently:

- Do **not** copy or download these data into production pipelines, commit anatomical meshes, derive/release redistributable commercial shape assets, train product models, or adopt coordinate targets into a commercial skeleton without confirming permitted use and obtaining a licence/permission where necessary.
- The Fischer 2023 **journal article itself is CC BY 4.0**, but this does **not** change the separate underlying dataset's non-commercial terms. Do not conflate article republication rights with cadaver scan/mesh licences.
- Restrict immediate work to citation, licence/provenance assessment, metadata-only source discovery and review of published aggregate scientific results that are independently licensable and endpoint-compatible.
- Coordinate with the rightsholder/source owner for explicit commercial permissions before source-data reuse. No assumption about legal entitlement follows from a public download link.
- The source model card's DOI badge gives \`10.57967/hf/10471\`, but its embedded BibTeX gives \`10.57967/HF/10470\`; verify the canonical registered identifier before generating attribution records.

## Source quality limitations

The derivative's fused foot bone geometries were manually split to individual bones in Rhino during dataset construction; this stage creates additional segmentation subjectivity. Initial first-release segmentations are called hollow shells; the second VSD mesh version was used for filled labels. Metadata gives sex, days of age, height and weight; multiple scans and altered source orientations require explicit per-subject coordinate checks.

An independent donor cohort does **not** supply articular cartilage, running/loaded joint trajectories, ankle/tarsal contact or normal anatomical ROM by itself. Subject sex/stature conditioning and bone measurement endpoint semantics remain essential.

## Decision/next action

**Source discovered, rights unresolved. No download, no donor data copied, no acceptance promotion.**

CP1 foot/ankle comparative-source option is now documented. Continue permitted open-literature population measurements or seek rights clarification; do not install source mesh geometry. Retain canonical region readiness **0 READY / 9 PARTIAL / 3 BLOCKED**, c005 unapproved and a003/r95 untouched.
