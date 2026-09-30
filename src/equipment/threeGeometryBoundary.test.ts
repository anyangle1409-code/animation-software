import { existsSync, readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = (relative: string) =>
  readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('first-party equipment boundary', () => {
  it('keeps the export helper free of direct Three imports', () => {
    expect(source('../export/rigBuilder.ts')).not.toMatch(/from ['"]three(?:\/|['"])/);
  });

  it('removes the legacy equipment scene and keeps the live scene first-party', () => {
    const legacy = new URL('../viewer/equipmentScene.ts', import.meta.url);
    expect(existsSync(legacy)).toBe(false);
    const live = source('../viewer/firstPartyEquipmentScene.ts');
    expect(live).not.toMatch(/from ['"]three(?:\/|['"])/);
    expect(live).toContain('HgPrimitiveMesh');
    expect(live).toContain('instance.group.matrix.copy(placement.matrix)');
  });
});
