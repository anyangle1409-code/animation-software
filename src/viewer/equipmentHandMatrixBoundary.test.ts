import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('first-party hand matrix contract', () => {
  it('keeps character hand placement and equipment display maths off renderer matrices', () => {
    const types = readFileSync(new URL('../character/types.ts', import.meta.url), 'utf8');
    const retarget = readFileSync(new URL('../character/retargetSource.ts', import.meta.url), 'utf8');
    const display = readFileSync(new URL('./equipmentDisplayTransforms.ts', import.meta.url), 'utf8');

    expect(types).toContain('target: HgMat4');
    expect(types).not.toContain('CharacterMatrix4');
    expect(retarget).not.toContain('CharacterMatrix4');
    expect(display).toContain("from '../core/linearMath'");
    expect(display).not.toContain("from '../character/bones'");
  });

  it('keeps first-party matrices first-party in the live equipment scene', () => {
    const scene = readFileSync(
      new URL('./firstPartyEquipmentScene.ts', import.meta.url),
      'utf8',
    );
    expect(scene).toContain('instance.group.matrix.copy(placement.matrix)');
    expect(scene).not.toContain('fromArray(Array.from(placement.matrix.elements))');
  });
});
