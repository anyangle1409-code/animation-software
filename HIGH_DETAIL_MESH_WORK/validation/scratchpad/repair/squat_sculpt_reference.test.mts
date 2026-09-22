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
import { EXERCISES } from '../../src/exercises/library';

it('captures the unchanged V5 squat-peak knee surface and inverse skin Jacobians',async()=>{
 const path='../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v5_hands_curved.glb';const bytes=readFileSync(path);
 const source=retargetedCharacterSource({id:path,label:path,data:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)});
 const c=await source.build(rig);const m=c.meshes.find(mesh=>/freeman/i.test(mesh.name))!;
 const exercise=EXERCISES.find(each=>each.id==='air_squat')!;const clip=generateClip(rig,exercise);
 const evaluation=new PoseEvaluation(rig),anchors=lockAnchors(evaluation,sampleClip(clip,0).pose,clip.locks);
 const peak=clip.keyframes.find(each=>each.marker==='peak')?.time??clip.duration*.4;
 const frame=resolveFrame(rig,evaluation,clip,peak,{anchors});
 applyCharacterPose(c,rig,frame.pose,evaluation,{contacts:frame.contacts,grip:{kind:exercise.hands.grip,closure:exercise.hands.closure}});
 m.skeleton.update();m.updateWorldMatrix(true,false);
 const position=m.geometry.getAttribute('position');const points:number[][]=[],inverse:number[][]=[];
 for(let i=0;i<position.count;i++){
  const posed=new Vector3();m.getVertexPosition(i,posed);posed.applyMatrix4(m.matrixWorld);points.push(posed.toArray());
  const origin=m.localToWorld(m.applyBoneTransform(i,new Vector3()));
  const axes=[new Vector3(1,0,0),new Vector3(0,1,0),new Vector3(0,0,1)].map(v=>m.localToWorld(m.applyBoneTransform(i,v)).sub(origin));
  inverse.push(new Matrix4().makeBasis(...axes as [Vector3,Vector3,Vector3]).invert().toArray());
 }
 const at=(name:string)=>new Vector3().setFromMatrixPosition(c.boneByName.get(name as never)!.matrixWorld).toArray();
 writeFileSync('../reports/squat_sculpt_reference_v5.json',JSON.stringify({path,time:peak,points,inverse,knees:{L:at('shin_l'),R:at('shin_r')},indices:Array.from(m.geometry.index!.array)}));
 console.log({vertices:points.length,knees:{L:at('shin_l'),R:at('shin_r')}});c.dispose();
},300000);
