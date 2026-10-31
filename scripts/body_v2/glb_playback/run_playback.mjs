// Review-only GLB playback test in headless Chromium (Playwright + three.js; WebGL is software-rendered here, so the
// timings are a floor for comparison between candidates, not an iPhone measurement).
//
// usage: NODE_PATH=<global node_modules> node run_playback.mjs <model.glb> <three dir> <out dir> [fps]
//   <three dir> holds three.module.js and addons/loaders/GLTFLoader.js (three@0.170.0, from the npm tarball)
// Writes <out>/playback_report.json (load time, counts, per-clip frame render times), <out>/frames_<clip>_<view>_<n>.png
// (lockout etc.: the clip's first, middle and last frames) and <out>/points_<clip>_<n>.json (CPU-skinned positions,
// glTF Y-up, every k-th vertex) for comparison with Blender's evaluated mesh.
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync } from "node:fs";
import { join, dirname, extname, basename } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const [glb, threeDir, outDir, fpsArg] = process.argv.slice(2);
const fps = +(fpsArg || 24);
mkdirSync(outDir, { recursive: true });
const here = dirname(fileURLToPath(import.meta.url));
const root = join(outDir, "_site");
mkdirSync(join(root, "addons/loaders"), { recursive: true }); mkdirSync(join(root, "addons/utils"), { recursive: true });
copyFileSync(join(here, "page.html"), join(root, "index.html"));
copyFileSync(join(threeDir, "three.module.js"), join(root, "three.module.js"));
copyFileSync(join(threeDir, "addons/loaders/GLTFLoader.js"), join(root, "addons/loaders/GLTFLoader.js"));
if (existsSync(join(threeDir, "addons/utils/BufferGeometryUtils.js")))
  copyFileSync(join(threeDir, "addons/utils/BufferGeometryUtils.js"), join(root, "addons/utils/BufferGeometryUtils.js"));
const types = { ".html": "text/html", ".js": "text/javascript", ".glb": "model/gltf-binary" };
const server = createServer((req, res) => {
  const p = decodeURIComponent(req.url.split("?")[0]);
  const f = p === "/model.glb" ? glb : join(root, p === "/" ? "index.html" : p);
  try { const b = readFileSync(f); res.writeHead(200, { "content-type": types[extname(f)] || "application/octet-stream" }); res.end(b); }
  catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 540, height: 960 } });
const logs = []; page.on("console", m => logs.push(m.text())); page.on("pageerror", e => logs.push("ERROR " + e.message));
await page.goto(`http://127.0.0.1:${port}/?w=540&h=960`);
await page.waitForFunction(() => window.READY === true, null, { timeout: 60000 });
const info = await page.evaluate(() => window.loadModel("/model.glb"));
const report = { glb: basename(glb), bytes: readFileSync(glb).length, engine: "three@0.170.0 WebGL (headless Chromium, SwiftShader)", ...info, playback: {} };
for (const clip of info.clips) {
  const n = Math.round(clip.duration * fps) + 1, times = [];
  const keyFrames = [0, Math.floor((n - 1) / 2), n - 1];
  for (let i = 0; i < n; i++) {
    const t = Math.min(clip.duration, i / fps);
    const r = await page.evaluate(([c, t, s]) => window.frame(c, t, s, "front"), [clip.name, t, keyFrames.includes(i) ? 3000 : 0]);
    times.push(r.render_ms);
    if (r.points) writeFileSync(join(outDir, `points_${clip.name}_${i}.json`), JSON.stringify({ clip: clip.name, frame: i, t, points: r.points }));
    if (keyFrames.includes(i)) for (const view of ["front", "back", "side"]) {
      await page.evaluate(([c, t, v]) => window.frame(c, t, 0, v), [clip.name, t, view]);
      await page.screenshot({ path: join(outDir, `frames_${clip.name}_${view}_${i}.png`) });
    }
  }
  const s = [...times].sort((a, b) => a - b);
  report.playback[clip.name] = { frames: n, render_ms_median: s[Math.floor(s.length / 2)], render_ms_p95: s[Math.floor(s.length * 0.95)], render_ms_max: s[s.length - 1] };
}
report.console = logs.slice(0, 20);
writeFileSync(join(outDir, "playback_report.json"), JSON.stringify(report, null, 1));
console.log(JSON.stringify({ ...report, console: undefined }, null, 1));
await browser.close(); server.close();
