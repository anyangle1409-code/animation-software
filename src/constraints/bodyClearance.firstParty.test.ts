import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { proceduralCharacter } from '../character/procedural';
import type { CharacterBuild } from '../character/types';
import { airSquat } from '../exercises/definitions/airSquat';
import { canonicalSkeleton } from '../rig/skeleton';
import { bodyMeshOf, measureArmTrunkSeparation } from './bodyClearance';

describe('first-party body-clearance character boundary', () => {
  let character: CharacterBuild;

  beforeAll(async () => {
    character = await proceduralCharacter.build(canonicalSkeleton);
  });

  afterAll(() => {
    character.dispose();
  });

  it('finds the clean procedural body structurally rather than by a legacy asset name', () => {
    const body = bodyMeshOf(character);
    expect(body).toBeDefined();
    expect(body).toBe(character.meshes[0]);
    expect(body!.name).not.toMatch(/freeman/i);
  });

  it('recognises canonical arm names in arm-to-trunk measurement', () => {
    const measured = measureArmTrunkSeparation(
      character,
      canonicalSkeleton,
      generateClip(canonicalSkeleton, airSquat),
      4,
    );
    expect(measured.trunkVertices).toBeGreaterThan(0);
    expect(measured.sides).toHaveLength(2);
    expect(measured.sides.every((side) => side.armVertices > 0)).toBe(true);
    expect(Number.isFinite(measured.closest)).toBe(true);
    expect(measured.closest).toBeGreaterThan(0);
  });
});
