from pathlib import Path

path = Path('src/retargeting/realCharacterDiagnostic.test.ts')
text = path.read_text(encoding='utf-8')
text = text.replace(
    "import { generateClip } from '../animation/generate';\nimport { sampleClip } from '../animation/clip';",
    "import { generateClip } from '../animation/generate';\nimport { sampleClip } from '../animation/clip';\nimport type { StudioClip } from '../animation/clip';",
)
text = text.replace(
    "import { applyCharacterPose } from '../character/pose';\nimport { retargetedCharacterSource } from '../character/retargetSource';",
    "import { applyCharacterPose } from '../character/pose';\nimport { retargetedCharacterSource } from '../character/retargetSource';\nimport type { CharacterBuild, Side } from '../character/types';\nimport { equipmentSocket } from '../equipment/library';\nimport { handAttachmentMatrix } from '../export/clipBuilder';",
)
text = text.replace(
    " * exercise families, and prints mesh strain plus hand-frame continuity.  It is\n",
    " * exercise families, and prints mesh strain, hand-frame continuity and\n * dumbbell-handle/skin clearance.  It is\n",
)
anchor = """function strain(mesh: SkinnedMesh, set: EdgeSet) {\n  const one = new Vector3();\n  const two = new Vector3();\n  const ratios: number[] = [];\n\n  mesh.skeleton.update();\n  set.edges.forEach(([a, b], slot) => {\n    // Three's vertex evaluator applies both morph targets and skinning in the\n    // rendered order. applyBoneTransform alone silently ignores correctives.\n    mesh.getVertexPosition(a, one);\n    mesh.getVertexPosition(b, two);\n    ratios.push(one.distanceTo(two) / set.rest[slot]);\n  });\n\n  const maximum = Math.max(...ratios);\n  const minimum = Math.min(...ratios);\n  return {\n    max: maximum,\n    p99: percentile(ratios, 0.99),\n    p95: percentile(ratios, 0.95),\n    min: minimum,\n    over2x: ratios.filter((value) => value > 2).length,\n    over3x: ratios.filter((value) => value > 3).length,\n    underHalf: ratios.filter((value) => value < 0.5).length,\n  };\n}\n"""
addition = anchor + """\nconst DUMBBELL_HANDLE_RADIUS = 0.015;\nconst DUMBBELL_HANDLE_HALF_LENGTH = 0.06;\n\n/**\n * Measure the visible imported skin against the exact handle transform used by\n * the viewport. This is diagnostic only: a sparse mesh can miss a triangle-level\n * intersection even when no vertex enters the cylinder, so the number is useful\n * for A/B calibration but is not a pass/fail threshold. Negative clearance means\n * at least one posed skin vertex is inside the 15 mm-radius handle volume.\n */\nfunction dumbbellHandleSkinClearance(character: CharacterBuild, clip: StudioClip) {\n  const result: Record<Side, { penetratingVertices: number; minClearanceMm: number | null; sampledVertices: number } | null> = {\n    l: null,\n    r: null,\n  };\n  if (!character.handMatrix) return result;\n\n  const vertex = new Vector3();\n  const handleLocal = new Vector3();\n\n  for (const side of ['l', 'r'] as const) {\n    const instance = clip.equipment.find(\n      (entry) =>\n        entry.kind === 'dumbbell' &&\n        entry.attachment.mode === 'hand' &&\n        entry.attachment.side === side,\n    );\n    if (!instance || instance.attachment.mode !== 'hand') continue;\n\n    const hand = character.handMatrix(side, new Matrix4());\n    if (!hand) continue;\n    const socket = equipmentSocket(instance.kind, instance.attachment.socket);\n    const grip = instance.attachment.gripOffset ?? { x: 0, y: 0.045, z: 0 };\n    const equipment = new Matrix4().multiplyMatrices(\n      hand,\n      handAttachmentMatrix(grip, socket?.position ?? { x: 0, y: 0, z: 0 }),\n    );\n    const toHandle = equipment.clone().invert();\n\n    let penetratingVertices = 0;\n    let sampledVertices = 0;\n    let minClearance = Number.POSITIVE_INFINITY;\n\n    for (const mesh of character.meshes) {\n      mesh.skeleton.update();\n      mesh.updateWorldMatrix(true, false);\n      const count = mesh.geometry.getAttribute('position').count;\n      for (let index = 0; index < count; index += 1) {\n        mesh.getVertexPosition(index, vertex);\n        handleLocal.copy(vertex).applyMatrix4(mesh.matrixWorld).applyMatrix4(toHandle);\n        if (Math.abs(handleLocal.z) > DUMBBELL_HANDLE_HALF_LENGTH) continue;\n        sampledVertices += 1;\n        const clearance = Math.hypot(handleLocal.x, handleLocal.y) - DUMBBELL_HANDLE_RADIUS;\n        minClearance = Math.min(minClearance, clearance);\n        if (clearance < 0) penetratingVertices += 1;\n      }\n    }\n\n    result[side] = {\n      penetratingVertices,\n      minClearanceMm: Number.isFinite(minClearance) ? Number((minClearance * 1000).toFixed(3)) : null,\n      sampledVertices,\n    };\n  }\n\n  return result;\n}\n"""
if anchor not in text:
    raise SystemExit('strain anchor not found')
text = text.replace(anchor, addition, 1)
old = """        samples.push({ fraction, meshStats, hands });\n"""
new = """        const handleSkin = dumbbellHandleSkinClearance(character, clip);\n        samples.push({ fraction, meshStats, hands, handleSkin });\n"""
if old not in text:
    raise SystemExit('sample anchor not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
