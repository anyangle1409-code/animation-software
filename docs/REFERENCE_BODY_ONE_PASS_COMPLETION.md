# Reference body — one-pass completion handoff

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting HEAD:** `8d37bd88aba5272e692c1945252264f6fbb3d35d`  
**Do not promote or merge.**

This file is the next-session execution handoff. It is deliberately written to minimise back-and-forth and usage. Continue from phase to phase automatically when the preceding phase meets its acceptance criteria. Stop only for a genuine structural conflict, a new non-pre-existing regression, or a visual choice that cannot be decided objectively from the existing references/measurements.

## Stage 1 status — freeze it

Stage 1 is accepted and may now be treated as **frozen baseline work**.

Retained Stage 1 state:

- `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
- SHA-256 `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`
- forearm proportion corrected to **14.86% of figure height**;
- Stage 1 forearm bind/surface correction retained;
- character-specific `handleGripOffsets` retained;
- renderer/exporter grip placement agreement retained;
- curl neutral rebase retained:
  - `startPose.upperarm_l/r.x = 4.3°`;
  - `peakPose.upperarm_l/r.x = 8.3°`;
  - relative upper-arm curve unchanged by exactly +4.3° throughout;
- curl Bottom/Return dumbbell/thigh contact cleared to **+1.74/+1.82 mm**, zero vertices inside;
- elbow-flexion, supination, timing/easing, clavicle behaviour and abduction otherwise unchanged;
- grip closure remains **85%** for the current profile until the dedicated grip phase below decides whether the reusable power-grip profile needs a different closure value;
- elbow corrective remains **0%**;
- Stage 2 shoulder widening has not started.

The carried-over solver/canonical-space limitation is **accepted for Stage 1** under the existing diagnostic allowance. Do not restructure the equipment pipeline solely to make renderer/exporter/solver share an identical runtime frame unless later evidence proves an actual error from that ordering.

Do not reopen Stage 1 curl mechanics unless a later retained change creates a measured regression.

---

# Phase 1 — lock a reusable full-fist cylindrical grip

The current visual problem is specific and important: the dumbbell can read as if only the **tips of the fingers** are hooked around the handle. The target is a convincing **full-fist / power grip**.

## Visual target

For a dumbbell/bar/straight cylindrical handle:

- handle sits **deeper in the palm**, not out near the fingertips;
- all four fingers curl substantially around the handle;
- proximal and middle phalanges participate in the wrap, not just fingertips;
- fingertips continue around/under the handle rather than merely touching it;
- thumb opposes and locks the handle naturally;
- palm visibly loads the handle;
- the closed hand reads as a **fist around an object**, not an open hand with bent fingertips;
- wrist remains neutral/natural for the exercise;
- no finger penetrates the handle unnaturally;
- no large air gap appears between palm and handle;
- left/right grips mirror correctly.

This is the user's approved grip standard.

## Make it reusable, not curl-specific

Do not solve this only by hand-authoring the bicep curl.

Create/refine a reusable **closed cylindrical-handle grip profile** that can be used by any exercise/equipment where a power grip is appropriate, including dumbbells, straight bars and compatible handles.

The reusable grip system should support:

- left/right mirroring;
- handle axis/orientation;
- handle radius/diameter where available;
- character-specific handle centre / `handleGripOffsets`;
- finger closure/contact around the real handle rather than a single fixed world pose;
- thumb opposition;
- deterministic reuse across exercises.

Do **not** apply the closed-fist profile to non-gripping contacts such as push-up palms on the floor. Pull-up/bar work may reuse the same cylindrical grip family but must preserve the appropriate wrist/forearm orientation for the bar.

## 85% closure is not sacred in this phase

The existing 85% closure was a safe working baseline. If it is objectively insufficient for a full-fist grip, it may be refined.

However:

- do not simply crank all finger joints uniformly;
- measure the actual handle-to-finger/palm relationship;
- preserve anatomical joint limits;
- keep the thumb functional and opposed;
- avoid finger self-intersection;
- avoid handle penetration through solid palm/finger geometry;
- prefer the **minimum profile change** that produces a convincing secure grip.

If a single reusable closure parameter is inadequate across handle diameters, use a compact diameter-aware mapping rather than per-exercise magic numbers.

## Grip acceptance evidence

Before moving on, provide close-up matched-camera evidence for at least:

- curl Bottom;
- curl Mid lift;
- curl Peak;
- one second exercise/handle use if available (e.g. shoulder press or pull-up/bar grip) to prove reuse.

Inspect both hands for:

- handle depth in palm;
- all four fingers;
- thumb;
- palm contact;
- wrist transition;
- handle centring;
- bilateral symmetry.

Add focused assertions/measurements that protect the intent rather than one arbitrary pose number. Useful checks may include handle-to-finger-loop distance, palm-side containment, bilateral symmetry and invariance through the rep.

Do not weaken existing grip/contact tests.

### Phase 1 pass condition

Proceed automatically when the full-fist grip is visually convincing, numerically stable, bilateral, reusable and does not regress curl/press/pull-up equipment lock or hand/wrist deformation.

If the only way to obtain the grip requires destructive hand reweighting or a topology change, stop and report before doing that.

---

# Phase 2 — Stage 2 shoulder-width correction

After the grip is locked, proceed to the already-approved Stage 2 direction.

The reference-fit investigation established:

- the Stage 1/canonical shoulder lateral offset is narrower than the supplied physique reference;
- fake deltoid inflation is not the correct solution;
- the canonical rig and source character should be widened **together**.

## Stage 2 goal

Bring the shoulder/clavicle system closer to the supplied reference while preserving the now-frozen Stage 1 forearm correction and grip work.

Use the previous rig proposal/decision docs as the measurement source. Re-verify current numbers before applying them; do not blindly reuse a stale transform if Stage 1 altered the relevant frame.

Expected direction is approximately the previously measured arm-chain lateral shift, but the retained value must be justified by the current calibrated reference overlay.

## Stage 2 hard constraints

- widen canonical shoulder/clavicle/upper-arm attachment and source character together;
- do not fake width using extra deltoid mass;
- preserve upper-arm length unless a fresh measurement proves otherwise;
- preserve corrected forearm proportion;
- preserve the full-fist grip profile;
- preserve accepted curl relative motion;
- preserve topology and skin weights unless the shoulder change objectively proves a local weight correction is required;
- recompute only the inverse binds/rest data actually affected by the moved chain;
- keep v7/v6/v5 and prior candidates untouched as fallbacks;
- make a separate Stage 2 candidate;
- do not promote.

## Reference-fit targets

Re-run the locked front reference overlay and report at minimum:

- shoulder span;
- humerus-axis lateral offset;
- shoulder slope;
- neck/trap-to-deltoid contour;
- chest/waist V-taper;
- arm silhouette;
- skeleton/joint-centre overlay.

The intended shoulder silhouette remains:

`neck → descending upper trap → rounded deltoid cap → upper arm`

not:

`neck → horizontal shelf → abrupt deltoid drop`.

Do not invent side/rear depth from a front-only reference. Keep unsupported depth changes close to the prior validated body until a side/rear reference exists.

### Phase 2 pass condition

Proceed automatically when the shoulder change is numerically closer to the reference, visually natural, joint centres sit plausibly inside the surface, strain/deformation remain acceptable, and no exercise/equipment regression appears that cannot be handled by re-derived contact rules.

---

# Phase 3 — full exercise/contact/deformation validation

With Stage 1 + full-fist grip + Stage 2 in place, run one complete validation pass rather than repeatedly running the expensive suite during tuning.

Required poses:

- bicep curl: Bottom / Mid / Peak / Return;
- deepest squat;
- shoulder press: Bottom / Overhead;
- push-up: Top / Bottom;
- pull-up: Bottom / Top.

Inspect:

- neck/traps/shoulders/armpits;
- elbows;
- forearms;
- wrists;
- palms;
- fingers/thumbs;
- equipment lock/contact;
- chest/waist;
- hips/groin/glutes;
- knees;
- calves/ankles/feet/toes.

Re-derive contacts from rules after the shoulder change. Do not preserve old world-space hand/equipment positions merely because they were previously accepted.

Curl remains closed unless a genuine Stage 2 regression is found.

---

# Phase 4 — push-up wrist + forearm deformation package

The push-up has two known issues that must now be treated together:

1. excessive wrist extension / hand-placement geometry;
2. visibly bad forearm deformation in the push-up pose.

Do **not** assume one causes the other. Diagnose both against the final Stage 2 proportions first.

## Re-measure after Stage 2

Re-measure at Push-up Top and Bottom:

- true wrist extension angle;
- shoulder-to-hand horizontal offset;
- forearm angle from vertical / floor;
- elbow position;
- hand-floor contact point;
- radius/ulna/forearm twist distribution;
- wrist-to-forearm silhouette;
- elbow-to-forearm silhouette;
- relevant skin-weight strain / ring metrics.

The old ~102.7° / ~95.5° wrist values and ~218 mm shoulder-ahead-of-hand finding are historical evidence, not the final target numbers. Stage 2 changes shoulder-to-hand geometry; re-measure from scratch.

## Forearm-deformation diagnosis

Explicitly determine whether the bad forearm shape comes from:

- excessive wrist extension;
- hand placement;
- forearm pronation/twist distribution;
- the Stage 1 lengthened forearm interacting with existing weights;
- the v5→v6 hand/wrist repair region;
- elbow/forearm orientation;
- skin weights;
- or a combination.

Do not mask a skinning/twist defect by moving the push-up pose unless the pose is actually the root cause.

Likewise, do not reweight the forearm if correcting hand placement/wrist angle removes the deformation cleanly.

Use systematic root-cause evidence and make the smallest fix at the source.

## Push-up acceptance

At Top and Bottom:

- wrist extension is anatomically plausible;
- palm remains planted and stable;
- forearm reads as a natural anatomical volume;
- no pinching/collapse;
- no corkscrew/twisted radius-ulna silhouette;
- smooth wrist-to-forearm transition;
- natural elbow-to-forearm transition;
- no new hand/wrist weight artefact;
- bilateral symmetry;
- technique still reads as a proper push-up;
- no compensation elsewhere in shoulder/chest/spine.

Only after the final proportions are known should hand placement be changed. Derive the new contact location from the anatomy and technique constraints; do not simply apply the old ~20 cm estimate.

---

# Phase 5 — final cleanup and review pack

When all preceding phases pass:

1. remove temporary diagnostic helpers/workflows that are not part of the retained solution;
2. keep useful reproducible diagnostics if they are genuinely part of the permanent validation path;
3. update `AI_CHANGELOG.md` with all retained changes;
4. update the relevant handoff/result docs;
5. typecheck;
6. build;
7. run the focused tests and then the full suite once;
8. record the known pre-existing `strainReview` timeout separately if it remains the only failure;
9. confirm tracked tree clean;
10. identify one final candidate body + dressed candidate with SHA-256 values;
11. do **not** promote or merge.

## Final review pack — one user review, not repeated approvals

Return one concise final package containing:

- branch HEAD;
- final candidate filenames + SHA-256;
- Stage 1 freeze confirmation;
- full-fist grip close-ups (Bottom / Mid / Peak and one reused grip example);
- grip metrics/profile summary, including final closure behaviour and handle-diameter handling;
- reference vs final body overlay;
- shoulder before/after comparison and measurements;
- skeleton/joint overlay;
- curl review sheet;
- push-up Top/Bottom close-ups emphasising wrists and forearms;
- final all-exercise validation sheet;
- strain/deformation summary;
- typecheck/build/test result;
- remaining known limitations, especially anything that truly requires a side/rear body reference;
- explicit statement that nothing was promoted or merged.

## Automatic-continuation rule

Do **not** stop for approval between these phases if the preceding phase meets its written acceptance criteria.

Continue automatically:

**freeze Stage 1 → lock reusable full-fist grip → Stage 2 shoulders → full validation → push-up wrist/forearm fix → final cleanup/review pack**.

Stop only if:

- a structural conflict means two acceptance criteria cannot both be met;
- a new genuine regression appears that cannot be isolated safely;
- a destructive topology/weight rewrite becomes necessary;
- or an unresolved visual decision has no objective answer from the supplied reference/evidence.

Keep usage low by using focused diagnostics during iteration and expensive full validation only on retained candidates.

**Do not promote or merge.**