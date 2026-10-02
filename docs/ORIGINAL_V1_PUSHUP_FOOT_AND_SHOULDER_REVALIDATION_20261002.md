# Push-up foot/toes and shoulder/axilla — re-validation against real humans (owner review of r41, 2026-10-02)

Status: COMPLETE for the skeleton question · skeleton RE-LOCKED as rev2c (`ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json`) after the first lock was withdrawn (`SKELETON_MOTION_LOCK_REOPEN_20261002.json`); the remaining shoulder problem is classified as DEFORMATION
Evidence folder: `ORIGINAL_V1_WORK/candidates/repair_checks/revalidation_20261002/` (+ earlier `skeleton_lock_r41/`)

## A. Push-up foot / toes

### Real-reference record (observation only; nothing stored; links + generic observations)

All viewed 2026-10-02 on Wikimedia Commons (public images of different people; viewed, not downloaded into the project).

| # | Reference (link) | Person / setting | Generic observation |
|---|---|---|---|
| R1 | [Caturaṅga Daṇḍāsana — Four-Limbed Staff](https://commons.wikimedia.org/wiki/File:Catura%E1%B9%85ga_Da%E1%B9%87%E1%B8%8D%C4%81sana-Four-Limbed_Staff.jpg) (barefoot, side, magnified on the foot) | adult man, carpet | body in one line, head slightly lower than feet; shin continues the body line; **foot about vertical** (ankle→ball line within ~5° of the floor normal, tilted a few degrees toward the head); **heel high**; **all toes lie flat on the floor pointing toward the head with their pads down**; hallux longest and lowest, lesser toes tucked beside it; the metatarsal heads (ball) are the pivot where the foot turns to the floor; toe interphalangeal joints nearly straight; load is carried by ball + toe pads |
| R2 | [Chaturanga-Dandasana low, Nina-Mel](https://commons.wikimedia.org/wiki/File:Chaturanga-Dandasana_low_Yoga-Asana_Nina-Mel.jpg) | adult woman, studio | same relationships: heel raised, foot ~vertical, toes flat, shin in line with trunk |
| R3 | [A posture in ashtanga yoga (15)](https://commons.wikimedia.org/wiki/File:A_posture_in_ashtanga_yoga_(15).jpg) | adult man, mat | same; toes flat, heel high |
| R4–R7 (shod) | [Law Enforcement Explorers close-up of push-ups](https://commons.wikimedia.org/wiki/File:2015_Law_Enforcement_Explorers_Conference_close_up_of_pushups.jpg), [2013 Best Warrior …-471](https://commons.wikimedia.org/wiki/File:2013_Best_Warrior_Competition_130624-A-YC962-471.jpg), [60 Hand-Release Push-ups](https://commons.wikimedia.org/wiki/File:60_Hand-Release_Push-ups_(6244934).jpg), [2CR Dragoon Week PT (8426303)](https://commons.wikimedia.org/wiki/File:2CR_Dragoon_Week_2024-_PT_Competition_(8426303).jpg) | different adults, boots/shoes | shank in line with trunk, heel raised, forefoot on the floor (shoes hide toes but confirm the foot steepness and that the load is at the forefoot) |
| R8 (hands) | [Person performs push-ups on a pink mat](https://commons.wikimedia.org/wiki/File:A_person_performs_push-ups_on_a_pink_exercise_mat.jpg) | adult woman | palms flat and planted, fingers forward and slightly spread, wrist extended, forearm leaning |

Biomechanics sources for foot/toe mechanics (>= 3 as required): PMC12019138 (first-MTP dorsiflexion ≈ 57–82°, plantarflexion ≈ 17–37°, passive > active),
PMC4266096 (MTP functional axis ≠ anatomical axis; the joint behaves as one unit in the walking data), PMC4994968 (ankle: dorsiflexion 10–20°, plantarflexion 40–55°),
PMC5095951 (foot as several functional segments), PMC6786540 (search summary: first MTP neutral ≈ 11–19° dorsiflexed; ≥ 50–75° in propulsion).
Human variability: toe extension in push-ups is at the top of the passive range (≈ 85–90° in R1–R3); hallux/lesser-toe length differences change which toe tips touch first.

### r41 versus the references

| Property | Real push-up (R1–R3, literature) | r41 (P2 pose) | r42 under P3 |
|---|---|---|---|
| ankle→ball line vs floor | ~85–90° (nearly vertical) | foot aimed D+0.1 F (≈ 84°) | same |
| ankle angle (rig convention, toes-up positive, relative to the rest bone which already tilts 17.6° down) | ≈ +20 | +21 | +22 |
| MTP / toe extension | ≈ 85–90° | 80° set, **toe axis finished 7.9° ABOVE the floor** (tip lifted; contact at the ball/base only) | toe axis **0.0°** (flat), MTP ≈ 84° |
| contact | ball + all toe pads | 262 vertices, tilted | 216 vertices, all owned by `toe_*`, flat |
| plank angle / hands | hands and toes both load | solved | solved (palm 3.6 mm, thumb pad 0, palm-normal 5.7° off the floor normal) |

**Diagnosis.** The ankle was already right (the earlier worry that it was wrong came from a sign mix-up; the numbers match the photographs). The real error was that r41 over-flexed the toe
by about 8° relative to a flat toe — the tip rose off the floor — a pose-construction value, not a rig defect. Fixed in P3: the toe is aimed flat along the floor (`aim(toe, F)`), a generic rule
(pad flat on the support surface), not an exercise name.

**Is the toe too rigid / a rigid block?** The mesh toe region is one slab with rounded digit lobes; every digit follows the single `toe_*` bone. In the references all toes bend the
same amount and lie flat, so a single transverse hinge reproduces the loaded forefoot. What is NOT yet believable is the *surface form* (slab thickness, digit separation, ball of the foot,
heel) — Phase 5F surface work, not skeleton work.

**Is a separate hallux / major-toe control justified?** Not by this evidence: no loaded exercise in the set needs the hallux to move independently of the lesser toes, the mesh has no
independent digits to deform, and a hallux bone driving the same slab would only add creases. Trigger to revisit (documented): Phase 5F models individual toes, or a contact audit shows the hallux and
lesser toes need different heights/angles on the same floor. Decision: single toe control retained; **no toe rig change.**

Images (r42/P3 skin, skin+skeleton, toe close-up, plus r41/P2 before): `revalidation_20261002/foot/`.

## B. Shoulder / axilla — skeleton-only diagnosis

Skeleton-only analysis (`audit_original_v1_joint_kinematics_blender.py`, 9 samples per pose, separate swing/twist interpolation) of press_bottom, press_top, press_top_rhythm, pullup_hang,
pullup_hang_rhythm and pullup_top on r42 under P3 (`revalidation_20261002/`), plus the earlier r41 sets.

1. **Pose/skeleton mechanics (cause found, fixed).** In P2 the plain `press_top`, `pullup_hang` and `pullup_bar` poses held clavicle and scapula still and raised the humerus 156–166° relative to the
   torso — glenohumeral-only elevation, which no human can do (references: scapula supplies ≈ 21–38 % of 30–90°, ≈ 53 % of 90–120°, and keeps contributing above that; PMC3377910, PMC9246406, PMC6620199).
   The `*_rhythm` variants used a fixed 14°/28° girdle, about half of the expected scapular rotation (≈ 60° at 166° total). The remaining "webbed" axilla in the owner's image is the
   skin being asked to absorb that impossible joint chain. P3 gives every elevated-arm pose an **interval-dependent** scapular profile (not a fixed ratio) and two plausible subjects
   (central estimate and a 1.25× high-scapular-share subject; references show 0.9:1–3.8:1).
2. **Humeral rotation.** Elbow hinge purity enforced (elbow abduction ≈ 0 in all poses); humeral external rotation 63–90° in elevated poses; forearm twist now only −5…+22°
   (P1: 85°). Skeleton-only path checks: 0 sign flips, 0 discontinuities, envelope PASS (13 392 components, 0 violations) for r42 under P3.
3. **Scapula pivot — a real rig-mechanics issue.** With a physiological 60° scapular upward rotation the plate pivots about the AC corner (the bone head), swinging the inferior angle about 0.27 m;
   the literature places the scapular instantaneous centre near the medial root of the scapular spine at low elevation, migrating toward the AC joint as elevation grows (PubMed 3196449, via search summary).
   Result in P3 (r42 dump analysis): the top 1 % stretched edges (up to 5.9×) are upper-back vertices weighted between `scapula` and `spine_02/03`. A pivot moved 35 % along the bone
   (candidate **r43**, declared before the edit in `repair_preparation/r43_scapula_pivot_declared/`) removes the torso-maximum and volume failures in metrics-only tests
   (14 → 11 failures) but moves stress to the shoulder minima; weights were tuned for the impossible poses, so each rig variant is being re-solved (`o41`) and compared.
4. **Twist helpers.** Under realistic P3 poses the both-segment helper rig (r41) is **worse** than no helpers (17 vs 14 failures; shoulder minimum 0.185 → 0.112/0.068, 28 regressions vs 20
   improvements); the forearm-only variant (r42) equals the 63-bone rig with 0 regressions and 7 improvements. **Decision: reject the upper-arm helpers** (their earlier benefit was an artefact of the impossible poses);
   **retain forearm helpers** (pronation/supination is a real, repeated 20–77° twist in curl, push-up, press, pull-up and they improved forearm/elbow metrics). Rev2b = 63 + 4 forearm helpers = 67 bones.

### Shoulder skin / deformation diagnosis (completed)

Weights re-solved on the realistic P3 poses (shoulder-zone solver, declared mask 2570 vertices, symmetric, bounds = pinned P3 baseline):

| Candidate | Rig | Weights | Dev failures | Visible form of press_top |
|---|---|---|---:|---|
| r42 | forearm helpers, scapula pivot at the AC corner | R2-era weights | 14 | torso side skin dragged up as a 0.2 m tent; volume 1.10–1.12 |
| r43 | + scapula pivot 35 % | same weights | 11 (metrics-only) | tent flaps remain |
| r45 | r43 + o41 (gate-only objective) + wrist band | | 5 | tent flaps (326 torso vertices > 10 cm from their trunk-driven position) |
| r46 | r43 + o43 (hard trunk anchoring: torso skin within 2 cm + 10 cm·exp(−(r/0.15)²) of trunk-driven position) | | 14 | flaps gone, **axilla web tears** (shoulder max stretch 7.9) |
| r47 | r43 + o44 (moderate anchoring) | | 4 | flaps reduced, jagged torn edges remain |
| r48 | r47 + wrist band (o26) | | **3** (torso max stretch: press_top 5.12, press_top_rhythm 6.34, pullup_hang_rhythm 5.84) | as r47 |

**Classification.** Rig: skeleton-only paths are correct (lock record); the causes found there (impossible poses, scapula pivot) are fixed. Weighting: 14 → 3 failures, push-up hand minimum cleared with wrist weights,
**but the tent ↔ tear frontier (r45 ↔ r46 ↔ r47) is the signature of a limit of linear blend skinning**: the lateral-torso skin below the armpit has to follow the arm a little and stay on the ribs a lot, and the web
between them has almost no rest-pose surface (the axilla is a hairline sliver at rest), so any weight field either lets the torso skin ride up with the scapula/arm or stretches the web 6–8×.
Topology: an earlier shoulder-yoke support loop (r23) did not help under the old poses; it has not been re-tested under P3 (candidate for the corrective step). Pose/contact: no longer the cause.

**Corrective deformation: justified, NOT implemented (prepared).** Exact trigger: glenohumeral elevation (angle between the humerus and the downward trunk axis) above ≈ 60°, ramping to full effect at ≈ 150°, together with the scapular upward rotation of the same pose.
Effect: slide the lateral-torso and axillary-web vertices back toward their trunk-driven positions and relax the web (a displacement field in rest-pose coordinates scaled by the elevation parameter), generic to every overhead/pull movement, deterministic,
authored first-party by a positions-level solve against the declared mask, stored as a shape key driven by the joint state (not by an exercise name). Evidence that weights alone cannot satisfy both gates and form: r45/r46/r47 above.
It is not implemented because it changes the asset's data model (shape keys/morph targets in the runtime) and needs an explicit design pass; the candidates, the solver prior (`w_trunk`) and the displacement diagnostics needed to build it are committed.

### Blockers (3 development failures on r48) — classification

1. `press_top`, `press_top_rhythm`, `pullup_hang_rhythm` torso `region_max_ratio` (5.12 / 6.34 / 5.84, gate 5.0): **corrective-deformation cause** (LBS limit at the axilla web); weights sit on the tent/tear frontier.
2. `pushup_bottom / hand` region minimum 0.119 → cleared on r48 by the wrist-band weight re-solve: **weighting cause** (the extended-wrist crease).
3. The earlier p99 blockers disappeared with the realistic poses + scapula pivot + weights.

## Answers required before locking the skeleton

* Are the toes/forefoot mechanically convincing in a loaded push-up? **Yes** after P3 (flat toe; ankle and MTP match three barefoot references; toe *surface form* is Phase 5F).
* Are the shoulder bones moving correctly through overhead press and pull-up? **Yes** (interval-dependent rhythm, smooth paths, envelope clean, pivot moved).
* Is humeral rotation correct? **Yes** (hinge rule; 63–90° external rotation; forearm twist −5…+22°).
* Is scapula/clavicle contribution believable? **Yes** (≈ 60° scapular upward rotation at 166° total, 1.25× variant; no fixed ratio).
* Are the twist helpers justified? **Forearm yes; upper-arm no (removed).**
* Are additional bones required? **No** (hallux, thigh/shin twist, palm, rib and extra shoulder helpers rejected with evidence).

The skeleton is therefore RE-LOCKED as rev2c; the remaining shoulder form issue is deformation.
