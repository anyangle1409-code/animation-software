import { describe, expect, it } from 'vitest';
import { AnimationMixer, Object3D, Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from './skeleton';
import { skeletonV2 } from './earlierRigs';
import { restPose } from './pose';
import { METACARPAL_BONES } from './boneNames';
import type { BoneName } from './boneNames';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { validateClip } from '../animation/validate';
import { lockAnchors } from '../constraints/locks';
import { sampleClip } from '../animation/clip';
import { bakeClip } from '../export/clipBuilder';
import { buildSkinnedRig } from '../export/rigBuilder';
import { EXERCISES } from '../exercises/library';

/**
 * The palm: a metacarpal for each finger, and a thumb base that can oppose.
 *
 * Structural, like the scapulae — nothing in any exercise moves a metacarpal
 * or twists the thumb base yet — so the rig is held here against the 55-bone
 * rig it replaced (`skeletonV2`, which reproduces that version's recorded
 * baseline bit for bit), and against what the new joints were measured to do.
 */
const rig = canonicalSkeleton;
const earlier = skeletonV2();
const NUMERIC = 1e-12;
const R = Math.PI / 180;

describe('the palm bones', () => {
  it('give each finger a metacarpal between the hand and its knuckle, and the thumb none', () => {
    expect(rig.bones).toHaveLength(63);
    for (const side of ['l', 'r'] as const) {
      for (const finger of ['index', 'middle', 'ring', 'pinky'] as const) {
        const metacarpal = rig.bone(`metacarpal_${finger}_${side}`);
        expect(metacarpal.parent).toBe(`hand_${side}`);
        expect(rig.bone(`${finger}_01_${side}`).parent).toBe(`metacarpal_${finger}_${side}`);
        // The metacarpal ends at the knuckle, which stays where it was.
        expect(metacarpal.restTail.distanceTo(rig.bone(`${finger}_01_${side}`).restHead)).toBeLessThan(NUMERIC);
      }
      // The thumb's first segment is its metacarpal; its head is the CMC joint.
      expect(rig.bone(`thumb_01_${side}`).parent).toBe(`hand_${side}`);
    }
    // Twist stays a character deformation helper: no canonical twist bones.
    expect(rig.bones.filter((bone) => /twist|_001|\.001/i.test(bone.name))).toEqual([]);
  });

  it('put the bases on the carpus, converging, at anatomical metacarpal lengths', () => {
    const wrist = rig.bone('hand_l').restHead;
    const lengths = { index: 0.068, middle: 0.065, ring: 0.057, pinky: 0.053 };
    for (const [finger, length] of Object.entries(lengths)) {
      const bone = rig.bone(`metacarpal_${finger}_l` as BoneName);
      expect(bone.length).toBeCloseTo(length * (0.187 / 0.19), 9);
      // Distal to the wrist, proximal to the knuckle.
      expect(bone.restHead.y).toBeLessThan(wrist.y);
      expect(bone.restHead.y - bone.restTail.y).toBeGreaterThan(0.045);
    }
    const across = (name: string, end: 'restHead' | 'restTail') => rig.bone(name as BoneName)[end].z;
    const baseSpan = across('metacarpal_index_l', 'restHead') - across('metacarpal_pinky_l', 'restHead');
    const knuckleSpan = across('metacarpal_index_l', 'restTail') - across('metacarpal_pinky_l', 'restTail');
    expect(baseSpan / knuckleSpan).toBeCloseTo(0.5, 9);
    expect(baseSpan).toBeGreaterThan(0.028);
    expect(baseSpan).toBeLessThan(0.035);
  });

  it('leave every bone of the 55-bone rig where it was', () => {
    for (const bone of earlier.bones) {
      const now = rig.bone(bone.name);
      expect(now.restHead.distanceTo(bone.restHead), bone.name).toBeLessThan(NUMERIC);
      expect(now.restTail.distanceTo(bone.restTail), bone.name).toBeLessThan(NUMERIC);
      expect(1 - Math.abs(now.restWorldQuaternion.dot(bone.restWorldQuaternion)), bone.name).toBeLessThan(NUMERIC);
      if (/^thumb_01_/.test(bone.name)) continue;
      expect(now.definition.limits, bone.name).toEqual(bone.definition.limits);
    }
  });

  it('keep the thumb base\'s old ranges inside its new ones', () => {
    for (const side of ['l', 'r'] as const) {
      const now = rig.bone(`thumb_01_${side}`).definition.limits;
      const then = earlier.bone(`thumb_01_${side}`).definition.limits;
      for (const axis of ['x', 'z'] as const) {
        expect(now[axis]!.min, `${side} ${axis}`).toBeLessThanOrEqual(then[axis]!.min);
        expect(now[axis]!.max, `${side} ${axis}`).toBeGreaterThanOrEqual(then[axis]!.max);
      }
      expect(then.y).toBeNull();
      expect(now.y).not.toBeNull();
    }
  });

  it('turn about the axes their limits name', () => {
    const evaluation = new PoseEvaluation(rig);
    const padNormal = (bone: BoneName) => new Vector3(1, 0, 0).applyQuaternion(evaluation.quaternion(bone)).negate();
    const posed = (bone: BoneName, axis: 'x' | 'y' | 'z', degrees: number) => {
      const pose = restPose();
      pose.rotations[bone] = { x: 0, y: 0, z: 0, [axis]: degrees * R };
      return evaluation.apply(pose);
    };
    evaluation.apply(restPose());
    const knuckle = evaluation.tail('metacarpal_pinky_l', new Vector3());
    const palmar = padNormal('metacarpal_pinky_l');
    const ringKnuckle = evaluation.tail('metacarpal_ring_l', new Vector3());
    const thumbBase = evaluation.head('thumb_01_l', new Vector3());
    const towardsThumb = thumbBase.clone().sub(evaluation.head('pinky_01_l', new Vector3())).normalize();
    const pinkyPad = padNormal('pinky_01_l').dot(towardsThumb);
    const thumbTip = evaluation.tail('thumb_01_l', new Vector3());
    const pinkyKnuckle = evaluation.head('pinky_01_l', new Vector3());
    const towardsFingers = evaluation.head('middle_01_l', new Vector3()).sub(evaluation.tail('thumb_03_l', new Vector3())).normalize();
    const thumbPad = padNormal('thumb_01_l').dot(towardsFingers);

    // Metacarpal: +z flexes the knuckle palmward (cupping), +x spreads it
    // towards the thumb, +y turns the finger towards the thumb.
    expect(posed('metacarpal_pinky_l', 'z', 10).tail('metacarpal_pinky_l', new Vector3()).sub(knuckle).dot(palmar)).toBeGreaterThan(0.008);
    expect(posed('metacarpal_pinky_l', 'x', 10).tail('metacarpal_pinky_l', new Vector3()).sub(knuckle).dot(ringKnuckle.clone().sub(knuckle).normalize())).toBeGreaterThan(0.008);
    posed('metacarpal_pinky_l', 'y', 10);
    expect(padNormal('pinky_01_l').dot(towardsThumb)).toBeGreaterThan(pinkyPad);
    expect(rig.bone('metacarpal_pinky_l').definition.limits.z!.positive).toBe('Flexion');
    expect(rig.bone('metacarpal_pinky_l').definition.limits.y!.positive).toBe('Rotation towards thumb');

    // Thumb base: -x sweeps across the palm, -y turns the pad to the fingers.
    expect(posed('thumb_01_l', 'x', -20).tail('thumb_01_l', new Vector3()).distanceTo(pinkyKnuckle)).toBeLessThan(thumbTip.distanceTo(pinkyKnuckle) - 0.01);
    posed('thumb_01_l', 'y', -20);
    expect(padNormal('thumb_01_l').dot(towardsFingers)).toBeGreaterThan(thumbPad);
    const thumb = rig.bone('thumb_01_l').definition.limits;
    expect([thumb.x!.negative, thumb.y!.negative, thumb.z!.positive]).toEqual(['Flexion across the palm', 'Pronation', 'Palmar abduction']);
  });

  it('let the thumb pad meet every fingertip pad in true opposition, within the limits', () => {
    // Found by searching for the least excursion that brings the pads together
    // with the thumb metacarpal at least 30° out of the palm plane — the
    // posture of opposition, not the thumb swept flat across the palm.
    const poses: Record<string, Record<string, number>> = {
      index: { tx: -30, ty: -3.9, tz: 24.7, t2: 2.5, t3: -25, fs: 6, f1: 55.5, f2: 35.3, f3: 77.4, mx: 3, my: 3, mz: -3 },
      middle: { tx: -45.7, ty: -0.4, tz: 26.8, t2: 4.3, t3: -24.3, fs: 5.3, f1: 55.4, f2: 43.7, f3: 68.8, mx: 3, my: 3, mz: -3 },
      ring: { tx: -61.6, ty: -4.6, tz: 27.8, t2: -19.3, t3: 1.9, fs: 5.3, f1: 32.4, f2: 74.8, f3: 76.3, mx: 5, my: 0, mz: 5 },
      pinky: { tx: -71.6, ty: -5.3, tz: 24.9, t2: -25, t3: -15.8, fs: 14, f1: 37.5, f2: 68.9, f3: 68.4, mx: 8, my: 5, mz: -5 },
    };
    const evaluation = new PoseEvaluation(rig);
    const pad = (name: BoneName) => {
      const bone = rig.bone(name);
      const normal = new Vector3(1, 0, 0).applyQuaternion(evaluation.quaternion(name)).negate();
      const point = evaluation.head(name, new Vector3()).lerp(evaluation.tail(name, new Vector3()), 0.6);
      return { point: point.addScaledVector(normal, (bone.definition.radius ?? 0.008) * 0.76), normal };
    };
    for (const [finger, v] of Object.entries(poses)) {
      const pose = restPose();
      const set = (name: BoneName, rotation: { x?: number; y?: number; z?: number }) => {
        const value = { x: (rotation.x ?? 0) * R, y: (rotation.y ?? 0) * R, z: (rotation.z ?? 0) * R };
        const limits = rig.bone(name).definition.limits;
        for (const axis of ['x', 'y', 'z'] as const) {
          const limit = limits[axis];
          const degrees = value[axis] / R;
          if (!limit) expect(degrees, `${name}.${axis} is locked`).toBe(0);
          else {
            expect(degrees, `${name}.${axis}`).toBeGreaterThanOrEqual(limit.min - 1e-9);
            expect(degrees, `${name}.${axis}`).toBeLessThanOrEqual(limit.max + 1e-9);
          }
        }
        pose.rotations[name] = value;
      };
      set('thumb_01_l', { x: v.tx, y: v.ty, z: v.tz });
      set('thumb_02_l', { z: v.t2 });
      set('thumb_03_l', { z: v.t3 });
      set(`${finger}_01_l` as BoneName, { x: v.fs, z: v.f1 });
      set(`${finger}_02_l` as BoneName, { z: v.f2 });
      set(`${finger}_03_l` as BoneName, { z: v.f3 });
      set(`metacarpal_${finger}_l` as BoneName, { x: v.mx, y: v.my, z: v.mz });
      evaluation.apply(pose);

      const thumb = pad('thumb_03_l');
      const tip = pad(`${finger}_03_l` as BoneName);
      expect(thumb.point.distanceTo(tip.point), `${finger} pad gap`).toBeLessThan(0.001);
      expect(Math.acos(thumb.normal.dot(tip.normal)) / R, `${finger} pads face`).toBeGreaterThan(150);
      // Opposition, not a flat sweep: the thumb metacarpal stands out of the palm.
      const wrist = evaluation.head('hand_l', new Vector3());
      const normal = evaluation.head('index_01_l', new Vector3()).sub(wrist)
        .cross(evaluation.head('pinky_01_l', new Vector3()).sub(wrist)).normalize();
      if (normal.dot(new Vector3(1, 0, 0).applyQuaternion(evaluation.quaternion('hand_l')).negate()) < 0) normal.negate();
      const thumbAxis = evaluation.tail('thumb_01_l', new Vector3()).sub(evaluation.head('thumb_01_l', new Vector3())).normalize();
      expect(Math.asin(thumbAxis.dot(normal)) / R, `${finger} palmar abduction`).toBeGreaterThan(30);
    }
  });
});

describe('every exercise, with the palm at rest', () => {
  it.each(EXERCISES.map((exercise) => [exercise.id, exercise] as const))(
    '%s moves, holds and contacts exactly as it did on the 55-bone rig',
    (_id, exercise) => {
      const now = { evaluation: new PoseEvaluation(rig), clip: generateClip(rig, exercise) };
      const then = { evaluation: new PoseEvaluation(earlier), clip: generateClip(earlier, exercise) };
      const anchorsNow = lockAnchors(now.evaluation, sampleClip(now.clip, 0).pose, now.clip.locks);
      const anchorsThen = lockAnchors(then.evaluation, sampleClip(then.clip, 0).pose, then.clip.locks);
      let worstJoint = 0;
      let worstEquipment = 0;
      let worstContact = 0;

      for (let step = 0; step <= 60; step += 1) {
        const time = (step / 60) * now.clip.duration;
        const a = resolveFrame(rig, now.evaluation, now.clip, time, { anchors: anchorsNow });
        const b = resolveFrame(earlier, then.evaluation, then.clip, time, { anchors: anchorsThen });
        now.evaluation.apply(a.pose);
        then.evaluation.apply(b.pose);

        // No cupping, no opposition twist: nothing moves a metacarpal or turns
        // the thumb base about its own axis.
        for (const name of METACARPAL_BONES) {
          const rotation = a.pose.rotations[name];
          expect(Math.max(Math.abs(rotation?.x ?? 0), Math.abs(rotation?.y ?? 0), Math.abs(rotation?.z ?? 0)), name).toBe(0);
        }
        expect(a.pose.rotations.thumb_01_l?.y ?? 0).toBe(0);
        expect(a.pose.rotations.thumb_01_r?.y ?? 0).toBe(0);

        for (const bone of earlier.bones) {
          const here = now.evaluation.matrix(bone.name).elements;
          const there = then.evaluation.matrix(bone.name).elements;
          for (let index = 0; index < 16; index += 1) worstJoint = Math.max(worstJoint, Math.abs(here[index] - there[index]));
        }
        for (const [id, placed] of a.equipment) {
          const was = b.equipment.get(id)!;
          worstEquipment = Math.max(worstEquipment, placed.position.distanceTo(was.position), 1 - Math.abs(placed.quaternion.dot(was.quaternion)));
        }
        // Hand, foot and grip contacts: the same contacts at the same places.
        expect(a.contacts.length).toBe(b.contacts.length);
        const flatten = (value: unknown): number[] =>
          typeof value === 'number' ? [value] : value && typeof value === 'object' ? Object.values(value).flatMap(flatten) : [];
        const x = flatten(a.contacts);
        const y = flatten(b.contacts);
        expect(x.length).toBe(y.length);
        x.forEach((value, index) => { worstContact = Math.max(worstContact, Math.abs(value - y[index])); });
      }
      expect(worstJoint).toBeLessThan(NUMERIC);
      expect(worstEquipment).toBeLessThan(NUMERIC);
      expect(worstContact).toBeLessThan(NUMERIC);
      const rules = (skeleton: typeof rig, clip: typeof now.clip) =>
        validateClip(skeleton, new PoseEvaluation(skeleton), exercise, clip, 20).violations.map((violation) => violation.ruleId);
      expect(rules(rig, now.clip)).toEqual(rules(earlier, then.clip));
    },
    // Two rigs, every frame: the calf raises' ball-of-foot solve runs past the
    // 5 s default on a slower machine.
    30_000,
  );
});

describe('export and runtime agree', () => {
  it.each(EXERCISES.map((exercise) => [exercise.id, exercise] as const))(
    '%s: every one of the 63 bones, played back through three.js, lands where the studio put it',
    (_id, exercise) => {
      const clip = generateClip(rig, exercise);
      const baked = bakeClip(clip, rig);
      const exported = buildSkinnedRig(rig);
      expect(exported.bones).toHaveLength(63);
      const holder = new Object3D();
      holder.add(exported.mesh);
      const mixer = new AnimationMixer(holder);
      mixer.clipAction(baked.clip).play();
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const times = baked.clip.tracks[0].times;
      let worst = 0;
      // Exactly on baked samples, so interpolation cannot hide or add error:
      // what remains is float32 track storage.
      for (let index = 0; index < times.length; index += Math.max(1, Math.floor(times.length / 12))) {
        const time = times[index];
        mixer.setTime(time);
        holder.updateMatrixWorld(true);
        evaluation.apply(resolveFrame(rig, evaluation, clip, time, { anchors }).pose);
        for (const bone of rig.bones) {
          const played = new Vector3().setFromMatrixPosition(exported.boneByName.get(bone.name)!.matrixWorld);
          worst = Math.max(worst, played.distanceTo(evaluation.head(bone.name, new Vector3())));
        }
      }
      expect(worst).toBeLessThan(1e-5);
    },
    30_000,
  );
});
