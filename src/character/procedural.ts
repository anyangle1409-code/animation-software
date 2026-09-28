import { MeshStandardMaterial } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { BODY_MATERIAL, buildProfileBodyGeometry } from '../body/profileMesh';
import { assembleCharacter } from './build';
import type { CharacterSource } from './types';

const MANNEQUIN_NAME = 'HGPT_Mannequin';

/**
 * Clean project-authored procedural fallback.
 *
 * This source is generated only from the pinned Home Gym PT profile tables.
 * It deliberately has no import path to any removed derived anatomical body.
 * It is a temporary operational fallback while ORIGINAL v1 is completed, not
 * the final production character.
 */
export const proceduralCharacter: CharacterSource = {
  id: 'procedural',
  label: 'Home Gym PT clean scaffold',
  note: 'Project-authored procedural fallback used while ORIGINAL v1 is completed.',
  capabilities: { anatomy: false, textured: false },
  async build(rig: Skeleton) {
    return assembleCharacter({
      source: proceduralCharacter.id,
      rig,
      capabilities: proceduralCharacter.capabilities,
      surfaces: [
        {
          geometry: buildProfileBodyGeometry(rig).geometry,
          material: new MeshStandardMaterial({ ...BODY_MATERIAL }),
          name: MANNEQUIN_NAME,
        },
      ],
    });
  },
};
