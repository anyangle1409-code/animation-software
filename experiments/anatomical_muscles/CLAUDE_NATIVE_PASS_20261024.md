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
