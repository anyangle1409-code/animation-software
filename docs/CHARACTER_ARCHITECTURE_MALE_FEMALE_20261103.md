# Home Gym PT characters: male and female on one exercise system (3 Nov 2026)

**Status:** design and scaffolding only.

- The male model is the work in progress and has priority.
- The female model is not started.
- Neither model is production-ready.
- Nothing here changes production, PT_MODEL_VERSION 1.0, the frozen canonical skeleton or PT-App.

**Goal (owner, 3 Nov):** two high-quality, realistic characters that share one reliable exercise-animation system.

- Each model has its own approved proportions, muscle definition, surface and exercise deformation.
- The female model is never a scaled copy of the male mesh.

## 1. What is shared and what belongs to each character

| Layer | Shared by both | Per character |
|---|---|---|
| Bone names | The canonical names in `src/rig/boneNames.ts` (root, pelvis, spine_01…03, clavicle/scapula/upperarm/…, fingers 01–03) | — |
| Skeleton | The naming, the hierarchy and the joint conventions (axes, sign, zero pose) | Bone lengths, joint centres and pelvis shape, fitted to that body (§3). The canonical 1.75 m rig stays frozen as the male reference |
| Exercise definitions | `src/exercises` joint targets in degrees on canonical bones; phases, tempo, grip kind, closure, muscles, cues | The resolution of anything in absolute metres (§2), and per-character joint limits where anatomy differs |
| Corrective drive rules | `scripts/body_v2/r121_drives.py`: the inputs (elevation, plane, extension, elbow, wrist, finger curl, upper-arm twist band) and the gate maths | The shape keys themselves, authored on that body at those angles |
| Skin weights | — | Fitted per character |
| Region and landmark profile | The profile format (`review-assets/body_v2/characters/*/profile.json`) | The values: GH centres, the trapezius line, the leg join, the pec band, the fairing centres |
| Test harness and thresholds | `movement_trajectory_test_blender.py` and the regression sets, with the same thresholds for both (no relaxed tests) | The baselines, results and renders |
| Reference images | — | Separate sets per character, kept out of git, listed by file name and hash |
| Approval | The process (§5) | A separate approval record per character |

**Why this split already fits the app:**

- **Exercises are written in canonical joint angles.** `PoseSpec.joints` is in degrees per `BoneName`.
- **Characters are replaceable sources.** `src/character/registry.ts` holds them.
- **A character can keep its own skeleton.** `CharacterBuild.driver` transfers joint angles onto it (`retargetSource.ts`).
- **Hands follow the character's own hands, not the rig's.** That is `handMatrix` and `gripOffset`.

So a second character is mostly a new source with its own fitted skeleton. The animation system does not need a rewrite.

## 2. Reusing exercise definitions between bodies

**Angles transfer as they are.** A curl is elbow flexion from about 10° to about 140° on any body.

**Some fields are absolute metres and depend on the body:**

- `HandSpec.width` and `FootSpec.width`;
- `PoseIKTarget.target` and `pole` (world positions on the 1.75 m rig);
- root positions.

Copied onto a smaller body, these put the hands too far apart or out of reach.

**Plan (no change to existing definitions):**

1. **Body-relative resolution.** Each character profile carries measured segment lengths and landmarks: biacromial and bi-iliac width, upper-arm, forearm, hand, thigh and shank length, shoulder and hip height. A resolver maps every absolute target through those landmarks before IK.
   - Example: a hand target at the chest is expressed relative to the shoulder centre and scaled by arm length; a stance width by hip width.
   - A metre value stays the authored value for the canonical male, so his clips do not change.
2. **Contact pass per character.** After angle transfer, a short IK pass restores the contacts the definition names: both hands on one bar, feet planted, hand-to-thigh clearance. These are the same checks the harness already measures.
3. **Validation, not assumption.** Every reused exercise runs the full regression on each character. A movement that needs a real anatomical difference gets a per-character override, recorded beside its test result, not a silent edit of the shared definition. Examples:
   - a larger elbow carrying angle;
   - a different Q angle in the squat;
   - breast tissue in the press and push-up.

## 3. Why the female model cannot be a scaled male, and what it needs

Scaling preserves the male's ratios and tissue. The differences that matter for exercise animation are ratios and tissue, not size:

- **Skeleton:** narrower biacromial width relative to stature; a wider, shallower pelvis and a larger Q angle (knee tracking in the squat and lunge); a larger elbow carrying angle (curl and press path); a smaller ribcage; often greater joint range.
- **Soft tissue:**
  - different fat distribution (hips, thighs, upper arm);
  - less visible muscle relief at the same fitness;
  - breast tissue, which moves with shoulder elevation and needs its own corrective family in the press, fly, push-up and row.
- **Surface:** different pec, deltoid and trapezius contours; waist and hip silhouette; gluteal shape; hands and feet.

**What the female model gets:**

- her own reference sheet;
- her own sculpt or fitted base mesh;
- her own skeleton fit, using the same bone names and conventions;
- her own skin weights;
- her own corrective keys, authored at the shared drive angles;
- her own landmark profile.

The pipeline enforces this. `scripts/body_v2/character_profile.py` rejects a profile that declares it was derived from another character's mesh by scaling.

## 4. What changes in the Blender pipeline (incremental)

**Now:**

- 36 places in `scripts/body_v2/*.py` name the male objects directly (`HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE`, `HGPT_CANONICAL_V4_ORIGINAL`).
- Several scripts hard-code male region values: the leg cut at 0.45 of stature, the trapezius neck at |x| 6 cm, the pec band heights, the fairing centres.

**Rule from today:**

- New scripts and edits read the object names and region values from the character profile through `character_profile.py`.
- The default is the male profile, so every existing command keeps its exact behaviour.
- Older scripts are converted when they are next touched. There is no mass refactor while the male rebuild is the priority.

**Per-character data in the profile:**

- the Blender object names;
- the rig's stature;
- landmark definitions in that character's own rest frame;
- the region values each script needs, named after the script that uses them;
- the reference-image list (names and hashes, not the images);
- the path to that character's results.

## 5. Status and approval

**States, in order:**

`not_started` → `in_development` → `candidate` → `owner_review` → `approved_appearance` → `approved_movement` → `production_ready`.

**Rules:**

- `approved_appearance`, `approved_movement` and `production_ready` need an owner approval entry: date, what was approved, and the evidence link. The profile validator refuses a profile in those states without one.
- Claude never sets them on its own. Only the owner's explicit approval does.
- A workflow passing, or tests passing, is not approval.
- `production_ready` needs both owner approvals and a separate owner decision to ship. Until then, the production model and PT_MODEL_VERSION 1.0 stay as they are.

**Order of work (owner, 3 Nov):**

1. Finish the male model's appearance, then its movement, through owner review.
2. Female: only this architecture for now.
   - Her reference sheet and base mesh start after the male appearance is approved, unless the owner says otherwise.
   - Starting her early would split the effort the male rebuild needs.

## 6. Files

| File | What |
|---|---|
| `review-assets/body_v2/characters/manifest.json` | The characters, their status and where each one's assets, references, results and approval record live |
| `review-assets/body_v2/characters/hgpt_male_v2/profile.json` | Male profile: object names, stature (1.855 m mesh), GH landmarks and region values used today |
| `review-assets/body_v2/characters/hgpt_male_v2/APPROVAL.md` | Male approval record: currently candidate W12c, **not approved** |
| `review-assets/body_v2/characters/hgpt_female_v2/profile.json` | Female profile: placeholders, `not_started` |
| `review-assets/body_v2/characters/hgpt_female_v2/APPROVAL.md` | Female approval record: not started |
| `scripts/body_v2/character_profile.py` | Loads and validates a profile. It enforces the approval and no-scaling rules |
| `scripts/body_v2/tests/test_character_profile.py` | Unit test, run by the free-runner check workflow |
