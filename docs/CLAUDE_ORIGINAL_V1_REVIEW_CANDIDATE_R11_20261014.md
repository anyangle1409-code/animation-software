# ORIGINAL_v1 review candidate R11: re-meshed shoulder (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner:** asked "Is it still the mesh that's not right?", then answered "Yes please" to re-meshing the shoulder as a separate review copy.

## Why

Measured on R10, the shoulder and armpit are the coarsest region of the body.
- **Edge length:** median 19.7 mm, against 9.5 mm for the whole body and 9.4 mm for the face.
- **Armpit slice:** about 40 vertices in a 12 mm slice through the armpit and upper arm.
- **Deltoid:** irregular sliver triangles over the cap.

## What R11 is

**Parent:** R10. R11 is R10 with the shoulder and armpit re-meshed on both sides (`scripts/build_original_shoulder_remesh_blender.py`).

1. **Region:** faces within 15 cm of a glenohumeral pivot, or within 10 cm of the armpit vault. That is 2,362 faces.
2. **Loop subdivision of the region:**
   - each triangle becomes four;
   - the median edge goes from 19.7 to 8.8 mm (90th percentile 29 → 14 mm);
   - Loop's stencils round the surface (midpoints are used on the region boundary);
   - neighbouring faces are re-triangulated, so the mesh stays watertight and all-triangle.
3. **What is carried across:** every deform weight and every corrective shape key (K1, C1, S1, S3, S4) uses the same linear
   stencils, so each correction keeps its shape on the new vertices. The body has no UV map.

**Outside the region:** the body is unchanged (same indices, positions, weights and keys). The new vertices are appended after
index 17,945, giving 21,600 vertices and 43,196 triangles. The bones and the rig are unchanged.

## Runtime contract

Work's bridge guard requires exactly **17,946 body vertices** (`original_v1_functional_fullbody.EXPECTED_BODY_VERTICES`).
- **For review only:** R11 declares its own count in `scene["hgpt_review_body_vertices"]`, and
  `original_v1_review_candidate_drives` wraps the guard in memory so it accepts that declared count only.
- **Other files:** every other file is checked exactly as before. Work's module is not edited.
- **Shipping:** shipping a re-meshed body changes the runtime vertex-count contract (owner + Lane G, PR #26).

## Variants measured and rejected

| Variant | Result |
|---|---|
| BMesh `subdivide_edges` | its vertex handles were invalidated with this mesh's shape-key layers; the result was rippled skin |
| Explicit midpoint subdivision + Taubin smoothing | rippled skin: each old flat facet was kept and only cut into four, so the old facet edges showed through smooth shading |
| Loop subdivision + S4 corrections re-solved on the new mesh, scale 2 and 3 | lockout pairs 61 and 39, against 1 with the carried corrections; scale 3 tears the armpit |
| **Loop subdivision + carried corrections** | **selected** |

## Results

**Face counts:** the region now has four times as many faces. Counts of stretched faces are therefore not comparable with
R10, while overlap and collapse counts are.

**Full press at lockout:** self-intersecting pairs 17 → 1.

**All 13 benchmarks** (`r11_validation.json`), R10 → R11 (collapse / stretch / pairs):

| Benchmark | R10 | R11 |
|---|---|---|
| Bent-over row | 2 / 5 / 26 | 2 / 11 / **4** |
| Shoulder press (160° path) | 2 / 108 / 0 | **0** / 310 / 0 |
| Push-up | 3 / 63 / 42 | 3 / 73 / 44 |
| Grip | 0 / 6 / 18 | 0 / 10 / 20 |
| Deadlift | 38 / 22 / 311 | 38 / 26 / 313 |
| Others | — | identical, or within the face-count effect |

**Visual** (`press/shoulder_press_r10_vs_r11.gif`; the photo comparison is kept outside the repo):
- **Better:** the skin is smoother everywhere, and the jagged shoulder outline and slivers are gone.
- **Unchanged:** the shapes are R10's. The deltoid is still flat, the armpit hollow shallow, and the crease remains at lockout.

## What this shows

A finer mesh was necessary but is not sufficient. It removes the faceting and gives room for detail, but it does not
create anatomy: the deltoid mass and the armpit hollow between the pectoral and latissimus folds still have to be shaped.

**Next (owner decision):**
- authored (sculpted) corrective shapes on this mesh at the press stages, against the owner's reference photos;
- or muscle/volume simulation.

The procedural shapes have reached their limit.

## Tests

`scripts/blender_tests/test_original_review_candidate_r11.py`, 6 native tests (CI: `original-review-candidate-r1.yml`):
- **Identity:** includes the declared vertex count.
- **Mesh:** watertight and all-triangle.
- **Rig, groups and keys:** unchanged.
- **Region:** finer (median under 10 mm, from over 18 mm), and only the reported Loop-repositioned original vertices move.
- **Keys outside the region:** unchanged.
- **Weights:** normalised.
- **Guard:** accepts only the declared count.
- **Benchmarks vs R10.**

R1–R10 tests still pass.
