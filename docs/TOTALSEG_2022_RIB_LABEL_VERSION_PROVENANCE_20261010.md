# Independent rib cohort: frozen upstream TotalSegmentator rib label semantics (2026-10-10)

**Status:** Public **source-code/class-map** verification only. **Not patient-level morphology**, not a human cohort sample, no licence approval, no CP1/Gate6 acceptance, no bone/joint-coordinate changes.

## Why this matters for the HOME GYM PT Phase 6 rib blocker

The original [TotalSegmentator dataset](https://zenodo.org/records/6802614) published in 2022 consists of **1,204 CT examinations with 104 labels** and 59 labelled bone structures; clinical subjects have real variation, fractures, missing field-of-view and heterogeneous scans. It could be an independent patient source for rib and thorax shapes, unlike the *one* NLM Visible Human male in PRs #32–34. The original archive is 28.4 GB; **this investigation does not download it**.

We must avoid assuming that a label's numeric ID or mere existence is proof of a physically correct rib. The [official TotalSegmentator source map](https://github.com/wasserth/TotalSegmentator/blob/master/totalsegmentator/map_to_binary.py) has changed between the historical \`total_v1\`, later \`total\`, and separate \`class_map_part_ribs\` maps. Its authors also explicitly warn of occasional 11-rib cases, additional cervical ribs and rarer caudal ribs; segmentation indices may not equal exact thoracic level.

## Actual pinned upstream code audit

Source: \`wasserth/TotalSegmentator/totalsegmentator/map_to_binary.py\`

Immutable Git **blob** SHA-1 \`34820bd066e0e930b81a741f8ccc6c81f588b528\` obtained from GitHub's source repository. This SHA pins the **file byte content**, not a specific release or the 2022 data archive.

\`scripts/anatomy_fit/verify_totalsegmentator_rib_labels.py\` downloads **only this short public file's immutable Git blob metadata**, validates its Git blob SHA-1 and parses just literal dictionaries from the Python AST. It **does not run imported upstream Python, install or invoke any segmentation models, access CT or segmentation mask bytes, or download the 28 GB archive**. Test and CI prohibit marking any patient or skeleton approved.

All three dictionaries contain 24 distinct bilateral named rib classes, but their **numeric IDs are incompatible**:

| Official source map | Left 1–12 | Right 1–12 | Sternum ID | Costal-cartilage ID |
|---|---:|---:|---:|---:|
| \`total_v1\` (historical) | 58–69 | 70–81 | Not present | Not present |
| \`total\` (later model) | 92–103 | 104–115 | 116 | 117 |
| \`class_map_part_ribs\` (specialized) | 1–12 | 13–24 | 25 | 26 |

The map **does not prove** that the 2022 archive stores these values as single integer voxels: some exports may store separate binary mask names. Before obtaining any individual source data, validate its exact published file structure, label representation and version against that source, rather than decoding according to an inferred global class map.

### Important original-source caveats

The project's [official class-map file](https://github.com/wasserth/TotalSegmentator/blob/master/totalsegmentator/map_to_binary.py) explicitly describes additional ribs at T12/L1 or C7 and apparent 11-rib cases with segmentation errors. Therefore even a complete 24-slot label map **never certifies that a particular CT is a normal 12-pair donor**. Each candidate case requires:

1. Source-level patient identity/deduplication (base dataset versus mirrors and tool outputs).
2. Complete left/right rib presence, acquisition field-of-view, integrity and vertebral-level identification independent of filename/label counts.
3. Screening for trauma, pathology, post-surgical deformation, fused vertebrae, rib count variants, age/sex/stature and supine versus standing posture.
4. Proven source coordinates in true CT world axes and isotropic physical unit conversions, and source label-mask quality.
5. Independent anatomical identification of rib head, tubercle, curved shaft and distal tip; missing costal cartilage must not be treated as a bone gap.
6. Rights verification at the exact original dataset/archive/file level. A GitHub software licence, journal article licence, or mirror's dataset-card label is NOT sufficient to establish patient CT reuse permissions.
7. Explicit measurement endpoints, population quantiles and suitably screened sample sizes for a future 182-cm male shape envelope. No rib shape can be promoted from the label schema alone.

The separate \`appendicular_bones\` model remains a commercial-rights restriction; the original 1,204-CT dataset is separate from both later pretrained model weights and some later subtasks.

## What is completed and what is blocked

**Completed:** pinned byte-level upstream class-map identity, exact historical/v2/specialized rib integer labels, documented co-label differences and author's rib count caveats, an offline adversarial and live public-source regression path.

**Not yet completed:** independent patient CT permission, any sample selection, patient-specific rib identification, bone-to-thorax fitting, costosternal or costovertebral contact, physical measurements, true rib surface labels or population normal anatomy certification.

This is a provenance and independent-cohort source **preflight only**. It never changes a003/c001–c004, 206 skeletal control inventory, 427 joint/contact definitions, Blender ORIGINAl-v1, Work's private CT files, or readiness (still **0 READY / 9 PARTIAL / 3 BLOCKED**). Original data and derived 3D mesh files must stay outside Git and commercial distribution until rights are confirmed.
