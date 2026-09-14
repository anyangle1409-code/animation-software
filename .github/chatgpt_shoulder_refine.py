from pathlib import Path

path = Path('src/muscles/model.ts')
text = path.read_text(encoding='utf-8')

old_delt = """    origin: at('clavicle_l', 0.03, 0.15, 0),
    insertion: at('upperarm_l', 0.05, 0.11, 0),
    thickness: 0.042,
    bulge: 0.3,
"""
new_delt = """    origin: at('clavicle_l', 0.03, 0.15, 0),
    insertion: at('upperarm_l', 0.05, 0.11, 0),
    thickness: 0.042,
    bulge: 0.3,
    // Shortens only the rendered belly, not the functional path. The 0.84
    // value is the largest measured taper that keeps the lateral head inside
    // the skin through the curl while preserving the corrected abduction path.
    taper: 0.84,
"""
if text.count(old_delt) != 1:
    raise SystemExit('expected one staged medial-deltoid block')
text = text.replace(old_delt, new_delt, 1)

old_pec = """    // A high anterior chest line represents the trainer-level pectoral group.
    // It keeps the proximal humeral insertion used for overhead containment,
    // but now shortens in both shoulder flexion and adduction instead of only
    // the latter. More detailed clavicular/sternal heads can be layered later
    // without changing the exercise-level activation group.
    origin: at('spine_03', -0.025, 0.1, 0.12),
    insertion: at('upperarm_l', 0, 0.05, 0.01),
    thickness: 0.032,
"""
new_pec = """    // Preserve the proven visible chest-to-humerus line. A hidden functional
    // via point on the proximal humerus supplies the wrap needed for the same
    // trainer-level pectoral group to shorten in both flexion and adduction,
    // without pulling the rendered belly through the armpit in a pull-up.
    origin: at('spine_03', -0.045, 0.04, 0.082),
    via: [at('upperarm_l', 0.02, 0.02, -0.02)],
    insertion: at('upperarm_l', 0.014, 0.028, 0.012),
    thickness: 0.032,
"""
if text.count(old_pec) != 1:
    raise SystemExit('expected one staged pectoral block')
text = text.replace(old_pec, new_pec, 1)

old_lat = """    // The lat wraps onto the anterior/proximal humerus before its insertion.
    // That route makes both shoulder extension and adduction shorten the path,
    // instead of a straight posterior chord lengthening during extension.
    origin: at('spine_01', -0.055, 0.02, -0.06),
    via: [at('upperarm_l', 0.04, 0.03, 0.04)],
    insertion: at('upperarm_l', 0.04, 0.04, 0.01),
    thickness: 0.032,
"""
new_lat = """    // Preserve the proven visible lat line and use a hidden proximal-humerus
    // via point for functional length. This keeps pull-up containment unchanged
    // while making both shoulder extension and adduction shorten the path.
    origin: at('spine_01', -0.055, 0.02, -0.06),
    via: [at('upperarm_l', 0.04, 0.04, 0.04)],
    insertion: at('upperarm_l', 0.014, 0.028, -0.014),
    thickness: 0.032,
"""
if text.count(old_lat) != 1:
    raise SystemExit('expected one staged latissimus block')
text = text.replace(old_lat, new_lat, 1)

path.write_text(text, encoding='utf-8')
print('Applied measured containment-safe shoulder refinements')
