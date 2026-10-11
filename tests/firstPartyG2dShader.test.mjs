import test from 'node:test';
import assert from 'node:assert/strict';
import {G2D_VERTEX,G2D_FRAGMENT,G2D_KIND} from '../src/viewer/firstPartyG2dShader.mjs';
test('G2d source shader keeps GPU palette, source UV and normal output',()=>{
  assert.match(G2D_VERTEX,/texelFetch\(uPalette/);
  assert.match(G2D_VERTEX,/vWorldNormal=normalize\(n\)/);
  assert.match(G2D_FRAGMENT,/texture\(uColor,vUV\)/);
  assert.match(G2D_KIND,/native-moving-source-png/);
});
