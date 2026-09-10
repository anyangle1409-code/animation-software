import { MeshStandardMaterial } from 'three';
import type { Skeleton } from '../rig/skeleton';
import { BODY_MATERIAL, buildBodyGeometry, buildProfileBodyGeometry } from '../body/mesh';
import { buildEcorcheGeometry, createEcorcheMaterial } from '../body/ecorche';
import { MANNEQUIN_NAME } from '../body/skin';
import { assembleCharacter } from './build';
import { builtinDeformation } from './builtinDeformation';
import type { CharacterBuildOptions, CharacterSource } from './types';

/**
 * The characters that ship with the studio.
 *
 * Both are built from code rather than loaded, so they are always available —
 * including in tests, and before any asset has been fetched.
 */

/**
 * The standard character: the anatomical surface in `src/body`, with the
 * head, neck and shoulder repairs and the elbow and armpit correctives that
 * mesh needs. All of it is specific to those vertices and none of it is
 * inherited by any other character.
 */
export const builtinCharacter: CharacterSource = {
  id: 'builtin',
  label: 'Studio character',
  note: 'The built-in anatomical surface, with its own corrective stack.',
  capabilities: { anatomy: true, textured: false },
  async build(rig: Skeleton, options: CharacterBuildOptions = {}) {
    const variant = options.variant ?? 'skin';
    const geometry = variant === 'ecorche' ? buildEcorcheGeometry(rig) : buildBodyGeometry(rig).geometry;
    const material =
      variant === 'ecorche' ? createEcorcheMaterial() : new MeshStandardMaterial({ ...BODY_MATERIAL });

    return assembleCharacter({
      source: builtinCharacter.id,
      rig,
      capabilities: builtinCharacter.capabilities,
      surfaces: [{ geometry, material, name: MANNEQUIN_NAME }],
      deformation: (meshes) => builtinDeformation(meshes[0], rig, variant),
    });
  },
};

/**
 * The original procedural mannequin — elliptical tubes and blobs generated
 * from the profile tables.
 *
 * Kept as a diagnostic model: it is cheap, it is obviously synthetic, and its
 * weights are trivially predictable, which makes it the right thing to look at
 * when the question is whether a deformation problem is in the rig or in the
 * surface.
 */
export const proceduralCharacter: CharacterSource = {
  id: 'procedural',
  label: 'Procedural mannequin (debug)',
  note: 'Generated tubes and blobs. Predictable weights, for diagnosing the rig.',
  diagnostic: true,
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
