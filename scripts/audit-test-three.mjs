#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const SRC = path.join(ROOT, 'src');
const imports = [];
const pattern = /(?:from\s+['"]three(?:\/[^'"]*)?['"]|import\s+['"]three(?:\/[^'"]*)?['"]|import\s*\(\s*['"]three(?:\/[^'"]*)?['"]\s*\))/g;

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(file);
      continue;
    }
    if (!/\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(entry.name)) continue;
    const text = fs.readFileSync(file, 'utf8');
    for (const match of text.matchAll(pattern)) {
      imports.push({
        file: path.relative(ROOT, file).replaceAll('\\', '/'),
        line: text.slice(0, match.index).split(/\r?\n/).length,
        statement: match[0],
      });
    }
  }
}

walk(SRC);
const operational = imports.filter(({ file }) =>
  !/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(file) &&
  !/(?:^|\/)tests?(?:\/|$)/i.test(file)
);
const testOnly = imports.filter(({ file }) => !operational.some((entry) =>
  entry.file === file && entry.line === entry.line && entry.statement === entry.statement
));

const report = {
  operationalCount: operational.length,
  testOnlyCount: testOnly.length,
  operational,
  testOnly,
};

fs.mkdirSync(path.join(ROOT, 'reports'), { recursive: true });
fs.writeFileSync(
  path.join(ROOT, 'reports', 'three_import_inventory.json'),
  JSON.stringify(report, null, 2) + '\n',
);

console.log(JSON.stringify(report, null, 2));
if (operational.length) process.exit(1);
