import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('character build Three compatibility boundary', () => {
  it('keeps build.ts free of direct Three imports', () => {
    const source = readFileSync(new URL('./build.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
  });
});
