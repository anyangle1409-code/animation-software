import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('posed mesh renderer-vector containment', () => {
  it('keeps contact solving on first-party vectors and skinning inside posedMesh', () => {
    const contact = readFileSync(new URL('./retargetContact.ts', import.meta.url), 'utf8');
    const posed = readFileSync(new URL('./posedMesh.ts', import.meta.url), 'utf8');

    expect(contact).toContain('skinnedBindVertexPoint');
    expect(contact).not.toContain('createCharacterVector3');
    expect(posed).toContain('const firstPartyBindSkinScratch = createCharacterVector3()');
    expect(posed).toContain('mesh.applyBoneTransform(index, firstPartyBindSkinScratch)');
  });
});
