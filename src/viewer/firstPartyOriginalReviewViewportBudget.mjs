/** First-party owner review drawing-buffer budget (not device benchmark). */
export function boundedOriginalReviewViewport(width,height,pixelRatio=1){
 if(!Number.isInteger(width)||!Number.isInteger(height)||
    width<160||height<160||width>2000||height>2400||
    !Number.isFinite(pixelRatio)||pixelRatio<0.5||pixelRatio>2)
  throw new RangeError('original owner viewport outside documented bounds');
 const maxPixels=2_000_000;
 const scale=Math.min(pixelRatio,Math.sqrt(maxPixels/(width*height)));
 // At pixelRatio >= 0.5 the minimum logical viewport remains visible.
 const effectiveDpr=Math.max(0.5,scale);
 const pixels=Math.floor(width*effectiveDpr)*Math.floor(height*effectiveDpr);
 return Object.freeze({width,height,pixelRatio:effectiveDpr,
   drawingBufferPixels:pixels,estimatedRgba8Bytes:pixels*4,
   qualityReduced:effectiveDpr<pixelRatio,maxPixels});
}
