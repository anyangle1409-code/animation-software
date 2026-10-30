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

### Why the trapezius lower flag will not resolve on R41 (added 29 Oct 2026)

R41's scapula landmarks (left; the right side mirrors them):

| Landmark | Position (m) | From the midline |
|---|---|---|
| TS | (0.052, 0.136, 1.440) | 52 mm |
| AI | (0.080, 0.140, 1.320) | |
| AA | (0.258, 0.061, 1.500) | 258 mm |

| Measure | R41 | Reference |
|---|---|---|
| **AA → TS** | **227 mm** | 113.0 ± 6.6 mm (male 3D-CT, posterolateral acromion to medial spine; range 90–129) |
| TS → AI | 123 mm | |
| AA → AI | 265 mm | |
| AC breadth (left to right) | 481 mm | 333–353 mm (the feasible clavicle family of the earlier skeleton work) |

Dry-bone studies put the whole scapular spine at about 128–129 mm, from the acromion tip to the medial edge.

**This is already established.** The skeleton tracker (`COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md`) records
the reference above and calls transverse scapular geometry "a confirmed rebuild defect" of a003. R41 carries a003's AC
breadth (481 mm). The corrected-width girdle candidates (c003 / c004: clavicle 151 mm, AC breadth 338 mm) are
non-canonical; adopting them is the owner's decision on validated skeletal data.

**Consequence for the muscle layer.**

- With a spine about twice the CT length, 50° of upward rotation about the AC joint swings the root of the spine through
  a chord of about 19 cm. Every girdle model tried therefore lengthens the T9 → root-of-spine line by 36–56 %.
- The glide model needed 72° of clavicle elevation to keep TS and AI on the thorax.
- The lower trapezius flag, and the girdle-dependence of the serratus verdict, are downstream of that defect, not anchor
  errors.

**Re-checking needs a corrected girdle.** A test that shrinks only the scapula (the clavicle still 481 mm wide) would put
TS about 155 mm from the midline, so it does not settle the question and was not run. The re-check should be made on the
c003/c004 girdle once the owner chooses it.

Sources for the dry-bone figures:

- [Scapula Morphometry and Types of Acromion](https://jcpres.com/article/2709) (spine length 128.0 ± 10.7 mm).
- [The Scapula: Osseous Dimensions and Gender Dimorphism in Thais](https://he02.tci-thaijo.org/index.php/sirirajmedj/article/view/245524)
  (spine 12.89 ± 0.94 cm).

### Rotator cuff: teres minor and subscapularis anchors, humeral-head wrap, humeral rotation (added 29 Oct 2026)

**New proposed anchors** (unreviewed; permanent IDs `hgpt.muscle.teres_minor.*` and `hgpt.muscle.subscapularis.*`,
both already in the registry seed and in the exercise contract). Both sides were regenerated. The diff against the
previous proposals shows exactly these two muscles added per side and nothing else changed. The source hash is
unchanged.

| Muscle | Origin rule | Insertion rule |
|---|---|---|
| Teres minor | Dorsal surface, upper two-thirds of the lateral border: 35 % from the infraglenoid tubercle (GH − 25 mm up) towards AI, 5 mm posterior | Greater tubercle, inferior facet: GH + 20 mm lateral, 12 mm posterior, 12 mm down |
| Subscapularis | Subscapular fossa (costal surface): centroid of TS, AI and GH, 15 mm anterior | Lesser tubercle: GH + 22 mm anterior, 10 mm lateral |

**New path options** (`path_length_direction_check_blender.py`):

- `PATHCHECK_HEAD_WRAP=1` wraps supraspinatus, infraspinatus, teres minor and subscapularis on a ball at the humeral
  head. The path is tangent, then a great-circle arc, then a tangent, in the plane of origin, insertion and centre.
  The radius is 20 mm (`PATHCHECK_HEAD_R`), just inside the tubercle anchors, which lie 24–26 mm from GH.
- `PATHCHECK_HUM_ER_TOP=<deg>` adds humeral external rotation, linear in elevation, reaching the given angle at 160°.
  Its sign is fixed by a landmark probe: the anterior humerus turns laterally.
- Both default off, so earlier results are unchanged.

**Press phase, left side, coupled girdle** (change as a fraction of rest length):

| | Straight | Head wrap | Wrap + ER 20° | Wrap + ER 40° | Wrap + ER 60° | Contract |
|---|---|---|---|---|---|---|
| Supraspinatus | −20.4 % | −20.4 % | −20.3 % | −18.9 % | −16.3 % | variable |
| Infraspinatus | −9.7 % | −9.7 % | −9.8 % | −9.4 % | −8.4 % | near-isometric |
| Teres minor | +7.7 % | +7.7 % | +5.1 % | **+2.7 %** | **+1.0 %** | near-isometric |
| Subscapularis | −8.8 % | −9.9 % | −11.4 % | −13.1 % | −15.2 % | near-isometric |

In the curl every cuff muscle is near-isometric, as the contract says. The curl does not move the shoulder.

**What this shows.**

- **The head wrap engages but barely changes the lengths.** The cuff lines touch a 20 mm ball only in some poses.
- **Humeral external rotation** behaves as expected at the start of the press: the subscapularis lengthens and the
  infraspinatus shortens. **Teres minor** becomes near-isometric from about 40° of external rotation.
- **Infraspinatus and subscapularis shorten in the press in every configuration.**
  - Both change length only with glenohumeral motion, since both ends ride on the scapula and humerus.
  - Their shortening during scapular-plane elevation is consistent with the elevation moment arms reported for both
    muscles (Otis et al. 1994; the infraspinatus contribution grows with internal rotation).
  - The contract's "near-isometric" for these two is therefore the questionable entry, like the triceps long head.
    These are contract questions for Work or the owner, not anchor errors. The contract file is Work's and is
    **not edited here**.
- How much external rotation the press really carries is not sourced here. The sweep shows the verdicts' sensitivity
  to it.

**Files:** `native_20261024/path_length_check_left_coupled_cuff_{straight,wrap,wrap_er20,wrap_er40,wrap_er60}.json`.
The unit tests still pass (38 / 38, run from the repository root).

Sources:

- [Changes in the moment arms of the rotator cuff and deltoid muscles with abduction and rotation](https://www.bisp-surf.de/Record/PU199509102783)
  (Otis et al., 1994).
- [PMC9149620](https://pmc.ncbi.nlm.nih.gov/articles/PMC9149620): the infraspinatus as an abductor or elevator in the
  scapular plane, especially with internal rotation.

## MG1: first belly / tendon envelopes, upper arm (added 30 Oct 2026)

This follows Work's handoff step 3: geometry inside the existing body, on a copy only.

**Script:** `build_arm_muscle_envelopes_blender.py`. It opens the hash-checked experiment copy and builds six muscles
per side:

- biceps long and short heads;
- brachialis;
- triceps long, lateral and medial heads.

Each muscle is a closed belly mesh in `HGPT_EXPERIMENT_MUSCLES`. Its origin and insertion tendons go to the proposed
anchors and live in `HGPT_EXPERIMENT_TENDONS`. `HGPT_EXPERIMENT_WRAP_GUIDES` is created empty. The script saves a
**new** suffixed blend and confirms the source hash is unchanged.

**Objects.**

- Every object is named and tagged with its permanent ID (`hgpt_muscle_id`), with status `ENVELOPE_PROXY_UNREVIEWED`.
- One neutral colour, no activation display.
- Each object is bound to the anatomical chain (scapula / humerus / radius / ulna) with an armature modifier.

### How the envelopes are sized

**Literature volumes are blocked.** The Holzbaur 2007 volume table could not be read: nmbl.stanford.edu,
sciencedirect.com, mobl.wordpress.ncsu.edu, Europe PMC and NCBI are all unreachable from this sandbox (proxy 403 / DNS).
So `tissue.rest_volume_m3` stays **null**. The volumes below are geometry-derived from this body, not reviewed values.

**Sizing rules:**

1. **Cross-sections.** The humeral axis (GH → EJC landmarks) is cut into sections. Each section's arm skin outline is
   measured by intersecting the arm's skin triangles with the section plane. Points more than 65 mm from the axis are
   shoulder or torso skin and are dropped.
2. **Available space.** The space between a humeral radius proxy and the skin, less a 4 mm subcutaneous layer, is split
   as an upper-arm cross-section is:

   | Compartment | Sector (0° anterior, +90° lateral) | Contents |
   |---|---|---|
   | Anterior | −78° to 78° | biceps long head (lateral half) and short head (medial half) superficial, over the brachialis (deep, distal) |
   | Posterior | 98° to 262° | triceps lateral head (posterolateral) and long head (posteromedial) superficial, over the medial head (deep, distal) |

3. **Deltoid.** A superficial band is kept free for the deltoid on the lateral side of the proximal humerus. The
   deltoid is not built yet.
4. **Lofting.** Bellies are lofted over authored axial ranges and taper in polar terms, so a deep band's end stays in
   its compartment. Every point is kept at least the subcutaneous layer below the body surface. That clamp never goes
   inside the bone radius: the skin wins only down to the bone, and anything left is reported, not hidden.
5. **Record.** All fractions, sectors, ranges and thicknesses are authored rules, written into the report.

**The humeral radius proxy** is 11 mm along the shaft, wider at the head and epicondyles. R41 has no bone meshes, only
an armature.

### Copy-only change

R41's anatomical master is a guide skeleton whose bones do not deform (`use_deform` False). The proxies could not follow
it, as measured: a 0 mm probe. In the copy only, deform is switched on for the four bones the proxies use. No rest data
changes, and the body stays driven by the runtime rig (`HGPT_CANONICAL_V4_ORIGINAL`). Both facts are recorded in the
report.

### Results (left; the right side was built independently from its own anchors)

| Muscle | Belly volume (geometry-derived) | Belly length | Tendons (origin / insertion) |
|---|---|---|---|
| Biceps long head | 176 cm³ | 181 mm | 86 / 78 mm |
| Biceps short head | 159 cm³ | 175 mm | 77 / 87 mm |
| Brachialis | 143 cm³ | 147 mm | 30 / 39 mm |
| Triceps lateral head | 185 cm³ | 192 mm | 36 / 45 mm |
| Triceps long head | 199 cm³ | 204 mm | 25 / 45 mm |
| Triceps medial head | 99 cm³ | 167 mm | 63 / 8 mm |

**Checks, both sides:**

- 0 vertices outside the skin;
- 0 shallower than the subcutaneous layer;
- 0 inside the humeral radius;
- **0 muscle–muscle triangle overlaps**;
- source hash unchanged.

**Elbow flexion on the anatomical chain:** the biceps insertion tendon follows the radius (55 mm of travel at 90°, 67 mm
at 120°).

**Right against left.**

- Runtime suffix `_l`, consistent with the side convention.
- Volumes are identical except the triceps long head (−0.3 %).
- Its origin tendon is 25 mm on the left against 36 mm on the right. The axilla depth clamp meets slightly different
  skin tessellation on the two sides, as already measured on the body.

### Limits and next steps

These are **rest envelopes only**.

- The bellies do not yet shorten or bulge with length (`kernel.belly_axes`).
- There is no fusiform or pennate surface, and no tendon wrap: the biceps long head through the groove, the triceps over
  the olecranon.
- Each envelope fills its compartment of *this* (muscular) body, so absolute volumes are not population values.
  Coracobrachialis, anconeus and fat beyond 4 mm are not separated.

**Next:**

- length response through Work's kernel (volume-preserving), checked on the path-length sweeps;
- the deltoid (three heads) and the rotator cuff;
- then reviewer sign-off.

**Files.**

- In git: `native_20261024/mg1/` holds `mg1_left_report.json`, `mg1_right_report.json` and the phone sheet
  `MG1_left_arm_sheet.jpg`. The sheet shows skin, muscle + tendon, overlay, and elbow at 90° and 120°.
- Not in git (no `.blend` files are committed): the experiment blends `HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT_MG1_arm_{left,right}.blend`.
  Their SHA256 values are in the reports.
