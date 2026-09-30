import { loadHgFirstPartyScene } from '../character/gltfFirstPartyScene';
import { parseHgGlb } from '../core/glbContainer';
import {
  readHgGltfAnimations,
  type HgGltfAnimation,
  type HgGltfAnimationChannel,
} from '../core/gltfAnimation';
import { hgRuntimeNodeNames } from '../core/gltfRuntimeNames';
import { HgQuat } from '../core/linearMath';
import type { HgObject3D } from '../core/sceneGraph';

export interface HgTestGltfPlayback {
  readonly scene: HgObject3D;
  readonly animation: HgGltfAnimation;
  object(name: string): HgObject3D | null;
  setTime(time: number): void;
}

const sample = (channel: HgGltfAnimationChannel, time: number): number[] => {
  const { times, values, valueSize } = channel;
  if (time <= times[0]) return values.slice(0, valueSize);
  const last = times.length - 1;
  if (time >= times[last]) {
    return values.slice(last * valueSize, (last + 1) * valueSize);
  }

  let upper = 1;
  while (upper < times.length && time > times[upper]) upper += 1;
  const lower = upper - 1;
  const alpha = (time - times[lower]) / (times[upper] - times[lower]);
  const from = values.slice(lower * valueSize, (lower + 1) * valueSize);
  const to = values.slice(upper * valueSize, (upper + 1) * valueSize);

  if (channel.path === 'rotation') {
    return new HgQuat(from[0], from[1], from[2], from[3]).normalize()
      .slerp(new HgQuat(to[0], to[1], to[2], to[3]).normalize(), alpha)
      .normalize()
      .toArray();
  }
  return from.map((value, index) => value + (to[index] - value) * alpha);
};

/**
 * Test-only playback for the LINEAR node-transform subset emitted by Home Gym
 * PT. Export regression tests can therefore exercise real GLBs without Three.
 */
export async function loadHgTestGltfPlayback(
  input: ArrayBuffer | Uint8Array,
  animationIndex = 0,
): Promise<HgTestGltfPlayback> {
  const document = parseHgGlb(input);
  const animations = readHgGltfAnimations(document);
  const animation = animations[animationIndex];
  if (!animation) throw new Error(`Missing animation ${animationIndex}`);

  const scene = await loadHgFirstPartyScene(input);
  const byName = new Map<string, HgObject3D>();
  scene.traverse((object) => {
    if (object.name) byName.set(object.name, object);
  });

  const nodes = document.json.nodes as Array<{ name?: string }> | undefined;
  const runtimeNames = hgRuntimeNodeNames((nodes ?? []).map((node) => node.name ?? ''));
  const runtimeNodes = runtimeNames.map((name) => byName.get(name) ?? null);

  return {
    scene,
    animation,
    object(name) {
      return byName.get(name) ?? null;
    },
    setTime(time) {
      for (const channel of animation.channels) {
        const object = runtimeNodes[channel.node];
        if (!object) throw new Error(`Missing runtime node ${channel.node}`);
        const values = sample(channel, time);
        if (channel.path === 'translation') {
          object.position.set(values[0], values[1], values[2]);
        } else if (channel.path === 'rotation') {
          object.quaternion.set(values[0], values[1], values[2], values[3]);
        } else if (channel.path === 'scale') {
          object.scale.set(values[0], values[1], values[2]);
        } else {
          throw new Error('Test playback does not apply morph weights');
        }
        object.matrixWorldNeedsUpdate = true;
      }
      scene.updateMatrixWorld(true);
    },
  };
}
