import { readFileSync } from 'node:fs';

const parse = (path) => {
  const text = readFileSync(path, 'utf8');
  const start = text.indexOf('RING_MEASUREMENT');
  const body = text.slice(text.indexOf('{', start));
  return JSON.parse(body.slice(0, body.lastIndexOf('}') + 1));
};

const rows = process.argv.slice(2).map((path) => ({ path, data: parse(path) }));

const cell = (value, width = 9) => String(value).padStart(width);

console.log('bind checksum:', rows.map((row) => `${row.path.split('/').pop()}=${row.data.bindChecksum}`).join('  '));
console.log('ring triangles:', rows.map((row) => row.data.ringTriangles).join(' '));

for (const id of Object.keys(rows[0].data.exercises)) {
  console.log(`\n=== ${id}`);
  console.log(
    '  whole-rep strain p95/p99/max  ' +
      rows
        .map((row) => {
          const s = row.data.exercises[id].wholeRepStrain;
          return `${s.p95.toFixed(4)}/${s.p99.toFixed(4)}/${s.max.toFixed(4)}`;
        })
        .join('   '),
  );
  const labels = rows[0].data.exercises[id].samples.map((sample) => sample.label);
  console.log(
    `  ${'frame'.padEnd(10)}` +
      rows.map((row) => `${cell('minKeep', 9)}${cell('<25%', 6)}${cell('<40%', 6)}${cell('maxAsp', 9)}`).join(' |'),
  );
  labels.forEach((label, slot) => {
    const line = rows
      .map((row) => {
        const ring = row.data.exercises[id].samples[slot].rings;
        return `${cell(ring.minRetention.toFixed(4))}${cell(ring.below25, 6)}${cell(ring.below40, 6)}${cell(ring.maxAspect.toFixed(2))}`;
      })
      .join(' |');
    console.log(`  ${label.padEnd(10)}${line}`);
  });
}

// Curl-only grip and handle figures.
const curl = rows[0].data.exercises.dumbbell_bicep_curl;
if (curl) {
  console.log('\n=== curl grip / handle');
  curl.samples.forEach((sample, slot) => {
    const line = rows
      .map((row) => {
        const s = row.data.exercises.dumbbell_bicep_curl.samples[slot];
        const reach = s.grip?.l?.reachUse;
        const wrap = s.grip?.l?.wrapCoverageDeg;
        return `reach ${reach} wrap ${wrap} | handle L ${s.handle?.l?.penetrating}@${s.handle?.l?.minMm}mm R ${s.handle?.r?.penetrating}@${s.handle?.r?.minMm}mm`;
      })
      .join('   ||   ');
    console.log(`  ${sample.label.padEnd(10)} ${line}`);
  });
}
