// Shorts review: the hip region through the poses that stress it.
import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { mkdirSync } from 'node:fs';

const GLB = process.argv[2];
const TAG = process.argv[3];
const OUT = '/home/user/animation-software/scratchpad/repair/shorts';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 950 }, deviceScaleFactor: 2 });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);

const selects = page.locator('.toolbar select');
await selects.first().selectOption('air_squat');
await page.waitForTimeout(800);
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(400);
await page.locator('input[type=file]').setInputFiles(GLB);
await page.waitForTimeout(14000);
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(1500);
await selects.nth(1).selectOption('studio');
await page.waitForTimeout(600);

const seek = async (fraction) => {
  const track = page.locator('.timeline__track').first();
  const box = await track.boundingBox();
  await page.mouse.click(box.x + box.width * fraction, box.y + box.height / 2);
  await page.waitForTimeout(800);
  return (await page.locator('.timeline__time').first().textContent())?.trim();
};

const camera = async (name) => {
  await selects.nth(2).selectOption(name);
  await page.waitForTimeout(2000);
};

const shot = async (name, clip) => {
  await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(900);
  await page.screenshot({ path: `${OUT}/${TAG}_${name}.png`, clip });
  await page.locator('button', { hasText: 'Show panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(400);
  console.log('shot', name);
};

const BODY = { x: 420, y: 100, width: 660, height: 760 };
const HIPS = { x: 560, y: 380, width: 380, height: 340 };

const plan = [
  ['air_squat', [['stand', 0], ['half', 0.25], ['deep', 0.5]], ['front', 'left', 'rear']],
  ['dumbbell_bicep_curl', [['bottom', 0]], ['front', 'left']],
  ['dumbbell_shoulder_press', [['mid', 0.5]], ['front']],
  ['push_up', [['bottom', 0.45]], ['left', 'front']],
  ['pull_up', [['mid', 0.45]], ['front', 'left']],
];

for (const [exercise, frames, cameras] of plan) {
  await selects.first().selectOption(exercise);
  await page.waitForTimeout(1600);
  for (const [label, fraction] of frames) {
    const at = await seek(fraction);
    console.log(exercise, label, at);
    for (const view of cameras) {
      await camera(view);
      await shot(`${exercise}_${label}_${view}`, BODY);
      if (view === 'front' || view === 'left') {
        await shot(`${exercise}_${label}_${view}_hips`, HIPS);
      }
    }
  }
}

console.log('done', TAG);
await browser.close();
