// The one view left unjudged: the deepest squat from behind, on a backdrop
// that actually lights the seat. The studio backdrop back-lights it, which is
// why the earlier rear capture was not a fair test.
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
await selects.first().selectOption('air_squat');
await page.waitForTimeout(800);
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(400);
await page.locator('input[type=file]').setInputFiles(GLB);
await page.waitForTimeout(14000);
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(1500);

const seek = async (fraction) => {
  const track = page.locator('.timeline__track').first();
  const box = await track.boundingBox();
  await page.mouse.click(box.x + box.width * fraction, box.y + box.height / 2);
  await page.waitForTimeout(900);
  return (await page.locator('.timeline__time').first().textContent())?.trim();
};

const shot = async (name, clip) => {
  await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/${TAG}_${name}.png`, clip });
  await page.locator('button', { hasText: 'Show panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(400);
  console.log('shot', name);
};

const orbit = async (dx, dy) => {
  await selects.nth(2).selectOption('free');
  await page.waitForTimeout(500);
  await page.mouse.move(750, 450);
  await page.mouse.down();
  await page.mouse.move(750 + dx, 450 + dy, { steps: 20 });
  await page.mouse.up();
  await page.waitForTimeout(1400);
};

const BODY = { x: 420, y: 100, width: 660, height: 760 };
const SEAT = { x: 540, y: 330, width: 420, height: 380 };

console.log('deepest squat at', await seek(0.5));

for (const backdrop of ['study', 'light']) {
  await selects.nth(1).selectOption(backdrop);
  await page.waitForTimeout(700);
  await selects.nth(2).selectOption('rear');
  await page.waitForTimeout(2400);
  await shot(`deepSquat_rear_${backdrop}`, BODY);
  await shot(`deepSquat_rear_${backdrop}_seat`, SEAT);
}

// A rear three-quarter, where a gap at the seat or the inseam would show.
await selects.nth(1).selectOption('study');
await page.waitForTimeout(600);
await selects.nth(2).selectOption('rear');
await page.waitForTimeout(2200);
await orbit(210, 40);
await shot('deepSquat_rearThreeQuarter_study', BODY);
await shot('deepSquat_rearThreeQuarter_study_seat', SEAT);

// And from below and behind, the hardest angle for an inseam.
await orbit(-120, -150);
await shot('deepSquat_rearLow_study', BODY);
await shot('deepSquat_rearLow_study_seat', SEAT);

console.log('done', TAG);
await browser.close();
