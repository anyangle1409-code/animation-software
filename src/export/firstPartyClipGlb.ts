import type { StudioClip } from '../animation/clip';
import { HgGltfBuilder } from '../core/gltfBuilder';
import { addHgGltfAnimation, type HgAnimationPath } from '../core/gltfAnimation';
import type { ExerciseDefinition } from '../exercises/types';
import { canonicalSkeleton } from '../rig/skeleton';
import { bakeClipData } from './clipData';

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
  const nodeIndex = new Map<string, number>(
    rig.bones.map((bone, index) => [bone.name, index + 1]),
  );

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

  const baked = bakeClipData(studioClip, rig, { fps });
  const tracks = baked.tracks.map((track) => {
    const node = nodeIndex.get(track.bone);
    if (node === undefined) throw new Error(`Animation track references unknown bone "${track.bone}"`);

    let path: HgAnimationPath;
    if (track.property === 'quaternion') path = 'rotation';
    else path = 'translation';

    return {
      node,
      path,
      times: track.times,
      values: track.values,
    };
  });

  addHgGltfAnimation(builder, { name: studioClip.name, tracks });
  const bytes = builder.toGlb();
  return new Blob([new Uint8Array(bytes)], { type: 'model/gltf-binary' });
}
