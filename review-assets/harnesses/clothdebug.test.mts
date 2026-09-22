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

describe('debug', () => {
  it('locates the worst standoff', async () => {
    const glbPath = process.env.GLB!;
    const bytes = readFileSync(glbPath);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'dbg', label: 'Debug', data });
    const character = await source.build(canonicalSkeleton);
    console.log('meshes:', character.meshes.map((m) => `${m.name}(${m.geometry.getAttribute('position').count})`).join(', '));
    const shorts = character.meshes.find((mesh) => /shorts/i.test(mesh.name))!;
    const body = character.meshes.find((mesh) => !/shorts/i.test(mesh.name))!;
    console.log('shorts morphs:', shorts.morphTargetInfluences?.length ?? 0, 'body morphs:', body.morphTargetInfluences?.length ?? 0);
    console.log('shorts world matrix:', shorts.matrixWorld.elements.map((v) => v.toFixed(4)).join(','));
    console.log('body   world matrix:', body.matrixWorld.elements.map((v) => v.toFixed(4)).join(','));

    const correspondence: [number, number][][] = JSON.parse(
      readFileSync(`${glbPath}.correspondence.json`, 'utf8'),
    );
    const outerCount = correspondence.length / 2;

    const rig = canonicalSkeleton;
    const clip = generateClip(rig, bicepCurl);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const frame = resolveFrame(rig, evaluation, clip, 0, { anchors });
    applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
    character.object.updateMatrixWorld(true);

    body.skeleton.update();
    shorts.skeleton.update();
    console.log('same skeleton object:', body.skeleton === shorts.skeleton);

    const point = new Vector3();
    const worst: { vertex: number; standoff: number; shortsAt: Vector3; bodyAt: Vector3 }[] = [];
    const bodyPoint = new Vector3();
    for (let vertex = 0; vertex < outerCount; vertex += 1) {
      shorts.getVertexPosition(vertex, point);
      bodyPoint.set(0, 0, 0);
      const scratch = new Vector3();
      for (const [sourceVertex, share] of correspondence[vertex]) {
        body.getVertexPosition(sourceVertex, scratch);
        bodyPoint.addScaledVector(scratch, share);
      }
      worst.push({
        vertex,
        standoff: point.distanceTo(bodyPoint),
        shortsAt: point.clone(),
        bodyAt: bodyPoint.clone(),
      });
    }
    worst.sort((a, b) => b.standoff - a.standoff);
    console.log('\nlargest garment-to-source distances (should all be ~11mm model units):');
    for (const entry of worst.slice(0, 6)) {
      console.log(
        `  v${entry.vertex} d=${(entry.standoff * 1000).toFixed(1)}mm shorts=${entry.shortsAt.toArray().map((v) => v.toFixed(3)).join(',')} body=${entry.bodyAt.toArray().map((v) => v.toFixed(3)).join(',')}`,
      );
    }
    console.log('smallest:');
    for (const entry of worst.slice(-4)) {
      console.log(
        `  v${entry.vertex} d=${(entry.standoff * 1000).toFixed(1)}mm shorts=${entry.shortsAt.toArray().map((v) => v.toFixed(3)).join(',')} body=${entry.bodyAt.toArray().map((v) => v.toFixed(3)).join(',')}`,
      );
    }
    character.dispose();
  }, 300_000);
});
