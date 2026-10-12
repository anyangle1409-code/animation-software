import {bindOriginalFullBodyOwnerLocalControls}
  from './firstPartyOriginalFullBodyLocalReview.mjs';
const controls=bindOriginalFullBodyOwnerLocalControls({
  fileInput:document.getElementById('original-file'),
  cameraSelector:document.getElementById('camera-view'),
  canvas:document.getElementById('review-canvas'),
  statusTarget:document.getElementById('review-status'),
});
window.addEventListener('pagehide',()=>controls.dispose(),{once:true});
