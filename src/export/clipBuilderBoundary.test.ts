import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('legacy clip builder containment', () => {
  it('keeps clipBuilder free of direct Three imports', () => {
    const source = readFileSync(new URL('./clipBuilder.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
  });

  it('keeps the live equipment viewer off the legacy clip builder', () => {
    const source = readFileSync(
      new URL('../viewer/equipmentDisplayTransforms.ts', import.meta.url),
      'utf8',
    );
    expect(source).not.toContain("../export/clipBuilder");
    expect(source).toContain('handAttachmentLocalMatrix');
  });

  it('does not expose the legacy clip builder from the production export barrel', () => {
    const source = readFileSync(new URL('./index.ts', import.meta.url), 'utf8');
    expect(source).not.toContain("export * from './clipBuilder'");
  });
});
