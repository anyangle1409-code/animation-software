# Claude native pass on the muscle-layer experiment: 24 October 2026

Branch: `claude/muscle-layer-native-20261024`, based on Work's `work/experimental-anatomical-muscles-20261022` at
`7c820d68`. Work's files are unchanged; this pass only adds files. Nothing is merged. The R41 source and its copy are
never saved. Muscle highlighting stays deferred, and the permanent IDs are used as they are.

## What was executed (previously BLOCKED in the handoff: "native Blender not executed")

**1. Source and copy.**

- The pinned R41 blob was extracted from
  `025d5f28fa7eba2064fba565b1c9b60119cdd2cb:ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend`.
  It is 5,294,269 bytes, SHA256 `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`, matching the pin.
- `prepare.py` made the experiment copy, with the same SHA256.

**2. Native inventory.**

- `inspect_blender.py`, unchanged, run with Blender **5.2.1 LTS** (the `bpy` module, factory settings, scripts disabled).
- Source unchanged before and after.
- Output: `native_20261024/native_inventory_R41.json`.
- Contents:
  - `HGPT_ANATOMICAL_MASTER`: a 206-bone anatomical skeleton (`anat_*`);
  - `HGPT_CANONICAL_V4_ORIGINAL`: the 67-bone runtime rig;
  - body `HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE`: 21,600 vertices, 43,196 faces, an ARMATURE modifier, 77 vertex groups
    and 79 shape keys;
  - 51 landmark empties (`LM_*`) and the `HGPT_JOINT_*` joint objects.

**3. Anatomical side, measured.** Anatomical `*_left` bones and landmarks lie at +X. The runtime V4 `_l` bones lie at
−X. So anatomical left drives runtime `_r` on this rig, which confirms Work's F-SIDE-001 note natively.

**4. ISB landmark crosswalk** (`native_20261024/isb_landmark_native_crosswalk_R41.json`). Work's 46 ISB requirements
(`HGPT_ISB_LANDMARK_REQUIREMENTS_V1.json`) against R41's own landmark empties:

- **34 have a native candidate:**
  - IJ and PX;
  - per side: TS, AI, AA, SC, AC, GH centre, EL, EM, RS, US, ASIS, hip joint centre, both femoral epicondyles and
    both malleoli.
- **12 are missing:**
  - C7 and T8 (vertebra bones exist, spinous tips not marked);
  - PC ×2 (coracoid);
  - PSIS ×2;
  - calcaneus ×2 and second metatarsal head ×2 (the bones exist);
  - hallux MTP ×2 (`HGPT_JOINT_mtp_1_*` exists).

None of these are verified:

- several are skin projections;
- the scapula placement metadata says `confidence: low`;
- the scapula looks large: TS–AA (spine of scapula) is 227 mm and AA is 258 mm from the midline.

Note for the Body v2 lane: the body_v2 blends carry these 51 empties at their **R41** positions, but their runtime
skeleton was refitted. The landmark positions are therefore stale for body_v2 and must be re-bound before use there.

**5. ISB scapula frame** from AA, TS and AI (Wu et al. 2005: Zs from TS to AA, Xs normal to the plane pointing forward,
Ys perpendicular to both):

- scapular plane 18.5° from the frontal plane;
- tipped 6° forward;
- left and right mirror-exact.

This frame now drives the corrected shoulder girdle in the Body v2 lane (`shoulder_girdle_candidate.py`,
`V2_GIRDLE_FRAME=isb`, on `claude/r120-surface-candidate-20261023`).

**6. Proposed attachments, one side (anatomical left).** Made by
`propose_upper_limb_anchors_blender.py` (new, read-only) and stored in
`native_20261024/proposed_anchors_left.json`.

- Twenty shoulder and arm muscles, each with an origin and an insertion anchor in the binding format: bone-local
  `local_m` on the `anat_*` bone, plus the rest world point and source SHA256.
- Each anchor records its rule, for example "deltoid tuberosity: 45 % GH→EJC, 12 mm lateral" or "olecranon: 22 mm
  posterior to the elbow joint centre".
- Rest straight-line lengths:

  | Muscle | Length |
  |---|---|
  | Biceps (long head) | 33.9 cm |
  | Brachioradialis | 32.5 cm |
  | Triceps (long head) | 25.8 cm |
  | Deltoid heads | 15.2–17.0 cm |
  | Brachialis | 15.3 cm |
  | Pectoralis major (sternocostal head) | 23.2 cm |

- Broad origins (latissimus, pectoralis sternocostal, serratus, trapezius) are represented by **one** point and marked
  "fan required". They are not finished attachments.
- `review` is left empty and `wrap_reviewed` is false, so `registry.binding_errors()` keeps every one of them as
  **not ready**. These are proposals, not reviewed bindings, and they are not merged into `registry_seed.json`.
- Image: `native_20261024/proposed_anchors_left_front_side_back.jpg` (anchor lines over the anatomical skeleton guide).

## Still blocked or not done

- **Reviewer sign-off** on every anchor; the **right side** (to be derived and checked independently, not mirrored
  blindly).
- **Fans and digitations** for the broad muscles. **Wrap paths** for the long biceps tendon (intertubercular groove),
  the triceps over the olecranon and the deltoid over the humeral head.
- **Belly and tendon geometry**, volumes, layer and contact maps, and skin masks.
- **No muscle mesh was added** to any blend; the experiment copy is unchanged.
- The **12 missing ISB landmarks** above.

## Right side (added)

`native_20261024/proposed_anchors_right.json` was derived **independently** from the right-side landmarks, using the same
rules and the same script with `right`. The copy was unchanged afterwards (SHA256 `4c44b1fe…`).

**Mirror check against the left proposals:** 39 of 40 anchors agree with the mirrored left anchor to within 0.01 mm.
The exception is the pectoralis major sternocostal origin, which differs by **2.44 mm**. Its rule uses the IJ–PX
midpoint, and R41's own `LM_sternum__px_skin` sits 2.4 mm off the midline (x = −0.0024 m). That asymmetry is in the
source landmark; it is flagged for landmark review, not corrected here.

Both sides remain **PROPOSED, UNREVIEWED**.

## Path-length direction check against the exercise contract (added)

Work's contract asks for path-length directions to be checked "in Blender ... against the scene". That check is now run
natively by `path_length_direction_check_blender.py` (read-only; the copy's SHA256 is unchanged, `4c44b1fe…`).

**How it works**

- R41's `HGPT_ANATOMICAL_MASTER` has **no constraints** to the runtime rig (posing `forearm_r` moved `anat_ulna_left`
  by 0.0 mm). The anatomical chain is therefore posed directly: clavicle → scapula → humerus → ulna/radius, as rigid
  rotations about R41's own SC, AC, GH and EJC landmarks.
- Every rotation sign is fixed by a landmark probe.
- The anchors are the proposals' bone-local points. Posing to rest reproduces `world_rest_m` within 0.007 mm.
- The girdle is coupled to humerothoracic elevation by approximate literature ratios (rule of thumb, not patient
  values). Per degree of elevation:

  | Motion | Ratio |
  |---|---|
  | Upward rotation | 0.33 |
  | Posterior tilt | 0.12 |
  | Clavicle elevation | 0.08 |
  | Clavicle retraction | 0.12 |

  External rotation is about 0.
- Control poses are the mid-points of the contract's joint targets:
  - curl: elbow flexion 10° → 112°;
  - press: elevation 35° → 160° with the elbow going from 92° to 8°.
- Paths are straight lines. Serratus anterior is the exception: it is wrapped on an elliptic cylinder fitted to the
  torso at its origin height.

**Results (left side; the right side is identical, 22 / 6 / 2 / 6)**

| Exercise | Matches | Mismatches | Contract "variable" | No anchors in proposal |
|---|---|---|---|---|
| Curl (concentric and eccentric) | 12 of 12 | 0 | – | subscapularis (2) |
| Press (press and lower) | 10 | 6 | supraspinatus (2) | teres minor, subscapularis (4) |

Curl changes as a fraction of rest length:

| Muscle | Change | Contract |
|---|---|---|
| Biceps long | −16 % | shortening |
| Biceps short | −17 % | shortening |
| Brachialis | −26 % | shortening |
| Brachioradialis | −27 % | shortening |
| Triceps long | +7 % | lengthening |
| Infraspinatus | 0 % | near-isometric |

Every curl result matches the contract.

The press mismatches are three muscles, each failing in both the press and lower phases:

1. **Triceps long: the model says lengthening (+4.9 %); the contract says shortening.**
   - The head crosses both joints. 125° of shoulder elevation lengthens it more than 84° of elbow extension shortens it.
   - The result is the same under both girdle models.
   - This is a contract question for Work or the owner, not an anchor error. The overhead position is the one that
     stretches the long head. "Near-isometric or lengthening" may be the correct entry.
   - The contract is Work's file, so it is **not edited here**.
2. **Trapezius lower: the model says lengthening (+55 %); the contract says shortening.**
   - This result is **not trustworthy**. With the pivot at the AC joint (the only pivot that keeps the AC joint closed
     in a rigid chain), 52° of upward rotation swings the root of the spine about 11 cm laterally and 10 cm down. That is
     more lateral travel than the scapula shows in vivo.
   - Moving the pivot towards the root of the spine makes the result near-isometric (+1 %), but it opens the AC joint by
     9 to 19 cm. That is impossible, so that setting is reported only as a bound.
   - The direction needs scapulothoracic gliding (the scapula on the rib cage), which this rigid chain does not have.
   - **Unresolved; flagged.**
3. **Infraspinatus: the model says shortening (−9.7 %); the contract says near-isometric.**
   - The straight line cuts across the humeral head, and there is no humeral axial rotation in the pose.
   - It needs the wrap path and the press's humeral external rotation before it can be judged.

**An anchor defect found and fixed by this check.** The serratus anterior origin rule took a point 55 % along the
rib-5 bone. R41's rib bones are straight chords, so that point lay inside the thorax, 4 cm from the midline. The
first run's serratus therefore lengthened in the press.

- The new rule puts the origin on the lateral chest wall on the mid-axillary line, at the height of rib 5's anterior
  end. It is taken from the torso skin and inset 15 mm.
- Both sides were regenerated. Only the serratus origin changed, as the diff of the two proposal files confirmed.
- With the new rule and the thorax wrap, serratus shortens in the press (−25 %), as the contract says.

**Files:** `native_20261024/path_length_check_left_coupled.json` (main result),
`…_left_ac_only.json` (the first crude girdle), `…_left_coupled_pivot0.5.json` (pivot bound),
`…_right_coupled.json`.

**Not covered:** the squat. No lower-limb anchors are proposed yet.

## Lower limb: proposed anchors and the squat path-length check (added)

**Proposed anchors.** `propose_lower_limb_anchors_blender.py` (read-only; the copy is unchanged) proposes origin and
insertion anchors for the 12 muscles in Work's squat contract, on both sides:
`native_20261024/proposed_anchors_lower_{left,right}.json`.

- Both sides were derived independently. They mirror to within 0.01 mm.
- The status is PROPOSED_UNREVIEWED: `review` is empty and `wrap_reviewed` is false.
- R41 has no landmarks for PSIS, AIIS, the ischial tuberosity, the tibial tuberosity or the femoral condyles. Those
  anchors are rule-of-thumb offsets from HJC, ASIS, the trochanterion, KJC, the epicondyles, AJC and the tibial plateau,
  and each one records its rule.
- Several muscles carry a `wrap_hint`:

  | Muscles | Wrap |
  |---|---|
  | Quadriceps | in front of the knee, radius 40 mm |
  | Hamstrings and gastrocnemius | behind the knee, radius 25 mm |
  | Gluteus maximus | behind the hip, radius 50 mm |

**Squat check.** `squat_path_length_check_blender.py` poses R41's anatomical leg natively:

- hip flexion about HJC;
- knee flexion about KJC, on the epicondyle axis;
- ankle dorsiflexion about AJC, on the malleolar axis.

Every sign is fixed by a landmark probe. The descent runs hip 5° → 100°, knee 5° → 102° and ankle 2° → 17°; the ascent
reverses it. Result files: `native_20261024/squat_path_length_check_{left,right}.json`.

| Result (each side, descent and ascent) | Count |
|---|---|
| Match | 10 |
| Contract "variable" | 12 |
| Mismatch | 2 (gluteus medius) |

Descent changes as a fraction of rest length:

| Muscle | Change | Contract |
|---|---|---|
| Gluteus maximus | +52 % | lengthening |
| Adductor magnus (hamstring part) | +26 % | lengthening |
| Vastus lateralis / medialis / intermedius | +16 / +22 / +21 % | lengthening |
| Rectus femoris | +1 % | variable |
| Biceps femoris long | +2 % | variable |
| Semitendinosus | +1 % | variable |
| Semimembranosus | +7 % | variable |
| Gastrocnemius medial | +9 % | variable |
| Soleus | +2 % | variable |
| Gluteus medius | −6 % | near-isometric (**mismatch**) |

**Findings**

- **Gluteus maximus needs its wrap.** As a straight line it ran through the hip joint and came out near-isometric
  (−2 %). That is anatomically wrong for the main hip extensor. With the posterior hip wrap it lengthens.
  - The +52 % magnitude depends on the rule-of-thumb 50 mm radius and is probably high.
- **Gluteus medius is a fan.** Anterior fibres shorten by 20 % in the deep squat, middle fibres by 6 %, and posterior
  fibres lengthen by 9 %.
  - The contract's whole-muscle "near-isometric" cannot be checked with one line.
  - It needs a fibre fan (or separate functional heads) first. The anchor was **not** tuned to match.
- The two-joint muscles (rectus femoris and the hamstrings) come out close to isometric. This agrees with the
  contract's "variable".

### Gluteus medius as a fibre fan (added)

**Schema.** Proposals may now carry `fibres`: extra origins that share the muscle's insertion, with the main origin
as the middle fibre. The squat check judges a fan muscle on the **mean** of its fibres' changes and reports each fibre.

**Gluteus medius origins.**

| Fibre | Origin rule |
|---|---|
| Anterior | Below the iliac crest, behind the ASIS |
| Middle | The original anchor |
| Posterior | In front of the posterior gluteal line |

The rules are recorded in the proposal.

**Squat descent (both sides).**

| Fibre | Change |
|---|---|
| Anterior | −24 % |
| Middle | −6 % |
| Posterior | +15 % |
| **Mean** | **−4.9 %** |

The mean is still just outside the 3 % near-isometric band, so the contract's "near-isometric" is **not** confirmed.

At 100° of hip flexion the medius's fibres change by different amounts. This is consistent with its known reversal of
rotation action in deep flexion. Two choices are left for Work or the owner:

- treat the whole-muscle entry as "variable" (per-fibre);
- or split the muscle into functional heads. That needs new permanent IDs, which only the owner can approve.

No other anchor changed. The diff of the regenerated proposals confirmed this, and the unit tests still pass.

### Scapulothoracic glide for the trapezius lower verdict (added)

**The model.** `PATHCHECK_GIRDLE=glide` keeps the scapula on the rib cage. The thorax is an ellipsoid fitted to R41's
torso skin over the scapular region, and its level set passes through the rest TS and AI. Upward rotation and
posterior tilt follow the ratios. Clavicle elevation, clavicle retraction and an extra scapular rotation are solved so
that TS and AI stay on the thorax, with a soft pull towards the ratio angles.

The solver needs finite-difference steps of about 0.01°: mathutils is single precision, and the default step gave a
zero Jacobian.

**Results at the press top (upward rotation 49°).**

| Pull towards the ratio angles | Clavicle elevation | TS / AI off the thorax |
|---|---|---|
| 0.002 m per degree | 45° | 24 / 68 mm |
| 0.0005 m per degree | **72°** (in vivo about 10–30°) | 3 / 10 mm (contact achieved) |

**What this shows.** With R41's AC position, its scapular-plane axis, and 49–52° of upward rotation about the AC joint,
the scapula cannot stay on the thorax at physiological clavicle angles. The lower angle swings out to about 25 cm from
the midline. Real kinematics needs scapular translation around the chest (protraction), which a rigid AC-pinned chain
cannot produce.

**The lower trapezius verdict.** In every girdle model tried (ac_only, coupled, glide at both settings), the
straight-line lower trapezius **lengthens by 36–56 %** in the press. The contract says "shortening".

The flag stays. Its next steps are:

- a proper scapulothoracic model with translation (for example, a closed-loop chain with the scapula gliding on the
  ellipsoid);
- and/or a fibre fan from T4–T12 instead of the single T9 point.

The other press verdicts are unchanged under glide, except serratus. Serratus depends on the girdle model: it shortens
at a pull of 0.002 and lengthens at 0.0005.

Files: `native_20261024/path_length_check_left_glide_reg0.002.json` and `…_reg0.0005.json`.
