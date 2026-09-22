import { chromium } from '/home/user/animation-software/node_modules/playwright/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const DIR = '/home/user/animation-software/scratchpad/repair/shorts';
const SETS = [
  [
    'shorts_squat',
    'Bodyweight squat — standing, half depth, deepest (front, side, rear)',
    [
      ['air_squat_stand_front', 'standing · front'],
      ['air_squat_half_front', 'half depth · front'],
      ['air_squat_deep_front', 'deepest · front'],
      ['air_squat_stand_left', 'standing · side'],
      ['air_squat_half_left', 'half depth · side'],
      ['air_squat_deep_left', 'deepest · side'],
    ],
  ],
  [
    'shorts_hips',
    'Hip and groin close-ups through the squat',
    [
      ['air_squat_stand_front_hips', 'standing · front'],
      ['air_squat_deep_front_hips', 'deepest · front'],
      ['air_squat_deep_left_hips', 'deepest · side'],
    ],
  ],
  [
    'shorts_other',
    'Curl, shoulder press, push-up, pull-up',
    [
      ['dumbbell_bicep_curl_bottom_front', 'curl bottom'],
      ['dumbbell_shoulder_press_mid_front', 'shoulder press'],
      ['push_up_bottom_left', 'push-up bottom'],
      ['pull_up_mid_front', 'pull-up'],
    ],
  ],
];

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium',
  args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--disable-gpu-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 900, height: 600 } });
const url = (file) => 'data:image/png;base64,' + readFileSync(`${DIR}/s3_${file}.png`).toString('base64');

for (const [name, title, views] of SETS) {
  const cells = views.map(([file, label]) => [url(file), label]);
  const data = await page.evaluate(async ([cells, title]) => {
    const load = (source) =>
      new Promise((resolve) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.src = source;
      });
    const columns = Math.min(3, cells.length);
    const rows = Math.ceil(cells.length / columns);
    const width = 400;
    const height = 460;
    const label = 26;
    const head = 46;
    const canvas = document.createElement('canvas');
    canvas.width = columns * width + 20;
    canvas.height = head + rows * (height + label) + 10;
    const context = canvas.getContext('2d');
    context.fillStyle = '#111';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#eee';
    context.font = 'bold 21px system-ui, sans-serif';
    context.fillText(title, 12, 30);
    context.font = '15px system-ui, sans-serif';
    for (let slot = 0; slot < cells.length; slot += 1) {
      const [source, caption] = cells[slot];
      const image = await load(source);
      const column = slot % columns;
      const row = Math.floor(slot / columns);
      const x = 10 + column * width;
      const y = head + row * (height + label);
      context.fillStyle = '#9ad';
      context.fillText(caption, x + 2, y + 18);
      const scale = Math.min(width / image.width, height / image.height);
      context.drawImage(
        image,
        x + (width - image.width * scale) / 2,
        y + label,
        image.width * scale,
        image.height * scale,
      );
    }
    return canvas.toDataURL('image/png');
  }, [cells, title]);
  writeFileSync(`${DIR}/${name}.png`, Buffer.from(data.split(',')[1], 'base64'));
  console.log('sheet', name);
}
await browser.close();
