import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const srcRoot = fileURLToPath(new URL('../', import.meta.url));
const repoRoot = fileURLToPath(new URL('../../', import.meta.url));

const operationalFiles = (dir: string, out: string[] = []): string[] => {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!/^tests?$/i.test(entry.name)) operationalFiles(path, out);
      continue;
    }
    if (!/\.(?:ts|tsx|js|jsx|mts|mjs)$/.test(entry.name)) continue;
    if (/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(entry.name)) continue;
    out.push(path);
  }
  return out;
};

describe('zero operational Three runtime seam', () => {
  it('has no direct Three imports in operational source', () => {
    const offenders: string[] = [];
    const importPattern =
      /(?:from\s+['"]three(?:\/[^'"]*)?['"]|import\s+['"]three(?:\/[^'"]*)?['"]|import\s*\(\s*['"]three(?:\/[^'"]*)?['"]\s*\))/;
    for (const file of operationalFiles(srcRoot)) {
      if (importPattern.test(readFileSync(file, 'utf8'))) {
        offenders.push(relative(repoRoot, file).replaceAll('\\', '/'));
      }
    }
    expect(offenders).toEqual([]);
  });

  it('removes the superseded Three viewer gateways from production source', () => {
    for (const relativePath of [
      'core/threeRuntimeBoundary.ts',
      'viewer/threeSceneBoundary.ts',
      'viewer/threeRendererAdapter.ts',
      'viewer/threeSceneHost.ts',
    ]) {
      expect(existsSync(join(srcRoot, relativePath)), relativePath).toBe(false);
    }
  });

  it('keeps runtime dependency and source ceilings at zero', () => {
    const pkg = JSON.parse(readFileSync(join(repoRoot, 'package.json'), 'utf8')) as {
      dependencies?: Record<string, string>;
      devDependencies?: Record<string, string>;
    };
    const allowlist = JSON.parse(
      readFileSync(join(repoRoot, 'RUNTIME_MIGRATION_ALLOWLIST.json'), 'utf8'),
    ) as {
      allowed_existing_runtime_dependencies: string[];
      source_import_ceilings: { three: { max_imports: number; allowed_files: string[] } };
    };
    expect(pkg.dependencies ?? {}).toEqual({});
    expect(pkg.devDependencies?.three).toBeUndefined();
    expect(pkg.devDependencies?.['@types/three']).toBeUndefined();
    expect(allowlist.allowed_existing_runtime_dependencies).toEqual([]);
    expect(allowlist.source_import_ceilings.three).toMatchObject({
      max_imports: 0,
      allowed_files: [],
    });
  });
});
