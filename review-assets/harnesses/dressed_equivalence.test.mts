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

/**
 * The dressed file is the app's default character, and it is built by
 * transplanting a body into a previous generation's dressed file. Anything the
 * transplant forgets to carry silently keeps the old generation's answer, and
 * every vertex-level check still passes — which is exactly how a promoted
 * default once shipped the previous bind, the previous rest pose and no
 * solved-grip metadata.
 *
 * So the pair is checked as a pair: same solved grip, and the same posed
 * result. This is the guard whose absence let that reach production.
 */
const BARE = process.env.BARE ?? 'public/characters/HomeGymPT_Male_BASELINE_v8.glb';
const DRESSED = process.env.DRESSED ?? 'public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb';

const load = async (url: string) => {
  const bytes = readFileSync(url);
  const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
  return retargetedCharacterSource({ id: url, label: url, data }).build(canonicalSkeleton);
};

const posed = (url: string) => async () => {
  const character = await load(url);
  const rig = canonicalSkeleton;
  const clip = generateClip(rig, bicepCurl);
  const evaluation = new PoseEvaluation(rig);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
  applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
  const mesh = character.meshes[0];
  mesh.skeleton.update();
  mesh.updateWorldMatrix(true, false);
  const count = mesh.geometry.getAttribute('position').count;
  const vertices = new Float32Array(count * 3);
  const scratch = new Vector3();
  for (let i = 0; i < count; i += 1) {
    mesh.getVertexPosition(i, scratch);
    scratch.applyMatrix4(mesh.matrixWorld);
    vertices[i * 3] = scratch.x;
    vertices[i * 3 + 1] = scratch.y;
    vertices[i * 3 + 2] = scratch.z;
  }
  const hand = new Vector3().setFromMatrixPosition(character.handMatrix!('l', new Matrix4()));
  const grip = character.gripOffset?.('l');
  const solution = character.gripSolutionId;
  character.dispose();
  return { vertices, hand, grip, solution };
};

describe('the dressed default matches the bare body it was built from', () => {
  it('carries the same solved grip and poses identically', async () => {
    const bare = await posed(BARE)();
    const dressed = await posed(DRESSED)();

    console.log(`EQUIV solution: bare=${bare.solution ?? 'NONE'} dressed=${dressed.solution ?? 'NONE'}`);
    expect(dressed.solution).toBe(bare.solution);
    expect(bare.solution).toBeTruthy();

    console.log(
      `EQUIV grip offset: bare=${JSON.stringify(bare.grip)} dressed=${JSON.stringify(dressed.grip)}`,
    );
    expect(dressed.grip).toEqual(bare.grip);
    expect(bare.grip).toBeTruthy();

    const handGap = bare.hand.distanceTo(dressed.hand) * 1000;
    console.log(`EQUIV posed hand difference: ${handGap.toFixed(4)} mm`);
    expect(handGap).toBeLessThan(0.001);

    expect(dressed.vertices.length).toBe(bare.vertices.length);
    let worst = 0;
    for (let i = 0; i < bare.vertices.length / 3; i += 1) {
      const d = Math.hypot(
        bare.vertices[i * 3] - dressed.vertices[i * 3],
        bare.vertices[i * 3 + 1] - dressed.vertices[i * 3 + 1],
        bare.vertices[i * 3 + 2] - dressed.vertices[i * 3 + 2],
      );
      if (d > worst) worst = d;
    }
    console.log(
      `EQUIV worst posed body vertex difference: ${(worst * 1000).toFixed(4)} mm over ${bare.vertices.length / 3} vertices`,
    );
    expect(worst * 1000).toBeLessThan(0.001);
  });
});
