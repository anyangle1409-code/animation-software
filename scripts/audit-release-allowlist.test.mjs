import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const script = resolve('scripts/audit-release-allowlist.mjs');

test('recursive deny patterns catch files at root and nested release paths', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-release-glob-'));
  try {
    mkdirSync(join(root, 'dist', 'nested'), { recursive: true });
    writeFileSync(join(root, 'dist', 'old.blend'), 'reference only');
    writeFileSync(join(root, 'dist', 'nested', 'old.blend'), 'reference only');
    writeFileSync(join(root, 'RELEASE_ASSET_ALLOWLIST.json'), JSON.stringify({
      mode: 'deny_by_default', approved_paths: ['**'], explicitly_denied_patterns: ['**/*.blend'],
    }));
    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 1, run.stdout);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'release_allowlist_audit.json'), 'utf8'));
    assert.deepEqual(report.blockers.deniedHits.map(x => x.file), ['nested/old.blend', 'old.blend']);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
