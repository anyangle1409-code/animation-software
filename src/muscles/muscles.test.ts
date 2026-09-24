import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { EXERCISES, getExercise } from '../exercises/library';
import { skinDepth } from '../body/containment';
import { MUSCLES, createMuscleTransform, resolveMuscle } from './model';
import type { MuscleInstance } from './model';
import { ACTIVATION_STYLES, activationMap, activationOf } from './activation';

const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);
const transform = createMuscleTransform();
const curl = getExercise('dumbbell_bicep_curl');
const curlClip = generateClip(skeleton, curl);

/** Bottom, midpoint and top of a repetition of the curl. */
const CURL_TIMES = [0, curlClip.duration * 0.25, 2.5, curlClip.duration * 0.75];

/** Points on the belly's surface, for measuring it against the skin. */
function bellyPoints(muscle: MuscleInstance): Vector3[] {
  resolveMuscle(evaluation, muscle, transform);
  const points: Vector3[] = [];
  for (let i = 0; i <= 8; i += 1) {
    const phi = (i / 8) * Math.PI;
    for (let j = 0; j < 12; j += 1) {
      const theta = (j / 12) * Math.PI * 2;
      points.push(
        new Vector3(
          Math.sin(phi) * Math.cos(theta),
          Math.cos(phi),
          Math.sin(phi) * Math.sin(theta),
        )
          .multiply(transform.scale)
          .applyQuaternion(transform.quaternion)
          .add(transform.position),
      );
    }
  }
  return points;
}

describe('muscle overlay', () => {
  it('keeps every belly inside the skin through the curl', () => {
    for (const time of CURL_TIMES) {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);
      for (const muscle of MUSCLES) {
        let worst = -Infinity;
        for (const point of bellyPoints(muscle)) {
          worst = Math.max(worst, skinDepth(evaluation, point).depth);
        }
        // A belly that breaks the surface is the one thing the overlay must
        // never do: it reads as the muscle cutting through the body. The
        // measurement is against the profiles rather than the built mesh, so a
        // millimetre of slack keeps it honest without being brittle.
        expect(worst, `${muscle.id} at ${time.toFixed(2)}s`).toBeLessThan(0.001);
      }
    }
  });

  it('keeps every belly inside the skin in every other exercise too', () => {
    for (const exercise of EXERCISES) {
      const clip = generateClip(skeleton, exercise);
      for (const fraction of [0, 0.25, 0.5, 0.75]) {
        const frame = resolveFrame(skeleton, evaluation, clip, clip.duration * fraction);
        evaluation.apply(frame.pose);
        for (const muscle of MUSCLES) {
          let worst = -Infinity;
          for (const point of bellyPoints(muscle)) {
            worst = Math.max(worst, skinDepth(evaluation, point).depth);
          }
          expect(worst, `${muscle.id} in ${exercise.id}`).toBeLessThan(0.007);
        }
      }
    }
    // Every exercise in the library, so it grows with it.
  }, 60_000);

  it('keeps every belly against the body rather than floating inside it', () => {
    for (const time of CURL_TIMES) {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);
      for (const muscle of MUSCLES) {
        let closest = Infinity;
        for (const point of bellyPoints(muscle)) {
          closest = Math.min(closest, Math.abs(skinDepth(evaluation, point).depth));
        }
        // Somewhere on its surface, every belly comes within a few millimetres
        // of the skin. A muscle floating in the middle of the body reads as
        // detached from it.
        expect(closest, `${muscle.id} at ${time.toFixed(2)}s`).toBeLessThan(0.025);
      }
    }
  });

  it('holds each belly between its own origin and insertion', () => {
    for (const time of CURL_TIMES) {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);
      for (const muscle of MUSCLES) {
        const origin = evaluation.localToWorld(
          muscle.origin.bone,
          muscle.origin.offset,
          new Vector3(),
        );
        const insertion = evaluation.localToWorld(
          muscle.insertion.bone,
          muscle.insertion.offset,
          new Vector3(),
        );
        resolveMuscle(evaluation, muscle, transform);

        // The belly sits on the line between its attachments, and stops short
        // of both of them in tendon.
        expect(
          transform.position.distanceTo(origin.clone().add(insertion).multiplyScalar(0.5)),
          `${muscle.id} centre at ${time.toFixed(2)}s`,
        ).toBeLessThan(1e-6);

        const axis = new Vector3(0, 1, 0).applyQuaternion(transform.quaternion);
        const half = origin.distanceTo(insertion) / 2;
        for (const [end, sign] of [
          [insertion, 1],
          [origin, -1],
        ] as const) {
          const pole = transform.position.clone().addScaledVector(axis, sign * transform.scale.y);
          expect(pole.distanceTo(end), `${muscle.id} end at ${time.toFixed(2)}s`).toBeLessThan(
            half * 0.3 + 1e-6,
          );
        }
      }
    }
  });

  it('mirrors the left and right sides exactly', () => {
    const byGroup = new Map<string, MuscleInstance[]>();
    for (const muscle of MUSCLES) {
      if (!muscle.side) continue;
      const list = byGroup.get(muscle.group) ?? [];
      list.push(muscle);
      byGroup.set(muscle.group, list);
    }

    for (const time of CURL_TIMES) {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);
      for (const [group, pair] of byGroup) {
        expect(pair, group).toHaveLength(2);
        const left = pair.find((muscle) => muscle.side === 'l')!;
        const right = pair.find((muscle) => muscle.side === 'r')!;
        resolveMuscle(evaluation, left, transform);
        const leftCentre = transform.position.clone();
        const leftScale = transform.scale.clone();
        resolveMuscle(evaluation, right, transform);
        // The curl is a symmetrical exercise, so the two sides must land as
        // mirror images — including the fit that trims a belly to the skin.
        expect(transform.position.x, `${group} x at ${time.toFixed(2)}s`).toBeCloseTo(
          -leftCentre.x,
          6,
        );
        expect(transform.position.y).toBeCloseTo(leftCentre.y, 6);
        expect(transform.position.z).toBeCloseTo(leftCentre.z, 6);
        expect(transform.scale.x).toBeCloseTo(leftScale.x, 6);
        expect(transform.scale.y).toBeCloseTo(leftScale.y, 6);
      }
    }
  });
});

describe('the biceps through a curl', () => {
  const both = MUSCLES.filter((muscle) => muscle.group === 'biceps');

  it('has one belly on the front of each upper arm', () => {
    expect(both).toHaveLength(2);
    for (const time of CURL_TIMES) {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);

      for (const muscle of both) {
        const side = muscle.side!;
        resolveMuscle(evaluation, muscle, transform);
        const local = evaluation.worldToLocal(
          `upperarm_${side}`,
          transform.position.clone(),
          new Vector3(),
        );
        // In front of the humerus, on its own side, and along its length — not
        // behind it where the triceps belongs.
        expect(local.z, `biceps_${side} forward at ${time.toFixed(2)}s`).toBeGreaterThan(0);
        expect(local.y, `biceps_${side} along at ${time.toFixed(2)}s`).toBeGreaterThan(0.05);
        expect(local.y).toBeLessThan(skeleton.bone(`upperarm_${side}`).length + 0.06);
        expect(Math.hypot(local.x, local.z), `biceps_${side} radius`).toBeLessThan(0.05);
      }
    }
  });

  it('shortens and thickens as the elbow closes', () => {
    const sample = (time: number) => {
      const frame = resolveFrame(skeleton, evaluation, curlClip, time);
      evaluation.apply(frame.pose);
      resolveMuscle(evaluation, both[0], transform);
      return { stretch: transform.stretch, width: transform.scale.x, length: transform.scale.y };
    };

    const bottom = sample(0);
    const middle = sample(1);
    const top = sample(2.5);

    // The whole point of the overlay: the working muscle visibly contracts.
    expect(middle.stretch).toBeLessThan(bottom.stretch);
    expect(top.stretch).toBeLessThan(middle.stretch);
    expect(top.length).toBeLessThan(bottom.length * 0.88);
    expect(top.width).toBeGreaterThan(bottom.width);
  });

  it('is the only muscle the curl marks as primary', () => {
    const activation = activationMap(curl.muscles);
    expect(activationOf(activation, 'biceps')).toBe('primary');
    expect(activationOf(activation, 'forearm_flexors')).toBe('secondary');
    expect(activationOf(activation, 'deltoid_anterior')).toBe('secondary');
    expect(activationOf(activation, 'triceps')).toBe('inactive');
    expect(curl.muscles.primary).toEqual(['biceps']);
  });
});

describe('activation styling', () => {
  it('steps down in emphasis so the primary muscle carries the eye', () => {
    const { primary, secondary, stabiliser, inactive } = ACTIVATION_STYLES;
    expect(primary.emissive).toBeGreaterThan(secondary.emissive);
    expect(secondary.emissive).toBeGreaterThan(stabiliser.emissive);
    expect(stabiliser.emissive).toBeGreaterThanOrEqual(inactive.emissive);
    expect(primary.opacity).toBeGreaterThan(stabiliser.opacity);
    expect(stabiliser.opacity).toBeGreaterThan(inactive.opacity);
  });

  it('paints the primary muscle a clear red and steps away from it', () => {
    const channels = (colour: string) => {
      const value = Number.parseInt(colour.slice(1), 16);
      const [r, g, b] = [(value >> 16) & 255, (value >> 8) & 255, value & 255].map((c) => c / 255);
      const max = Math.max(r, g, b);
      const min = Math.min(r, g, b);
      return { r, g, b, saturation: max === 0 ? 0 : (max - min) / max };
    };

    const primary = channels(ACTIVATION_STYLES.primary.colour);
    const secondary = channels(ACTIVATION_STYLES.secondary.colour);
    const stabiliser = channels(ACTIVATION_STYLES.stabiliser.colour);

    // Primary is the reddest and most saturated; the stabilisers are close
    // enough to flesh tone that they do not compete with it.
    expect(primary.r).toBeGreaterThan(0.75);
    expect(primary.g).toBeLessThan(0.25);
    expect(primary.saturation).toBeGreaterThan(0.85);
    expect(secondary.g).toBeGreaterThan(primary.g);
    expect(secondary.saturation).toBeGreaterThan(0.6);
    expect(stabiliser.saturation).toBeLessThan(0.35);
  });
});
