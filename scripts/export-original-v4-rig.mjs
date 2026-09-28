#!/usr/bin/env node
import { build } from 'esbuild';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const { outputFiles } = await build({
  entryPoints: [resolve(root, 'src/rig/canonicalV4OriginalExport.ts')],
  bundle: true, platform: 'node', format: 'esm', write: false,
});
const { originalV4RigData } = await import(`data:text/javascript;base64,${Buffer.from(outputFiles[0].contents).toString('base64')}`);
const output = resolve(root, 'ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json');
const data = JSON.stringify(originalV4RigData(), null, 2) + '\n';
if (process.argv.includes('--check')) {
  if (readFileSync(output, 'utf8') !== data) throw new Error(`Stale v4 rig export: ${output}`);
  console.log(`Verified ${output}`);
} else {
  writeFileSync(output, data);
  console.log(`Exported ${output}`);
}
