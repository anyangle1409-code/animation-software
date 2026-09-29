import type { StudioClip } from '../animation/clip';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { addHgGltfAnimation, type HgAnimationPath } from '../core/gltfAnimation';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { bakeClip } from './clipBuilder';

/**
 * Write an animation-only GLB with project-owned glTF/GLB code.
 *
 * This deliberately contains the canonical hierarchy and baked animation only:
 * no character mesh and no equipment, matching the public clip-only contract.
 */
export function exportFirstPartyClipGlb(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  fps?: number,
): Blob {
  const builder = new HgGltfBuilder();
  const rig = canonicalSkeleton;
  const sceneRootIndex = 0;
  const nodeIndex = new Map(rig.bones.map((bone, index) => [bone.name, index + 1]));

  const boneNodes = rig.bones.map((bone) => {
    const children = rig.bones
      .filter((candidate) => candidate.parent === bone.name)
      .map((candidate) => nodeIndex.get(candidate.name)!);
    return {
      name: bone.name,
      translation: [bone.offset.x, bone.offset.y, bone.offset.z],
      rotation: [
        bone.restLocalQuaternion.x,
        bone.restLocalQuaternion.y,
        bone.restLocalQuaternion.z,
        bone.restLocalQuaternion.w,
      ],
      ...(children.length ? { children } : {}),
    };
  });

  builder.json.nodes = [
    {
      name: exercise.clipName,
      children: [nodeIndex.get(rig.bones[0].name)!],
      ...(exercise.travel
        ? { extras: { homeGymPT: { travelSpeed: exercise.travel.speed } } }
        : {}),
    },
    ...boneNodes,
  ];
  builder.json.scenes = [{ name: exercise.clipName, nodes: [sceneRootIndex] }];
  builder.json.scene = 0;

  const baked = bakeClip(studioClip, rig, { fps });
  const tracks = baked.clip.tracks.map((track) => {
    const separator = track.name.lastIndexOf('.');
    if (separator <= 0) throw new Error(`Unsupported animation track name "${track.name}"`);
    const boneName = track.name.slice(0, separator);
    const property = track.name.slice(separator + 1);
    const node = nodeIndex.get(boneName);
    if (node === undefined) throw new Error(`Animation track references unknown bone "${boneName}"`);

    let path: HgAnimationPath;
    if (property === 'quaternion') path = 'rotation';
    else if (property === 'position') path = 'translation';
    else if (property === 'scale') path = 'scale';
    else throw new Error(`Unsupported animation track property "${property}"`);

    return {
      node,
      path,
      times: Array.from(track.times),
      values: Array.from(track.values),
    };
  });

  addHgGltfAnimation(builder, { name: studioClip.name, tracks });
  const bytes = builder.toGlb();
  return new Blob([new Uint8Array(bytes)], { type: 'model/gltf-binary' });
}
