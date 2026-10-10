# Independent 30-bone/44-pair wrist-and-foot source adjacency screening — 10 October 2026

**Status: SOURCE-ONLY / NONCANONICAL.** This independent work extends already verified raw-source PR #38, itself stacked on PR #34's 54 SHA-verified Original Visible Human surfaces. **It does not certify physiological joint anatomy, contact spacing, patient-normal cartilage, relative 182-cm male stature, medical image correspondence or source physical millimetres.** Neither a003/c001–c004, c005, production character meshes, Blender sessions, Work or Claude branches are modified.

## Verified original input provenance

- Source: BoneHub Visible Human Full-Skeleton 3D Bone Models (DOI 10.57967/hf/10464), immutable upstream commit `ac8de2b38f5ae1a0996053ca0639dd6ae43358f1`. Same **one NLM Visible Human male** already used by previous CP1 CT work. Thirty source files are not thirty donor subjects.
- All eight carpal named bone STLs per labelled hand (16), all seven tarsal named bone STLs per labelled foot (14). Every raw byte read privately from the source and independently SHA256 compared against the upstream LFS OID, original file length and `SPACE=LPS` source header. All unmodified medical-derived meshes remain outside Git.
- Real face vertices from *every* nondegenerate source triangle, no point decimation, with small valid detached islands retained. Degenerate-only orphan points excluded from measurement, never removed from the raw source.
- Graph candidate source for nominal bone naming/neighbor topology: IMAIOS [intercarpal joints](https://www.imaios.cn/en/e-anatomy/anatomical-structures/intercarpal-joints-1162088) and [intertarsal joints](https://www.imaios.cn/en/e-anatomy/anatomical-structures/intertarsal-joints-1537028712). These are **labels for pairs to inspect**, not proof all these exact contacts exist in this one CT donor. Optional lunate–hamate and cuboid–navicular edges are tagged **CONTEXT_CANDIDATE** to avoid assuming universal articulations.
- Existing independent [PR #38](https://github.com/anyangle1409-code/animation-software/pull/38) and its successful live CI [38086284050](https://github.com/anyangle1409-code/animation-software/actions/runs/38086284050) confirmed eight bilateral source mesh pair upper/lower proximity bounds across 12 files. The new graph **rechecks those eight figures within their original 3-decimal recorded precision** to detect accidentally changed files, math, mapping or vertex handling.

## What the machine measures and does not measure

A 3D balanced nearest-neighbour tree is built **once per bone** and reused for all adjacent pairs. It tests 12 nominal wrist-pair types + 10 nominal foot-pair types = **22 distinct label-pair types × 2 sides = 44 measures**; verifies all 30 distinct source meshes.

Every pair reports:
- its labelled side and two original source file paths plus immutable SHA256 pins;
- an absolute **lower bound** from the separation of their source-aligned axis-aligned bounding boxes;
- the exact nearest original **valid-face VERTEX ↔ VERTEX** distance, which is an **upper bound** on minimum real triangle-to-triangle surface distance;
- explicit denial flags for actual direct articular identity, accepted joint/capsule contact, physical unit calibration, image registration, normal human anthropometry and c005 geometry acceptance.

AABB boxes may overlap when real surfaces do NOT meet; therefore a zero lower bound gives no contact assurance. Conversely a positive vertex-to-vertex upper bound does not rule out intersecting surfaces/penetration between faces. Source smoothing and small detached genuine label fragments may drive unexpectedly short bounds. Hence a correct tool **must not automatically select articular surface contact points or bind a runtime motion axis from this numeric proxy**.

Source relation candidates encompass carpal proximal row, pisotriquetral, distal row and midcarpal interfaces, and foot subtalar, talonavicular, calcaneocuboid, naviculocuneiform, intercuneiform and lateral cuneocuboid interfaces. The optional cuboid–navicular source-pair check is not an assertion that the single original donor has a physical synovial joint.

## Execution, test and output guarantees

New first-party-only files:
- `scripts/anatomy_fit/bonehub_wrist_foot_pair_graph.py`
- `scripts/test_bonehub_wrist_foot_pair_graph.py`
- `.github/workflows/bonehub_30_complete_pair_graph.yml`

Workflow acquires the 30 actual original STLs in an **ephemeral private GitHub runner directory**, verifies each source raw byte and publishes **only the 44-pair numeric diagnostic JSON** in Actions artifact `original-30-bones-44-bilateral-pair-bounds-NONCANONICAL`, with no patient source STL/image, vertex coordinates or CT uploaded. Neither the report nor any original source file is committed to the repository. Tests include identity/missing-bone guards, graph duplicate detection, checked prior 8 real source measurements, 3D KD nearest-neighbour exactness against brute force, symmetry, wrong side/path labels and explicit anatomical non-promotion.

Direct invocation on a machine (use only an external private folder):
```
python -m unittest discover -s scripts -p 'test_bonehub_wrist_foot_pair_graph.py' -v
python scripts/anatomy_fit/bonehub_wrist_foot_pair_graph.py \
  --private-dir /tmp/hgpt-30-real-source-bones \
  --output /tmp/hgpt-30-real-source-bones/complete-source-bone-pair-graph.json \
  --download
```

## What physically remains before the canonical skeleton

Work must independently accept actual STL-to-CT image transforms and physical length units, distinguish segmentation/smoothing defects from genuine bone shape, localise actual opposing articular surface patches rather than global nearest points, and verify clinically normal radiocarpal/carpometacarpal/subtalar/midfoot contact geometry. Independent adult-male datasets are required for 182-cm target envelope; this same single donor never becomes representative by more mesh processing. Correct carpal and tarsal bone positions, physical cartilage contacts and meaningful ROM axis definition remain **BLOCKED**, readiness **0 READY / 9 PARTIAL / 3 BLOCKED**, no new freeze.


## Verified full original source 30/30, all 44/44 bilateral observations

Actual [GitHub Actions run 38086748803](https://github.com/anyangle1409-code/animation-software/actions/runs/38086748803): **both jobs SUCCESS; 19 new graph tests + 17 previous tests = 36 PASS**. All 30 full raw immutable-LFS-SHA256-verified source meshes, 44 numbered pair results, and **8/8 earlier PR38 source-value regressions** passed. The only publication in the GitHub artifact is the numeric pair/source SHA report, with no raw source STL/image or patient voxel/mesh coordinates.

Each range is **[lower-bound from axis-aligned bounding boxes, upper-bound from the closest two valid-face vertices]**. **Neither endpoint is a measured cartilage gap or a true triangle-surface contact. Units have NOT been accepted as millimetres or registered to the full original CT; the graph's pair identity is a source-labelled hypothesis for one cadaver.** The values below are rounded to 3 decimal source-coordinate units for review; the CI's full JSON report stores the validated 9-decimal diagnostic values.

| Region | Labelled bone pair | LEFT lower–upper | RIGHT lower–upper |
|---|---|---:|---:|
| carpus | scaphoid–lunate | 0.000–0.875 | 0.000–0.910 |
| carpus | lunate–triquetrum | 0.213–0.461 | 0.000–1.146 |
| carpus | triquetrum–pisiform | 0.000–0.160 | 0.000–0.158 |
| carpus | trapezium–trapezoid | 0.000–0.264 | 0.000–0.599 |
| carpus | trapezoid–capitate | 0.000–0.718 | 0.000–0.728 |
| carpus | capitate–hamate | 0.000–0.219 | 0.000–0.242 |
| carpus | scaphoid–trapezium | 0.000–0.711 | 0.000–0.688 |
| carpus | scaphoid–trapezoid | 0.000–1.087 | 0.000–1.465 |
| carpus | scaphoid–capitate | 0.000–0.542 | 0.000–0.876 |
| carpus | lunate–capitate | 0.000–0.366 | 0.000–0.761 |
| carpus | lunate–hamate | 1.237–3.443 | 0.174–4.168 |
| carpus | triquetrum–hamate | 0.000–0.152 | 0.000–0.669 |
| tarsus | talus–calcaneus | 0.000–0.382 | 0.000–0.590 |
| tarsus | talus–navicular | 0.000–0.347 | 0.000–0.907 |
| tarsus | calcaneus–cuboid | 0.000–0.590 | 0.000–1.057 |
| tarsus | navicular–medial cuneiform | 0.000–1.057 | 0.000–0.895 |
| tarsus | navicular–intermediate cuneiform | 0.000–1.200 | 0.000–0.993 |
| tarsus | navicular–lateral cuneiform | 0.000–0.714 | 0.000–0.924 |
| tarsus | medial cuneiform–intermediate cuneiform | 0.000–0.981 | 0.000–0.208 |
| tarsus | intermediate cuneiform–lateral cuneiform | 0.000–0.975 | 0.000–0.110 |
| tarsus | lateral cuneiform–cuboid | 0.000–1.218 | 0.000–1.319 |
| tarsus | navicular–cuboid | 0.000–0.856 | 0.000–1.084 |

### Reviewable cases, without claiming a defect

- **Lunate–hamate (optional wrist connection):** nonzero AABB lower bounds (LEFT 1.237; RIGHT 0.174 source units), vertex upper bounds 3.443 and 4.168. This *source individual's surface-mesh-label relationship* may reflect morphology, segmentation or pose; it **must not be upgraded to a missing normal joint or production rig error**. Optional joint contact is not universal.
- **Medial/intermediate and intermediate/lateral cuneiform pairs:** bilateral vertex-proximity upper bounds differ (0.981/0.208 and 0.975/0.110 native units). Do not use as anatomical asymmetry until source units, imaging registration and original segmentation quality are reconciled. Sampled donor N=1.
- Several other pairs show an AABB lower bound of zero and small nearest source-vertex distances; this **does not prove that the surfaces intersect or that cartilage is compressed**. The nearest vertex may be a source segmentation fragment rather than the genuine articular patch.
- The **8 original Source PR38 measurements reproduce at original 3dp precision**, supporting computational cross-run consistency, not physiological validity.

**Engineering completion:** all 30 wrist/foot original meshes were processed, and 44 candidate label-pair proximity intervals recorded with SHA provenance. **Clinical/cartilage/muscle/ligament/ROM/correct joint axes still unresolved, no accepted c005 geometry, CP1 Gate6 remains blocked 0 READY /9 PARTIAL /3 BLOCKED.**
