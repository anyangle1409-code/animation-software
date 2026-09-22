import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { mkdirSync } from 'node:fs';

const GLB = process.argv[2];
const TAG = process.argv[3];
const OUT = '/home/user/animation-software/scratchpad/repair/rear';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 950 }, deviceScaleFactor: 2 });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);

const selects = page.locator('.toolbar select');
console.log('backdrops:', await selects.nth(1).locator('option').evaluateAll((o) => o.map((x) => x.value)));

await selects.first().selectOption('air_squat');
await page.waitForTimeout(800);
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(400);
await page.locator('input[type=file]').setInputFiles(GLB);
await page.waitForTimeout(14000);
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(1500);

const track = page.locator('.timeline__track').first();
const box = await track.boundingBox();
await page.mouse.click(box.x + box.width * 0.5, box.y + box.height / 2);
await page.waitForTimeout(900);
console.log('playhead', (await page.locator('.timeline__time').first().textContent())?.trim());

const shot = async (name, clip) => {
  await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/${TAG}_${name}.png`, clip });
  await page.locator('button', { hasText: 'Show panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(400);
  console.log('shot', name);
};

const fromRear = async (dx, dy) => {
  await selects.nth(2).selectOption('rear');
  await page.waitForTimeout(2200);
  if (dx || dy) {
    await selects.nth(2).selectOption('free');
    await page.waitForTimeout(500);
    await page.mouse.move(750, 450);
    await page.mouse.down();
    await page.mouse.move(750 + dx, 450 + dy, { steps: 20 });
    await page.mouse.up();
    await page.waitForTimeout(1400);
  }
};

const SEAT = { x: 560, y: 340, width: 400, height: 360 };
const BODY = { x: 430, y: 120, width: 640, height: 740 };

// The void backdrop is rim-lit, which is the only lighting in the studio that
// reaches a figure from behind.
await selects.nth(1).selectOption('void');
await page.waitForTimeout(700);
await fromRear(0, 0);
await shot('rear_void_body', BODY);
await shot('rear_void_seat', SEAT);

for (const [dx, label] of [[70, 'left45'], [-70, 'right45']]) {
  await fromRear(dx, 0);
  await shot(`rear_void_${label}_seat`, SEAT);
}

// Slightly above and behind, which is where a gap at the seat would read.
await fromRear(0, -70);
await shot('rear_void_high_seat', SEAT);

console.log('done', TAG);
await browser.close();
