import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { exportGlb } from '../../export/glb';
import { EXERCISES } from '../library';
import { farmersWalk } from '../definitions/farmersWalk';
import { bicepCurl } from '../definitions/bicepCurl';
import type { ExerciseDefinition } from '../types';

/**
 * The carry family: a walk in place, each planted foot sliding back at the
 * speed the character is to be moved (`ExerciseDefinition.travel`).
 */
const rig = canonicalSkeleton;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, farmersWalk);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
const step = clip.duration / 2;
const speed = farmersWalk.travel!.speed;

const all = Array.from({ length: 401 }, (_, index) => {
  const time = (index / 400) * clip.duration;
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);
  const side = (name: 'l' | 'r') => ({
    ankle: evaluation.head(`foot_${name}`, new Vector3()),
    ball: evaluation.tail(`foot_${name}`, new Vector3()),
  });
  // The left foot is down for the first step, the right for the second.
  const planted = time < step ? 'l' : 'r';
  return { time, frame, planted: side(planted), swinging: side(planted === 'l' ? 'r' : 'l') };
});

async function sceneExtras(exercise: ExerciseDefinition) {
  const buffer = await (await exportGlb(generateClip(rig, exercise), exercise, { fps: 10, clipOnly: true })).arrayBuffer();
  const view = new DataView(buffer);
  const length = view.getUint32(12, true);
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 20, length)));
  // The exported group is the file's root node, named after the clip.
  const root = json.nodes.find((node: { name?: string }) => node.name === exercise.clipName);
  return root?.extras;
}

describe('the carry family', () => {
  it('has one registered variant, the only exercise that walks', () => {
    expect(EXERCISES.filter((exercise) => exercise.travel).map((exercise) => exercise.id)).toEqual(['farmers_walk']);
  });

  it('walks 44 cm per 0.6 s step: 0.733 m/s', () => {
    expect(speed).toBeCloseTo(0.44 / 0.6, 12);
    expect(clip.duration).toBeCloseTo(1.2, 9);
  });

  it('solves every frame: both legs reach', () => {
    for (const { frame, time } of all) {
      for (const result of frame.ikResults) expect(result.error, `${result.chain} at ${time.toFixed(2)}s`).toBeLessThan(0.002);
    }
  });

  it('holds each planted foot still on the floor once the character travels at that speed', () => {
    for (const { time, planted } of all) {
      const since = time < step ? time : time - step;
      // The ball lands 36 cm ahead of the hips (22 cm, plus the foot's 14).
      expect(planted.ball.z + speed * since, `${time.toFixed(3)}s`).toBeCloseTo(0.36, 2);
      expect(Math.abs(planted.ball.z + speed * since - 0.36)).toBeLessThan(0.0015);
      expect(Math.abs(planted.ball.y - 0.025)).toBeLessThan(0.001);
    }
  });

  it('swings the other foot clear of the floor and never through it', () => {
    const lift = Math.max(...all.map(({ swinging }) => swinging.ankle.y - 0.08));
    expect(lift).toBeGreaterThan(0.06);
    expect(lift).toBeLessThan(0.08);
    for (const { swinging } of all) {
      expect(swinging.ball.y).toBeGreaterThan(0.025 - 0.0005);
      expect(swinging.ankle.y).toBeGreaterThan(0.08 - 0.0005);
    }
  });

  it('writes its travel speed onto the exported root node, and no other exercise writes one', async () => {
    expect(await sceneExtras(farmersWalk)).toEqual({ homeGymPT: { travelSpeed: speed } });
    expect(await sceneExtras(bicepCurl)).toBeUndefined();
  });
});
