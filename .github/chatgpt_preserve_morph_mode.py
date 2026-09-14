from pathlib import Path

path = Path('src/character/importedDeformation.ts')
text = path.read_text(encoding='utf-8')
old = '''  const morph = new BufferAttribute(delta, 3);\n  morph.name = `homeGymPT_elbow_${side}`;\n  mesh.geometry.morphTargetsRelative = true;\n  const attributes = mesh.geometry.morphAttributes.position ?? [];\n'''
new = '''  // Three.js stores one morph convention per geometry. Do not flip an imported\n  // character from absolute to relative morphs (or vice versa) just to append\n  // this corrective: doing so would reinterpret every pre-existing expression\n  // or body shape. Encode the new target in the geometry's existing convention.\n  const morph = mesh.geometry.morphTargetsRelative\n    ? new BufferAttribute(delta, 3)\n    : absoluteMorph(position, delta);\n  morph.name = `homeGymPT_elbow_${side}`;\n  const attributes = mesh.geometry.morphAttributes.position ?? [];\n'''
if old not in text:
    raise SystemExit('morph block not found')
text = text.replace(old, new, 1)
anchor = '''function pointFrom(\n  position: BufferAttribute | InterleavedBufferAttribute,\n  vertex: number,\n  target: Vector3,\n): Vector3 {\n  return target.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));\n}\n'''
addition = anchor + '''\n/** Build an absolute-position morph target without changing the source convention. */\nfunction absoluteMorph(\n  position: BufferAttribute | InterleavedBufferAttribute,\n  delta: Float32Array,\n): BufferAttribute {\n  const values = new Float32Array(position.count * 3);\n  for (let vertex = 0; vertex < position.count; vertex += 1) {\n    const start = vertex * 3;\n    values[start] = position.getX(vertex) + delta[start];\n    values[start + 1] = position.getY(vertex) + delta[start + 1];\n    values[start + 2] = position.getZ(vertex) + delta[start + 2];\n  }\n  return new BufferAttribute(values, 3);\n}\n'''
if anchor not in text:
    raise SystemExit('pointFrom anchor not found')
text = text.replace(anchor, addition, 1)
path.write_text(text, encoding='utf-8')
