import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

describe('clip builder Three compatibility boundary', () => {
  it('keeps clipBuilder free of direct Three imports', () => {
    const source = readFileSync(new URL('./clipBuilder.ts', import.meta.url), 'utf8');
    expect(source).not.toMatch(/from ['"]three(?:\/|['"])/);
  });
});
