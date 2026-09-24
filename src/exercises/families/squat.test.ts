import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { airSquat } from '../definitions/airSquat';
import { bicepCurl } from '../definitions/bicepCurl';
import { squatFamily } from './squat';
import type { ExerciseDefinition } from '../types';

/**
 * The squat family, and the one modelling gap it exposed.
 *
 * A squat's hip and knee angles are solved, not authored: the root placement
 * sets how far the body sinks, the feet are locked, and the IK fills in the
 * legs. The `jointTargets` for hip and knee therefore describe the result
 * rather than produce it — which is fine, and is what the technique rules and
 * the documentation read, but only while they agree with what the solver
 * actually produces.
 *
 * Nothing else in the codebase would notice them drifting apart. The exercise
 * would still validate, the feet would still hold to 0.25 mm, and the
 * definition would quietly describe a movement different from the one it plays.
 * So the agreement is measured here.
 */
const rig = canonicalSkeleton;
const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;

/** The pose at the bottom hold, which is halfway through a symmetric tempo. */
function atBottom(exercise: ExerciseDefinition) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const frame = resolveFrame(rig, evaluation, clip, clip.duration * 0.5, { anchors });
  evaluation.apply(frame.pose);
  return {
    hip: deg(frame.pose.rotations.thigh_l?.x),
    knee: deg(frame.pose.rotations.shin_l?.x),
    ankle: deg(frame.pose.rotations.foot_l?.x),
    pelvis: evaluation.head('pelvis', new Vector3()).y,
  };
}

describe('the squat family', () => {
  it('authors hip and knee angles that agree with what the solver produces', () => {
    // 3° is comfortably inside the measured agreement (1.5° at the hip, 1.2° at
    // the knee) and far outside the disagreement an inconsistent bundle causes:
    // authoring the hip 15° shallower moves the solved angle by 0.6°, leaving a
    // 16° gap between what the definition says and what the body does.
    const solved = atBottom(airSquat);
    const asked = {
      hip: airSquat.jointTargets.find((t) => t.bone === 'thigh_l' && t.axis === 'x')!.peak,
      knee: airSquat.jointTargets.find((t) => t.bone === 'shin_l' && t.axis === 'x')!.peak,
      ankle: airSquat.jointTargets.find((t) => t.bone === 'foot_l' && t.axis === 'x')!.peak,
    };
    expect(Math.abs(solved.hip - asked.hip), `hip: asked ${asked.hip}, solved ${solved.hip.toFixed(1)}`)
      .toBeLessThan(3);
    expect(Math.abs(solved.knee - asked.knee), `knee: asked ${asked.knee}, solved ${solved.knee.toFixed(1)}`)
      .toBeLessThan(3);
    // The ankle is an input rather than an output — a floor lock fixes where the
    // foot is, not which way it points — so it lands exactly.
    expect(Math.abs(solved.ankle - asked.ankle)).toBeLessThan(0.5);
  });

  it('is driven by the root placement, not by the leg angles', () => {
    // The claim the family's header rests on, checked rather than asserted.
    const shallower = squatFamily({
      id: 'probe', name: 'probe', clipName: 'probe', description: 'probe',
      depth: { hip: 100, knee: -114, ankle: 26, root: { y: -0.34, z: -0.23 } },
    });
    const base = atBottom(airSquat);
    const raised = atBottom(shallower);
    // 10 cm less root descent is 10 cm less pelvis descent, near enough exactly.
    expect(raised.pelvis - base.pelvis).toBeCloseTo(0.1, 2);
    // And the legs follow it, unasked: the angles were left alone.
    expect(raised.hip).toBeLessThan(base.hip - 5);
    expect(raised.knee).toBeGreaterThan(base.knee + 5);
  });

  it('gives the lower body its own stance, which the upper body does not share', () => {
    // Building this family is what turned up that `plantedStance` had baked in
    // the upper body's numbers while claiming all three exercises agreed on them.
    expect(airSquat.feet).toEqual({ width: 0.42, toeOut: 12, planted: true });
    expect(bicepCurl.feet).toEqual({ width: 0.32, toeOut: 6, planted: true });
    const tolerance = (exercise: ExerciseDefinition) => {
      const rule = exercise.technique.find((entry) => entry.id === 'foot_planted_l');
      return rule && rule.kind === 'stationary' ? rule.tolerance : null;
    };
    expect(tolerance(airSquat)).toBe(0.015);
    expect(tolerance(bicepCurl)).toBe(0.012);
    // The shape is still shared: same rule, same locks, same shape of foot spec.
    expect(airSquat.locks).toEqual(bicepCurl.locks);
  });

  it('has exactly one registered variant, which the header explains', () => {
    // The hinge is the other lower-body family; `hinge.test.ts` holds its own.
    const legs = EXERCISES.filter((exercise) => exercise.category === 'legs');
    expect(legs.map((exercise) => exercise.id)).toEqual(['air_squat', 'dumbbell_romanian_deadlift']);
    expect(legs.filter((exercise) => !exercise.rootPivot).map((exercise) => exercise.id)).toEqual(['air_squat']);
  });
});
