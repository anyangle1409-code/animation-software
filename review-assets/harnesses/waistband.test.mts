import { readFileSync } from 'node:fs';
import { describe, it } from 'vitest';
import { Vector3 } from 'three';
import type { SkinnedMesh } from 'three';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { airSquat } from '../../src/exercises/definitions/airSquat';
import { canonicalSkeleton, PoseEvaluation } from '../../src/rig/skeleton';
import { applyCharacterPose } from '../../src/character/pose';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

/** How much standoff the waistband strip actually keeps through a squat. */
describe('waistband', () => {
  it('measures the strip the containment test excluded', async () => {
    const glbPath = process.env.GLB!;
    const bytes = readFileSync(glbPath);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'waist', label: 'Waist', data });
    const rig = canonicalSkeleton;
    const character = await source.build(rig);
    const shorts = character.meshes.find((m) => /shorts/i.test(m.name))! as SkinnedMesh;
    const body = character.meshes.find((m) => !/shorts/i.test(m.name))! as SkinnedMesh;
    const correspondence: [number, number][][] = JSON.parse(
      readFileSync(`${glbPath}.correspondence.json`, 'utf8'),
    );
    const outerCount = correspondence.length / 2;
    const bodyPosition = body.geometry.getAttribute('position');

    // Garment vertices that sit in the waistband strip, and the skin under them.
    const strip: number[] = [];
    for (let vertex = 0; vertex < outerCount; vertex += 1) {
      const sources = correspondence[vertex];
      const y = sources.reduce((sum, [v, w]) => sum + bodyPosition.getY(v) * w, 0);
      if (y > 1.14) strip.push(vertex);
    }
    const scale = source.lastReport!.scale;
    console.log(`waistband garment vertices: ${strip.length}`);

    const clip = generateClip(rig, airSquat);
    const evaluation = new PoseEvaluation(rig);
    const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
    const a = new Vector3();
    const b = new Vector3();

    for (const fraction of [0, 0.25, 0.5, 0.75]) {
      const frame = resolveFrame(rig, evaluation, clip, clip.duration * fraction, { anchors });
      applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
      character.object.updateMatrixWorld(true);
      shorts.skeleton.update();
      body.skeleton.update();
      let worst = Infinity;
      let mean = 0;
      for (const vertex of strip) {
        shorts.getVertexPosition(vertex, a);
        b.set(0, 0, 0);
        const scratch = new Vector3();
        for (const [sourceVertex, share] of correspondence[vertex]) {
          body.getVertexPosition(sourceVertex, scratch);
          b.addScaledVector(scratch, share);
        }
        const gap = a.distanceTo(b) * scale * 1000;
        worst = Math.min(worst, gap);
        mean += gap;
      }
      console.log(
        `  squat ${(fraction * 100).toString().padStart(3)}%  waistband gap: worst ${worst.toFixed(2)} mm, mean ${(mean / strip.length).toFixed(2)} mm`,
      );
    }
    character.dispose();
  }, 300_000);
});
