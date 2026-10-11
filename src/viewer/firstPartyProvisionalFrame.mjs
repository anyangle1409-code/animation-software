/** G4 provisional frame helper: never author geometry or anatomy. */
export const G4_FRAME_STATUS='PROTOTYPE_ONLY';
export function validateProvisionalTime(t){
  if(!Number.isFinite(t)||t<0||t>86400)throw new RangeError('Invalid provisional frame time');
  return t;
}
