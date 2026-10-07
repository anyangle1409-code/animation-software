#!/usr/bin/env python3
"""Reproduce the Phase 5 static comparison. Reads production inputs; writes audit data only."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'ORIGINAL_V1_WORK/anatomy'
INPUTS = ['ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json',
          'scripts/pose_test_original_v1_o4_candidate_blender.py',
          'scripts/r97/scapula_pivot.py', 'scripts/r97/add_gh_helper.py',
          'ORIGINAL_V1_WORK/anatomy/adult_bone_inventory_206.json',
          'ORIGINAL_V1_WORK/anatomy/adult_bone_blender_aliases_206.json',
          'ORIGINAL_V1_WORK/anatomy/adult_articulation_inventory.json',
          'ORIGINAL_V1_WORK/anatomy/whole_body_movement_atlas.json']


def build_matrix(root=ROOT):
    data = root / 'ORIGINAL_V1_WORK/anatomy'
    def read(path): return json.loads((root / path).read_text())
    canonical = read(INPUTS[0]); names = {b['name'] for b in canonical['bones']}
    aliases = {a['anatomical_id']: a for a in read(INPUTS[5])['aliases']}
    inventory = read(INPUTS[6]); atlas = read(INPUTS[7])
    source = (root / INPUTS[1]).read_text()
    functions = {n.name: ast.get_source_segment(source,n) for n in ast.parse(source).body
                 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    def select(prefix): return sorted(n for n in names if n.startswith(prefix))
    bones = {b['name']: b for b in canonical['bones']}
    facts = {'canonical_bone_count':len(names), 'canonical_names':sorted(names),
             'neck_segments':select('neck'), 'torso_segments':select('spine_'),
             'forearm_twist_helpers':select('forearm_tw'),
             'explicit_carpals':[n for n in sorted(names) if n.split('_')[0] in
                                 {'scaphoid','lunate','triquetrum','pisiform','trapezium','trapezoid','capitate','hamate'}],
             'explicit_patella':select('patella'), 'explicit_talus':select('talus'),
             'explicit_calcaneus':select('calcaneus'), 'toe_segments':select('toe_'),
             'uniform_long_finger_recipe':all(x in functions.get('grip','') for x in
                    ['("index", "middle", "ring", "pinky")','((1, 70), (2, 88), (3, 55))']),
             'thumb_parallel_hinge_recipe':'thumb MCP/IP joints are parallel hinges too' in functions.get('grip',''),
             'ac_gh_bind_separation_mm':{side:round(1000*sum((x-y)**2 for x,y in zip(bones['clavicle_'+side]['tail'],bones['upperarm_'+side]['head']))**.5,6) for side in ['l','r']},
             'r97_relocates_scapula_to_clavicle_tail':all(x in (root/INPUTS[2]).read_text() for x in ['off = cl.tail - sc.head','sc.head += off']),
             'r97_gh_uses_upperarm_head':'h.head = ua.head.copy()' in (root/INPUTS[3]).read_text()}
    descriptions = {
      'fixed':('Grouped/absent anatomical reference structures','reference_grouping_review','Represent all fixed references in master; choose fusion variants; rigid runtime grouping requires later comparison.'),
      'tmj':('No explicit mandible or TMJ controls','absent_explicit_structure','Separate mandible with bilateral constrained condylar/disc contact and glide.'),
      'c0_c1':('One neck plus head','collapsed_segments','Separate skull/atlas/axis and resolve paired condyle contact.'),
      'c1_c2':('One neck plus head','collapsed_segments','Separate atlas/axis, dens and lateral facets sharing a level transform.'),
      'cervical':('One neck plus head','collapsed_segments','Represent C2–C7 individually and cervicothoracic transition.'),
      'thoracic':('Three aggregate spine segments for torso','collapsed_segments','Represent T1–T12 with disc/facet level transforms and rib attachments.'),
      'lumbar':('Three aggregate spine segments for torso','collapsed_segments','Represent L1–L5/sacrum and level-dependent sagittal contribution.'),
      'ribs':('No individual rib controls','absent_explicit_structure','Posterior rib contacts, rib-specific follower trajectories and cartilage compliance.'),
      'anterior_thorax':('No explicit sternum/cartilage mechanics','absent_explicit_structure','Anterior thoracic follower system; preserve fusion/first-rib exceptions.'),
      'si':('Single pelvis segment','collapsed_segments','Separate sacrum and bilateral hip bones; constrained SI/pubic ring compliance.'),
      'pubis':('Single pelvis segment','collapsed_segments','Reference symphysis and pelvic-ring follower compliance.'),
      'coccyx':('No explicit coccygeal components','absent_explicit_structure','Reference coccyx; choose component/fusion variant before follower fitting.'),
      'sc':('Clavicle control; generic elevation driver','mechanics_gap','SC three-dimensional elevation/retraction/roll with separate sternum centre.'),
      'ac':('Scapula/clavicle present; r97 pivot coincides with GH','verified_static_gap','Fit distinct AC and GH centres; relative scapula/clavicle rotations.'),
      'st':('Scapula present; generic upward-rotation rule','mechanics_gap','Thorax-relative upward rotation, tilt and axial rotation; surface follower.'),
      'gh':('Upperarm present; generic elevation/ER rule','mechanics_gap','Plane-dependent GH rotation and glenoid-relative translation; distinct GH centre.'),
      'elbow':('Upperarm/forearm present; radius/ulna grouped','present_requires_dynamic_validation','Separate humeroulnar/radiocapitellar references; fit carrying angle and centre.'),
      'radioulnar':('One forearm plus twist helpers','collapsed_segments','Separate radius/ulna and constrained PRUJ/DRUJ rotation; helper twist is not osseous articulation.'),
      'ru_iom':('Radius/ulna grouped','collapsed_segments','Forearm interosseous membrane follower constraint.'),
      'radiocarpal':('One hand for gross wrist','collapsed_segments','Separate radiocarpal and midcarpal stages; no ulna–carpal osseous contact.'),
      'carpal':('No explicit eight carpal bones; metacarpals excluded from count','absent_explicit_structure','Individual carpal references and shared contact/row mechanics.'),
      'pisiform':('No explicit pisiform','absent_explicit_structure','Pisotriquetral/FCU follower reference.'),
      'thumb_cmc':('Three thumb segments; parallel hinge recipe','verified_static_gap','Saddle CMC axes and coupled opposition roll; distinguish metacarpal from phalanges.'),
      'thumb_mcp':('Thumb segment present; common-axis recipe','mechanics_gap','Anatomical MCP axis and task-dependent CMC/MCP/IP coordination.'),
      'thumb_ip':('Thumb segment present; common-axis recipe','mechanics_gap','Anatomical IP hinge and independent measured coordination.'),
      'metacarpal':('Four long metacarpals per hand','present_requires_dynamic_validation','Fit CMC/intermetacarpal cupping; preserve ray differences.'),
      'mcp':('Long-finger chains present; uniform70deg recipe','verified_static_gap','Digit-specific MCP flexion/spread and wrist/posture-dependent coupling.'),
      'pip':('Long-finger chains present; uniform88deg recipe','verified_static_gap','Digit-specific PIP hinge and grip/release trajectory.'),
      'dip':('Long-finger chains present; uniform55deg recipe','verified_static_gap','Digit-specific DIP hinge and tendon/task coupling.'),
      'hip':('Pelvis/thigh present; centres not anatomically fitted','present_requires_dynamic_validation','Fit femoral head/acetabulum and posture-dependent three-axis rotation.'),
      'knee':('Thigh/shin present; no anatomical contact solver verified','present_requires_dynamic_validation','Condyle/tibial contact, rolling/sliding, screw-home and load/path dependence.'),
      'patella':('No explicit patella','absent_explicit_structure','Patellar follower track and trochlear/contact geometry.'),
      'ptf':('One shin groups tibia/fibula','collapsed_segments','Separate proximal tibiofibular follower reference.'),
      'dtf':('One shin groups tibia/fibula','collapsed_segments','Distal syndesmosis compliance driven by ankle motion.'),
      'tf_iom':('One shin groups tibia/fibula','collapsed_segments','Interosseous membrane constraint between tibia/fibula.'),
      'ankle':('One foot at shin','collapsed_segments','Talus/tibia/fibula talocrural contact and fitted oblique axis.'),
      'subtalar':('One foot; no separate talus/calcaneus','collapsed_segments','Independent anatomical hindfoot reference and coupled inversion/rotation.'),
      'tcn':('One foot; no separate talonavicular stage','collapsed_segments','Talocalcaneonavicular complex constrained with hindfoot/midfoot.'),
      'midfoot':('One foot segment','collapsed_segments','Individual tarsals; deformable load-dependent midfoot, no universal locking assumption.'),
      'tmt':('No separate metatarsal rays','collapsed_segments','Ray-dependent tarsometatarsal/intermetatarsal follower mechanics.'),
      'hallux':('One toe segment groups all toes','collapsed_segments','Separate hallux MTP; weightbearing task and passive measurements kept distinct.'),
      'lesser_mtp':('One toe segment groups all toes','collapsed_segments','Four lesser-toe rays with individual MTP flexion/spread.'),
      'toe_ip':('One toe segment groups all toes','collapsed_segments','Hallux IP and lesser PIP/DIP separately represented.'),
      'sesamoid':('No separate hallucal sesamoids','absent_explicit_structure','Two plantar sesamoid follower tracks per foot.'),
    }
    profiles={}
    for k,p in atlas['profiles'].items():
        current,status,change=descriptions[k]
        profiles[k]=dict(anatomical_requirement=p['title'],current_rig=current,status=status,
            required_change=change,evidence_sources=p['sources'],mechanics_profile=k,
            verification='Canonical names/aliases and pinned driver source; qualitative requirement from sourced movement profile.',
            acceptance_tests=p['bone_only_tests'],acceptance_criteria=p['acceptance_criteria'],character_validated=False)
    bone_rows={k:dict(anatomical_id=k,reference_blender_name=v['reference_blender_name'],current_rig=v['current_rig'],relationship=v['relationship'],
                      required_change='Include this named anatomical reference in master; fit and validate before runtime grouping.',character_validated=False) for k,v in aliases.items()}
    joints={}
    for j in inventory['articulations']:
        k=atlas['joint_assignments'][j['id']]['profile_id']
        joints[j['id']]=dict(profile_id=k,participants=j['participants'],role=j['role'],variant=j['variant'],
            current_rig_by_participant={b:aliases[b]['current_rig'] if b in aliases else [] for b in j['participants']},
            anatomy_sources=j['sources'],status=profiles[k]['status'],required_change=profiles[k]['required_change'],character_validated=False)
    locators={name:dict(file=INPUTS[1],function=name,source=functions[name]) for name in
              ['grip','girdle_for_elevation','scapular_upward_rotation','external_rotation_for_elevation','pose_squat_bottom','pose_lunge']}
    return dict(schema_version=1,scope='Read-only static comparison of exported canonical rig and named driver; not live Blender inspection.',
        input_sha256={p:dict(sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in INPUTS},
        static_facts=facts,driver_locators=locators,bones=bone_rows,joints=joints,profiles=profiles,
        production_approved=False,character_validated=False,next_blocking_phase=6,
        limitations=['A missing explicit named control is a master-reference gap, not proof that current skin cannot approximate motion.',
                     'Static driver inspection does not prove every possible runtime path lacks a feature.',
                     'The older whole-body audit carpal substring also matches metacarpal; this matrix counts exact carpal names.',
                     'Later recovery candidates and the local Blender character have not been dynamically evaluated by this comparison.'])

if __name__ == '__main__':
    matrix=build_matrix()
    (DATA/'current_rig_anatomical_gap_matrix.json').write_text(json.dumps(matrix,indent=2)+'\n')
    print('Wrote audit matrix:',len(matrix['bones']),'bones,',len(matrix['joints']),'joints,',len(matrix['profiles']),'mechanics profiles')
