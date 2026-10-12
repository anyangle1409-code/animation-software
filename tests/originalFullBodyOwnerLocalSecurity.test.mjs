import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../src/viewer/originalFullBodyOwnerLocalReview.html',import.meta.url),'utf8');
const boot=readFileSync(new URL('../src/viewer/originalFullBodyOwnerLocalReviewBoot.mjs',import.meta.url),'utf8');
test('owner review prevents network connections, submissions and plugin objects',()=>{
 assert.match(html,/connect-src &#39;none&#39;/);
 assert.match(html,/form-action &#39;none&#39;/);
 assert.match(html,/object-src &#39;none&#39;/);
 assert.match(html,/default-src &#39;none&#39;/);
 assert.match(html,/script-src &#39;self&#39;/);
});
test('browser security policy needs a local external module entry, not inline JS',()=>{
 assert.match(html,/<script type="module" src="\.\/originalFullBodyOwnerLocalReviewBoot\.mjs"><\/script>/);
 assert.doesNotMatch(html,/<script(?: [^>]*)?>\s*(?:import|const|let|function)/);
 assert.match(boot,/bindOriginalFullBodyOwnerLocalControls/);
 assert.match(boot,/pagehide/);
});
test('no remote addresses or private asset literals introduced by boot module',()=>{
 assert.doesNotMatch(boot,/https?:\/\/|fetch\s*\(|XMLHttpRequest|WebSocket|\.glb/);
 assert.match(html,/type="file"/);
});
