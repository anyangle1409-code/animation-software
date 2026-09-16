import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { FINGERS } from '../rig/boneNames';
import type { BoneName } from '../rig/boneNames';
import { gripProfile } from '../exercises/gripProfiles';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { solvedGripFor } from './solvedGrip';

describe('solved cylindrical grip', () => {
  const solved = solvedGripFor('homeGymPTMale', 'dumbbell');

  it('carries a solved grip for the dumbbell family at the bar it was solved against', () => {
    expect(solved).not.toBeNull();
    // src/equipment/geometry.ts: bar(0.015, 0.12). A grip solved against one
    // diameter means nothing at another, so the radius travels with it.
    expect(solved!.radius).toBeCloseTo(0.015, 6);
  });

  it('gives every digit its own row', () => {
    // One row for all four fingers is what makes a fist rather than a grip:
    // each digit meets the cylinder at a different place, so they cannot all
    // stop in the same pose.
    const rows = (['index', 'middle', 'ring', 'pinky'] as const).map((finger) =>
      solved!.digits[finger].join('/'),
    );
    expect(new Set(rows).size).toBeGreaterThan(1);
    for (const finger of FINGERS) expect(solved!.digits[finger]).toHaveLength(3);
  });

  it('opposes the thumb rather than driving it into the handle', () => {
    // thumbOppositionX goes to thumb_01.x with no per-side sign flip, unlike
    // flexion on z, so the profiles' shared negative value rotates the thumb
    // into the bar on both hands. Measured: -10.43 mm and 21 vertices inside,
    // against +2.54 mm and none when the sign is right.
    expect(gripProfile('dumbbell').thumbOppositionX).toBeLessThan(0);
    expect(solved!.thumbOppositionX).toBeGreaterThan(0);
  });

  it('stays inside the rig’s joint limits at the curl’s own closure', () => {
    // The substitution in applyCharacterPose writes rotations straight to the
    // character and does not re-run clampPose, so the solved angles have to be
    // reachable on their own.
    const closure = bicepCurl.hands.closure;
    for (const finger of FINGERS) {
      solved!.digits[finger].forEach((maximum, index) => {
        const bone = canonicalSkeleton.byName.get(`${finger}_0${index + 1}_l` as BoneName);
        expect(bone, `${finger}_0${index + 1}_l`).toBeDefined();
        const limit = bone!.definition.limits.z;
        const applied = maximum * closure;
        if (!limit) return;
        expect(applied, `${finger}_0${index + 1} z`).toBeGreaterThanOrEqual(limit.min - 1e-9);
        expect(applied, `${finger}_0${index + 1} z`).toBeLessThanOrEqual(limit.max + 1e-9);
      });
    }
    const thumbBase = canonicalSkeleton.byName.get('thumb_01_l');
    const opposition = solved!.thumbOppositionX * closure;
    expect(opposition).toBeLessThanOrEqual((thumbBase!.definition.limits.x?.max ?? 0) + 1e-9);
  });

  it('offers nothing for a character or grip family it was not solved for', () => {
    expect(solvedGripFor('homeGymPTMale', 'bar')).toBeNull();
    expect(solvedGripFor('homeGymPTMale', 'floor')).toBeNull();
    expect(solvedGripFor(undefined, 'dumbbell')).toBeNull();
    expect(solvedGripFor('someoneElse', 'dumbbell')).toBeNull();
  });
});
