import { readFileSync,writeFileSync } from 'node:fs';
import { it } from 'vitest';
import { Matrix4,Vector3 } from 'three';
import { retargetedCharacterSource } from '../../src/character/retargetSource';
import { canonicalSkeleton as rig,PoseEvaluation } from '../../src/rig/skeleton';
import { generateClip } from '../../src/animation/generate';
import { sampleClip } from '../../src/animation/clip';
import { resolveFrame } from '../../src/animation/pipeline';
import { lockAnchors } from '../../src/constraints/locks';
import { applyCharacterPose } from '../../src/character/pose';
import { bicepCurl } from '../../src/exercises/definitions/bicepCurl';

it('exports fixed-rig sculpt reference at curl Bottom',async()=>{
 const path=process.env.GLB!;const bytes=readFileSync(path);
 const source=retargetedCharacterSource({id:path,label:path,data:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)});
 const c=await source.build(rig);const m=c.meshes.find(m=>/freeman/i.test(m.name))!;
 const clip=generateClip(rig,bicepCurl),e=new PoseEvaluation(rig),anchors=lockAnchors(e,sampleClip(clip,0).pose,clip.locks);
 const f=resolveFrame(rig,e,clip,0,{anchors});applyCharacterPose(c,rig,f.pose,e,{contacts:f.contacts,grip:{kind:bicepCurl.hands.grip,closure:bicepCurl.hands.closure}});
 m.skeleton.update();m.updateWorldMatrix(true,false);
 const p=m.geometry.getAttribute('position'), j=m.geometry.getAttribute('skinIndex'),w=m.geometry.getAttribute('skinWeight');
 const points=[], transforms=[],rest=[],ownership=[];
 for(let i=0;i<p.count;i++){
  const a=new Vector3(); m.getVertexPosition(i,a);a.applyMatrix4(m.matrixWorld);points.push(a.toArray());
  rest.push([p.getX(i),p.getY(i),p.getZ(i)]);
  const origin=m.localToWorld(m.applyBoneTransform(i,new Vector3()));
  const axes=[new Vector3(1,0,0),new Vector3(0,1,0),new Vector3(0,0,1)].map(v=>m.localToWorld(m.applyBoneTransform(i,v)).sub(origin));
  transforms.push(new Matrix4().makeBasis(...axes as [Vector3,Vector3,Vector3]).invert().toArray());
  const shares={L:0,R:0,hand:0};for(let lane=0;lane<4;lane++){const n=m.skeleton.bones[j.getComponent(i,lane)].name;const weight=w.getComponent(i,lane);if(/upper_?arm.?L/i.test(n))shares.L+=weight;if(/upper_?arm.?R/i.test(n))shares.R+=weight;if(/hand|palm|f_|thumb/i.test(n))shares.hand+=weight;}ownership.push(shares);
 }
 const at=(n:string)=>new Vector3().setFromMatrixPosition(c.boneByName.get(n as never)!.matrixWorld).toArray();
 const boneTransforms=m.skeleton.bones.map((bone,i)=>m.matrixWorld.clone().multiply(m.bindMatrixInverse).multiply(bone.matrixWorld).multiply(m.skeleton.boneInverses[i]).multiply(m.bindMatrix).toArray());
 writeFileSync('../reports/sculpt_reference.json',JSON.stringify({path,points,transforms,rest,ownership,boneTransforms,shoulders:{L:at('upperarm_l'),R:at('upperarm_r')},indices:Array.from(m.geometry.index!.array),report:source.lastReport}));
 console.log(source.lastReport);c.dispose();
},300000);
