import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { SHOULDER_SETBACK, SHOULDER_WIDENING } from '../rig/humanoid';
import { buildBodyGeometry } from '../body/mesh';
import { generateClip } from '../animation/generate';
import { validateClip } from '../animation/validate';
import { resolveFrame } from '../animation/pipeline';
import { sampleClip } from '../animation/clip';
import { lockAnchors } from '../constraints/locks';
import { EXERCISES } from '../exercises/library';
import type { BoneName } from './boneNames';

/**
 * The guard on shared changes.
 *
 * The canonical rig is shared by every exercise, the procedural body, the muscle
 * model and the retargeter, so a correction made for one of them lands on all of
 * them. That is how it should be — but it means a rig edit needs checking
 * against the whole library, not against the exercise that motivated it.
 *
 * This file exists because that check was missing. Correcting the clavicle's
 * rest angle moved the arm chain 35 mm posterior, which was right for the
 * shoulder it was aimed at and silently broke the push-up's reach, the arm's
 * registration with the baked surface, the ecorche sculpt and a deltoid belly —
 * eight failures that landed in the suite as a diff rather than as a report.
 *
 * Two things are asserted, and neither is a duplicate of a per-module test:
 *
 *   1. Everything the rig moved, moved together. The bone positions are authored
 *      as literals so the accepted rig keeps the values it was reviewed with,
 *      and the constants that drive the surface, the equipment sockets and the
 *      muscle anchors are tied back to those literals here.
 *
 *   2. Every exercise in the library still passes its own contract, reported per
 *      exercise with the rule and the measured value, so a shared change says
 *      what it broke instead of leaving it to be bisected.
 */
const rig = canonicalSkeleton;
const mm = (metres: number) => `${(metres * 1000).toFixed(2)} mm`;

describe('shared-rig regression', () => {
  describe('the arm chain and the surfaces built against it', () => {
    const arm: BoneName[] = ['clavicle_l', 'upperarm_l', 'forearm_l', 'hand_l'];

    it('carries the shoulder setback through every bone of the chain', () => {
      // The clavicle's head is the sternoclavicular joint and does not move; its
      // tail is the acromion, and everything outboard of it follows.
      expect(rig.bone('clavicle_l').definition.head.z).toBeCloseTo(0.012, 6);
      for (const bone of arm) {
        const { head, tail } = rig.bone(bone).definition;
        if (bone !== 'clavicle_l') {
          expect(head.z, `${bone}.head.z`).toBeCloseTo(-SHOULDER_SETBACK, 6);
        }
        expect(tail.z, `${bone}.tail.z`).toBeCloseTo(-SHOULDER_SETBACK, 6);
      }
    });

    it('carries it into the knuckles, which are authored in world space', () => {
      // The five metacarpal heads are absolute rest positions rather than
      // offsets from the hand, so they do not follow it automatically. Leaving
      // them behind tilts the palm axis, which is what the grip solves against.
      const knuckles: BoneName[] = ['thumb_01_l', 'index_01_l', 'middle_01_l', 'ring_01_l', 'pinky_01_l'];
      const spread = knuckles.map((bone) => rig.bone(bone).definition.head.z + SHOULDER_SETBACK);
      // The fingers fan front-to-back across the palm, so they do not share one
      // z — what has to hold is that the fan is still centred on the hand.
      const mean = spread.reduce((total, value) => total + value, 0) / spread.length;
      expect(Math.abs(mean), `knuckle fan centre, ${mm(mean)} off the hand`).toBeLessThan(0.02);
    });

    it('keeps the baked surface registered with the bone inside it', () => {
      // The one that was missed. The procedural body is a baked asset: its
      // vertices are absolute, so a bone that moves inside it leaves the two out
      // of register, and everything that reads the pair — skin strain, the
      // muscle map, the ecorche sculpt — degrades without any of them naming the
      // cause. `realignArmSurface` shifts the surface to follow; this measures
      // that it worked, in both axes at once.
      const geometry = buildBodyGeometry(rig).geometry;
      const position = geometry.getAttribute('position');
      const skinIndex = geometry.getAttribute('skinIndex');
      const skinWeight = geometry.getAttribute('skinWeight');
      const slot = rig.bones.findIndex((bone) => bone.name === 'upperarm_l');
      expect(slot).toBeGreaterThanOrEqual(0);

      let count = 0;
      const centre = new Vector3();
      for (let vertex = 0; vertex < position.count; vertex += 1) {
        let owned = 0;
        for (let lane = 0; lane < 4; lane += 1) {
          if (skinIndex.getComponent(vertex, lane) === slot) owned += skinWeight.getComponent(vertex, lane);
        }
        // Only the arm's own tube, not the blend into the shoulder.
        if (owned < 0.9) continue;
        count += 1;
        centre.x += position.getX(vertex);
        centre.z += position.getZ(vertex);
      }
      expect(count, 'upper-arm surface vertices').toBeGreaterThan(100);
      centre.divideScalar(count);

      const joint = new PoseEvaluation(rig).apply(restPose()).head('upperarm_l', new Vector3());
      // The authored profile puts the arm's surface a few millimetres in front
      // of its bone; 20 mm is comfortably inside that and nowhere near the
      // 38.7 mm the surface sat behind when the shift was missing.
      expect(Math.abs(centre.z - joint.z), `arm surface is ${mm(centre.z - joint.z)} off its bone in z`)
        .toBeLessThan(0.02);
      expect(Math.abs(centre.x - joint.x), `arm surface is ${mm(centre.x - joint.x)} off its bone in x`)
        .toBeLessThan(0.02);
      // Both constants are load-bearing for that registration, so neither may be
      // quietly zeroed to make the check pass.
      expect(SHOULDER_SETBACK).toBeGreaterThan(0.01);
      expect(SHOULDER_WIDENING).toBeGreaterThan(0.01);
    });
  });

  describe('every exercise still meets its own contract', () => {
    const results = EXERCISES.map((exercise) => {
      const evaluation = new PoseEvaluation(rig);
      const clip = generateClip(rig, exercise);
      const validation = validateClip(rig, evaluation, exercise, clip, 20);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

      let drift = 0;
      let driftAt = '';
      const start = new Map<string, Vector3>();
      for (let step = 0; step <= 40; step += 1) {
        const time = (step / 40) * clip.duration;
        const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
        evaluation.apply(frame.pose);
        for (const lock of clip.locks) {
          const side = lock.chain.endsWith('_l') ? 'l' : 'r';
          const bone = (lock.chain.startsWith('arm') ? `hand_${side}` : `foot_${side}`) as BoneName;
          const position = evaluation.head(bone, new Vector3());
          const first = start.get(lock.id);
          if (!first) start.set(lock.id, position.clone());
          else if (position.distanceTo(first) > drift) {
            drift = position.distanceTo(first);
            driftAt = `${lock.id} at ${time.toFixed(2)}s`;
          }
        }
      }
      return { exercise, validation, drift, driftAt };
    });

    it('reports the whole library, exercise by exercise', () => {
      const lines = results.map(({ exercise, validation, drift, driftAt }) => {
        const worstIK = validation.unreachable.reduce((most, one) => Math.max(most, one.error), 0);
        const failures = [
          validation.violations.length ? `technique ${validation.violations.length}` : '',
          validation.unreachable.length ? `unreachable ${validation.unreachable.length} (worst ${mm(worstIK)})` : '',
          validation.loopClosed ? '' : 'loop open',
          drift > 0.005 ? `contact drift ${mm(drift)} ${driftAt}` : '',
        ].filter(Boolean);
        const detail = validation.violations
          .map((violation) => `\n        ${violation.ruleId}: ${violation.message}`)
          .join('');
        return `  ${failures.length ? 'FAIL' : 'PASS'}  ${exercise.name.padEnd(24)} ` +
          `${failures.join(', ') || `contact drift ${mm(drift)}`}${detail}`;
      });
      // Printed whichever way it goes: a shared change that costs an exercise
      // something should say so in one place, in the plan's own report shape.
      console.log(`\nSHARED-RIG REGRESSION — ${EXERCISES.length} exercises\n${lines.join('\n')}`);
      expect(lines.filter((line) => line.startsWith('  FAIL'))).toEqual([]);
    });

    it.each(results.map((result) => [result.exercise.name, result] as const))(
      '%s',
      (_name, { validation, drift, driftAt }) => {
        expect(validation.violations.map((one) => `${one.ruleId}: ${one.message}`)).toEqual([]);
        expect(validation.unreachable).toEqual([]);
        expect(validation.loopClosed).toBe(true);
        expect(drift, driftAt || 'locked contacts').toBeLessThan(0.005);
      },
    );
  });
});
