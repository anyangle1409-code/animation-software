import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { toDeg } from '../core/math';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { generateClip, phaseBoundaries } from './generate';
import { closesLoop, sampleClip } from './clip';
import { resolveFrame } from './pipeline';
import { validateClip } from './validate';
import { ease } from './easing';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);
const clip = generateClip(skeleton, bicepCurl);

describe('clip generation', () => {
  it('lays keyframes on the tempo', () => {
    expect(clip.duration).toBeCloseTo(5.5, 6);
    expect(clip.keyframes.map((frame) => frame.time)).toEqual([0, 2, 3, 5, 5.5]);
    expect(clip.name).toBe('bicep_curl');
  });

  it('closes the loop exactly', () => {
    expect(closesLoop(clip)).toBe(true);
    const start = sampleClip(clip, 0);
    const end = sampleClip(clip, clip.duration);
    expect(end.pose.rotations.forearm_l?.x).toBeCloseTo(start.pose.rotations.forearm_l!.x, 9);
    // And wrapping past the end lands back at the beginning.
    const wrapped = sampleClip(clip, clip.duration + 0.001);
    expect(wrapped.pose.rotations.forearm_l?.x).toBeCloseTo(start.pose.rotations.forearm_l!.x, 4);
  });

  it('is deterministic', () => {
    const again = generateClip(skeleton, bicepCurl);
    for (let time = 0; time <= clip.duration; time += 0.25) {
      expect(sampleClip(again, time).pose.rotations.forearm_l?.x).toBeCloseTo(
        sampleClip(clip, time).pose.rotations.forearm_l!.x,
        12,
      );
    }
  });

  it('holds the pose through pause phases', () => {
    const squeeze = sampleClip(clip, 2.5).pose.rotations.forearm_l?.x ?? 0;
    const peak = sampleClip(clip, 2).pose.rotations.forearm_l?.x ?? 0;
    expect(toDeg(squeeze)).toBeCloseTo(toDeg(peak), 6);
  });

  it('curls through the authored range', () => {
    const bottom = toDeg(sampleClip(clip, 0).pose.rotations.forearm_l?.x ?? 0);
    const top = toDeg(sampleClip(clip, 2).pose.rotations.forearm_l?.x ?? 0);
    expect(bottom).toBeCloseTo(6, 3);
    expect(top).toBeCloseTo(138, 3);
  });

  it('names phases across the timeline', () => {
    expect(phaseBoundaries(bicepCurl).map((entry) => [entry.phase.id, entry.start, entry.end])).toEqual([
      ['concentric', 0, 2],
      ['squeeze', 2, 3],
      ['eccentric', 3, 5],
      ['reset', 5, 5.5],
    ]);
  });
});

describe('grip', () => {
  const pose = sampleClip(clip, 0).pose;

  it('closes both hands by the same amount', () => {
    // Finger flexion is a handed axis, so the two hands take opposite signs.
    // Sending both the same sign silently opens the right hand: the limits
    // clamp the extension away and the fingers end up flat.
    const evaluated = new PoseEvaluation(skeleton).apply(pose);
    const reach = (side: 'l' | 'r') =>
      evaluated
        .head(`middle_01_${side}`, new Vector3())
        .distanceTo(evaluated.tail(`middle_03_${side}`, new Vector3()));

    expect(reach('r')).toBeCloseTo(reach('l'), 6);
    // A closed hand is much shorter than an open one: 9.5 cm of finger folds
    // to a little over half that.
    expect(reach('l')).toBeLessThan(0.07);
  });

  it('mirrors every finger joint rather than clamping one hand flat', () => {
    for (const finger of ['thumb', 'index', 'middle', 'ring', 'pinky'] as const) {
      for (const segment of ['01', '02', '03'] as const) {
        const left = pose.rotations[`${finger}_${segment}_l`];
        const right = pose.rotations[`${finger}_${segment}_r`];
        expect(right?.z, `${finger}_${segment}`).toBeCloseTo(-(left?.z ?? 0), 9);
      }
    }
  });
});

describe('resistance-training easing', () => {
  it('starts and ends a lift at rest rather than at full speed', () => {
    const delta = 1e-4;
    expect(ease('lift', delta) / delta).toBeLessThan(0.05);
    expect((1 - ease('lift', 1 - delta)) / delta).toBeLessThan(0.05);
    // Fastest in the middle, like a real repetition.
    expect(ease('lift', 0.5)).toBeCloseTo(0.5, 6);
    expect(ease('lift', 0.6) - ease('lift', 0.5)).toBeGreaterThan(ease('lift', 0.1) - ease('lift', 0));
  });

  it('holds still through a hold phase', () => {
    expect(ease('hold', 0.5)).toBe(0);
  });
});

describe('resolved frames', () => {
  it('keeps the feet planted for the whole repetition', () => {
    const positions: Vector3[] = [];
    for (let time = 0; time <= clip.duration; time += 0.1) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      positions.push(evaluation.head('foot_l', new Vector3()));
    }
    const first = positions[0];
    for (const position of positions) {
      expect(position.distanceTo(first)).toBeLessThan(0.012);
    }
  });

  it('holds each dumbbell rigidly in its hand', () => {
    for (let time = 0; time <= clip.duration; time += 0.25) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      const dumbbell = frame.equipment.get('dumbbell_l');
      expect(dumbbell).toBeDefined();
      const gripInHand = evaluation.localToWorld('hand_l', { x: 0, y: 0.045, z: 0 }, new Vector3());
      expect(dumbbell!.position.distanceTo(gripInHand)).toBeLessThan(1e-6);
    }
  });

  it('moves both dumbbells identically', () => {
    for (let time = 0; time <= clip.duration; time += 0.25) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      const left = frame.equipment.get('dumbbell_l')!.position;
      const right = frame.equipment.get('dumbbell_r')!.position;
      expect(right.x).toBeCloseTo(-left.x, 6);
      expect(right.y).toBeCloseTo(left.y, 6);
      expect(right.z).toBeCloseTo(left.z, 6);
    }
  });
});

describe('technique validation', () => {
  const validation = validateClip(skeleton, evaluation, bicepCurl, clip);

  it('passes the exercise’s own technique rules', () => {
    expect(validation.violations.map((violation) => violation.label)).toEqual([]);
  });

  it('reaches every IK target', () => {
    expect(validation.unreachable).toEqual([]);
  });

  it('reports a loop that closes', () => {
    expect(validation.loopClosed).toBe(true);
  });

  it('catches bad form when the definition is broken', () => {
    const swinging = {
      ...bicepCurl,
      peakPose: {
        ...bicepCurl.peakPose,
        joints: { ...bicepCurl.peakPose.joints, spine_01: { x: 22 }, spine_02: { x: 18 } },
      },
    };
    const badClip = generateClip(skeleton, swinging);
    const result = validateClip(skeleton, evaluation, swinging, badClip);
    const labels = result.violations.map((violation) => violation.ruleId);
    expect(labels).toContain('torso_upright');
    expect(labels).toContain('no_swing');
  });
});
