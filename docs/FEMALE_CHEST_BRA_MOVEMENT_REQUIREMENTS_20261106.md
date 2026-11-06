# Female chest, breast and sports-bra movement requirements (6 Nov 2026)

**Status:** limited structural tests only. No movement development has started. Female V1 is not approved.

## Scope

**In scope:**
- what the female standing candidate needs before V1 is frozen;
- what was checked and fixed now;
- what is deliberately left for after both standing characters are approved.

**Out of scope, and untouched:**
- the male 07c;
- the production model;
- PT_MODEL_VERSION.

## 1. Test (`scripts/meshy/female/chest_bra_elevation_test_f_blender.py`)

**Method:**
- Both upper arms are raised in the coronal plane, about the shoulder joint, to 0°, 45°, 90°, 135° and 170° from the downward vertical.
- 0° means the arms hang by her sides. Her rest pose is an A-pose.
- The movement is glenohumeral only, because scapulohumeral rhythm is **off** in the first-party exercise system (`docs/CANONICAL_SKELETON_FREEZE.md`). This is what a shared clip would do to her today.
- The test is read-only.

**Measured:**
- **Breast tissue:** body vertices under the cups (front chest box, 2,219 vertices) and its core, which is everything within 60 mm of each breast's front-most point.
- **Bra:** fit to the skin.
- **Chest:** self-intersections.

**Renders:** clay, front, side, back and chest views at every elevation.

| elevation | breast core stretch p95, F10d → F10e | breast centre shift in the sternum frame (L / R mm), F10d → F10e | skin outside the bra (verts) | chest self-intersections |
|---|---|---|---|---|
| 0° (arms by the sides) | 1.01 → **1.00** | 5.4 / 4.7 → **2.6 / 2.3** | 71 → 76 | 322 → 322 |
| 45° | 1.12 → **1.00** | 4.3 / 3.7 → **2.1 / 1.8** | 2 → 5 | 0 → 0 |
| 90° | 1.57 → **1.00** | 13.3 / 11.5 → **6.4 / 5.7** | 9 → 29 | 52 → 53 |
| 135° | 2.02 → **1.00** | 20.2 / 17.5 → **9.8 / 8.7** | 27 → 34 | 97 → 97 |
| 170° | 2.22 → **1.00** | 23.6 / 20.4 → **11.4 / 10.2** | 23 → 24 | 107 → 106 |

**Bra fit, all elevations, F10e** (the bra weights follow the skin, so these do not change with the pose):

| Part | Off the skin, p95 | Off the skin, max | Vertices over 6 mm |
|---|---|---|---|
| Band | 4.0 mm | 7.7 mm | 5 |
| Cups | 4.5 mm | 7.3 mm | — |
| Straps | 4.0 mm | 5.7 mm | 0 |

The distances measure fabric over the 3 mm inset under-garment body, so there are no floating garments.

**Reading the results:**
- At 0° the arms lie against her sides with no clearance. The self-intersections there are arm against torso, and they are the same before and after.
- At 90° and above, the remaining intersections and the skin through the bra's side panel are in the armpit. That is the shoulder-only motion (see section 3).

## 2. What was found and fixed now (F10e, `scripts/meshy/female/breast_rig_f_blender.py`)

- **Problem: the breasts carried arm and girdle skin weight from the bone-heat bind.** Upper arm, clavicle and scapula shares averaged 18%, with 720 of 2,219 vertices over 20%. The breasts stretched with the upper arm: core stretch 2.2× and the centre moving 24 mm at 170°. This is the male-style chest weighting she must not inherit.
- **Fix: her own breast weights.**
  - 75% of the arm and girdle share moves to the ribcage (`spine_03`). It is faded over 50 mm towards the armpit, so the axillary tail and the pectoral border still follow the arm a little.
  - Result: the core no longer stretches (1.00 at every elevation), and the centre shift halves.
- **Fix: independently controllable breast soft tissue.**
  - `breast_l` and `breast_r` are deforming character helpers under `spine_03`.
    - Each head sits on the chest wall behind the breast, with the tail through its front-most point.
    - Weight rises to 0.55 at the front, falling to 0 at the base and the edges.
  - They do nothing at identity, so the standing pose is unchanged.
  - They let the movement phase add subtle follow-through, support and compression without touching the arm or contract bones.
  - The frozen 63-bone contract is unaffected, because the freeze document allows deformation helpers.
- **Fix: bra containment.**
  - Bra and shorts weights are re-transferred from the skin under them (nearest face, interpolated).
  - Cups, band, side panels and straps therefore move exactly with the skin: any breast-helper motion is contained by the cups.
  - At rest the skin is at least 1.4 mm under the fabric's outer face (F10c).

## 3. Outstanding deformation requirements (after both standing characters are approved)

1. **Shoulder girdle:**
   - Scapulohumeral rhythm, about 2:1 above 30°, with clavicle elevation and retraction and scapular upward rotation.
   - Her own scapula-glide helper, fitted to her back, never copied from the male.
   - The shoulder-only test is the worst case: most of the armpit stretch and crumple at 90°–170° comes from missing rhythm.
2. **Armpit and pectoral:**
   - Corrective shapes, or helper bones, for the anterior axillary fold (the pectoralis major tendon to the humerus) and the posterior fold.
   - Pectoral elongation at 135°–170°, which also drives the bra side panel.
   - Authored on her own mesh at the shared drive angles.
3. **Breast soft tissue**, driven through `breast_l` and `breast_r`:
   - subtle lift as the pectoral and ribcage elevate with overhead arms;
   - medial compression in the press, fly and push-up;
   - limited follow-through in dynamic moves (jumping jacks, running), damped, with a cap of a few millimetres inside a supportive bra;
   - no stretching onto the arm.
   - Driven by the chest, not by the upper-arm bones.
4. **Sports bra:**
   - **Band:** stays anchored to the ribcage (ribcage weights only) at every elevation.
   - **Side panel:** a corrective at 90°–170° so it follows the stretched armpit skin instead of folding. In the test it crumples where the skin under it crumples.
   - **Straps:** slide over the trapezius with clavicle elevation. A strap-slide helper, or a cloth-free corrective, is needed once girdle rhythm exists.
   - **Cups:** contain the breast-helper motion. Containment checks are needed in every exercise pose: skin-through-fabric count 0, floating cup or band under 6 mm.
5. **Contacts:** arms by the sides (0°) need hand-to-thigh and arm-to-torso clearance by the contact pass. The architecture document's "contact pass per character" rule applies.
6. **Compatibility:**
   - **Roll:** all 63 contract bones are aligned to the male roll convention in the parent frame (F10d). `metacarpal_index_r` was flipped by 173° before alignment.
   - **Clips:** shared clips drive her through the canonical names. Her helpers (forearm twist, breast) are driven by the character layer.
   - **Regression:** every reused exercise needs the full regression run on her (architecture document §2), including these chest metrics and the bra containment checks.

## 4. Evidence

- **Metrics:** `review-assets/meshy_retopo_20261105/female_f10/chest_test_F10d.json` and `chest_test_F10e.json`.
- **Renders:** the session review sheet `07_chest_bra_elevation` (licensed geometry; not committed).
