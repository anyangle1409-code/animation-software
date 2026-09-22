import { readFileSync } from 'node:fs';
import { describe, it, expect } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { equipmentSocket } from '../../src/equipment/library';
import { handAttachmentMatrix } from '../../src/export/clipBuilder';

/**
 * The renderer, the exporter and the solver must place a held dumbbell at the
 * same point. The viewport uses the pipeline's resolved transform directly, so
 * this checks the exporter's independent composition against it.
 */
describe('grip frame agreement', () => {
  it('renderer, solver and exporter resolve the same handle transform', async () => {
    const rig = canonicalSkeleton;
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({ id: 'agree', label: 'Agree', data }).build(rig);
    const clip = generateClip(rig, bicepCurl);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    for (const time of [0, 2, 4]) {
      const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      for (const side of ['l', 'r'] as const) {
        const instance = clip.equipment.find(
          (entry) => entry.kind === 'dumbbell' && entry.attachment.mode === 'hand' && entry.attachment.side === side,
        );
        if (!instance || instance.attachment.mode !== 'hand') continue;
        // What the viewport draws: the character's own hand frame, after the
        // pose has been applied, with the character's own handle offset. The
        // pipeline's transform is resolved before the character is posed, so it
        // is the solver's canonical-space answer, not the drawn one.
        const drawnHand = character.handMatrix?.(side, new Matrix4());
        const drawnOffset = instance.attachment.gripOffset ?? character.gripOffset?.(side);
        if (!drawnHand || !drawnOffset) continue;
        const socketForDraw = equipmentSocket(instance.kind, instance.attachment.socket);
        const drawn = new Matrix4().multiplyMatrices(
          drawnHand,
          handAttachmentMatrix(drawnOffset, socketForDraw?.position ?? { x: 0, y: 0, z: 0 }),
        );

        // The exporter's composition, independently.
        const bone = character.boneByName.get(side === 'l' ? 'hand_l' : 'hand_r');
        const socket = equipmentSocket(instance.kind, instance.attachment.socket);
        const offset = instance.attachment.gripOffset ?? character.gripOffset?.(side);
        if (!bone || !offset) continue;
        bone.updateWorldMatrix(true, false);
        const frameMatrix = character.handMatrix?.(side, new Matrix4());
        if (!frameMatrix) continue;
        const local = new Matrix4().copy(bone.matrixWorld).invert().multiply(frameMatrix)
          .multiply(handAttachmentMatrix(offset, socket?.position ?? { x: 0, y: 0, z: 0 }));
        const exported = new Matrix4().multiplyMatrices(bone.matrixWorld, local);

        const a = new Vector3().setFromMatrixPosition(drawn);
        const b = new Vector3().setFromMatrixPosition(exported);
        const mm = a.distanceTo(b) * 1000;
        console.log(`GRIP_AGREE t=${time} ${side}: rendered vs exported ${mm.toFixed(4)} mm`);
        expect(mm).toBeLessThan(0.05);
      }
    }
  });
});
