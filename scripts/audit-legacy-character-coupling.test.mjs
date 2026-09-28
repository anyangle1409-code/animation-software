import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const script = resolve('scripts/audit-legacy-character-coupling.mjs');

test('legacy coupling report excludes tests but retains operational source', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-legacy-scan-'));
  try {
    mkdirSync(join(root, 'src', 'tests'), { recursive: true });
    writeFileSync(join(root, 'src', 'live.ts'), 'const provenance = "MakeHuman";\n');
    writeFileSync(join(root, 'src', 'ignored.test.ts'), 'const fixture = "MakeHuman";\n');
    writeFileSync(join(root, 'src', 'tests', 'helper.ts'), 'const fixture = "MakeHuman";\n');
    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 0, run.stderr);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'legacy_character_coupling.json'), 'utf8'));
    assert.deepEqual(report.byToken.MakeHuman.files, ['src/live.ts']);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
