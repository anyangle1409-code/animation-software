import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { captureSceneFrame } from './sceneFrameSnapshot';

describe('renderer-neutral scene frame snapshot', () => {
  it('copies the solved curl pose, equipment and contacts at distinct phases', () => {
    const skeleton = canonicalSkeleton;
    const evaluation = new PoseEvaluation(skeleton);
    const clip = generateClip(skeleton, bicepCurl);
    const boneNames = ['upperarm_l', 'forearm_l', 'hand_l'] as const;
    const captured = [0, 1, 2, 4, clip.duration].map((time) => {
      const frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
      const snapshot = captureSceneFrame(evaluation, frame, boneNames);
      expect(snapshot.time).toBe(time);
      expect(snapshot.phaseId).toBe(frame.phaseId);
      expect([...snapshot.bones.keys()]).toEqual(boneNames);
      expect([...snapshot.equipment.keys()]).toEqual([...frame.equipment.keys()]);
      for (const name of boneNames) {
        expect(snapshot.bones.get(name)).toEqual([...evaluation.matrix(name).elements]);
      }
      for (const [id, transform] of frame.equipment) {
        expect(snapshot.equipment.get(id)).toEqual([...transform.matrix.elements]);
      }
      expect(snapshot.contacts).toEqual(frame.contacts);
      return snapshot;
    });
    expect(captured[0].bones.get('forearm_l')).not.toEqual(captured[2].bones.get('forearm_l'));
    expect(captured[0].bones.get('forearm_l')).toEqual(captured[4].bones.get('forearm_l'));
    expect(captured[0].equipment.size).toBe(2);
  });

  it('does not retain mutable matrix or contact objects from the resolved frame', () => {
    const skeleton = canonicalSkeleton;
    const evaluation = new PoseEvaluation(skeleton);
    const clip = generateClip(skeleton, bicepCurl);
    const frame = resolveFrame(skeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const snapshot = captureSceneFrame(evaluation, frame, ['forearm_l']);
    const originalBone = snapshot.bones.get('forearm_l')![12];
    const originalEquipment = snapshot.equipment.get('dumbbell_l')![12];
    const originalContact = snapshot.contacts[0]?.target.x;

    evaluation.matrix('forearm_l').elements[12] += 3;
    frame.equipment.get('dumbbell_l')!.matrix.elements[12] += 3;
    if (frame.contacts[0]) frame.contacts[0].target.x += 3;
    expect(snapshot.bones.get('forearm_l')![12]).toBe(originalBone);
    expect(snapshot.equipment.get('dumbbell_l')![12]).toBe(originalEquipment);
    expect(snapshot.contacts[0]?.target.x).toBe(originalContact);
  });
});
