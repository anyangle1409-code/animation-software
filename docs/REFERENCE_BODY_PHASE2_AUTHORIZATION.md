# Reference body — Phase 2 authorization

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting HEAD:** `03c77730567da8d2861ca94d5b7febbb7927831b`  
**Phase 1 is locked. Phase 2 derivation is accepted. Do not promote or merge.**

This file resolves the explicit decisions needed to execute and finish the already-derived Stage 2 shoulder widening. The derivation itself is complete; the next step is implementation and validation, not re-derivation.

## Locked Phase 1 state

Do not reopen Phase 1 unless Stage 2 creates a measured regression.

Retained together:

- corrected forearm proportion from Stage 1;
- close-until-contact cylindrical grip solver;
- character-specific handle centre shifted **9 mm proximally/deeper into the palm**;
- curl neutral rebase **4.55° / 8.55°**;
- relative upper-arm late drift remains exactly **4.000000°**;
- Bottom / Return dumbbell-to-thigh clearance **+1.81 / +1.90 mm**, zero inside;
- grip contact:
  - fingers about **−0.46 / −0.36 / −0.22 / −0.11 mm** skin press, zero inside;
  - thumb about **+1.18 mm** clear/opposing;
  - palm about **−2.54 mm** loaded;
  - wrap about **252°**;
  - both hands effectively identical;
- all 22 authored curl technique rules pass;
- renderer/exporter grip agreement remains **0.0000 mm**;
- shoulder press reuses the solved grip without per-exercise finger tuning;
- elbow profile, supination, timing/easing and other accepted curl mechanics remain unchanged.

## Accepted Stage 2 derivation

The latest calibrated front overlay supersedes the older shoulder-row measurement.

Current finding:

- every major landmark is within about **0.8% of figure height** of the supplied reference except the shoulders;
- current shoulder span is about **4.17% of figure height too narrow**;
- widening must be achieved structurally through the clavicle/shoulder/arm chain, not by scaling arm lengths and not by adding fake deltoid mass;
- measured response shows **1.924% of figure height per side** is the retained target direction;
- the shoulder landmark vertical mismatch independently improves from about **+2.6% to +0.4%**;
- the residual left/right mismatch is inherited from the source asset's own asymmetric weights and is not a reason to deform one side differently.

The first character-side implementation was proven invalid because translating `DEF-upper_arm.*` sideways changed the clavicle-tail direction without updating the clavicle's stored rest orientation, and a matrix-order error compounded it. That method is superseded by the corrected bind representation below.

## Proven Stage 2 bind/retarget fix

The corrected character widening is now the retained implementation method:

- clavicle head remains fixed;
- clavicle tail moves to the widened shoulder position;
- clavicle stored rest orientation rotates by the exact tail-direction change, about **10.147°**, symmetrically;
- affected arm descendants follow the new clavicle tail;
- matrix composition uses the verified glTF/row-major order established against an independent reader;
- the tool re-reads its own output and verifies achieved placement;
- clavicle heads remain fixed to **0.00 mm**;
- arm chains move purely laterally by about **38.82 mm** on both sides;
- achieved placement is exact to numerical noise;
- import height/scale remain identical to the locked Stage 1 character;
- bones outside the arm chain remain stationary under the same canonical poses;
- locked Phase 1 grip contact remains identical to the digit on the widened rig;
- curl Bottom/Return thigh clearance improves rather than regresses.

Do **not** reopen or replace this bind fix unless a later retained change proves an actual regression. The character and canonical rig must always be validated as a matched pair.

---

# Decision 1 — shoulder-relative contact rules are authorised

Where an exercise/equipment rule explicitly expresses intent such as **"shoulder width"**, **"just wider than shoulders"**, or another shoulder-relative span, the contact rule may and should be re-derived from the widened shoulders rather than preserving stale absolute world-space widths.

This applies to the affected press / push-up / pull-up width logic discovered in the Stage 2 derivation.

## Pull-up

The current pull-up hands are locked to fixed rack sockets (`pullup_l/r`). A wider shoulder-derived grip cannot simply move the hands off those sockets.

Authorisation:

- update the relevant pull-up grip anchor/socket geometry or equipment contact definition **together with** the shoulder-derived hand target so the hands still visibly and mechanically hold the bar;
- preserve the exercise's stated grip intent rather than its previous absolute span;
- do not create free-floating hands or keep a fixed rack socket merely to satisfy an old test;
- do not introduce exercise-specific finger magic numbers — continue using the locked reusable cylindrical grip system.

If the rack has a real physical maximum/minimum that conflicts with the new shoulder-relative target, stop and report that physical conflict rather than forcing the body or grip.

## Push-up

Authorisation:

- re-derive push-up hand/floor placement from the widened shoulder geometry where the existing rule is shoulder-relative;
- keep palms properly planted and preserve push-up technique intent;
- **do not perform the dedicated wrist/forearm-deformation repair yet** beyond changes that are strictly required to carry the Stage 2 shoulder-width geometry through the existing contact rule.

The full push-up wrist-extension and forearm-deformation package remains Phase 4. Re-measure it after Stage 2 rather than applying historical offsets or the old ~20 cm estimate.

## Press and other width envelopes

Where the rule label/definition explicitly means shoulder-relative width, shift/recompute the envelope by the same shoulder-width change so the semantic rule is preserved.

Do not alter rules that are truly absolute equipment dimensions merely because a nearby shoulder-relative rule changed.

---

# Decision 2 — procedural body and muscle anchors must follow the widened rig

The canonical rig, character and procedural anatomy must remain mutually consistent.

Authorisation:

- widen/move only the **shoulder-dependent procedural anchors, attachment points and muscle placements** required by the new canonical shoulder position;
- carry clavicle / shoulder / deltoid / upper-arm attachment placement outward consistently with the measured Stage 2 shift;
- preserve already-correct torso measurements such as chest, waist, ribcage and other landmarks that the calibrated reference already places within tolerance;
- do **not** scale the whole torso;
- do **not** globally widen muscle bellies;
- do **not** inflate deltoid mass to fake shoulder width;
- keep muscle radii/volumes unchanged unless the widened joint/anchor objectively places a procedural belly outside the skin or produces a demonstrated anatomical mismatch;
- if a local belly/anchor needs translation to remain inside the surface, translate/re-anchor it by the smallest shoulder-derived amount rather than scaling it by default.

The aim is:

**wider skeleton placement with the same appropriate muscle mass**, not a generally bulkier character.

---

# Decision 3 — local containment-proxy armpit bridge is authorised

After the corrected bind/retarget implementation and full Stage 2 re-application, one small containment failure remains:

- `pectoralis_l` reaches about **7.84 mm outside** the containment skin in push-up against the existing **7 mm** allowance;
- latissimus reaches about **7.34 mm outside**;
- both exit nearest `spine_03`, at the lateral chest/armpit transition;
- the visible chest must not widen and the moved deltoid/upper-arm section must remain at the new shoulder position;
- permitted muscle-placement/taper/flatten/outward adjustments were measured and do not solve the problem cleanly;
- the residual is therefore treated as a **local gap in the containment proxy coverage**, not evidence that the visible torso or muscle bellies need more mass.

### Authorised fix

Open the containment/profile skin's coverage **locally and symmetrically** through the lateral chest → armpit → moved deltoid/upper-arm transition.

This is a proxy/coverage correction only. It is **not** permission to change the rendered body silhouette or make the character bulkier.

Use the smallest smooth bridge that:

- brings both pectoralis and latissimus comfortably back inside the existing **7 mm** allowance;
- gives a small sensible safety margin rather than targeting a fragile 6.99 mm pass;
- remains local to the shoulder/armpit transition around the `spine_03` lateral chest edge;
- is left/right symmetric;
- joins the fixed chest region to the widened shoulder/deltoid region without a discontinuity;
- does not create excess containment volume elsewhere.

### Hard constraints

Do **not**:

- widen the visible chest or ribcage;
- change waist width;
- scale the pectoralis or latissimus belly;
- inflate deltoid mass;
- change the accepted Stage 2 shoulder span merely to satisfy containment;
- alter Phase 1 grip/curl work;
- relax or globally raise the **7 mm** containment threshold;
- use a broad torso-wide proxy expansion when a local armpit bridge solves the measured gap.

The expected correction is small — the present overages are under 1 mm beyond the existing allowance — so prefer the minimum smooth local proxy adjustment that clears both muscles with margin.

### Stage 2 completion rule after this fix

After applying the local containment bridge, rerun focused Stage 2 validation and then the full suite once.

Stage 2 may be locked when:

- `pectoralis_l` and latissimus both pass the existing containment limit;
- all four exercises still validate cleanly;
- the matched Stage 2 character/canonical-rig bind equivalence remains intact;
- shoulder span and silhouette remain unchanged from the accepted Stage 2 result;
- Phase 1 grip/contact and curl mechanics remain preserved;
- typecheck/build pass;
- the full suite is green apart from any clearly pre-existing environmental skip/timeout already documented;
- no new structural regression remains.

If those conditions pass, **lock Stage 2 and continue automatically to Phases 3–5**. Do not stop for another approval merely because the proxy bridge was the last Stage 2 blocker.

---

# Stage 2 execution sequence

1. Start from the locked Phase 1 state.
2. Apply the accepted Stage 2 shoulder widening using the **corrected clavicle-rest/bind method** above; do not return to the broken rigid child-translation method.
3. Widen the matching canonical rig shoulder/clavicle chain by the same intended anatomical change.
4. Recompute only the inverse binds/rest data genuinely affected by the moved chain.
5. Keep upper-arm and forearm lengths unchanged.
6. Keep skin weights/topology unchanged unless a fresh, local, objective failure proves a correction is necessary.
7. Re-apply the already-derived explicitly shoulder-relative press/push-up/pull-up widths, rack sockets and measured pull-up hang correction without re-deriving their values unless current geometry proves a mismatch.
8. Re-apply the already-derived 2-hop shoulder surface ramp and shoulder-dependent procedural-body/muscle anchor changes.
9. Apply Decision 3's smallest local containment-proxy armpit bridge only if the recorded pectoralis/latissimus residual still reproduces.
10. Preserve the locked full-fist grip solver and Phase 1 curl mechanics.
11. Produce/retain a separate Stage 2 candidate; do not overwrite fallbacks.
12. Run focused Stage 2 validation first; run the expensive full suite only on the retained candidate.

## Stage 2 acceptance

Stage 2 may be retained when all of these are true:

- shoulder span is at or effectively on the calibrated reference target;
- shoulder slope / neck-trap-deltoid contour is visibly improved and natural;
- no fake deltoid inflation was used;
- shoulder/upper-arm joint centres sit plausibly inside the surface;
- upper-arm and corrected forearm lengths remain unchanged;
- topology and weights remain unchanged unless a documented local exception became necessary;
- procedural body/muscles follow the widened rig without belly-outside-skin artifacts;
- press validates;
- pull-up hands remain on the real bar with the intended shoulder-relative grip;
- push-up contact rule follows the widened shoulder geometry without prematurely doing the Phase 4 wrist/forearm redesign;
- curl Phase 1 grip, motion and thigh clearance remain clean;
- no new structural regression remains unresolved.

Do not preserve old absolute contact positions merely to keep legacy assertions green. Update assertions only where their stated semantic intent is shoulder-relative and the re-derived value preserves that intent. Do not weaken unrelated tests.

---

# After Stage 2

If Stage 2 passes, continue automatically with the remaining phases from `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`:

1. **Phase 3 — full exercise/contact/deformation validation**;
2. **Phase 4 — push-up wrist + forearm-deformation package**, explicitly re-measured after Stage 2;
3. **Phase 5 — cleanup and final review pack**.

Do not stop for approval between those phases when the written acceptance criteria pass.

Stop only for a genuine structural conflict, an unavoidable destructive topology/weight rewrite, or a visual decision that cannot be resolved from the existing reference and measurements.

Keep usage low. Do not promote or merge.
