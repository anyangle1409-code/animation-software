import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader','--enable-unsafe-swiftshader','--disable-gpu-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1500, height: 950 }, deviceScaleFactor: 2 });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(String(e)));
page.on('requestfailed', (r) => errors.push('FAILED ' + r.url()));
page.on('response', (r) => { if (r.status() >= 400) errors.push(r.status() + ' ' + r.url()); });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(16000);
// Which character sources does the studio offer, and which is active?
await page.locator('.studio__side--left .tabs button').nth(5).dispatchEvent('click');
await page.waitForTimeout(700);
const selects = page.locator('.studio__side--left select');
const n = await selects.count();
for (let i = 0; i < n; i += 1) {
  const opts = await selects.nth(i).locator('option').evaluateAll((o) => o.map((x) => `${x.value}:${x.textContent}`));
  if (opts.length && opts.some((o) => /baseline|Procedural|Built/i.test(o))) {
    console.log('character source options:', opts.join(' | '));
    console.log('selected:', await selects.nth(i).inputValue());
  }
}
await page.locator('.segmented button', { hasText: /^Character$/ }).click();
await page.waitForTimeout(3000);
await page.locator('.toolbar select').first().selectOption('air_squat');
await page.waitForTimeout(1200);
await page.locator('.toolbar select').nth(2).selectOption('front');
await page.waitForTimeout(2500);
await page.locator('button', { hasText: 'Hide panels' }).first().dispatchEvent('click');
await page.waitForTimeout(1200);
await page.screenshot({ path: '/home/user/animation-software/scratchpad/repair/rear/boot_default.png',
  clip: { x: 430, y: 100, width: 660, height: 760 } });
console.log('console errors:', errors.length ? errors.slice(0, 5) : 'none');
await browser.close();
