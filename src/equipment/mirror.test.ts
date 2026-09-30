import { describe, expect, it } from 'vitest';
import { HgMat4, HgQuat, HgVec3 } from '../core/linearMath';
import { EQUIPMENT_PARTS } from './geometry';
import { equipmentPartDistances } from '../constraints/collision';
import { EXERCISES } from '../exercises/library';
import { mirrorInvariant, reflectBakedTrack, reflectedStaticPlacement, reflectPlacement } from './mirror';
import type { EquipmentKind } from './types';

/**
 * Reflecting what the rig placed into a mirrored character's world
 * (`equipment/mirror.ts`).
 */

/**
 * The two kinds whose shape is not its own mirror image. Both are two-handed
 * bars no exercise uses yet; a baked two-hand track reflected with S·M·S would
 * draw them with their bends the wrong way round.
 */
const NOT_SELF_MIRRORED = new Set<EquipmentKind>(['ez_curl_bar', 'lat_pulldown_bar']);

describe('reflecting rig-placed equipment', () => {
  it('draws the same item: every other kind is its own mirror image about local x = 0', () => {
    let seed = 7;
    const random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (const kind of Object.keys(EQUIPMENT_PARTS) as EquipmentKind[]) {
      let worst = 0;
      for (let sample = 0; sample < 2000; sample += 1) {
        const point = new HgVec3(random() * 2 - 1, random() * 2.5 - 0.2, random() * 2 - 1);
        const here = Math.min(...equipmentPartDistances(kind, point));
        const there = Math.min(...equipmentPartDistances(kind, point.clone().set(-point.x, point.y, point.z)));
        worst = Math.max(worst, Math.abs(here - there));
      }
      if (NOT_SELF_MIRRORED.has(kind)) expect(worst, kind).toBeGreaterThan(0.01);
      else expect(worst, kind).toBeLessThan(1e-9);
    }
  });

  it('uses none of the kinds that are not, in any exercise', () => {
    for (const exercise of EXERCISES) {
      for (const instance of exercise.equipment.instances) expect(NOT_SELF_MIRRORED.has(instance.kind), exercise.id).toBe(false);
    }
  });

  it('puts an item where the mirror puts it, as a proper rotation', () => {
    const matrix = new HgMat4().compose(
      new HgVec3(0.9, 1.2, 0.3),
      new HgQuat().setFromEulerXYZ(0.3, -0.7, 0.2),
      new HgVec3(1, 1.5, 1),
    );
    const reflected = reflectPlacement(matrix);
    const determinant = (m: HgMat4) => {
      const e = m.elements;
      return (
        e[0] * (e[5] * (e[10] * e[15] - e[14] * e[11]) - e[9] * (e[6] * e[15] - e[14] * e[7]) + e[13] * (e[6] * e[11] - e[10] * e[7])) -
        e[4] * (e[1] * (e[10] * e[15] - e[14] * e[11]) - e[9] * (e[2] * e[15] - e[14] * e[3]) + e[13] * (e[2] * e[11] - e[10] * e[3])) +
        e[8] * (e[1] * (e[6] * e[15] - e[14] * e[7]) - e[5] * (e[2] * e[15] - e[14] * e[3]) + e[13] * (e[2] * e[7] - e[6] * e[3])) -
        e[12] * (e[1] * (e[6] * e[11] - e[10] * e[7]) - e[5] * (e[2] * e[11] - e[10] * e[3]) + e[9] * (e[2] * e[7] - e[6] * e[3]))
      );
    };
    expect(determinant(reflected)).toBeCloseTo(determinant(matrix), 12);
    // A point on the item lands on the mirror image of where it was.
    const local = new HgVec3(0.1, 0.2, -0.3);
    const before = local.clone().applyMatrix4(matrix);
    const after = local.clone().set(-local.x, local.y, local.z).applyMatrix4(reflected);
    before.set(-before.x, before.y, before.z);
    expect(after.distanceTo(before)).toBeLessThan(1e-12);
    // In place, as the clearance test uses it.
    expect(Array.from(reflectPlacement(matrix.clone(), undefined).elements))
      .toEqual(Array.from(reflectPlacement(matrix).elements));
    const same = matrix.clone();
    expect(Array.from(reflectPlacement(same, same).elements)).toEqual(Array.from(reflected.elements));
  });

  it('reflects a static placement and a baked track the same way as a matrix', () => {
    const instance = { position: { x: 0.9, y: 0, z: 0.35 }, rotation: { x: 10, y: -90, z: 5 } };
    const R = Math.PI / 180;
    const toMatrix = (placement: typeof instance) =>
      new HgMat4().compose(
        new HgVec3(placement.position.x, placement.position.y, placement.position.z),
        new HgQuat().setFromEulerXYZ(placement.rotation.x * R, placement.rotation.y * R, placement.rotation.z * R),
        new HgVec3(1, 1, 1),
      );
    const expected = reflectPlacement(toMatrix(instance));
    const actual = toMatrix(reflectedStaticPlacement(instance));
    for (let index = 0; index < 16; index += 1) expect(actual.elements[index]).toBeCloseTo(expected.elements[index], 12);

    const quaternion = new HgQuat().setFromEulerXYZ(0.3, -0.7, 0.2);
    const track = { position: [0.9, 1.2, 0.3], quaternion: quaternion.toArray() };
    reflectBakedTrack(track);
    const baked = new HgMat4().compose(new HgVec3(...track.position), new HgQuat(...track.quaternion), new HgVec3(1, 1, 1));
    const matrix = reflectPlacement(new HgMat4().compose(new HgVec3(0.9, 1.2, 0.3), quaternion, new HgVec3(1, 1, 1)));
    for (let index = 0; index < 16; index += 1) expect(baked.elements[index]).toBeCloseTo(matrix.elements[index], 12);
  });

  it('leaves an item already its own mirror image exactly as it was', () => {
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: -0.45 }, rotation: { x: 0, y: 180, z: 0 } })).toBe(true);
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 30, y: -180, z: 0 } })).toBe(true);
    expect(mirrorInvariant({ position: { x: 0.9, y: 0, z: 0 }, rotation: { x: 0, y: -90, z: 0 } })).toBe(false);
    expect(mirrorInvariant({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: -90, z: 0 } })).toBe(false);
    // And never writes −0 for a zero.
    const reflected = reflectedStaticPlacement({ position: { x: 0, y: 0, z: 0 }, rotation: { x: 0, y: 0, z: 0 } });
    expect(Object.is(reflected.position.x, 0) && Object.is(reflected.rotation.y, 0) && Object.is(reflected.rotation.z, 0)).toBe(true);
  });
});
