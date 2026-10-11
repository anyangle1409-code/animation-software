/** First-party provisional scene compatibility gate. */
export const PROVISIONAL_SCENE_KIND='hgpt-g4-provisional-scene-v1';
export function requireProvisionalStatus(status){
  if(status!=='PROVISIONAL_FUNCTIONAL')throw new RangeError('Provisional-only model status required');
  return true;
}
