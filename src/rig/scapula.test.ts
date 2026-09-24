import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from './skeleton';
import { skeletonV1 } from './earlierRigs';
import { restPose } from './pose';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { validateClip } from '../animation/validate';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { EXERCISES } from '../exercises/library';
import type { BoneName } from './boneNames';
import { measureJointPath } from '../editor/motionDiagnostics';
import { MUSCLES } from '../muscles/model';
import { shoulderPress } from '../exercises/definitions/shoulderPress';

/**
 * The scapulae are structural: they sit between the clavicles and the upper
 * arms and nothing moves them. That is a strong claim about a change to the
 * hierarchy every exercise runs through, so it is held here against the rig
 * as it was — `skeletonV1`, derived from the same definitions, which
 * reproduces the pre-scapula baseline bit for bit.
 *
 * Equality is to 1e-12, not bitwise. The extra bone adds one quaternion product
 * to every arm chain, and measured over the seven exercises that moves the last
 * bits of about a third of all values, by at most 2.7e-15.
 */
const rig = canonicalSkeleton;
const legacy = skeletonV1();
const NUMERIC = 1e-12;

describe('the scapulae', () => {
  it('hang from the clavicles and carry the arms, on both sides', () => {
    // 55 when they were added; the metacarpals since make 63 (palm.test.ts).
    expect(rig.bones.filter((bone) => bone.name.startsWith('scapula_'))).toHaveLength(2);
    for (const side of ['l', 'r'] as const) {
      const scapula = rig.bone(`scapula_${side}`);
      expect(scapula.parent).toBe(`clavicle_${side}`);
      expect(rig.bone(`upperarm_${side}`).parent).toBe(`scapula_${side}`);
      // Hinged at the acromioclavicular joint: the clavicle's tail, which is
      // also where the upper arm's head is.
      expect(scapula.restHead.distanceTo(rig.bone(`clavicle_${side}`).restTail)).toBeLessThan(1e-12);
      expect(scapula.restHead.distanceTo(rig.bone(`upperarm_${side}`).restHead)).toBeLessThan(1e-12);
    }
    // The inferior angle, 2 cm under the measured back skin, mirrored.
    expect(rig.bone('scapula_l').restTail.toArray()).toEqual([-0.09, 1.25, -0.15]);
    expect(rig.bone('scapula_r').restTail.toArray()).toEqual([0.09, 1.25, -0.15]);
  });

  it('leave every other bone exactly where the 53-bone rig had it', () => {
    for (const bone of legacy.bones) {
      const now = rig.bone(bone.name);
      expect(now.restHead.distanceTo(bone.restHead), bone.name).toBeLessThan(NUMERIC);
      expect(now.restTail.distanceTo(bone.restTail), bone.name).toBeLessThan(NUMERIC);
      expect(1 - Math.abs(now.restWorldQuaternion.dot(bone.restWorldQuaternion)), bone.name).toBeLessThan(NUMERIC);
      // The thumb base has since gained an axis and a wider sweep; palm.test.ts
      // holds its old ranges inside the new ones.
      if (/^thumb_01_/.test(bone.name)) continue;
      expect(now.definition.limits, bone.name).toEqual(bone.definition.limits);
    }
    // The shoulder's anatomical parent joint is still the clavicle's.
    expect(rig.jointParent('upperarm_l')).toBe('clavicle_l');
    expect(rig.jointParent('scapula_l')).toBe('clavicle_l');
    for (const bone of rig.bones) {
      if (/^upperarm_/.test(bone.name)) continue;
      expect(rig.jointParent(bone.name), bone.name).toBe(bone.parent);
    }
    // The upper arm is the only bone hinged exactly where its parent is.
    expect(rig.bones.filter((bone) => bone.parent && rig.jointParent(bone.name) !== bone.parent).map((bone) => bone.name))
      .toEqual(['upperarm_l', 'upperarm_r']);
  });

  it('turn about the axes their limits name', () => {
    // Measured, left side, 10° each: which way the inferior angle and the
    // superior angle (near the medial border) actually go.
    const evaluation = new PoseEvaluation(rig).apply(restPose());
    const superior = new Vector3(-0.08, 1.4, -0.15);
    const superiorLocal = evaluation.worldToLocal('scapula_l', superior.clone(), new Vector3());
    const inferior = evaluation.tail('scapula_l', new Vector3());
    const moved = (axis: 'x' | 'y' | 'z', degrees: number) => {
      const pose = restPose();
      pose.rotations.scapula_l = { x: 0, y: 0, z: 0, [axis]: (degrees * Math.PI) / 180 };
      evaluation.apply(pose);
      return {
        inferior: evaluation.tail('scapula_l', new Vector3()).sub(inferior),
        superior: evaluation.localToWorld('scapula_l', superiorLocal).sub(superior),
      };
    };
    // Upward rotation (-z on the left) swings the inferior angle out, away
    // from the spine. Pivoting at the acromion it also drops; the rise real
    // upward rotation shows comes from the clavicle elevating above it.
    const up = moved('z', -10);
    expect(up.inferior.x).toBeLessThan(-0.03);
    expect(rig.bone('scapula_l').definition.limits.z!.negative).toBe('Upward rotation');
    // Posterior tilt (+x) drives the inferior angle forward, into the ribs.
    expect(moved('x', 10).inferior.z).toBeGreaterThan(0.03);
    expect(rig.bone('scapula_l').definition.limits.x!.positive).toBe('Posterior tilt');
    // External rotation (+y) presses the medial border in against the ribs.
    expect(moved('y', 10).superior.z).toBeGreaterThan(0.01);
    expect(rig.bone('scapula_l').definition.limits.y!.positive).toBe('External rotation');
    // The right side is the mirror: its upward rotation is +z.
    expect(rig.bone('scapula_r').definition.limits.z!.positive).toBe('Upward rotation');
  });
});

describe('every exercise, with the scapulae at rest', () => {
  it.each(EXERCISES.map((exercise) => [exercise.id, exercise] as const))(
    '%s moves exactly as it did on the 53-bone rig',
    (_id, exercise) => {
      const now = { evaluation: new PoseEvaluation(rig), clip: generateClip(rig, exercise) };
      const then = { evaluation: new PoseEvaluation(legacy), clip: generateClip(legacy, exercise) };
      const anchorsNow = lockAnchors(now.evaluation, sampleClip(now.clip, 0).pose, now.clip.locks);
      const anchorsThen = lockAnchors(then.evaluation, sampleClip(then.clip, 0).pose, then.clip.locks);
      let worstJoint = 0;
      let worstEquipment = 0;

      for (let step = 0; step <= 60; step += 1) {
        const time = (step / 60) * now.clip.duration;
        const a = resolveFrame(rig, now.evaluation, now.clip, time, { anchors: anchorsNow });
        const b = resolveFrame(legacy, then.evaluation, then.clip, time, { anchors: anchorsThen });
        now.evaluation.apply(a.pose);
        then.evaluation.apply(b.pose);

        // Nothing drives the scapulae: no rhythm, no IK, no authored target.
        for (const side of ['l', 'r'] as const) {
          const rotation = a.pose.rotations[`scapula_${side}`];
          expect(Math.max(Math.abs(rotation?.x ?? 0), Math.abs(rotation?.y ?? 0), Math.abs(rotation?.z ?? 0))).toBe(0);
        }
        for (const bone of legacy.bones) {
          const name = bone.name as BoneName;
          const here = now.evaluation.matrix(name).elements;
          const there = then.evaluation.matrix(name).elements;
          for (let index = 0; index < 16; index += 1) {
            worstJoint = Math.max(worstJoint, Math.abs(here[index] - there[index]));
          }
        }
        for (const [id, placed] of a.equipment) {
          const was = b.equipment.get(id)!;
          worstEquipment = Math.max(
            worstEquipment,
            placed.position.distanceTo(was.position),
            1 - Math.abs(placed.quaternion.dot(was.quaternion)),
          );
        }
        expect(a.contacts.length).toBe(b.contacts.length);
      }
      expect(worstJoint).toBeLessThan(NUMERIC);
      expect(worstEquipment).toBeLessThan(NUMERIC);

      // And the technique rules read the same motion the same way.
      const rules = (skeleton: typeof rig, clip: typeof now.clip) =>
        validateClip(skeleton, new PoseEvaluation(skeleton), exercise, clip, 20).violations.map(
          (violation) => violation.ruleId,
        );
      expect(rules(rig, now.clip)).toEqual(rules(legacy, then.clip));
    },
    // Two rigs, every frame: the calf raises' ball-of-foot solve runs past the
    // 5 s default on a slower machine.
    30_000,
  );
});

describe('what reads a bone\'s parent joint', () => {
  it('still measures the shoulder against the clavicle, not the scapula it shares a point with', () => {
    // Against the scapula the shoulder would be measured against itself and
    // never move; against the clavicle it moves as it always did.
    const now = measureJointPath(generateClip(rig, shoulderPress), rig, 'upperarm_l')!;
    const then = measureJointPath(generateClip(legacy, shoulderPress), legacy, 'upperarm_l')!;
    expect(now.parent).toBe('clavicle_l');
    expect(then.parent).toBe('clavicle_l');
    expect(Math.abs(now.maxDriftMetres - then.maxDriftMetres)).toBeLessThan(NUMERIC);
    expect(Math.abs(now.pathLengthMetres - then.pathLengthMetres)).toBeLessThan(NUMERIC);
  });

  it('fits no muscle to a scapula, and keeps the clavicle for the upper arm\'s', () => {
    for (const muscle of MUSCLES) {
      expect([...muscle.fitBones].some((bone) => /^scapula_/.test(bone)), muscle.id).toBe(false);
      const onUpperArm = [muscle.origin, ...(muscle.via ?? []), muscle.insertion].find((attachment) =>
        /^upperarm_/.test(attachment.bone),
      );
      if (onUpperArm) expect(muscle.fitBones.has(`clavicle_${onUpperArm.bone.slice(-1)}`), muscle.id).toBe(true);
    }
  });
});
