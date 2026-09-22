// Matched before/after stills for the hand/wrist weight repair.
//
// Same Studio, same document, same cameras; only the imported GLB differs, so
// a difference between two runs is a difference in the asset.
import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { mkdirSync } from 'node:fs';

const GLB = process.argv[2];
const TAG = process.argv[3];
const OUT = '/home/user/animation-software/scratchpad/repair/shots';
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 950 }, deviceScaleFactor: 3 });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);

const selects = page.locator('.toolbar select');
await selects.first().selectOption('dumbbell_bicep_curl');
await page.waitForTimeout(800);
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(400);
await page.locator('input[type=file]').setInputFiles(GLB);
await page.waitForTimeout(14000);
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(1500);
await selects.nth(1).selectOption('void');
await page.waitForTimeout(500);

const exercise = async (id) => {
  await selects.first().selectOption(id);
  await page.waitForTimeout(1600);
};

const curlFrame = async (name) => {
  await page.locator('.studio__side--left .tabs button').nth(1).dispatchEvent('click');
  await page.waitForTimeout(500);
  await page
    .locator('.studio__side--left button', { hasText: new RegExp(`^${name}$`) })
    .first()
    .dispatchEvent('click');
  await page.waitForTimeout(1000);
};

/** Scrub the timeline track to a fraction of the clip. */
const seek = async (fraction) => {
  const track = page.locator('.timeline__track').first();
  const box = await track.boundingBox();
  await page.mouse.click(box.x + box.width * fraction, box.y + box.height / 2);
  await page.waitForTimeout(900);
  return (await page.locator('.timeline__time').first().textContent())?.trim();
};

const focusOn = async (bone) => {
  await page.locator('.studio__side--left .tabs button').nth(0).dispatchEvent('click');
  await page.waitForTimeout(400);
  await page.locator('.studio__side--left select').first().selectOption(bone);
  await page.waitForTimeout(600);
  await selects.nth(2).selectOption('focus');
  await page.waitForTimeout(2800);
  // Deselect, so the rotation gizmo is not drawn over the joint under review;
  // the focus camera keeps the placement it has already settled into.
  await page.locator('.studio__side--left select').first().selectOption('');
  await page.waitForTimeout(1200);
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

const shot = async (name, clip) => {
  await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/${TAG}_${name}.png`, clip });
  await page.locator('button', { hasText: 'Show panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(500);
  console.log('shot', name);
};

const HAND = { x: 590, y: 300, width: 340, height: 340 };
const BODY = { x: 430, y: 120, width: 640, height: 720 };

// Neutral reference: the whole figure, so a repair that disturbed anything
// outside the hands would show.
await curlFrame('Bottom');
await selects.nth(2).selectOption('front');
await page.waitForTimeout(2400);
await shot('rest_front', BODY);

// A — fingertip shards at curl Peak.
await curlFrame('Peak');
await focusOn('hand_l');
await shot('curl_peak_focus', HAND);
await orbit(0, 160);
await shot('curl_peak_under', HAND);

// B — wrist-to-palm facet at curl Bottom, both hands.
await curlFrame('Bottom');
await focusOn('hand_l');
await shot('curl_bottom_L', HAND);
await orbit(140, 60);
await shot('curl_bottom_L_orbit', HAND);
await curlFrame('Bottom');
await focusOn('hand_r');
await shot('curl_bottom_R', HAND);

// Cross-exercise stressed hand/wrist poses.
for (const [id, fraction, label] of [
  ['dumbbell_shoulder_press', 0.5, 'press'],
  ['push_up', 0.45, 'pushup'],
  ['pull_up', 0.45, 'pullup'],
]) {
  await exercise(id);
  const at = await seek(fraction);
  console.log(label, 'playhead', at);
  await focusOn('hand_l');
  await shot(`${label}_hand`, HAND);
  await orbit(120, 90);
  await shot(`${label}_hand_orbit`, HAND);
}

console.log('done', TAG);
await browser.close();
