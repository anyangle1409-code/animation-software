import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { mkdirSync } from 'node:fs';
const GLB = process.argv[2], TAG = process.argv[3];
const OUT = '/home/user/animation-software/scratchpad/repair/rear';
mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1500, height: 950 }, deviceScaleFactor: 4 });
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
await selects.nth(1).selectOption('void');
await page.waitForTimeout(600);
const track = page.locator('.timeline__track').first();
const box = await track.boundingBox();
const seek = async (f) => { await page.mouse.click(box.x + box.width * f, box.y + box.height/2); await page.waitForTimeout(900); };
const shot = async (name, clip) => {
  await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/${TAG}_${name}.png`, clip });
  await page.locator('button', { hasText: 'Show panels' }).first().dispatchEvent('click');
  await page.waitForTimeout(400);
  console.log('shot', name);
};
for (const [f, label] of [[0,'stand'],[0.5,'deep']]) {
  await seek(f);
  await selects.nth(2).selectOption('rear');
  await page.waitForTimeout(2300);
  await shot(`waist_${label}_rear`, { x: 640, y: 470, width: 240, height: 150 });
}
await browser.close();
