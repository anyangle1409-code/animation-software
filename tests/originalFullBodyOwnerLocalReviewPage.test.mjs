import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../src/viewer/originalFullBodyOwnerLocalReview.html',import.meta.url),'utf8');
test('review UI requires local file selection and its exact original controller',()=>{
 assert.match(html,/type="file"/);
 assert.match(html,/bindOriginalFullBodyOwnerLocalControls/);
 assert.match(html,/from '\.\/firstPartyOriginalFullBodyLocalReview\.mjs'/);
});
test('all five bounded review directions offered',()=>{
 for(const v of ['front','rear','left','right','three-quarter'])
 assert.match(html,new RegExp('value="'+v+'"'));
});
test('owner page does not load remote scripts or include private model',()=>{
 assert.doesNotMatch(html,/<script[^>]+src=/i);
 assert.doesNotMatch(html,/https?:\/\/|fetch\s*\(|\.glb["']|base64,/i);
 assert.match(html,/never uploaded/);
});
test('preserves mobile-friendly zoom and keyboard form control font size',()=>{
 assert.match(html,/width=device-width/);
 assert.doesNotMatch(html,/user-scalable=no|maximum-scale=1/i);
 assert.match(html,/font-size:16px/);
});
test('local preview disposes GPU on page exit',()=>{
 assert.match(html,/pagehide/);assert.match(html,/controls\.dispose\(\)/);
});
