import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../../src/rig/skeleton';
import { retargetedCharacterSource } from '../../src/character/retargetSource';

describe('bone names as the runtime sees them', () => {
  it('prints hand-area bone names', async () => {
    const bytes = readFileSync(process.env.GLB!);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const source = retargetedCharacterSource({ id: 'names', label: 'Names', data });
    const character = await source.build(canonicalSkeleton);
    const mesh = character.meshes[0];
    const names = mesh.skeleton.bones.map((bone) => bone.name);
    console.log('bones', names.length);
    console.log(names.filter((name) => /hand|forearm|f_|palm|thumb/i.test(name)).join(' | '));
    const skinIndex = mesh.geometry.getAttribute('skinIndex');
    console.log('skinIndex itemSize', skinIndex.itemSize, 'count', skinIndex.count);
    console.log('attributes', Object.keys(mesh.geometry.attributes).join(','));
    expect(names.length).toBeGreaterThan(0);
    character.dispose();
  });
});
