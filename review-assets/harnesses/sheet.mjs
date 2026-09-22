// Side-by-side before/after sheets from the matched stills.
import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const SETS = [
  ['curl_peak', 'Curl Peak 2.00s — fingertip shards', ['curl_peak_focus', 'curl_peak_under']],
  ['curl_bottom', 'Curl Bottom 0.00s — wrist-to-palm facet', ['curl_bottom_L', 'curl_bottom_R']],
  ['cross', 'Stressed hand/wrist in other exercises', ['press_hand', 'pushup_hand', 'pullup_hand']],
];

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
const url = (file) =>
  'data:image/png;base64,' +
  readFileSync(`/home/user/animation-software/scratchpad/repair/shots/${file}.png`).toString('base64');

for (const [name, title, views] of SETS) {
  const pairs = views.map((view) => [url(`v5_${view}`), url(`c035_${view}`), view]);
  const data = await page.evaluate(async ([pairs, title]) => {
    const load = (source) =>
      new Promise((resolve) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.src = source;
      });
    const cell = 460;
    const head = 56;
    const label = 30;
    const canvas = document.createElement('canvas');
    canvas.width = cell * 2 + 30;
    canvas.height = head + pairs.length * (cell + label) + 10;
    const context = canvas.getContext('2d');
    context.fillStyle = '#111';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#eee';
    context.font = 'bold 22px system-ui, sans-serif';
    context.fillText(title, 12, 32);
    context.font = '16px system-ui, sans-serif';
    for (let row = 0; row < pairs.length; row += 1) {
      const [before, after, view] = pairs[row];
      const [a, b] = await Promise.all([load(before), load(after)]);
      const top = head + row * (cell + label);
      context.fillStyle = '#9ad';
      context.fillText(`${view} — v5 (before)`, 12, top + 20);
      context.fillText(`${view} — candidate (after)`, cell + 22, top + 20);
      context.drawImage(a, 10, top + label, cell, cell);
      context.drawImage(b, cell + 20, top + label, cell, cell);
      context.strokeStyle = '#444';
      context.strokeRect(10, top + label, cell, cell);
      context.strokeRect(cell + 20, top + label, cell, cell);
    }
    return canvas.toDataURL('image/png');
  }, [pairs, title]);
  writeFileSync(
    `/home/user/animation-software/scratchpad/repair/shots/compare_${name}.png`,
    Buffer.from(data.split(',')[1], 'base64'),
  );
  console.log('sheet', name);
}
await browser.close();
