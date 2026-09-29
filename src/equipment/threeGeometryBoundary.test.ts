import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const source = (relative: string) =>
  readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('equipment Three compatibility boundary', () => {
  it('keeps the export helper free of direct Three imports', () => {
    expect(source('../export/rigBuilder.ts')).not.toMatch(/from ['"]three(?:\/|['"])/);
  });

  it('keeps the viewer equipment scene free of direct Three imports', () => {
    expect(source('../viewer/equipmentScene.ts')).not.toMatch(/from ['"]three(?:\/|['"])/);
  });
});
