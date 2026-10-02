import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

const script = resolve('scripts/audit-release-allowlist.mjs');

test('current software-shell allowlist accepts only index and hashed JS/CSS assets', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-release-shell-'));
  try {
    mkdirSync(join(root, 'dist', 'assets'), { recursive: true });
    writeFileSync(join(root, 'dist', 'index.html'), '<main>Home Gym PT</main>');
    writeFileSync(join(root, 'dist', 'assets', 'index-ABC123.js'), 'console.log("first party");');
    writeFileSync(join(root, 'dist', 'assets', 'index-ABC123.css'), 'body{}');
    writeFileSync(join(root, 'RELEASE_ASSET_ALLOWLIST.json'), JSON.stringify({
      mode: 'deny_by_default',
      approved_paths: ['index.html', 'assets/*.js', 'assets/*.css'],
      explicitly_denied_patterns: ['**/*.blend'],
    }));

    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 0, run.stdout);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'release_allowlist_audit.json'), 'utf8'));
    assert.equal(report.pass, true);
    assert.deepEqual(report.blockers.unapproved, []);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('software-shell allowlist does not pre-approve ORIGINAL v1 character paths', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-release-character-block-'));
  try {
    mkdirSync(join(root, 'dist', 'characters'), { recursive: true });
    writeFileSync(join(root, 'dist', 'index.html'), '<main>Home Gym PT</main>');
    writeFileSync(
      join(root, 'dist', 'characters', 'HomeGymPT_Male_ORIGINAL_v1.glb'),
      'not approved yet',
    );
    writeFileSync(join(root, 'RELEASE_ASSET_ALLOWLIST.json'), JSON.stringify({
      mode: 'deny_by_default',
      approved_paths: ['index.html', 'assets/*.js', 'assets/*.css'],
      explicitly_denied_patterns: [],
    }));

    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 1, run.stdout);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'release_allowlist_audit.json'), 'utf8'));
    assert.deepEqual(
      report.blockers.unapproved,
      ['characters/HomeGymPT_Male_ORIGINAL_v1.glb'],
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

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

test('release package refuses an allowlisted symbolic link to outside content', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-release-symlink-'));
  try {
    mkdirSync(join(root, 'dist'));
    writeFileSync(join(root, 'outside.txt'), 'external content');
    symlinkSync(join(root, 'outside.txt'), join(root, 'dist', 'approved.txt'));
    writeFileSync(join(root, 'RELEASE_ASSET_ALLOWLIST.json'), JSON.stringify({
      mode: 'deny_by_default', approved_paths: ['**'], explicitly_denied_patterns: [],
    }));
    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 1, run.stdout);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'release_allowlist_audit.json'), 'utf8'));
    assert.deepEqual(report.blockers.symlinkHits, ['approved.txt']);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('release gate requires deny-by-default policy mode', () => {
  const root = mkdtempSync(join(tmpdir(), 'hgpt-release-mode-'));
  try {
    mkdirSync(join(root, 'dist'));
    writeFileSync(join(root, 'dist', 'index.html'), '<main>Home Gym PT</main>');
    writeFileSync(join(root, 'RELEASE_ASSET_ALLOWLIST.json'), JSON.stringify({
      mode: 'allow_all', approved_paths: ['index.html'], explicitly_denied_patterns: [],
    }));
    const run = spawnSync(process.execPath, [script], { cwd: root, encoding: 'utf8' });
    assert.equal(run.status, 1, run.stdout);
    const report = JSON.parse(readFileSync(join(root, 'reports', 'release_allowlist_audit.json'), 'utf8'));
    assert.equal(report.blockers.wrongMode, true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
