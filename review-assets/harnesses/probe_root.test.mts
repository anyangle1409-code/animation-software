import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Vector3 } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/** Posed world position of the arm root, for building the rest->posed Jacobian. */
describe('posed arm root', () => {
  it('prints posed joint positions', async () => {
    const rig = canonicalSkeleton;
    for (const p of (process.env.ASSETS ?? '').split(',').filter(Boolean)) {
      const bytes = readFileSync(p);
      const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
      const character = await retargetedCharacterSource({ id: p, label: p, data }).build(rig);
      const clip = generateClip(rig, bicepCurl);
      const evaluation = new PoseEvaluation(rig);
      const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
      const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      const at = (n: string) => {
        const b = character.boneByName.get(n as never) as never as { matrixWorld: never } | undefined;
        return b ? new Vector3().setFromMatrixPosition(b.matrixWorld) : null;
      };
      const v = (x: Vector3 | null) => x ? x.toArray().map((q) => (q * 1000).toFixed(2).padStart(9)).join(' ') : '—';
      console.log(`PROBE ${p.split('/').pop()!.replace('HomeGymPT_Male_', '').replace('.glb', '').padEnd(14)} sh[${v(at('upperarm_l'))}] el[${v(at('forearm_l'))}] hd[${v(at('hand_l'))}]`);
      character.dispose?.();
    }
  }, 600_000);
});
