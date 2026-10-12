import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../src/viewer/originalFullBodyOwnerLocalReview.html',import.meta.url),'utf8');
const boot=readFileSync(new URL('../src/viewer/originalFullBodyOwnerLocalReviewBoot.mjs',import.meta.url),'utf8');
test('review UI requires local file selection and its exact original controller',()=>{
 assert.match(html,/type="file"/);
 assert.ok(html.includes('src="./originalFullBodyOwnerLocalReviewBoot.mjs"'));
 assert.ok(boot.includes("from './firstPartyOriginalFullBodyLocalReview.mjs'"));
 assert.ok(boot.includes('bindOriginalFullBodyOwnerLocalControls'));
});
test('all five bounded review directions offered',()=>{
 for(const view of ['front','rear','left','right','three-quarter'])
 assert.ok(html.includes('value="'+view+'"'));
});
test('owner page does not load remote scripts or include private model',()=>{
 assert.doesNotMatch(html,/<script[^>]+src="https?:/i);
 assert.doesNotMatch(html,/https?:\/\/|fetch\s*\(|base64,/i);
 assert.match(html,/never uploaded/);
});
test('preserves mobile-friendly zoom and keyboard form control font size',()=>{
 assert.match(html,/width=device-width/);
 assert.doesNotMatch(html,/user-scalable=no|maximum-scale=1/i);
 assert.match(html,/font-size:16px/);
});
test('local preview disposes GPU on page exit through local boot module',()=>{
 assert.match(boot,/pagehide/);
 assert.ok(boot.includes('controls.dispose()'));
});
