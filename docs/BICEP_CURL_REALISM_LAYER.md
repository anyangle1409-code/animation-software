# Bicep curl realism layer — preserve the accepted curl, add human motion quality

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting tracked checkpoint:** `98811bfb7591e656eb203faea47b71a067a418fe`  
**Do not merge. Do not promote. Do not start another exercise.**

## Why this phase exists

The current dumbbell bicep curl is mechanically accepted and technically clean, but a newly supplied reference video reads more lifelike in motion. The goal is **not** to replace the curl or throw away the validated work. The goal is to build a candidate **realism layer** over the accepted motion while preserving the existing grip, equipment contact, clearance, rig compatibility and loop quality.

The user should attach/provide the same movement reference video when this phase is executed. Use it as a motion-quality reference only, not as an appearance or identity target.

## Accepted baseline that must remain available as rollback

Keep the current accepted curl and current accepted character candidate untouched as rollback. The latest appearance candidate may live only in the working environment because the GLBs are gitignored; do not assume a fresh checkout contains it.

Preserve unless a candidate proves an improvement without regression:

- current dumbbell grip and 252° finger wrap;
- dumbbell/hand lock and no handle slipping;
- neutral wrist control with no bend-back at Peak;
- elbow staying beside the torso rather than flaring;
- accepted shoulder position with no shrugging;
- thigh/shorts clearance;
- bilateral control and clean Return to Bottom;
- renderer/exporter agreement;
- current rig, weights, skeleton, retargeting and solved-grip metadata;
- current accepted body appearance geometry unless pose-dependent deformation is added non-destructively.

## What the reference movement has that the current curl lacks

### 1. Pose-dependent muscle deformation — highest priority

The reference reads as if the arm muscles change shape as they shorten and lengthen. The current character mostly looks like a skinned mesh following bones.

Target a subtle, anatomically believable deformation layer so that:

- the biceps become visibly fuller/shorter toward Peak and lengthen toward Bottom;
- brachialis/upper-forearm mass participates rather than remaining static;
- forearm silhouette changes naturally through flexion/supination;
- the deformation blends smoothly into elbow, deltoid and armpit regions;
- Bottom returns exactly to the accepted baseline shape.

Prefer pose-space correctives / corrective morphs / equivalent non-destructive deformation driven by curl pose. Do **not** remodel the static body merely to fake contraction.

### 2. More continuous forearm supination

The reference progressively rotates from a more neutral start toward palms-up through the lift, then unwinds on the way down. The current curl should feel less like a fixed wrist/forearm orientation.

Target continuous neutral → supinated → neutral rotation distributed through the forearm/twist chain, while preserving the accepted wrist alignment and grip contact. Do not spin the wrist independently or break the dumbbell lock.

### 3. Small elbow and shoulder/scapular secondary motion

The elbow should remain anchored beside the torso but not look nailed to one point. Allow only subtle natural motion:

- a small forward elbow contribution late in the lift;
- natural return during lowering;
- slight shoulder-head/scapular response to the arm shortening;
- no shrugging, flare, torso swing or cheating.

This is secondary motion, not a new exercise technique.

### 4. Timing / turnaround realism

The current 5.5 s curl with an obvious Peak/Squeeze hold reads more like an instructional keyframe demo than the supplied reference.

After deformation and kinematics are visually sound, make a timing candidate with:

- continuous controlled lift and lowering;
- smoother acceleration/deceleration;
- a much shorter, softer Peak turnaround instead of a hard hold;
- no bounce or ballistic reversal;
- clean loop continuity.

Do not force the reference video's exact duration if it harms instructional clarity. Compare the current 5.5 s baseline with a more natural candidate and let visual review decide.

### 5. Micro-asymmetry only if still necessary

Only after the above is working, consider tiny natural bilateral differences in timing/position. Keep them subtle enough that the exercise still demonstrates correct symmetrical technique. Do not add visible wobble or sloppy form merely to look less procedural.

## Work order

Work in this order and stop for visual review after each meaningful retained stage:

1. pose-dependent biceps/brachialis/forearm deformation;
2. progressive forearm supination while maintaining grip/wrist correctness;
3. subtle elbow + shoulder/scapular secondary motion;
4. softer/shorter Peak turnaround and timing candidate;
5. optional micro-asymmetry only if the motion still looks unnaturally perfect.

Do not jump directly to timing or asymmetry before solving deformation and arm kinematics.

## Guardrails / validation

For every retained candidate, prove that:

- grip contact remains locked and the dumbbells do not slide/rotate independently;
- wrists stay anatomically neutral rather than compensating for supination;
- elbows do not flare or drift excessively;
- shoulders do not shrug;
- the torso remains stable with no cheating swing;
- thigh/shorts clearance stays valid;
- hands/fingers do not penetrate the dumbbell;
- clothing remains valid;
- Bottom and Return still match cleanly;
- the loop has no snap at Bottom, Peak or Return;
- the current accepted static body shape is unchanged at Bottom unless an explicitly reviewed corrective requires otherwise;
- no unrelated exercise is retuned.

Use focused diagnostics first. Run expensive/full validation only on a candidate proposed for retention.

## Required review evidence

For each meaningful candidate, provide the real app/rendered dressed character, not an approximation:

- full loop or short recording at normal playback speed;
- Bottom, Mid, Peak and Return stills;
- 3/4 full-body view;
- close-up of shoulders/elbows/forearms/hands during the lift;
- side view showing elbow and shoulder secondary motion;
- before/after comparison against the accepted curl using the same camera and playback speed;
- short written note explaining exactly what changed and what stayed locked.

## Exit condition

This phase is complete only when the user visually approves the more natural curl and the accepted mechanical/technical guards still pass. Until then, retain the old accepted curl as rollback.

**Do not merge or promote without separate user authorisation.**
