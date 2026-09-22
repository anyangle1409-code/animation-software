import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';
const GLB = '/home/user/animation-software/scratchpad/candidate/HomeGymPT_Male_HAND_WRIST_WEIGHT_CANDIDATE.glb';
const SPEED = process.argv[2] || '1';
const TAG = process.argv[3] || 'normal';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1 });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);
await page.locator('.toolbar select').first().selectOption('dumbbell_bicep_curl');
await page.waitForTimeout(800);
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(400);
await page.locator('input[type=file]').setInputFiles(GLB);
await page.waitForTimeout(12000);
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(1200);
const selects = page.locator('.toolbar select');
await selects.nth(1).selectOption('void');
await selects.nth(2).selectOption('three_quarter');
await page.waitForTimeout(2200);
const speedSelect = page.locator('.timeline select').first();
await speedSelect.selectOption(SPEED).catch(async () => { console.log('speed options:', await speedSelect.locator('option').allTextContents()); });
await page.waitForTimeout(400);
await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
await page.waitForTimeout(800);
await page.locator('button', { hasText: /^Play$/ }).first().dispatchEvent('click');
const shots = [];
const total = 5.5 / Number(SPEED);
const count = 24;
for (let i = 0; i < count; i += 1) {
  await page.waitForTimeout((total * 1000) / count);
  const buf = await page.screenshot({ clip: { x: 330, y: 120, width: 540, height: 660 } });
  shots.push('data:image/png;base64,' + buf.toString('base64'));
}
// contact sheet
const sheet = await page.evaluate(async (shots) => {
  const load = (s) => new Promise((r) => { const i = new Image(); i.onload = () => r(i); i.src = s; });
  const imgs = await Promise.all(shots.map(load));
  const cols = 6, rows = Math.ceil(imgs.length / cols), w = 270, h = 330;
  const c = document.createElement('canvas'); c.width = cols * w; c.height = rows * h;
  const x = c.getContext('2d');
  x.fillStyle = '#000'; x.fillRect(0, 0, c.width, c.height);
  imgs.forEach((img, i) => {
    x.drawImage(img, (i % cols) * w, Math.floor(i / cols) * h, w, h);
    x.fillStyle = '#6f6'; x.font = '16px monospace';
    x.fillText(String(i + 1), (i % cols) * w + 6, Math.floor(i / cols) * h + 20);
  });
  return c.toDataURL('image/png');
}, shots);
writeFileSync(`/home/user/animation-software/scratchpad/repair/shots/playback_cand_${TAG}.png`, Buffer.from(sheet.split(',')[1], 'base64'));
console.log('sheet written', TAG);
await browser.close();
