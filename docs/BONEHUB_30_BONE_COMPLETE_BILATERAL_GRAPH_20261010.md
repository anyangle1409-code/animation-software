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
