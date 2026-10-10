# CP1 wrist/foot: actual immutable BoneHub source mesh proximity (10 October 2026)

**Purpose:** reduce the previously unresolved carpal/tarsal source-contact evidence gap without requiring the laptop, private CT, Blender rendering, mesh changes or unsupported articular centre guesses.

## What this tool truly measures

First-party, dependency-free source-vertex reader and exact balanced 3D nearest-vertex query: `scripts/anatomy_fit/bonehub_carpal_tarsal_vertex_proximity.py`.

1. Reuse existing immutable 54-STL source manifest from PR #34. For **12 unique files**, acquire actual full binary STLs into a private cache; every one is checked byte-for-byte against the frozen original upstream LFS SHA256 and size. All headers must declare `SPACE=LPS`; RAS or conflicting headers fail.
2. Read every triangle, retain **all** float32 vertex coordinates belonging to a *nonzero-area face*. Drop only degenerate-only vertices from the proximity point set, **not** any detached triangle island or source face. **No original file is modified**.
3. Build a balanced nearest-neighbour index (all valid vertices; no sampling, no decimation), compute exact **minimum VERTEX-TO-VERTEX distance** for these bilateral filename pairs:
   - scaphoid ↔ lunate (left and right);
   - talus ↔ calcaneus (left and right);
   - talus ↔ navicular (left and right);
   - calcaneus ↔ cuboid (left and right).
4. Report per-pair a lower bound from the two source surface bounding boxes and an upper bound from the nearest **surface vertices**. Both are expressed **only in unaccepted native source coordinate units**; neither is a true minimum triangle-to-triangle surface distance, signed gap, penetration determination or patient articular contact. The source donor is the *same one NLM Visible Human male*, **not** 10 independent cohorts and not an 182 cm reference human.

The actual source mesh of a complex bone surface may have triangles whose surfaces nearly touch or intersect **between** their sampled vertex sites: nearest vertex distance is an upper bound, never the accepted contact distance. A negative/signed separation, cartilage thickness, joint contact patch, connected articular surfaces, true 3D registration, and joint centre cannot be inferred. Bbox separation is a lower bound but overlapping boxes are also **not** contact evidence.

**Engineering/QA contribution:** independent exact full-point-cloud proximity means the source STL **relative geometrical adjacency** can be examined and obvious misleading centre/AABB-only proxies rejected. It will support independent bilateral checks on Work's later private CT registration once source-to-CT affine/units and anatomy labels are independently verified.

## How to run with no laptop

1. Inspect GitHub Actions `Actual bilateral source carpal-tarsal vertex proximity`; it runs the offline synthetic adversarial checks and **downloads each of the ten frozen/hashed public BoneHub source files privately on an Actions runner**, not into Git.
2. Its successful artifact `noncanonical-8-bilateral-source-mesh-surface-vertex-gap-ranges` contains eight paired numeric source-space bounds, labels and immutable file checksums **only**. It contains no source patient bytes/mesh/STL/image or raw source vertex coordinates.
3. Do **not** turn those numbers into millimetres or skeleton geometry before source-grid registration, no-transform source-coordinates agreement, accepted physical units and documented contact patch correspondence.

To reproduce on a machine with internet access:
```
python scripts/anatomy_fit/bonehub_carpal_tarsal_vertex_proximity.py \
  --private-dir /path/outside/repo/private-bonehub \
  --output /path/outside/repo/private-bonehub/source-bilateral-gap-report.json \
  --download
```
Without `--download` it works only from the exact already-SHA-verified private cache. It never overwrites an existing source file or report.

**Acceptance:** no source bone endpoints, bone-to-bone articular centres, joint surfaces, anatomical population envelope or correct ankle/wrist kinematics accepted. **0 READY / 9 PARTIAL / 3 BLOCKED.** Anatomically blocked wrist/tarsal regions still require actual independent contact surface identification, physical frame matching and neutral-pose joint correspondence. This is source-bound geometric measurement progress, not premature CP1/Gate6 completion.

Source attribution: BoneHub Visible Human 3D Models source revision `ac8de2b38f5ae1a0996053ca0639dd6ae43358f1` (University of Twente/Visible Human single male, CC BY 4.0 declared; original upstream terms still govern reuse); see PR #34 frozen source audits.
