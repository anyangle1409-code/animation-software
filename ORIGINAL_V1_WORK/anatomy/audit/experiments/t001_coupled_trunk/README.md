# T001: isolated experimental coupled trunk rebuild (U10 + U5)

**Status:** experiment only. This is not a candidate and not c005, nothing is promoted, and production is untouched. The owner approved it on 9 October 2026 as "isolated experimental coupled trunk rebuild addressing U10 and U5".

## What is fixed and what is solved

**Held fixed** (byte-identical to c004; test-enforced):
- **Sacrum and pelvis:** the pelvic ring is a separate question.
- **C2, C1, skull and hyoid:** head height comes from stature.
- **Sternum, clavicles, scapulae and arms:** c003/c004 already put the bony sternal notch at the ANSUR suprasternale height (1,494.5 mm) and solved the shoulder girdle relative to it.
- **Legs.**

**Solved:** the column from S1 to C2, as explicit vertebral bodies plus non-zero discs.
- **Heights:**
  - lumbar from Hegazy 2014 male MRI;
  - thoracic bodies from source B (CT 2016), which the ANSUR check found compatible;
  - thoracic discs from the 2011 anatomical source;
  - cervical from Yukawa 2012 male;
  - all multiplied by one stature scale.
- **Angles:**
  - sacral slope, lumbar lordosis (Kim/Fang pattern), thoracic kyphosis and cervical lordosis (Reinhold pattern);
  - each has a Hasegawa male prior;
  - they are fitted by minimum χ² so the chain ends exactly on the fixed C2.

**Solution** (Hasegawa cervical prior):

| Angle | Fitted value | Male mean | z |
|---|---|---|---|
| Sacral slope | 37.0° | 40.9° | -0.406 |
| Lumbar lordosis (L1–S1) | 62.719° | 56.4° | 0.498 |
| Thoracic kyphosis (T1–T12) | 41.787° | 43.7° | -0.213 |
| Cervical lordosis (C2–C7) | -0.33° | −0.6° | 0.031 |

χ² is 0.4587.
- **Stature scale:** 0.99803, i.e. an implied source-cohort stature of 1.824 m.
- **Interpretation:** the sourced vertebra and disc heights close the fixed sacrum-to-C2 distance at population-mean curvature with essentially no rescaling. The column the evidence predicts fits this body.
- **Reinhold cervical prior:** z within 0.5, scale 0.995.

**Ribs.**
- **Heads:** each rib head stays rigidly attached to its articular level, so its offset from that level is preserved.
- **True ribs 1–10:** each keeps its exact length and re-aims at its unchanged anterior attachment. The residual is a costal-cartilage length change of 1.0 to +8.4 mm.
- **Floating ribs 11–12:** move rigidly with their vertebra.
- **Rib inclination:** flatter; for example rib 1 goes from 44.51° to 26.24° of descent.
- **No inclination source exists:** the Holcombe 2017 pump-handle angle frame is not mapped, so these inclinations are unverified.

## Checks (none of these were inputs to the solve)

| Check | c004 | T001 |
|---|---|---|
| T12/L1 vs pelvis-anchored lumbar prediction | +38.5 mm | **+6.2 mm** |
| Smallest disc centre gap | 0.0 mm (CP2 FAIL) | **3.19 mm** (CP2: 0 FAIL, endplate surfaces UNVERIFIED) |
| Sternal notch within the T2–T3 bodies (Razzouk 2023) | True | True |
| Notch to T2/T3 depth | 64.5 mm | 79.6 mm |
| Rib heads vs articular levels | preserved | preserved (within 1.5 mm of c004) |
| C7 tip vs ANSUR cervicale (grade-D tip offset) | -17.8 mm | **-29.0 mm** (worse) |
| Rib 10 anterior end vs ANSUR tenth rib | +28.0 mm | +29.3 mm (unchanged; anterior ends held) |
| Shoulder girdle and arms | — | unchanged (fixed) |

**Blender** (5.2.1): the CP3 round trip passes (max endpoint error 0.06 µm). In the isolated movement run, 135/135 tests pass integrity with the same mirror result as c004 (41/43).

**Checks against the run:**
- Solver vs Blender: AGREE.
- Joint frames: 0 issues and 0 sign flips.
- Frame continuity: 0 issues.
- Mirror: 0 failures.
- Amplitude provenance: TRACED.
- Crossing scan: no new crossings beyond c004's inherited hip-adduction tibia crossing (test design, L4).
- Interaction scan: no new pairs. Clavicle–rib-1 clearance improves by about 0.6–0.9 mm, and 2 clavicle–rib-2 approaches drop out.

**Movement vs c004** (`checks/run_comparison_vs_c004.json`; tolerance 1e-3° and 1e-6 m):
- **Changed:** 60 tests, all spinal or rib (36 thoracic, 14 rib inspiration, 6 cervical, 4 lumbar).
- **Unchanged:** all 75 limb, hand, head, girdle and glenohumeral (GH) tests.
- **GH singularity:** the plane of elevation is undefined at zero elevation and is excluded there; this is documented in `compare_isolated_runs.py`.

## Open problems (why this stays an experiment)

1. **Thoracic per-level shape** is c004's own, not sourced; only its total is solved.
2. **C7 drops about 11 mm against ANSUR cervicale.** It falls within the already OPEN thorax-pitch / C7–notch conflict and depends on a grade-D tip offset; it is not resolved.
3. **Rib inclination** has no usable source, and the rib-10 height residual (+28 mm) is unchanged.
4. **The sacrum is not moved.** Its position relative to the pelvis-derived P1 S1 frame (42 mm) is a separate pelvic item.
5. **Endplate surfaces, curved ribs and costal cartilage** do not exist yet, so contact and clearance are UNVERIFIED.

**Before / after renders:** `before_after/*.jpg`. Each pairs c004's committed render with the T001 render from the same script; framing is recomputed per record, so panels can be offset sideways.

**Rebuild:**
- `python3 scripts/anatomy_fit/build_experiment_t001_coupled_trunk.py --out-dir <new>` (deterministic).
- Tests: `scripts/test_t001_coupled_trunk.py`.
