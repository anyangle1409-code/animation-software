"""Prepare Phase B review from the pinned runtime exercise harness.

The knee/shoulder harness requires exact original-hand geometry. Phase B
intentionally changes that geometry, so this derived test instead limits its
size and enforces identical push-up hand-floor height, bone matrices, equipment
matrices, exercise validity, and closed motion loops. The pinned source file
is never edited.
"""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=root/'validation_63/scratchpad/repair/review_v3.test.mts'
out=root/'harnesses/review_hand_geometry.test.mts'
scratch=root/'validation_63/scratchpad/repair/review_hand_geometry.test.mts'
text=source.read_text()
def replace_once(old,new):
    global text
    assert text.count(old)==1,(old,text.count(old))
    text=text.replace(old,new)
replace_once("baseline:'../reference/anyangle1409-code-animation-software-f9cca7c/HOME_GYM_PT_GPT_MESH_HANDOFF/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb'",
             "baseline:'../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb'")
replace_once("let maxHand=0,maxBones=0,maxEquipment=0;",
             "let maxHand=0,maxBones=0,maxEquipment=0,maxFloor=0;")
replace_once("pair[id]={bones,hands,equipment,meshes};",
"""const handFloor={l:Infinity,r:Infinity};
 for(let i=0;i<body.geometry.getAttribute('position').count;i++){
   let owned=0;
   for(let lane=0;lane<4;lane++){
    const name=body.skeleton.bones[si.getComponent(i,lane)].name;
    if(/hand|palm|f_|thumb/.test(name))owned+=sw.getComponent(i,lane);
   }
   if(owned>.001){const side=body.geometry.getAttribute('position').getX(i)>0?'l':'r';handFloor[side]=Math.min(handFloor[side],meshes[0].positions[i][1]);}
 }
 pair[id]={bones,hands,equipment,meshes,handFloor};""")
replace_once("const a=pair.baseline,b=pair.candidate;expect(b.hands.length)",
"""const a=pair.baseline,b=pair.candidate;
 if(ex.id==='push_up')for(const side of ['l','r']){
  const difference=Math.abs(a.handFloor[side]-b.handFloor[side]);
  maxFloor=Math.max(maxFloor,difference);
  expect(difference).toBeLessThan(1e-6);
 }
 expect(b.hands.length)""")
replace_once("equipmentMatrixMaxDifference:maxEquipment,techniqueViolations:",
             "equipmentMatrixMaxDifference:maxEquipment,pushupFloorMaxDifferenceMm:maxFloor*1000,techniqueViolations:")
replace_once("expect(maxHand).toBeLessThan(1e-6);",
             "expect(maxHand).toBeLessThan(.004);")
out.parent.mkdir(exist_ok=True)
out.write_text(text)
scratch.write_text(text)
print('Prepared hand-specific exercise comparison from pinned runtime source:',out)
