import { canonicalSkeleton } from '../rig/skeleton';
import type { StudioClip } from '../animation/clip';
import type { ExerciseDefinition } from '../exercises/types';
import { bakeClipData } from './clipData';
import { exportFirstPartyClipGlb } from './firstPartyClipGlb';
import { exportFirstPartyCanonicalCharacterGlb } from './firstPartyCharacterGlb';
import { exportFirstPartyPreservedCharacterGlb } from './firstPartyPreservedCharacterGlb';
import { exportFirstPartyReboundCharacterGlb } from './firstPartyReboundCharacterGlb';
import { characterSource } from '../character';
import type { CharacterSource } from '../character';

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
  /**
   * Which character to write. Defaults to the registered default, so the
   * exported file is the character the studio is showing rather than a
   * hard-wired mesh.
   */
  character?: CharacterSource | string;
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
  if (clipOnly) return exportFirstPartyClipGlb(studioClip, exercise, options.fps);

  const source =
    typeof options.character === 'object' ? options.character : characterSource(options.character);

  if (!clipOnly && source.id === 'procedural') {
    return exportFirstPartyCanonicalCharacterGlb(
      studioClip,
      exercise,
      source,
      options.fps,
      includeEquipment,
    );
  }
  const character = await source.build(canonicalSkeleton);
  // Whatever the character's deformation stack does beyond posing bones —
  // morph-target correctives, most of it — has to be baked in as well, or the
  // exported animation deforms differently from the studio.
  // A character with its own skeleton carries the animation on that skeleton:
  // the canonical bone tracks would name bones the exported file has no nodes
  // for, and the character's own sampler holds the retargeted rotations.
  const ownSkeleton = Boolean(character.driver);
  const sampler = clipOnly
    ? null
    : character.sampler?.() ?? character.deformation?.sampler?.() ?? null;

  // A preserved imported character keeps its exact authored GLB and receives
  // project-owned source-bone/morph animation plus first-party equipment.
  // Hand-held items are parented to the imported character's own hand nodes;
  // world-space items keep their baked transforms outside the character scale.
  if (character.preservedGlb && ownSkeleton) {
    const bakedData = bakeClipData(studioClip, canonicalSkeleton, {
      fps: options.fps,
      deformation: sampler,
      boneTracks: false,
    });
    try {
      return exportFirstPartyPreservedCharacterGlb(
        character,
        bakedData,
        exercise,
        includeEquipment ? studioClip.equipment : [],
      );
    } finally {
      character.dispose();
    }
  }

  if (character.sourceGlb && !ownSkeleton) {
    try {
      return exportFirstPartyReboundCharacterGlb(
        studioClip,
        exercise,
        character,
        options.fps,
        includeEquipment,
      );
    } finally {
      character.dispose();
    }
  }

  character.dispose();
  throw new Error(
    'Character source "' + source.id +
    '" has no first-party GLB export contract. ' +
    'Use the canonical, preserved-import, or diagnostic rebind character path.',
  );
}
