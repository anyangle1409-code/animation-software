import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import {
  createNativeIndexedMeshWebGL2,
  deformIndexedSkin,
  invertRigidBind,
  makeTwoBoneSkinProbe,
} from './firstPartyIndexedSkinnedMesh.mjs';

/**
 * Truly first-party, independent mesh-skinned WebGL2 exercise proof.
 *
 * This shows a SYNTHETIC two-bone sleeve deforming to real generated IK/FK
 * movement, not the ORIGINAL_v1 biological mesh. CPU four-weight LBS is
 * reference-only; no normal/face geometry from anyone else's character.
 */
const canvas=document.querySelector<HTMLCanvasElement>('#hgpt-native-skin-canvas');
const label=document.querySelector<HTMLElement>('#hgpt-native-skin-description');
if(!canvas||!label)throw new Error('Native LBS diagnostic page is incomplete');
const rig=canonicalSkeleton;
const evaluator=new PoseEvaluation(rig);
const clip=generateClip(rig,EXERCISES[0]);
if(clip.duration<=0)throw new Error('Invalid first-party exercise duration');

const arm=['upperarm_l','forearm_l'] as const;
const pos=(v:{x:number;y:number;z:number}):number[]=>[v.x,v.y,v.z];
const a=rig.bone(arm[0]),b=rig.bone(arm[1]);
// Source skeleton owns these rest heads/tails; never shift a bone to fit mesh.
const sleeve=makeTwoBoneSkinProbe(pos(a.restHead),pos(a.restTail),pos(b.restTail),
  {radius:0.065,sides:12});
evaluator.apply(restPose());
const inverse=new Float32Array(32);
for(let i=0;i<2;i++){
  const bind=evaluator.matrix(arm[i]).elements;
  inverse.set(invertRigidBind(new Float32Array(bind)),16*i);
}
const mesh={...sleeve,inverseBindMatrices:inverse};
const gpu=createNativeIndexedMeshWebGL2(canvas);
canvas.dataset.hgptNativeSkinned='true';
canvas.dataset.hgptNativeThirdPartyModules='none';
canvas.dataset.hgptNativeSkinnedRenderer=gpu.kind;
canvas.dataset.hgptNativeExercise=EXERCISES[0].id;
canvas.dataset.hgptNativeMeshTriangles=String(sleeve.indices.length/3);
label.textContent='FIRST-PARTY WebGL2 indexed triangles + original FK/IK exercise + '+
  'CPU linear-blend skinning. This sleeve is a generated geometric test proxy, not a realistic anatomical human body.';

let disposed=false,start:number|null=null,frameCount=0,motion=0;
let initialPose:Float32Array|null=null;
const parent=canvas.parentElement;
if(!parent)throw new Error('Missing native mesh canvas viewport');
const resize=()=>{
  if(disposed)return;
  const box=parent.getBoundingClientRect();
  if(box.width>0&&box.height>0)
    gpu.setSize(box.width,box.height,Math.min(2,window.devicePixelRatio||1));
};
const resizeObserver=new ResizeObserver(resize);
resizeObserver.observe(parent);
window.addEventListener('resize',resize);
resize();
const draw=(ms:number)=>{
  if(disposed)return;
  if(start===null)start=ms;
  const seconds=((ms-start)/1000)%clip.duration;
  const resolved=resolveFrame(rig,evaluator,clip,seconds);
  evaluator.apply(resolved.pose);
  const poses=new Float32Array(32);
  for(let i=0;i<2;i++)poses.set(evaluator.matrix(arm[i]).elements,16*i);
  const skinned=deformIndexedSkin(mesh,poses);
  if(initialPose===null)initialPose=skinned.positions.slice();
  else for(let k=0;k<initialPose.length;k++)
    motion=Math.max(motion,Math.abs(initialPose[k]-skinned.positions[k]));
  gpu.render(skinned,{eye:[1.5,1.4,2.4],target:[-.32,1.10,0],color:[.55,.85,.92]});
  frameCount++;
  canvas.dataset.hgptNativeSkinnedFrame=String(frameCount);
  canvas.dataset.hgptNativeSkinnedTime=seconds.toFixed(4);
  canvas.dataset.hgptNativeSkinnedMotion=motion.toFixed(6);
  canvas.dataset.hgptNativeSkinnedTriangles=String(skinned.triangleCount);
  requestAnimationFrame(draw);
};
requestAnimationFrame(draw);
window.addEventListener('pagehide',()=>{
  if(disposed)return;
  disposed=true;
  resizeObserver.disconnect();window.removeEventListener('resize',resize);gpu.dispose();
},{once:true});
