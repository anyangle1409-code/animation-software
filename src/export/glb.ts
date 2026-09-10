import {
  Group,
  Object3D,
  QuaternionKeyframeTrack,
  Vector3,
  VectorKeyframeTrack,
} from 'three';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';
import { canonicalSkeleton } from '../rig/skeleton';
import type { StudioClip } from '../animation/clip';
import type { ExerciseDefinition } from '../exercises/types';
import { equipmentSocket } from '../equipment/library';
import { bakeClip, handAttachmentMatrix } from './clipBuilder';
import { buildEquipmentObject, buildSkinnedRig } from './rigBuilder';
import type { ShoulderCorrective } from '../body/shoulder';

export interface GlbExportOptions {
  /** Sampling rate for the baked clip. */
  fps?: number;
  /** Include the equipment meshes in the file. */
  includeEquipment?: boolean;
  /**
   * Export the animation clip without the character mesh, so several exercises
   * can share one downloaded character instead of duplicating the whole mesh.
   */
  clipOnly?: boolean;
}

/**
 * Export an animated GLB.
 *
 * With `clipOnly`, the file carries the bone hierarchy and the animation but no
 * mesh — which is the file you want when a dozen exercises all play on the same
 * Home Gym PT character.
 */
export async function exportGlb(
  studioClip: StudioClip,
  exercise: ExerciseDefinition,
  options: GlbExportOptions = {},
): Promise<Blob> {
  const { includeEquipment = true, clipOnly = false } = options;
  const rig = buildSkinnedRig(canonicalSkeleton);
  // The mesh carries the shoulder correctives as morph targets; the clip has to
  // carry their weights, or the exported animation deforms differently from the
  // studio wherever an arm is raised.
  const shoulders = rig.mesh.geometry.userData.shoulders as ShoulderCorrective[] | undefined;
  const baked = bakeClip(studioClip, canonicalSkeleton, {
    fps: options.fps,
    shoulders: clipOnly ? [] : shoulders,
    mesh: rig.mesh.name,
  });

  const scene = new Group();
  scene.name = exercise.clipName;

  if (clipOnly) {
    scene.add(rig.root);
  } else {
    scene.add(rig.mesh);
  }

  const animations = [baked.clip];

  if (includeEquipment && !clipOnly) {
    for (const instance of studioClip.equipment) {
      if (!instance.visible) continue;
      const object = buildEquipmentObject(instance.kind);
      object.name = instance.label ?? instance.id;

      if (instance.attachment.mode === 'hand') {
        // Rigidly parented to the hand bone: no extra animation needed, and the
        // attachment stays exact in whatever engine plays the file.
        const hand = rig.boneByName.get(instance.attachment.side === 'l' ? 'hand_l' : 'hand_r');
        const socket = equipmentSocket(instance.kind, instance.attachment.socket);
        const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };
        const matrix = handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 });
        object.applyMatrix4(matrix);
        hand?.add(object);
      } else if (instance.attachment.mode === 'static') {
        object.position.set(instance.position.x, instance.position.y, instance.position.z);
        scene.add(object);
      } else {
        // Driven by both hands, so its motion is baked as its own track.
        applyBakedEquipmentTrack(object, baked, instance.id);
        scene.add(object);
      }
    }
  }

  const exporter = new GLTFExporter();
  const result = await exporter.parseAsync(scene as Object3D, {
    binary: true,
    animations,
    onlyVisible: false,
    includeCustomExtensions: false,
  });

  return new Blob([result as ArrayBuffer], { type: 'model/gltf-binary' });
}

/**
 * Park a two-handed item at its first baked sample and attach the rest of the
 * motion as an animation on that object.
 */
function applyBakedEquipmentTrack(
  object: Object3D,
  baked: ReturnType<typeof bakeClip>,
  id: string,
): void {
  const track = baked.equipmentTracks.get(id);
  if (!track || track.position.length < 3) return;
  object.name = `equipment_${id}`;
  object.position.copy(new Vector3(track.position[0], track.position[1], track.position[2]));

  // three.js binds tracks by object name, which the exporter preserves.
  baked.clip.tracks.push(
    new VectorKeyframeTrack(`${object.name}.position`, baked.times, track.position),
    new QuaternionKeyframeTrack(`${object.name}.quaternion`, baked.times, track.quaternion),
  );
}
