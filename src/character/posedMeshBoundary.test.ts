import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('posed mesh first-party skinning boundary', () => {
  it('keeps contact and posed-mesh deformation off renderer vectors and skinning helpers', () => {
    const contact = readFileSync(new URL('./retargetContact.ts', import.meta.url), 'utf8');
    const posed = readFileSync(new URL('./posedMesh.ts', import.meta.url), 'utf8');
    const bones = readFileSync(new URL('./bones.ts', import.meta.url), 'utf8');

    expect(contact).toContain('skinnedBindVertexPoint');
    expect(contact).not.toContain('createCharacterVector3');
    expect(posed).toContain("from './skinningMath'");
    expect(posed).not.toMatch(/applyBoneTransform|getVertexPosition|createCharacterVector3/);
    expect(bones).not.toMatch(/CharacterVector3|createCharacterVector3/);
  });
});
