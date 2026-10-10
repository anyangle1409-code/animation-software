import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { EXERCISES } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import {
  createFirstPartyWebGL2BoneRenderer,
  packBoneSegments,
} from './firstPartyWebGL2SkeletonPreview.mjs';

/**
 * ISOLATED full first-party FK/IK -> native GPU demonstration.
 *
 * This secondary HTML entry must NOT import the editor's ThreeSceneHost,
 * threeSceneBoundary, threeRuntimeBoundary, or studioStore modules. It is
 * diagnostic only, outside the editor production bundle: this is a moving
 * skeleton, not a production human skin/mesh renderer.
 */
const canvas=document.querySelector<HTMLCanvasElement>('#hgpt-native-only-canvas');
const label=document.querySelector<HTMLElement>('#hgpt-native-only-description');
if (!canvas || !label) throw new Error('Native renderer preview HTML is incomplete');

const skeleton=canonicalSkeleton;
const evaluation=new PoseEvaluation(skeleton);
const exercise=EXERCISES[0];
const clip=generateClip(skeleton,exercise);
if (!Number.isFinite(clip.duration)||clip.duration<=0)
  throw new Error('Actual exercise clip has no valid duration');
const drawable=skeleton.names.filter(name=>skeleton.bone(name).length>1e-10);
const gpu=createFirstPartyWebGL2BoneRenderer(canvas);
canvas.dataset.hgptNoVendorModules='true';
canvas.dataset.hgptRealExerciseSource=exercise.id;
canvas.dataset.hgptNativeRenderer=gpu.kind;
const container=canvas.parentElement;
if(!container)throw new Error('Native preview canvas missing its container');
label.textContent='FIRST-PARTY WebGL2 skeletal diagnostic — '+
  exercise.name+' — no Three.js, no mesh/skin anatomical approval';

let disposed=false,start:number|null=null,frameCount=0,lastPose:Float32Array|null=null;
const viewport=()=>{
  if(disposed)return;
  const box=container.getBoundingClientRect();
  if(box.width>0&&box.height>0)
    gpu.setSize(box.width,box.height,Math.min(2,window.devicePixelRatio||1));
};
const observer=new ResizeObserver(viewport);
observer.observe(container);
window.addEventListener('resize',viewport);
viewport();

const advance=(ms:number)=>{
  if(disposed)return;
  if(start===null)start=ms;
  const time=((ms-start)/1000)%clip.duration;
  const frame=resolveFrame(skeleton,evaluation,clip,time);
  evaluation.apply(frame.pose);
  const vertices=packBoneSegments(skeleton,evaluation,drawable);
  if(lastPose){
    let delta=0;
    for(let i=0;i<vertices.length;i++)delta=Math.max(delta,Math.abs(vertices[i]-lastPose[i]));
    canvas.dataset.hgptNativePoseDifference=String(delta);
  }
  lastPose=vertices;
  gpu.render(vertices);
  canvas.dataset.hgptNativeFrame=String(++frameCount);
  canvas.dataset.hgptNativeTime=time.toFixed(6);
  canvas.dataset.hgptNativeBoneCount=String(drawable.length);
  requestAnimationFrame(advance);
};
requestAnimationFrame(advance);

window.addEventListener('pagehide',()=>{
  if(disposed)return;
  disposed=true;observer.disconnect();window.removeEventListener('resize',viewport);
  gpu.dispose();
},{once:true});
