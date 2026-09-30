import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { retargetedCharacterSource } from '../character/retargetSource';
import { sampleClip } from '../animation/clip';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { IK_CHAINS } from '../ik/chains';
import { airSquat } from '../exercises/definitions/airSquat';
import { EXERCISES } from '../exercises/library';
import { HGPT_CANONICAL_V4_ORIGINAL_BONES } from './canonicalV4Original';
import { HUMANOID_BONES } from './humanoid';
import { PoseEvaluation, Skeleton } from './skeleton';
import { hgRigifyFixture } from '../test/rigifyGlbFixture';
import { reviewExercise } from '../editor/review';

const v3 = new Skeleton(HUMANOID_BONES);
const v4 = new Skeleton(HGPT_CANONICAL_V4_ORIGINAL_BONES);

const finitePose = (pose: ReturnType<typeof generateClip>['keyframes'][number]['pose']): boolean => {
  for (const rotation of Object.values(pose.rotations)) {
    if (!rotation) continue;
    if (![rotation.x, rotation.y, rotation.z].every(Number.isFinite)) return false;
  }
  if (![pose.rootPosition.x, pose.rootPosition.y, pose.rootPosition.z].every(Number.isFinite)) {
    return false;
  }
  if (![pose.rootRotation.x, pose.rootRotation.y, pose.rootRotation.z].every(Number.isFinite)) {
    return false;
  }
  return true;
};

describe('canonical v4 ORIGINAL shadow runtime compatibility', () => {
  it('keeps the complete v3 bone-name and parent architecture', () => {
    expect(v4.names).toEqual(v3.names);
    for (const name of v3.names) {
      expect(v4.bone(name).parent, name).toBe(v3.bone(name).parent);
    }
  });

  it('generates every exercise with unchanged clip structure and finite poses', () => {
    for (const exercise of EXERCISES) {
      const current = generateClip(v3, exercise);
      const shadow = generateClip(v4, exercise);

      expect(shadow.duration, exercise.id).toBe(current.duration);
      expect(shadow.fps, exercise.id).toBe(current.fps);
      expect(shadow.loop, exercise.id).toBe(current.loop);
      expect(shadow.keyframes.length, exercise.id).toBe(current.keyframes.length);
      expect(shadow.keyframes.map(frame => frame.marker), exercise.id)
        .toEqual(current.keyframes.map(frame => frame.marker));
      expect(shadow.keyframes.map(frame => frame.phaseId), exercise.id)
        .toEqual(current.keyframes.map(frame => frame.phaseId));
      expect(shadow.equipment, exercise.id).toEqual(current.equipment);
      expect(shadow.hands, exercise.id).toEqual(current.hands);
      expect(shadow.locks, exercise.id).toEqual(current.locks);

      for (const frame of shadow.keyframes) {
        expect(finitePose(frame.pose), `${exercise.id} @ ${frame.time}s`).toBe(true);
        for (const name of Object.keys(frame.pose.rotations)) {
          expect(v4.has(name), `${exercise.id}: unknown v4 pose bone ${name}`).toBe(true);
        }
      }
    }
  }, 60_000);

  it('resolves full v4 frames through IK, locks, contacts and equipment with finite output', () => {
    const fractions = [0, 0.13, 0.27, 0.43, 0.61, 0.79, 0.97];

    for (const exercise of EXERCISES) {
      const clip = generateClip(v4, exercise);
      const evaluation = new PoseEvaluation(v4);
      const anchors = lockAnchors(
        evaluation,
        sampleClip(clip, 0).pose,
        clip.locks,
      );

      for (const fraction of fractions) {
        const time = clip.duration * fraction;
        const frame = resolveFrame(v4, evaluation, clip, time, { anchors });

        expect(finitePose(frame.pose), `${exercise.id} @ ${fraction}: pose`).toBe(true);

        for (const result of frame.ikResults) {
          expect(IK_CHAINS[result.chain], `${exercise.id} @ ${fraction}: ${result.chain}`)
            .toBeDefined();
          expect(Number.isFinite(result.error), `${exercise.id} @ ${fraction}: IK error`)
            .toBe(true);
          expect(typeof result.reached).toBe('boolean');
          expect(typeof result.overExtended).toBe('boolean');
          if (result.reached) {
            expect(result.error, `${exercise.id} @ ${fraction}: reached IK residual`)
              .toBeLessThan(0.01);
          }
        }

        for (const contact of frame.contacts) {
          expect(IK_CHAINS[contact.chain], `${exercise.id} @ ${fraction}: contact chain`)
            .toBeDefined();
          expect(
            [contact.target.x, contact.target.y, contact.target.z].every(Number.isFinite),
            `${exercise.id} @ ${fraction}: contact target`,
          ).toBe(true);
          if (contact.aim) {
            expect(
              [contact.aim.direction.x, contact.aim.direction.y, contact.aim.direction.z]
                .every(Number.isFinite),
              `${exercise.id} @ ${fraction}: contact aim`,
            ).toBe(true);
            if (contact.aim.forward) {
              expect(
                [contact.aim.forward.x, contact.aim.forward.y, contact.aim.forward.z]
                  .every(Number.isFinite),
                `${exercise.id} @ ${fraction}: contact forward`,
              ).toBe(true);
            }
          }
          if (contact.lift !== undefined) {
            expect(Number.isFinite(contact.lift)).toBe(true);
            expect(contact.lift).toBeGreaterThanOrEqual(0);
          }
        }

        for (const [id, equipment] of frame.equipment) {
          expect(
            [equipment.position.x, equipment.position.y, equipment.position.z]
              .every(Number.isFinite),
            `${exercise.id} @ ${fraction}: equipment ${id} position`,
          ).toBe(true);
          expect(
            [equipment.quaternion.x, equipment.quaternion.y, equipment.quaternion.z, equipment.quaternion.w]
              .every(Number.isFinite),
            `${exercise.id} @ ${fraction}: equipment ${id} quaternion`,
          ).toBe(true);
          expect(
            Array.from(equipment.matrix.elements).every(Number.isFinite),
            `${exercise.id} @ ${fraction}: equipment ${id} matrix`,
          ).toBe(true);
          if (equipment.scale) {
            expect(
              [equipment.scale.x, equipment.scale.y, equipment.scale.z].every(Number.isFinite),
              `${exercise.id} @ ${fraction}: equipment ${id} scale`,
            ).toBe(true);
          }
        }

        evaluation.apply(frame.pose);
        for (const bone of v4.bones) {
          const head = evaluation.head(bone.name);
          const tail = evaluation.tail(bone.name);
          expect(
            [head.x, head.y, head.z, tail.x, tail.y, tail.z].every(Number.isFinite),
            `${exercise.id} @ ${fraction}: ${bone.name}`,
          ).toBe(true);
        }
      }
    }
  }, 90_000);

  it('scales a preserved GLB to the height of the supplied skeleton', async () => {
    const fixture = hgRigifyFixture();
    const currentSource = retargetedCharacterSource({
      id: 'v3-shadow-scale',
      label: 'v3 shadow scale',
      data: fixture.data,
    });
    const shadowSource = retargetedCharacterSource({
      id: 'v4-shadow-scale',
      label: 'v4 shadow scale',
      data: fixture.data,
    });

    const current = await currentSource.build(v3);
    const shadow = await shadowSource.build(v4);
    try {
      const sourceHeight = currentSource.lastReport!.height;
      expect(sourceHeight).toBeGreaterThan(0);
      expect(shadowSource.lastReport!.height).toBeCloseTo(sourceHeight, 9);
      expect(currentSource.lastReport!.scale).toBeCloseTo(1.75 / sourceHeight, 9);
      expect(shadowSource.lastReport!.scale).toBeCloseTo(1.82 / sourceHeight, 9);
      expect(shadowSource.lastReport!.scale / currentSource.lastReport!.scale)
        .toBeCloseTo(1.82 / 1.75, 9);
    } finally {
      current.dispose();
      shadow.dispose();
    }
  }, 30_000);

  it('does not introduce new automated review-gate failures on v4', () => {
    const regressions: string[] = [];

    for (const exercise of EXERCISES) {
      const currentClip = generateClip(v3, exercise);
      const shadowClip = generateClip(v4, exercise);
      const current = reviewExercise(v3, exercise, currentClip, 3);
      const shadow = reviewExercise(v4, exercise, shadowClip, 3);
      const shadowById = new Map(shadow.gates.map(gate => [gate.id, gate]));

      for (const gate of current.gates) {
        if (!gate.passed) continue;
        const candidate = shadowById.get(gate.id);
        if (!candidate?.passed) {
          regressions.push(
            `${exercise.id}/${gate.id}: v3 PASS -> v4 FAIL (${candidate?.detail ?? 'missing gate'})`,
          );
        }
      }
    }

    expect(regressions, regressions.join('\n')).toEqual([]);
  }, 90_000);

  it('uses each skeleton own hip width and leg span for generated stance', () => {
    const current = generateClip(v3, airSquat);
    const shadow = generateClip(v4, airSquat);

    const v3HalfHip = Math.abs(v3.bone('thigh_l').restHead.x);
    const v3LegSpan = Math.abs(
      v3.bone('thigh_l').restHead.y - v3.bone('shin_l').restTail.y,
    );
    const v4HalfHip = Math.abs(v4.bone('thigh_l').restHead.x);
    const v4LegSpan = Math.abs(
      v4.bone('thigh_l').restHead.y - v4.bone('shin_l').restTail.y,
    );
    const halfStance = airSquat.feet.width / 2;

    const expectedV3 = -Math.atan2(halfStance - v3HalfHip, v3LegSpan);
    const expectedV4 = -Math.atan2(halfStance - v4HalfHip, v4LegSpan);

    expect(v3HalfHip).toBeCloseTo(0.09, 12);
    expect(v3LegSpan).toBeCloseTo(0.84, 12);
    expect(v4HalfHip).toBeCloseTo(0.092, 12);
    expect(v4LegSpan).toBeCloseTo(0.875, 12);

    expect(current.keyframes[0].pose.rotations.thigh_l?.z).toBeCloseTo(expectedV3, 12);
    expect(shadow.keyframes[0].pose.rotations.thigh_l?.z).toBeCloseTo(expectedV4, 12);
    expect(expectedV4).not.toBeCloseTo(expectedV3, 6);
  });
});
