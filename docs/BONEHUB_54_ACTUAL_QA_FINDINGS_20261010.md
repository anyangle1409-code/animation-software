# HGPT whole-region 54-STL actual source and QA findings — 10 October 2026

**Verified source audit:** GitHub Actions run [38074136528](https://github.com/anyangle1409-code/animation-software/actions/runs/38074136528), 50/50 first-party tests passed. The run downloaded **all 54 actual male STL files** (16 wrist carpals, 14 tarsals, 24 ribs), at the immutable BoneHub source revision \`ac8de2b38f5ae1a0996053ca0639dd6ae43358f1\`. Every STL's original raw-byte SHA256 matches the source manifest LFS OID or the independently pinned example, and input sizes agree with source metadata. No original mesh, CT, identifying image or Blender asset is in Git.

Evidence artifact: **bonehub-54-stl-provenance-topology-no-raw-mesh**, attached to run 38074136528. Contains 54 exact raw source SHA256 pins and per-file numeric diagnostics; artifact ID 11677697672. The current report used no inferred physical units, patient-to-HGPT transform or anatomy acceptance.

## Quantitative QA over the 54 source files

- **950,008 binary STL triangles** parsed.
- **122 exactly degenerate source triangles** (zero geometric cross product).
- **17 undirected edges** with more than two nondegenerate incident faces.
- **0 single-incidence open edges** under exact float32 source-vertex position welding.
- **46 of 54** pass the strict exact-vertex consistency predicate: all faces nondegenerate, single vertex-connected component, no open/nonmanifold or same-direction paired edges.
- **8 of 54** do not pass that predicate. The reason may include tiny islands or segmentation artefacts, not necessarily a material defect in the primary bone volume.

These are numerical engineering QA results. The 46 are **NOT anatomically accepted bones**, and the eight are **NOT automatically unusable**. In particular, no inference about articular surface, true bone continuity, correct size, clinical morphology, interbone cartilage or physiological joint motion follows from closed STL topology alone.

## Exactly which eight source STL meshes need review

| Source mesh | Raw STL triangles | Zero-area triangles | Nonmanifold edges | Exact-weld connected components |
|---|---:|---:|---:|---:|
| LEFT calcaneus | 37,816 | 0 | 0 | 2 |
| LEFT intermediate cuneiform | 4,920 | 8 | 0 | 3 |
| LEFT talus | 24,812 | 38 | 0 | 7 |
| RIGHT hamate | 4,608 | 8 | 0 | 3 |
| LEFT rib 1 | 15,360 | 6 | 0 | 2 |
| RIGHT rib 1 | 17,708 | 32 | 0 | 5 |
| LEFT rib 3 | 28,344 | 16 | 5 | 8 |
| LEFT rib 4 | 31,872 | 14 | 12 | 7 |

All eight have **zero boundary edges** under exact matching, so the defects are not simply open cut edges. They need component-size and local nonmanifold scrutiny before any use as skeletal targets. Degenerate triangles may create extra vertex groups; whole-bone identity cannot be inferred from group count.

### Source integrity pins for the flagged meshes

The following are raw verified source hashes, not hashes of modified or repaired models:

- \`FOOT_LEFT/CALCANEUS_LEFT.stl\`: \`5e160f34aff9c2bfb1e3b6546add17a083ec4f6bb4be0f29392e714d44132eb9\`
- \`FOOT_LEFT/INTERMEDIATE_CUNEIFORM_LEFT.stl\`: \`8ddda7e43de0a58eb89e960be33894acc0438edf8f79770eef01a99c8a5380b9\`
- \`FOOT_LEFT/TALUS_LEFT.stl\`: \`b79dcb8037223d2652e300cb42124c9d4e16dfedcc49ff36b4d44ed3fc24602e\`
- \`HAND_RIGHT/HAMATE_RIGHT.stl\`: \`bbb430688f01ed97ce4dfc713ace4afb4df1a5787f6bcf0262ffa51d75a65c2b\`
- \`THORAX/RIB_1_LEFT.stl\`: \`5b5216f2df8cac598aa94b1fe89039ce6734a15e520b9f1f788ddae3a6070295\`
- \`THORAX/RIB_1_RIGHT.stl\`: \`fbf031187ac17d7949c5b498bd971e055c9faabe4b133f83b413fcc4d2138636\`
- \`THORAX/RIB_3_LEFT.stl\`: \`84c9ddd3b15a7eb72d9d2709f9fd2ebb8bb999c601d28d53e25770972af06e83\`
- \`THORAX/RIB_4_LEFT.stl\`: \`ef49d0a539d69b0254ad402ee745263aa3a360b42bff54dc2e1097320a8911db\`

## Priorities for isolated engineering follow-up

1. Group source nondegenerate triangles by connected component and compute *face counts and relative geometry extent* per component. Determine whether the small detached islands are finite-volume shapes, zero-area remnants or ambiguous surface segmentation islands.
2. Inspect the 17 overused edges in LEFT ribs 3–4. Do not automatically manifoldize or delete source faces; preserve raw bytes and hashes.
3. Cross-check STL source unit, frame, laterality and CT registration before interpreting sizes as millimetres or anatomical left/right.
4. Obtain independently sourced population geometry or explicit rights to appropriate comparative data. BoneHub VSD 30-subject lower-limb data are listed as CC BY-NC-SA and **must remain separated from any commercial product data** until permissible terms are established (see \`VSD_30_SUBJECT_FOOT_SOURCE_LICENSE_QUARANTINE_20261010.md\`).
5. Identify joint-specific articular landmarks/patches and compare them to independent source cohorts before proposing any change to canonical coordinates.

**No CP1/Gate6 promotion. Readiness stays 0 READY / 9 PARTIAL / 3 BLOCKED. The original r95/a003/c001–c004 character and all Work/Claude branches remain unchanged.**
