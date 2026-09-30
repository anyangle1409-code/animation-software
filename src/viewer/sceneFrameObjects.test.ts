import { describe, expect, it } from 'vitest';
import { HgMat4, HgVec3 } from '../core/linearMath';
import { HgGroup } from '../core/sceneGraph';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { captureSceneFrame } from './sceneFrameSnapshot';
import { applySceneFrameObjects } from './sceneFrameObjects';

describe('isolated scene frame objects', () => {
  it('applies solved world matrices to flat, directly owned scene objects', () => {
    const skeleton = canonicalSkeleton;
    const evaluation = new PoseEvaluation(skeleton);
    const clip = generateClip(skeleton, bicepCurl);
    const root = new HgGroup();
    const forearm = new HgGroup();
    const dumbbell = new HgGroup();
    const rightDumbbell = new HgGroup();
    root.add(forearm, dumbbell, rightDumbbell);
    const bones = new Map([['forearm_l' as const, forearm]]);
    const equipment = new Map([['dumbbell_l', dumbbell], ['dumbbell_r', rightDumbbell]]);

    for (const time of [0, 1, 2, 4, clip.duration]) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      const snapshot = captureSceneFrame(evaluation, frame, ['forearm_l']);
      applySceneFrameObjects(snapshot, { root, bones, equipment });
      root.updateMatrixWorld(true);
      expect([...forearm.matrixWorld.elements]).toEqual(snapshot.bones.get('forearm_l'));
      expect([...dumbbell.matrixWorld.elements]).toEqual(snapshot.equipment.get('dumbbell_l'));
      expect([...rightDumbbell.matrixWorld.elements]).toEqual(snapshot.equipment.get('dumbbell_r'));
      expect(forearm.matrixAutoUpdate).toBe(false);
      expect(dumbbell.matrixAutoUpdate).toBe(false);
    }
  });

  it('rejects nested objects and missing required targets rather than silently misplacing them', () => {
    const root = new HgGroup();
    const child = new HgGroup();
    const parent = new HgGroup();
    root.add(parent);
    parent.add(child);
    const snapshot = {
      time: 0,
      bones: new Map([['forearm_l' as const, new Array(16).fill(0)]]),
      equipment: new Map<string, number[]>(),
      contacts: [],
    };
    expect(() => applySceneFrameObjects(snapshot, { root, bones: new Map(), equipment: new Map() })).toThrow(/forearm_l/);
    expect(() => applySceneFrameObjects(snapshot, {
      root, bones: new Map([['forearm_l', child]]), equipment: new Map(),
    })).toThrow(/flat/);
  });

  it('validates all targets before changing the first object', () => {
    const root = new HgGroup();
    const first = new HgGroup();
    const second = new HgGroup();
    root.add(first, second);
    const initial = [...first.matrix.elements];
    const snapshot = {
      time: 0,
      bones: new Map([
        ['forearm_l' as const, new Array(16).fill(2)],
        ['hand_l' as const, new Array(16).fill(Number.NaN)],
      ]),
      equipment: new Map<string, number[]>(),
      contacts: [],
    };
    expect(() => applySceneFrameObjects(snapshot, {
      root, bones: new Map([['forearm_l', first], ['hand_l', second]]), equipment: new Map(),
    })).toThrow(/hand_l/);
    expect([...first.matrix.elements]).toEqual(initial);
    expect(first.matrixAutoUpdate).toBe(true);
  });

  it('preserves a BoneHgGroups-style local child under a world-matrix bone group', () => {
    const skeleton = canonicalSkeleton;
    const evaluation = new PoseEvaluation(skeleton);
    const clip = generateClip(skeleton, bicepCurl);
    const root = new HgGroup();
    const bone = new HgGroup();
    const leftEquipment = new HgGroup();
    const rightEquipment = new HgGroup();
    const equipment = new Map([['dumbbell_l', leftEquipment], ['dumbbell_r', rightEquipment]]);
    const localChild = new HgGroup();
    localChild.position.y = skeleton.bone('forearm_l').length / 2;
    root.add(bone, leftEquipment, rightEquipment);
    bone.add(localChild);

    for (const time of [0, 2, clip.duration]) {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      const snapshot = captureSceneFrame(evaluation, frame, ['forearm_l']);
      applySceneFrameObjects(snapshot, {
        root, bones: new Map([['forearm_l', bone]]), equipment,
      });
      root.updateMatrixWorld(true);
      const expected = new HgMat4().fromArray(snapshot.bones.get('forearm_l')!)
        .multiply(new HgMat4().makeTranslation(0, localChild.position.y, 0));
      expect(new HgVec3().setFromMatrixPosition(localChild.matrixWorld).distanceTo(
        new HgVec3().setFromMatrixPosition(expected),
      )).toBeLessThan(1e-12);
    }

    root.remove(bone);
    const frame = resolveFrame(skeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const snapshot = captureSceneFrame(evaluation, frame, ['forearm_l']);
    expect(() => applySceneFrameObjects(snapshot, {
      root, bones: new Map([['forearm_l', bone]]), equipment,
    })).toThrow(/flat/);
  });
});
