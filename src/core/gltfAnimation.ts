import type { HgGlbDocument } from './glbContainer';
import { readHgAccessor, type HgAccessorData, type HgAccessorType } from './gltfAccessors';
import { HgGltfBuilder } from './gltfBuilder';

type JsonObject = Record<string, unknown>;

export type HgAnimationPath = 'translation' | 'rotation' | 'scale' | 'weights';

export interface HgGltfAnimationChannel {
  readonly node: number;
  readonly path: HgAnimationPath;
  readonly interpolation: 'LINEAR';
  readonly times: number[];
  readonly values: number[];
  readonly valueSize: number;
}

export interface HgGltfAnimation {
  readonly index: number;
  readonly name: string;
  readonly channels: HgGltfAnimationChannel[];
}

export interface HgAnimationTrackInput {
  readonly node: number;
  readonly path: HgAnimationPath;
  readonly times: readonly number[];
  readonly values: readonly number[];
}

export interface HgAnimationInput {
  readonly name?: string;
  readonly tracks: readonly HgAnimationTrackInput[];
}

function object(value: unknown, label: string): JsonObject {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value as JsonObject;
}

function objectArray(value: unknown, label: string): JsonObject[] {
  if (value === undefined) return [];
  if (!Array.isArray(value)) throw new Error(`${label} must be an array`);
  return value.map((entry, index) => object(entry, `${label}[${index}]`));
}

function nonNegativeInteger(value: unknown, label: string): number {
  if (!Number.isInteger(value) || (value as number) < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return value as number;
}

function animationPath(value: unknown, label: string): HgAnimationPath {
  if (value === 'translation' || value === 'rotation' || value === 'scale' || value === 'weights') {
    return value;
  }
  throw new Error(`${label} has unsupported animation path ${String(value)}`);
}

function assertTimes(times: readonly number[], label: string): void {
  if (!times.length) throw new Error(`${label} has no keyframe times`);
  let previous = Number.NEGATIVE_INFINITY;
  for (let index = 0; index < times.length; index += 1) {
    const time = times[index];
    if (!Number.isFinite(time)) throw new Error(`${label} time ${index} is not finite`);
    if (time <= previous) throw new Error(`${label} times must be strictly increasing`);
    previous = time;
  }
}

function expectedOutputType(path: HgAnimationPath): HgAccessorType | null {
  switch (path) {
    case 'translation':
    case 'scale':
      return 'VEC3';
    case 'rotation':
      return 'VEC4';
    case 'weights':
      return null;
  }
}

function validateSamplerInput(accessor: HgAccessorData, label: string): void {
  if (accessor.type !== 'SCALAR' || accessor.componentType !== 5126 || accessor.normalized) {
    throw new Error(`${label} input must be a non-normalized FLOAT SCALAR accessor`);
  }
  assertTimes(accessor.values, label);
}

function channelValueSize(
  path: HgAnimationPath,
  input: HgAccessorData,
  output: HgAccessorData,
  label: string,
): number {
  if (output.componentType !== 5126 || output.normalized) {
    throw new Error(`${label} output must use non-normalized FLOAT values`);
  }

  const expected = expectedOutputType(path);
  if (expected) {
    if (output.type !== expected || output.count !== input.count) {
      throw new Error(`${label} output shape does not match ${path}`);
    }
    return path === 'rotation' ? 4 : 3;
  }

  if (output.type !== 'SCALAR' || output.count % input.count !== 0) {
    throw new Error(`${label} weight output must be SCALAR values per keyframe`);
  }
  const size = output.count / input.count;
  if (size < 1) throw new Error(`${label} weight output has no values per keyframe`);
  return size;
}

/** Decode the project-supported LINEAR glTF animation subset as plain data. */
export function readHgGltfAnimations(document: HgGlbDocument): HgGltfAnimation[] {
  const nodeCount = objectArray(document.json.nodes, 'nodes').length;
  return objectArray(document.json.animations, 'animations').map((animation, animationIndex) => {
    const samplers = objectArray(animation.samplers, `animations[${animationIndex}].samplers`);
    const channels = objectArray(animation.channels, `animations[${animationIndex}].channels`).map(
      (channel, channelIndex): HgGltfAnimationChannel => {
        const label = `animations[${animationIndex}].channels[${channelIndex}]`;
        const samplerIndex = nonNegativeInteger(channel.sampler, `${label}.sampler`);
        const sampler = samplers[samplerIndex];
        if (!sampler) throw new Error(`${label} references missing sampler ${samplerIndex}`);

        const interpolation = sampler.interpolation ?? 'LINEAR';
        if (interpolation !== 'LINEAR') {
          throw new Error(`${label} only supports LINEAR interpolation`);
        }

        const target = object(channel.target, `${label}.target`);
        if (target.extensions !== undefined) throw new Error(`${label}.target extensions are not supported`);
        const node = nonNegativeInteger(target.node, `${label}.target.node`);
        if (node >= nodeCount) throw new Error(`${label} references missing node ${node}`);
        const path = animationPath(target.path, `${label}.target.path`);

        const input = readHgAccessor(
          document,
          nonNegativeInteger(sampler.input, `animations[${animationIndex}].samplers[${samplerIndex}].input`),
        );
        const output = readHgAccessor(
          document,
          nonNegativeInteger(sampler.output, `animations[${animationIndex}].samplers[${samplerIndex}].output`),
        );
        validateSamplerInput(input, label);
        const valueSize = channelValueSize(path, input, output, label);

        return {
          node,
          path,
          interpolation: 'LINEAR',
          times: [...input.values],
          values: [...output.values],
          valueSize,
        };
      },
    );

    return {
      index: animationIndex,
      name: typeof animation.name === 'string' ? animation.name : '',
      channels,
    };
  });
}

function trackShape(track: HgAnimationTrackInput, label: string): { type: HgAccessorType; valueSize: number } {
  assertTimes(track.times, label);
  if (!track.values.every(Number.isFinite)) throw new Error(`${label} contains a non-finite value`);

  if (track.path === 'translation' || track.path === 'scale') {
    if (track.values.length !== track.times.length * 3) {
      throw new Error(`${label} requires three values per keyframe`);
    }
    return { type: 'VEC3', valueSize: 3 };
  }
  if (track.path === 'rotation') {
    if (track.values.length !== track.times.length * 4) {
      throw new Error(`${label} requires four quaternion values per keyframe`);
    }
    return { type: 'VEC4', valueSize: 4 };
  }

  if (track.values.length % track.times.length !== 0) {
    throw new Error(`${label} weight values must divide evenly across keyframes`);
  }
  const valueSize = track.values.length / track.times.length;
  if (valueSize < 1) throw new Error(`${label} has no weight values per keyframe`);
  return { type: 'SCALAR', valueSize };
}

/**
 * Add one project-owned LINEAR animation to a first-party glTF builder.
 *
 * Each track gets its own sampler deliberately: deterministic, transparent,
 * and sufficient for Home Gym PT's baked exercise clips.
 */
export function addHgGltfAnimation(builder: HgGltfBuilder, animation: HgAnimationInput): number {
  const nodeCount = Array.isArray(builder.json.nodes) ? builder.json.nodes.length : 0;
  const samplers: JsonObject[] = [];
  const channels: JsonObject[] = [];

  animation.tracks.forEach((track, index) => {
    const label = `animation track ${index}`;
    if (!Number.isInteger(track.node) || track.node < 0 || track.node >= nodeCount) {
      throw new Error(`${label} references missing node ${track.node}`);
    }
    const shape = trackShape(track, label);
    const input = builder.addAccessor(track.times, { type: 'SCALAR', componentType: 5126 });
    const output = builder.addAccessor(track.values, { type: shape.type, componentType: 5126 });
    samplers.push({ input, output, interpolation: 'LINEAR' });
    channels.push({ sampler: index, target: { node: track.node, path: track.path } });
  });

  const animations = Array.isArray(builder.json.animations)
    ? [...builder.json.animations]
    : [];
  const animationIndex = animations.length;
  animations.push({
    ...(animation.name ? { name: animation.name } : {}),
    samplers,
    channels,
  });
  builder.json.animations = animations;
  return animationIndex;
}
