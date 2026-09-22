import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
await page.goto('http://localhost:5174/', { waitUntil: 'networkidle' });
await page.waitForTimeout(2500);

const selects = page.locator('.toolbar select');
console.log('exercises:', await selects.first().locator('option').allTextContents());
console.log('exercise values:', await selects.first().locator('option').evaluateAll((o) => o.map((x) => x.value)));
console.log('camera values:', await selects.nth(2).locator('option').evaluateAll((o) => o.map((x) => x.value)));

for (const exercise of ['dumbbell_bicep_curl', 'dumbbell_shoulder_press', 'push_up', 'pull_up']) {
  await selects.first().selectOption(exercise);
  await page.waitForTimeout(700);
  await page.locator('.studio__side--left .tabs button').nth(1).dispatchEvent('click');
  await page.waitForTimeout(400);
  const buttons = await page.locator('.studio__side--left button').allTextContents();
  console.log(`\n${exercise} grip-panel buttons:`, JSON.stringify(buttons));
}
await browser.close();
