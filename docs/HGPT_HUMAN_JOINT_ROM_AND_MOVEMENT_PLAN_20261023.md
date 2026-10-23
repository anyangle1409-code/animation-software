# Home Gym PT: Human Joint Range of Motion and Whole-Body Motion Reference
**23 October 2026 — source-backed clinical/biomechanics information; no model movement certified yet.**

This extends [the anatomical modelling roadmap](HGPT_ANATOMICAL_MODEL_MUSCLE_ACCURACY_ROADMAP_20261023.md) with researched human movement. Machine-readable data: [HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json](anatomy/HGPT_HUMAN_JOINT_ROM_REFERENCE_V1.json). Validator + non-production descriptive preview: `scripts/cloud_body_analysis/human_rom_reference.py`; synthetic guards: `scripts/cloud_body_analysis/tests/test_human_rom_reference.py`.

## Owner's intended behaviour

The goal is **one anatomically plausible, naturally deforming human rig** where we can author a new exercise by specifying the activity, variants, joint paths, movement phases and objects, rather than re-sculpting the character for every individual exercise. This is a rigorous aim, not a guarantee: new movements, loads, orientations and unusual combinations still require tests for collisions, tendon routing, skin contacts, exercise mechanics and visibility.

A pose should be plausible when the whole chain of human joints, tissues and contacts is considered, not merely when every individual Euler angle fits an arbitrary range.

## Research foundations and exact meaning

**CDC (Soucie et al. 2010)**: measured more than 600 individuals without known conditions affecting joint mobility. Published joint ROM population means and **95% confidence intervals for those means**, grouped by age and sex, for shoulder, elbow/forearm, hip, knee, ankle. These do not define individual maxima, safe exercise limits, or a distribution for a specific user. Full reference: https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html

**ISB part I and II**: conventions for anatomical segment/joint coordinate systems. Particularly important for comparing positions from Blender, camera views and export/runtime animations. They are standards for how to **describe/measure** motion, not a table of safe movement maxima:
- Part I ankle/hip/spine: https://pubmed.ncbi.nlm.nih.gov/11934426/
- Part II shoulder/elbow/wrist/hand: https://pubmed.ncbi.nlm.nih.gov/15844264/

**Norkin & White, 6th ed., Appendix A**: normative goniometry compiled from studies and an AAOS comparison column. Its values are **separately labelled secondary context**, not mixed into CDC sample means: https://fadavispt.mhmedical.com/content.aspx?bookid=3621&sectionid=303386712

**Young-adult cervical/lumbar study (2023)**: 300 healthy volunteers ages 18–29; goniometric *regional* mean and SD for flexion, extension, bending and rotation; these are not per-vertebra limits: https://jtss.org/articles/normative-values-for-cervical-and-lumbar-range-of-motion-in-healthy-young-adults/jtss.galenos.2023.33042

**2025 scapular kinematics systematic review**: independently moving scapula from the beginning of elevation; variation in upward rotation, posterior tilt and axial orientation means a universal fixed scapulohumeral ratio is not supported: https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/

**ISB multisegment foot standard (2021)**: don't reduce foot + toes to one ankle hinge: https://www.isbweb.org/activities/standards

## Verbatim selected CDC references (age 20–44)

| CDC clinical measured movement | Female population mean | Male population mean |
|---|---:|---:|
| Shoulder complex flexion | 172.0° | 168.8° |
| Elbow flexion | 150.0° | 144.6° |
| Forearm pronation | 82.0° | 76.9° |
| Forearm supination | 90.6° | 85.0° |
| Hip flexion | 133.8° | 130.4° |
| Hip extension | 18.1° | 17.4° |
| Knee flexion | 141.9° | 137.7° |
| Ankle dorsiflexion | 13.8° | 12.7° |
| Ankle plantarflexion | 62.1° | 54.6° |

The authoritative JSON also pins CDC's corresponding 95% confidence interval for each group mean and adds the age 45–69 adult reference cohort (all 11 measured motions × 2 sex groups × 2 age bands = **44 recorded group rows**). These are not individual maxima. The original CDC "elbow extension" values can include measured hyperextension, so a fixed 0° hard stop would also misread clinical measurement conventions.

**Selected AAOS normative goniometry context**, not a physiological hard ceiling: shoulder complex abduction ~180°, shoulder extension ~60°, wrist flexion ~80°, wrist extension ~70°, wrist radial deviation ~20°, ulnar deviation ~30°, forearm pronation/supination ~80°. These are a separate source type, not imputed into CDC age/sex groups.

**Cervical / lumbar group context**, NOT single intervertebral motion: cervical flexion mean ~57.7° (SD 8.2°), extension ~59.1° (SD 10.2°); lumbar flexion ~69.9° (SD 14.5°) in one young adult sample. Lumbar values are *regional* and should not be divided evenly among bones. Distinct population/methodology from CDC.

## Machine-readable atlas built now

The `V1.json` reference defines:
- **43 permanent coordinate names** from shoulder complex through scapula/clavicle/GH elbow/radius-ulna, wrist/fingers/thumb, cervical/thoracolumbar spine, hip/knee/patella, ankle/subtalar/midtarsal/forefoot/toes.
- **44 CDC group mean + CI measurements**, plus **12 AAOS nominal clinical goniometry values** and **12 young adult regional cervical/lumbar group means + SD**.
- Six source links plus an added 2023 cervical/lumbar population reference (seven sources total), source identifiers on every metric.
- **19 conceptual joint and compound movement tests** with separate targets for bilateral arm motion, elbow forearm pronation/supination, wrist/grip, spine, hips, knees, feet, overhead press, squat and curl.
- Coupling rules for shoulder/scapula/clavicle, radioulnar rotation, patellofemoral/knee, multisegment foot and biarticular muscle routing.
- Every native hard limit, axis mapping, model source hash, anatomical side mapping, executed Blender pose, accepted image and anatomical approval **UNRESOLVED / NULL / NOT_GRANTED**.
- Muscle highlighting is explicitly **DEFERRED**: permanent IDs should be retained for future use, but no UI style or visual implementation is selected.

## Proposed validation gates (strict order, no premature PASS)

**0. Provenance and coordinate calibration.** Identify one exact source model file, frozen rig rest transforms, all skeleton bones/joint-centre landmarks. Resolve anthropometric proportional landmarks and anatomical left/right against 3D axes and camera, not `_l` labels. Match each canonical semantic coordinate to the actual rig and define neutral zero and positive direction. Until this is reviewed, CDC's elbow flexion number **cannot** be automatically compared against Blender Euler X/Y/Z.

**1. Isolated joint articulation.** In memory on original-hash-verified candidate copies, test each major axis from neutral through *relevant, reviewed* intermediate poses, then return to neutral. Inspect skin and joint rotation centres, forearm radius/ulna and tendon routes, ring/pinching at elbow and knee, glenohumeral rotation, foot arches/toes. Test L and R independently. Do not invent a numeric limit where the actual rig lacks calibrated axes.

**2. Coupled skeletal motion.** Test scapular upward rotation, clavicle rotation/elevation, trunk stabilization, GH elevation under overhead reach; hip-knee-ankle coordination and foot contacts through squat; elbow flexion with different radioulnar orientations. No hard-coded universal scapular rhythm. Record path direction and bone-/skin-space continuity. Knee flexion cannot be treated as a 3-axis ball joint; forearm pronation does not twist the hand as if the radius/ulna were a single static cylinder.

**3. Tissue shape under skin.** When soft tissues and tendons are fitted, test *movement with explicit visual activation zero*, then *activation at fixed pose*, then combined. Ensure medial/lateral elbow volume continuity and a believable distal biceps tendon/brachialis/brachioradialis layering; shoulder-cap/axilla and hip/groin shape require matched front/back/side and rotating-camera views. Avoid artificial muscle-belly balloons. Skinning/correctives must preserve topology and envelope without collision or pop.

**4. Contact, resistance, stability, variants.** Wrist/dumbbell grips, soles, toe-off, floor, balance/trunk and bilateral/uneven load. Full trajectories rather than a few endpoints; compare neutral/loaded poses with active/eccentric/eccentric-return phases. A physiologically attainable passive range does not automatically imply a good or safe exercise technique.

**5. Full exercise and mobile application.** Only AFTER generic component validation, connect PR124 exercise-to-muscle contracts to real reviewed muscles. Exports must reproduce approved bone+skin animation and educational labels in the first-party mobile renderer; no runtime force/EMG inference or untested skin sim.

Every gate requires source SHA256, calibrated coordinate provenance, measured numerical evidence, before/after matching renders, and an explicit **PASS/FAIL/BLOCKED** result. A report of clinical population means is never a passing Blender test.

## Current known shortcomings (explicit BLOCKED)

- Three reconstructed model .blend candidates (W8/V14/R120) do not establish verified equivalence to lost original authoring files; V14 vertex discrepancy and W8 displacement mismatch remain.
- Their existing 77-bone rigs are not certified, and old 67-bone runtime bridge mapping is unresolved.
- Shoulder/axilla, squat/hip, foot and grip deformation/contacts all fail current movement acceptance; additional elbow volume concern identified by owner is not yet quantitatively localized.
- Static S7 corrective and helper metadata do not establish actual loaded pose. Named skin-weight groups do not define accurate muscle insertions.
- No native motion limit, clinically safe exercise envelope or individual anatomical model can be asserted from literature means alone.

## Implementation and tests

```bash
python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_human_rom_reference.py -v
python scripts/cloud_body_analysis/human_rom_reference.py --output /tmp/hgpt_human_rom_readiness.json
```

The output explicitly states **source-backed research ready**, native anatomical calibration and exercise validation **NOT_GRANTED / NOT_RUN**. The existing isolated phone GitHub Actions workflow's standard Python test discovery includes these tests; check the triggered run and logs before recording them as verified.

**Owner's principle:** the model is a real moving *human*, not a collection of exercise-specific pose exceptions. Full realistic deformation still requires validation of new exercise variants, contacts and loads even after general joints are accepted. This document is a no-model-edit research and planning artifact; no production, original Blender file, muscle binding or app code is altered.
