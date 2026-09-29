import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = (relative: string) =>
  readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('retarget first-party math boundary', () => {
  it('keeps retarget movement maths on the Home Gym PT algebra layer', () => {
    const retarget = source('./retarget.ts');
    expect(retarget).toContain("from '../core/linearMath'");
    expect(retarget).not.toMatch(/createCharacter(?:Euler|Matrix|Quaternion|Vector3)/);
    expect(retarget).not.toMatch(/type Character(?:Matrix4|Quaternion|Vector3)/);
  });

  it('keeps imported hand-frame maths first-party until the renderer-target copy', () => {
    const character = source('../character/retargetSource.ts');
    expect(character).toContain("from '../core/linearMath'");
    expect(character).not.toMatch(/createCharacter(?:Quaternion|Vector3)/);
    expect(character).toContain('copyCharacterMatrix(scratch.output, target)');
  });
});
