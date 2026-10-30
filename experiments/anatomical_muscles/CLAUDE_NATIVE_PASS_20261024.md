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

## MG2: length response through the curl (added 30 Oct 2026)

**Script:** `arm_muscle_length_response_blender.py`. It runs on the MG1 left blend (hash-checked) and saves a new MG2
blend. The MG1 blend is unchanged.

**Method.**

1. Per elbow angle, the anatomical chain is posed natively.
2. Each muscle's path comes from its proposed anchors via `kernel.resolve_path` / `kernel.path_length`.
3. Belly length = path − the MG1 tendon lengths.
4. `kernel.belly_axes` is used with activation 0: positioning only, no activation display. `evaluate.evaluate` is not
   used, because it refuses unreviewed bindings by design.
5. The response is stored per angle as a rest-space shape key, `HGPT_LEN_ELBOW_<deg>`, in the humeral axis's
   cylindrical frame:
   - stations move along the axis about the belly's proximal end by k = L / L_rest;
   - each section keeps its deep surface;
   - the outer surface takes r_o′² = r_i² + (r_o² − r_i²) / k, so the section area scales by 1 / k and the volume is
     kept;
   - the belly bulges towards the skin, not into the bone.

**Two first-version faults were found and fixed.**

- Widening about each belly's own axis pushed the bellies into the bone and their deep neighbours: brachialis against
  triceps medial reached 380 overlapping triangle pairs.
- Belly ends weighted to the forearm double-counted the length change, so brachialis volume went ×1.51. The bellies now
  ride the humerus, and only the tendons cross the elbow. MG1 was rebuilt with that binding: checks unchanged, the
  report updated.

**Left side:**

| Elbow | Biceps long, k / radius | Brachialis, k / radius | Triceps lateral / long / medial, k | Volume range against rest | Overlapping pairs |
|---|---|---|---|---|---|
| 45° | 0.91 / ×1.05 | 0.86 / ×1.08 | 1.13 / 1.08 / 1.35 | 0.9997–1.0001 | biceps–brachialis 302 + 206 |
| 90° | 0.75 / ×1.15 | 0.63 / ×1.26 | 1.19 / 1.12 / 1.52 | 0.9996–1.0001 | biceps–brachialis 188 + 194; triceps lat–med 17 |
| 140° | 0.60 / ×1.29 | 0.41 / ×1.56 | 1.14 / 1.09 / 1.41 | 0.9994–1.0001 | biceps–brachialis 164 + 180 |

**What this shows.**

- **Volume is conserved for every muscle at every angle.** The biceps visibly shortens and thickens through the curl
  (`MG2_left_curl_sheet.jpg`, lateral view, muscle-only and with the skin overlaid at 35 %).
- **The remaining overlaps are deep-under-superficial layering:** the growing brachialis under the biceps. Each belly
  responds alone. A layered or contact response is needed, pushing the superficial belly out by the deep one's
  growth. It belongs with Work's step 6 (skin response).
- **The triceps medial head is a known limit.** Its single representative origin point lies inside its own belly range,
  and it lengthens 35–50 %. A straight proxy riding the humerus can only lengthen axially, so it extends past the elbow
  instead of wrapping around it. It needs a belly swept along the posed path (per-frame loft) or an elbow wrap guide.
  This is flagged, not hidden.
- **Skin crossings rise with flexion** (biceps 280–330 vertices at 140°). The body is posed by its own runtime rig, which
  does not bulge, and the two skeletons' elbow centres differ by 11–17 mm. This diagnoses where a skin response is
  needed. It is not a proxy failure.

**Files:** `native_20261024/mg2/mg2_left_report.json` (k, radius scale, volume, overlaps and skin crossings per angle)
and `MG2_left_curl_sheet.jpg`. The MG2 blend is not in git; its SHA256 is in the report.

## MG3: layered length response (added 30 Oct 2026)

`arm_muscle_length_response_blender.py` with `MG_LAYERED=1` (now the default; `MG_LAYERED=0` reproduces MG2).

**Method.**

- The deep bellies (brachialis, triceps medial) respond first, as in MG2.
- Each superficial belly over them keeps its deep surface on the deep neighbour's **new** outer surface plus the 1.2 mm
  gap. The pairs are the biceps long and short heads over the brachialis, and the triceps lateral and long heads over
  the triceps medial.
- Its outer surface follows by the same area rule, so the volume is still kept.

**Three fixes were needed to close it.**

1. The deep outer surface is looked up with a 3° tolerance. Sector edges coincide, and floating-point rounding put
   edge points "outside" the deep belly.
2. The deep outer surface is taken as the maximum over ±1.2 % of the humerus length around each point, because it peaks
   between the sampled stations.
3. End-cap centres follow their ring's largest push.

**Left side:**

| Elbow | Muscle–muscle overlapping pairs (MG2 → MG3) | Biceps pushed out by (max) | Triceps lateral / long pushed out by | Volume against rest |
|---|---|---|---|---|
| 45° | 508 → **0** | 2.0 mm | 1.5 / 1.5 mm | 0.9997–1.0001 |
| 90° | 399 → **0** | 8.7 mm | 3.4 / 1.2 mm | 0.9996–1.0001 |
| 120° | 373 → **0** | 15.2 mm | 1.9 / 1.1 mm | 0.9995–1.0001 |
| 140° | 344 → **0** | 19.2 mm | 1.5 / 1.2 mm | 0.9994–1.0002 |

**What this shows.**

- The swelling brachialis lifts the biceps outward, up to 19 mm at 140°. That forms the biceps peak.
- No belly penetrates another at any angle.
- The cost appears where it physically belongs, at the skin: biceps vertices outside the non-bulging posed skin rise to
  264 / 272 at 140°. This is the input for a skin response (Work's step 6): a rest-relative corrective driven by the same
  per-angle length state, not by proximity.
- The triceps medial head's past-the-elbow extension (MG2) is unchanged.

**Files:** `native_20261024/mg3/mg3_left_report.json` and `MG3_left_curl_sheet.jpg` (lateral view, muscle-only and
with the skin overlaid at 35 %).

## MG4: deltoid envelopes, and the MG1 / MG3 rebuild (added 30 Oct 2026)

**Script:** `build_deltoid_envelopes_blender.py`. It runs on an MG1 blend (hash-checked) and saves a new MG4 blend
with the anterior, middle and posterior heads. Both sides were built independently.

**Why the frame is a hybrid.** The deltoid runs along the shaft and caps the humeral head, and one frame does not fit
both parts. A first all-spherical version (rays from GH) cut the shaft-aligned layers obliquely: sections were squeezed
to the 3 mm minimum at 96–190 points per head, with 174 triangle overlaps against the arm envelopes. Each head is now
built in two parts:

1. **Along the shaft** (s 0.40 → 0.12 of GH → EJC): cylindrical sections that fill exactly the reserve band MG1 leaves
   for the deltoid. The inner surface is where MG1's envelopes stop, plus the gap, so there is no overlap by
   construction.
2. **Over the head:** a GH-centred spherical frame.
   - It starts from a 58° cone, whose ring lies wholly above the last shaft ring.
   - It ends at each head's origin direction (from its proposed anchor) less a 10° aponeurotic margin.
   - Outer surface: the skin less the 4 mm layer, as a true depth. The rays meet the skin obliquely, so it is clamped by
     nearest-point depth.
   - Inner surface: the deepest of the humeral head (24 mm) + a 6 mm rotator-cuff reserve, the shaft proxy, and the
     MG1 envelopes.
   - Thickness: up to 24 mm, tapering to the origin.

**Head spans at the top** (φ about the humeral axis; the AC joint lies at about φ 72°, θ 147° from GH):

| Head | Origin | Span at the top |
|---|---|---|
| Anterior | lateral third of the clavicle | −45° to 55° |
| Middle | acromion | 58° to 139° |
| Posterior | spine of the scapula | 141° to 210° |

All three converge on thirds of φ 70–110° at the deltoid tuberosity.

**Binding.** Each head blends from the humerus (shaft part) to its origin bone (the clavicle for the anterior head, the
scapula for the others) over the cap. `use_deform` was switched on for the clavicle bone in the copy, as MG1 did for
four other bones.

**MG1 and MG3 rebuilt to match.**

- **Wider deltoid reserve.** It now covers φ −40° to 210° at the top, narrowing to 50–130° by s 0.40; 55 % of the
  available thickness to s 0.20, none by 0.45. The first, lateral-only 45 % reserve squeezed the deltoid.
- **Feathered window.** The reserve window is feathered over 30° inside its edges. A hard edge, then a 15° feather,
  stepped the arm envelopes' outer surface into a visible staircase.
- **Finer sampling.** Stations every 1.2 % of the humerus and 14 samples per arc. The sample count is now recorded in
  the MG1 report, and MG3 reads it from there.

**Results:**

| | Left | Right |
|---|---|---|
| MG1 arm envelopes: outside skin / too shallow / inside bone / overlaps | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| MG4 deltoid heads: outside skin / too shallow / inside head or shaft / overlaps (with each other and the arm) | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| Deltoid volumes (anterior / middle / posterior) | 121 / 91 / 60 cm³ | identical |
| MG3 layered curl: muscle–muscle overlaps at 0–140° | 0 at every angle | 0 at every angle |
| MG3 volume against rest | 0.9996–1.0003 | 0.9997–1.0004 |

Arm envelope volumes after the rebuild:

| Muscle | Volume |
|---|---|
| Biceps long head | 179 cm³ |
| Biceps short head | 160 cm³ |
| Brachialis | 145 cm³ |
| Triceps lateral head | 185 cm³ |
| Triceps long head | 198 cm³ |
| Triceps medial head | 100 cm³ |

**Limits.**

- The deltoid's length response in arm elevation is not built. A muscle bound to the scapula-to-humerus blend cannot
  follow 160° of elevation; this needs a per-pose sweep along the posed path.
- The cap's top edge is uneven: the heads end at different origin angles, and the cap shows tendon stubs from above.
- The deltoid is smaller than this body's triceps. Its thickness cap (24 mm) and the 6 mm cuff reserve are authored,
  not measured.
- As everywhere, the volumes are geometry-derived, not reviewed.

**Files.**

- `native_20261024/mg4/`: `mg4_left_report.json`, `mg4_right_report.json` and `MG4_left_shoulder_sheet.jpg`
  (anterior / lateral / posterior / superior, muscle-only and with the skin overlaid at 35 %).
- `mg1/` and `mg3/`: refreshed reports and sheets, both sides.
- The blends are not in git; their SHA256 values are in the reports.

## MG5: the armpit-fold muscles: pectoralis major, latissimus dorsi, teres major (added 30 Oct 2026)

**Script:** `build_axillary_fold_envelopes_blender.py`. It runs on an MG4 blend (hash-checked) and saves a new MG5 blend
with four muscles per side:

- `pectoralis_major_clavicular` and `pectoralis_major_sternocostal`;
- `latissimus_dorsi`;
- `teres_major`.

These muscles form the two armpit folds. The movement work found a skinning artifact at the posterior fold in the
press lockout (`docs/R121_MOVEMENT_TRAJECTORIES_20261024.md` on the surface branch). Muscle-driven skin there needs
these volumes first.

**How a fan is built.** Each muscle is a sheet of 11 fibres × 28 stations. Fibre u runs in three stages:

1. **Origin:** a point O(u) on an authored origin line.
2. **Via point:** V(u), on its armpit fold. It is where the trunk skin meets the arm skin at the fold's height:
   - rays from the thorax axis are swept from straight ahead (or behind) towards the side, up to 70°;
   - V is the last trunk hit before the first arm hit;
   - it is then pulled towards the trunk until it is clear of the MG1 / MG4 envelopes.
3. **Insertion:** a point I(u) on a line along the humerus, through the proposed insertion anchor, with each muscle's
   twist.

Along the fibre:

- **On the trunk** (O → V): the chord is cast radially from the thorax axis onto the trunk skin (arm skin excluded).
  The mid-surface lies the 4 mm subcutaneous layer plus half the thickness below it. For a deep muscle the cast stops
  at the superficial muscle instead, less a 1.2 mm gap.
- **Across the fold** (V → I): the mid-surface follows the chord. Where the chord leaves the skin (the rest armpit is
  closed) it is snapped below the nearest skin.

The sheet is then built up as follows:

- **Thickening.** It is thickened along its own normal: the skin normal on the trunk, and the grid normal kept
  continuous across the fold. The grid's own cross product degenerates where fibres start along their origin line, as
  on the clavicle.
- **Belly end.** Each fibre's belly ends one station before it would enter another envelope (the MG1 arm envelopes,
  the MG4 deltoid unless it lies under it, or the fans already built). A tendon proxy runs on to the insertion anchor.
- **Layering.** The deep muscles are moved towards the thorax axis until no face crosses the superficial one:
  - teres major under the latissimus;
  - both pectoral heads under the anterior deltoid;
  - the sternocostal under the clavicular head.
- **Final pass.**
  - Where the sheet crosses itself (an offset sheet thicker than its bend radius), it is thinned towards 3 mm and
    smoothed locally.
  - Every vertex is clamped 4 mm below the skin.
  - A fibre that cannot satisfy the clamp, the layering and (near its belly end) the self-crossing test is shortened
    one station and rebuilt.
  - Neighbouring fibres end within a station of each other.
  - The build-time overlap tests use Blender's own triangulation, so they agree with the final checks.

**Authored rules** (all recorded in the reports):

| Muscle | Origin line | Insertion (s along GH → EJC, u 0 → 1) | Fold height (u 0 → 1) | Thickness (trunk / fold) |
|---|---|---|---|---|
| Latissimus dorsi | T7 spinous level 15 mm lateral → T12 → L3 70 mm lateral → posterior iliac crest. This is the belly's medial edge; the thoracolumbar aponeurosis is not modelled. | floor of the sulcus 0.20 → 0.10 (upper fibres lowest) | 1.415 → 1.375 m, back fold | 6 / 16 mm |
| Teres major | 35 mm across the dorsal inferior angle, perpendicular to the fibres in the scapular plane, 22 mm from AI along the fibre line | medial lip 0.25 → 0.15 | 1.385 → 1.405 m, back fold | 20 / 22 mm |
| Pectoralis major, clavicular | anterior clavicle 8 % → 48 % SC → AC, 8 mm anterior | lateral lip 0.28 → 0.18 (most distal) | 1.455 → 1.48 m, front fold (medial fibres lowest) | 10 / 14 mm |
| Pectoralis major, sternocostal | sternum 15 mm lateral of the guide line, z 1.495 → 1.33, then along the 6th costal cartilage to 75 mm lateral | lateral lip 0.24 → 0.12 (lowest fibres highest) | 1.445 → 1.395 m, front fold | 10 / 18 mm |

**Two origins were revised so they cross the fibres.**

- The teres major origin first ran along the lateral border, and the clavicular head's fibres ran along the clavicle.
- In both, the origin line ran parallel to the fibres. The grid cells collapsed and the sheets crossed themselves
  (81 and 320 face pairs at rest).

**Results:**

| | Left | Right |
|---|---|---|
| Outside skin / shallower than the layer | 0 / 0 for every muscle | 0 / 0 |
| Overlaps (with each other and with MG1 / MG4) | 0 | 0 |
| Self-crossing face pairs | clavicular head 5, others 0 | clavicular head 5, others 0 |
| Latissimus / teres major / pectoral clavicular / sternocostal (cm³) | 219 / 53 / 50 / 185 | 217 / 53 / 50 / 185 |
| Within 6 mm of a rib guide segment (latissimus / sternocostal) | 2 / 3 vertices | 2 / 3 |
| Input blend unchanged | yes | yes |

- **Where the bellies end.** The latissimus and teres major bellies end at the triceps long head, every fibre on both
  sides. MG1's long-head envelope fills the arm side of the posterior fold (its sections reach 65 mm from the humeral
  axis), so the fold's bulk is long head on the arm side and latissimus / teres on the trunk side. The tendons
  (59–68 mm) run on to the humerus.
- **The pectoral heads** run under the anterior deltoid nearly to the humerus (tendons 16–26 mm).
- **Copy-only change:** `use_deform` was switched on for the sternum, T7–L5 and the hip bone on the experiment copy,
  as MG1 and MG4 did for the limb bones. A check confirmed that the evaluated envelopes do not move at rest.

**Limits.**

- **No rib-cage surface.** R41's ribs are guide segments, so the depth floor is the authored thickness. The
  rib-proximity count is the only check of it.
- **The clavicular head's lateral edge** curls against its own inner surface: 5 face pairs per side, at fibres 8–10,
  stations 5–8.
- **Pre-existing self-crossings.** The MG6a check below found them in MG1 / MG4, which never checked self-crossings:
  triceps long head 13 face pairs, posterior deltoid 4.
- **Rest pose only.** No length response in arm elevation, as for the deltoid. A muscle bound from its trunk origin
  bone to the humerus cannot follow 160° of elevation; this needs the same per-pose sweep. Driving the skin of the
  posterior fold with these volumes is the next step.
- **Fold heights are authored**, not found. Serratus anterior, trapezius and the thoracolumbar aponeurosis are not
  built.
- **Volumes** are geometry-derived from this body. No reviewed literature values were reachable (see MG1).

**Files.**

- `native_20261024/mg5/`: `mg5_left_report.json`, `mg5_right_report.json`, and `MG5_left_axilla_sheet.jpg` /
  `MG5_right_axilla_sheet.jpg`. The sheets show anterior, anterolateral, lateral, posterolateral and posterior views:
  muscles and tendons, then the skin overlaid at 35 %.
- The blends are not in git; their SHA256 values are in the reports.

## MG6a: the bound proxies through the press (read-only check, added 30 Oct 2026)

**Script:** `muscle_press_pose_check_blender.py`. It runs on an MG5 blend (hash-checked) and saves nothing.

- **Posing.** R41's anatomical chain is posed natively, re-implementing the coupled girdle of
  `path_length_direction_check_blender.py`: upward rotation 0.33 e, posterior tilt 0.12 e, clavicle elevation 0.08 e and
  retraction 0.12 e, with the humerus in a plane 30° anterior of the frontal plane.
- **The press path:** start → humerothoracic 60° → rack (90°, elbow 90°) → 120° → lockout (160°, elbow 0°).
- **What it measures:** the envelopes deform with their armature bindings. The skin is not posed, because R41's
  anatomical master is a guide skeleton, so this checks the envelopes against each other only.

**Results, left side:**

| | Start | Rack 90° | Lockout 160° |
|---|---|---|---|
| Face overlaps between muscles | 6 (latissimus / teres) | 169 | 314 |
| Middle deltoid volume / rest | 0.98 | 0.41 | 0.22 |
| Anterior deltoid volume / rest | 1.00 | 0.56 | 0.58 |
| Clavicular pectoral head volume / rest | 1.01 | 0.93 | 0.69 |
| Latissimus, maximum edge stretch | 1.09× | 5.6× | 8.4× |
| Sternocostal pectoral head, maximum edge stretch | 1.12× | 9.0× | 15.5× |

- **The overlaps are mostly the deltoid's:** anterior / middle 140 at the rack; middle / posterior 106 and anterior
  deltoid / clavicular pectoral 118 at the lockout.
- **The arm envelopes stay rigid** (bound to the humerus; ratio 1.00).
- **The start pose** turns the rest humerus into the 30° plane, hence its small changes.

**Reading.** As MG4 anticipated, proxies bound by blending an origin bone into the humerus cannot follow elevation:
the deltoid collapses and the fans over-stretch. The positioning step this needs is a per-pose rebuild. Each MG4 / MG5
construction would be re-run on the posed landmarks and skin, and stored as shape keys over the binding, driven by
humerothoracic elevation, as MG2 / MG3 did for the elbow. The skin in those poses has to come from a posed body, which
R41's guide skeleton does not drive.

**Files:** `native_20261024/mg6a/mg6a_left_press_pose_report.json` and `MG6a_left_press_sheet.jpg` (start, rack and
lockout; anterior, lateral and posterior).

**MG6a with the posed skin** (`muscle_press_pose_check_blender.py ... r57src`, read-only).

- **Setup.** The body's own rig (`HGPT_CANONICAL_V4_ORIGINAL`) is retargeted onto the posed anatomical chain: each
  mapped bone gets the same world rigid delta. Sides are matched by x, since anatomical left = +x = the body rig's
  `_r`.
- **Retarget check.** The rig's upper arm then coincides with the anatomical humerus (head identical; tail within
  10 mm, because the bone lengths differ). R41's corrective drives do not move these bones.
- **Skin weights.** The skin beside the biceps is 93 % `upperarm_r`.

Envelope vertices outside the posed skin, at the lockout (maximum distance):

| | R41 drives on (its correctives) | Plain skinning (`MG6A_DRIVES=0`) |
|---|---|---|
| Biceps long head | 701 (33 mm) | 210 |
| Triceps lateral head | 485 (36 mm) | 261 |
| Deltoid anterior / middle / posterior | 441 / 305 / 319 | 372 / 343 / 331 |
| Teres major | 596 (99 mm) | 616 |
| Clavicular / sternocostal pectoral | 188 / 96 | 154 / 42 |

- **At the rack** (elbow 90°, plain skinning) the brachialis has 388 vertices outside the collapsed elbow crease.
  R41's elbow keys bring that to 20.
- **Reading.**
  - R41's posed skin is not a reliable container at elevation. Its shoulder correctives were authored for its own
    (r57) press path and push the upper-arm skin inward by up to about 30 mm here, and plain skinning collapses at
    the shoulder and elbow.
  - A per-pose rebuild that clamps the muscles to this skin would copy its faults. The positioning step should
    instead be bone-driven and volume-preserving:
    - the deltoid wrapped on the posed humeral head and cuff;
    - the fans run from the posed origin lines to the posed insertion lines over a thorax proxy;
    - each section scaled by the length change.
  - The skin would then follow the muscles. This is the system-level route the movement work also points to (the
    posterior armpit corner).
- **Files.**
  - Reports: `native_20261024/mg6a/mg6a_left_press_pose_skin_drives_report.json` and
    `mg6a_left_press_pose_skin_lbs_report.json`.
  - Sheet: `MG6a_left_press_posed_skin_sheet.jpg` (rack and lockout, skin at 45 %).

## MG7: leg muscles for the squat (added 30 Oct 2026)

**Script:** `build_leg_muscle_envelopes_blender.py`. It carries MG1's method to the leg, runs on an MG5 blend
(hash-checked) and saves a new MG7 blend. It builds the 10 muscles of Work's squat contract that sit around the femur
and the tibia, on both sides. The glutes (maximus and medius) need cap / fan treatment, as the deltoid did, and are
not built yet.

**Segments.** Each segment is cut into cross-sections along a bone line. The space between a bone-radius proxy and
the skin, less the 4 mm layer, is divided into compartment sectors and depth bands (φ: 0 anterior, +90 lateral).

- **Thigh.** The line runs from below the greater trochanter (trochanterion landmark, 45 mm medial and 30 mm down) to
  KJC. R41's femur bone is the mechanical axis HJC → KJC, which runs medial of the proximal shaft, through the neck.
  - Bone proxy: 13.5 mm, wider at the trochanter and the condyles.
- **Calf.** The line runs KJC → AJC.
  - Bone proxy: 21 mm (tibia, fibula and interosseous membrane), wider at the plateau.
- **Sections:** the leg's own skin triangles.
- **Depth clamp:** the trunk and leg skin only. The hands rest on the thighs and are not the thigh's surface.

| Muscle | Sector (°) | Band | s range | Volume L / R (cm³) |
|---|---|---|---|---|
| Rectus femoris | −25..25 | outer 55 % | 0.06–0.80 | 488 / 488 |
| Vastus intermedius | −60..115 | inner 45 % | 0.20–0.86 | 443 / 443 |
| Vastus lateralis | 25..150 | above the intermedius, full beyond it | 0.08–0.88 | 866 / 866 |
| Vastus medialis | −80..−25 | above the intermedius, full below it | 0.42–0.93 | 295 / 295 |
| Biceps femoris long | 150..205 | full | 0.14–0.84 | 413 / 413 |
| Semitendinosus | 205..245 | outer 50 % | 0.12–0.78 | 244 / 244 |
| Semimembranosus | 205..258 | inner 50 % | 0.24–0.88 | 131 / 131 |
| Adductor magnus (hamstring part) | 258..278 | full | 0.16–0.90 | 139 / 139 |
| Gastrocnemius medial | 195..262 | outer 55 % | 0.03–0.50 (calf) | 267 / 267 |
| Soleus | 135..265 | inner 45 % under the gastrocnemius, full from s 0.60 | 0.14–0.82 (calf) | 414 / 414 |

**Reserves.**

- Over the proximal vastus medialis and adductor magnus, a superficial medial reserve is left for sartorius,
  gracilis and the other adductors (not in the contract).
- The posterolateral calf is left for the lateral gastrocnemius.

**Tendons and binding.** Tendons run to the proposed anchors. Thigh bellies ride the femur and calf bellies the tibia;
only the tendons cross the hip, knee and ankle. `use_deform` was switched on for the femur, tibia, fibula, calcaneus
and patella on the copy only.

**Getting the checks to zero:**

- **Sectors.** Two neighbouring sectors overlapped (vastus medialis / adductor magnus). They were separated.
- **Soleus.** It thickened before the gastrocnemius ended, so its rise now runs s 0.50 → 0.60.
- **Intermedius floor.** The lateralis and medialis now start above the intermedius's actual tapered outer surface
  plus the gap.
  - It is held for 12° beyond its sector edges, feathered over the next 12°.
  - It takes the largest value over the neighbouring stations.
  - A narrow feather and single-station sampling had let their inner faces slope through the intermedius's corner
    (256 face pairs).
- **End caps** are strips between the outer and inner arcs rather than centroid fans. A fan cuts through the concave
  side of a wide curved band.

**Results, both sides:** 0 outside the skin, 0 shallower than the layer, 0 inside the bone proxy, 0 self-crossings,
0 overlaps (with each other and with MG1 / MG4 / MG5). The input blends are unchanged.

**Squat check** (`muscle_squat_pose_check_blender.py`, read-only). R41's anatomical leg is posed natively:

- hip about HJC, knee about the epicondyle axis, ankle about the malleolar axis, with probe-fixed signs;
- the descent runs 5 / 5 / 2° → 100 / 102 / 17°.

Results:

- 0 overlaps through three-quarter depth (knee 78°).
- At full depth (knee 102°) the hamstrings meet the medial gastrocnemius behind the knee: biceps femoris 8,
  semitendinosus 38 and semimembranosus 46 face pairs.
- That is the thigh–calf contact the skin also has. It needs a contact response (flattening at the interface), not a
  change of the rest shapes.

**Limits.**

- Proxies.
- The glutes are not built.
- The patellar mechanism is represented only by the quadriceps' insertion tendons.
- No length response through the squat yet (MG2 / MG3's method would carry over).
- Volumes are geometry-derived.

**Files.**

- `native_20261024/mg7/`:
  - reports: `mg7_left_report.json`, `mg7_right_report.json`, `mg7_left_squat_pose_report.json`;
  - sheets: `MG7_left_leg_sheet.jpg`, `MG7_right_leg_sheet.jpg` (anterior / lateral / posterior / medial; muscles,
    then skin at 35 %), and `MG7_left_squat_sheet.jpg`.
- The blends are not in git; their SHA256 values are in the reports.

## MG8: the glutes, with the MG5 fan builder's gluteal mode (added 30 Oct 2026)

**Script:** `build_axillary_fold_envelopes_blender.py ... gluteal` (6th argument). It runs on an MG7 blend with
`proposed_anchors_lower_<side>.json` and saves a new MG8 blend with the gluteus maximus and gluteus medius. The
default (`axilla`) mode reproduces MG5. This was checked twice: once with 0.0 mm vertex difference before the
inside-test change below, and again with all checks unchanged after it.

**What differs from MG5.**

- **No armpit fold.** The via point is a fixed fraction along the fibre, where the belly leaves the buttock or hip
  surface for the femur. Gluteus maximus leaves at 88 %: its upper fibres pass superficially over the trochanter, and
  leaving at 72 % ran them through the medius's insertion. Gluteus medius leaves at 80 %.
- **The projection axis** is the vertical through HJC. A line 40 mm off the midline lay between the thighs below
  0.92 m: rays from it hit the inner thigh first and dragged the lower fibre ends medially.
- **Insertion lines** slide along the femoral mechanical axis HJC → KJC, and the insertion ends are bound to the
  femur.
- **Gluteus medius** is a converging fan (a ~12 cm iliac-crest origin to a ~1 cm trochanter insertion):
  - it is no thicker than 0.8× its fibre spacing;
  - it counts as lying under the maximus only where the maximus is found from the skin inward (within 16 mm). Cast
    from the axis outward, the maximus's deep insertion part was hit first, and the medius sank towards the hip
    joint.

**Inside test (all modes).** The inside test is now the majority of three ray-parity casts.

- A single fixed ray, which isn't mirrored between sides, grazed mesh edges. That stopped gluteal bellies "inside"
  the latissimus and the teres major, far away, on one side only.
- **MG5 re-run with it:** vertices move by at most 0.9 mm. Every check is unchanged (0 / 0 / 0; 5 self-crossing face
  pairs at the clavicular head's edge), and so are the volumes. The `mg5/` reports and sheets are refreshed.
- **MG7 rebuilt on that MG5:** identical volumes, all checks 0. The `mg7/` reports are refreshed.
- The MG6a reports still name the earlier MG5 blend (recorded by SHA). The difference is under 1 mm.

**Authored rules** (in the report):

| | Origin line | Insertion (s along HJC → KJC, u 0 → 1) | Thickness (trunk / fold) |
|---|---|---|---|
| Gluteus maximus | posterior iliac crest near PSIS (75 mm lateral, z 1.055) → lateral sacrum (40 mm, 0.99) → coccyx (15 mm, 0.925) | gluteal-tuberosity anchor slid from 0.06 (upper fibres, towards the iliotibial tract) to 0.26 | 32 / 40 mm |
| Gluteus medius | outer iliac crest from behind the ASIS (115 mm lateral, 40 mm anterior) to the posterior gluteal line (75 mm, 80 mm posterior) | greater-trochanter anchor, 0.13 → 0.16 | 14 / 22 mm, capped by fibre spacing |

**Results, both sides:**

- 0 outside the skin, 0 shallower than the layer, 0 self-crossings, 0 overlaps.
- No fibre shortened.
- Volumes: maximus 345 / 346 cm³, medius 144 / 144 cm³.

**Squat check** (`muscle_squat_pose_check_blender.py`, now including the glutes and reporting their volume and edge
stretch):

- The glutes add no overlaps. The only ones are the 92 hamstring–gastrocnemius face pairs behind the knee at 102°
  (MG7).
- At hip 100°:
  - maximus volume 1.017 of rest, edges 0.74–2.09×;
  - medius volume 1.008, edges 0.66–4.47×, local to where its binding blends from the pelvis to the femur.
- The bellies stay with the pelvis and stretch over the flexing hip. This is the same limit of a rest-pose binding
  that MG6a found at the shoulder.

**Limits.**

- Proxies. A real gluteus maximus is larger: the 4 mm subcutaneous layer is thin for the buttock, and the volumes
  are geometry-derived.
- The iliotibial tract, the tensor fasciae latae and gluteus minimus are not built.
- No per-pose response.

**Files.**

- `native_20261024/mg8/`:
  - reports: `mg8_left_report.json`, `mg8_right_report.json`, `mg8_left_squat_pose_report.json`;
  - sheets: `MG8_left_gluteal_sheet.jpg`, `MG8_right_gluteal_sheet.jpg`, `MG8_left_squat_sheet.jpg`.
- The blends are not in git; their SHA256 values are in the reports.

**Status of Work's squat contract.** All 12 muscles now have envelope proxies on both sides: the four quadriceps, the
three hamstrings, adductor magnus, the medial gastrocnemius, soleus, and both glutes.

## MG9a: bone-driven positioning of the shoulder proxies through the press (read-only check, added 30 Oct 2026)

**Status: partial. It works through the rack (90°). It does not hold above 120°. Not adopted.**

MG6a showed that blended bindings cannot follow the press. MG9a tries the bone-driven, volume-preserving positioning
that MG6a proposed, for the MG4 deltoid and the MG5 fans. The script is `muscle_fibre_sweep_press_blender.py`. It
runs on the MG8 blends (hash-checked, unchanged) and saves nothing.

**Method kept (the script's defaults):** rotation-blended Poisson deformation of each sheet's mid-surface.

- **Sheets.** Each sheet is F fibres × K stations, with an outer and a deep surface. The three deltoid heads are
  solved as one 36-fibre sheet, since they are adjacent in φ.
- **Ends.** Fibre ends are fixed rigidly to their bones: the origin end to its dominant bone, the belly end to the
  humerus.
- **Rotations.** Each station gets the origin bone's rotation slerped to the humerus's, weighted by its own rest
  humerus weight (the binding MG4 and MG5 authored).
- **Solve.** The mid-surface keeps its rotated rest along-fibre and across-fibre differentials, with the ends held.
  The along-fibre part fades out as the fibre goes taut:
  - after 30° of joint rotation (an active muscle pulls taut), or
  - once the end-to-end chord grows by 15 % of the fibre.
- **Obstacles.** The deep surface is kept outside three obstacles by least-squares soft constraints, re-solved:
  - the humeral head + cuff sphere about the posed GH;
  - the MG1 arm envelopes;
  - for the fans, the static thorax skin depth.
  Each clearance is never stricter than the node's own at rest, so the rest pose is admissible.
- **Thickness.** Thickness runs along the posed sheet normal (the rotated rest normal where the grid degenerates). The
  deep surface stays; the outer surface takes the thickness change, 1 / the fibre's stretch.
- **Rest round trip:** ≤ 0.0001 mm. Continuation in 3° steps.

**Results, left** (the right side agrees; reports `native_20261024/mg9a/mg9a_{left,right}_press_sweep_report.json`).
MG6a's blended binding is in brackets.

| | Rack 90° | Lockout 160° |
|---|---|---|
| Face overlaps (with MG1) | 257 [169] | 1638 [314] |
| Self-crossing face pairs | 163 | 1704 |
| Deltoid volume: anterior / middle / posterior | 0.96 / 1.41 / 1.07 [0.56 / 0.41 / –] | 0.35 / 0.40 / 0.38 [0.58 / 0.22 / –] |
| Fans volume: latissimus / teres / clavicular / sternocostal | 1.16 / 1.29 / 0.83 / 1.13 | 1.11 / 1.22 / 0.39 / 0.60 |
| Largest edge stretch: latissimus / sternocostal | 2.8× / 4.1× [5.6× / 9.0×] | 4.6× / 6.6× [8.4× / 15.5×] |
| Mean fibre length: deltoid anterior / middle | 0.65 / 0.65 | 0.64 / 0.54 |

**Reading.**

- **Through the rack** the deltoid keeps its volume, where MG6a lost 44–59 %, and the fans stretch about half as much.
  The middle deltoid overshoots (1.41), because the 1 / stretch thickness rule ignores width changes.
- **New overlaps at the rack** are mostly latissimus / teres major (141): both stretch, and the deep one meets the
  superficial one. MG5's separation pass would need to run per pose.
- **Deltoid shortening agrees with the path-length check.** The contract check gives −32 % / −39 % at the lockout for
  the anterior / middle heads (anchor paths with the cuff wrap). The sheet's mean fibre lengths are 0.64 / 0.54.
- **Above 120° the deltoid folds**, and the clavicular / sternocostal pectoral heads lose volume.
- **Teres major and latissimus fibres reach 2.0× / 1.6×** at the lockout. Those lengths follow from the bone-fixed ends,
  not the positioning method. They need re-checking on the corrected girdle: R41's scapula is about twice as wide as
  the CT reference, so its inferior angle is far from the humerus. This is a hypothesis, not measured.

**Why the deltoid fails above 120°.** At the lockout the glenohumeral joint has turned about 107° relative to the
scapula. That is more than the cap's own angular span (58° → about 140° from the humeral axis). The sheet has to unwrap
from the head and lie along the arm, which is a genuine change of curvature.

**Six schemes measured.** All were run on the left side through the same press; volumes are at the rack unless
stated.

1. **Taut string per fibre with the rest offsets carried along it:** turned inside out (anterior deltoid volume 0.03
   at the rack). The deltoid's rest fibres are meridians of its spherical frame, not shortest paths, so the carried
   offsets are larger than the fibre spacing. First the frames were built from neighbouring fibres; those degenerated,
   and a 4 mm path change swung the outer surface 30–58 mm.
2. **Rotation-blended Poisson keeping the rest shape:** deltoid volumes 0.46 / 0.71 / 0.88, then 0.08–0.20 at the
   lockout.
3. **The same, with the rest shape fading as the fibres go taut (kept):** the table above.
4. **"Membrane" (the across-fibre rest shape fades too):** every sheet loses width (volumes 0.2–0.3 at 60°).
5. **Great circles about GH (the deltoid re-laid in its own spherical chart):** anterior deltoid volume 0.17 already
   at 60°. Fixed-radius re-laying cannot unwrap the cap.
6. **The deltoid rebuilt as taut fibres in every pose, the rest pose included:** 28–37 mm from MG4 at rest, and the
   three heads collapse onto the same routes (4400 overlaps at rest).

**Also found.** MG1's envelopes are wound inward (negative signed volume). MG4's ray-march used a nearest-face inside
test that therefore reads them backwards. This was measured to have no effect: every MG4 cap ring is at its full
24 mm, and the thin rings are the tapered insertion end, as designed. MG9a orients the faces before testing.

**Next.**

1. **The deltoid above 120°** needs a construction that changes curvature. Two options:
   - a pose-aware rebuild by MG4's own rules in a moving frame: fibres on the posed head, cuff and MG1 floor between
     the posed origin and insertion lines, heads kept in their φ bands, thickness from the rest profile;
   - a volumetric (tetrahedral) simulation.
2. **A per-pose separation pass** for latissimus / teres major.
3. **The fan lengths** re-checked on the corrected girdle (c003/c004).

**Sheets.**

- `native_20261024/mg9a/MG9a_left_press_sheet.jpg` and `MG9a_right_press_sheet.jpg`: rest, rack and lockout.
- `MG9a_left_deltoid_closeup_sheet.jpg`: the deltoid alone, heads coloured (anterior red, middle green, posterior
  blue).
