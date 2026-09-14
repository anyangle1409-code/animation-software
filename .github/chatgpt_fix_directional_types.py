from pathlib import Path

path = Path('src/character/importedDeformation.ts')
text = path.read_text(encoding='utf-8')
text = text.replace(
    "import type { Bone, BufferGeometry, KeyframeTrack, SkinnedMesh } from 'three';",
    "import type { Bone, BufferGeometry, InterleavedBufferAttribute, KeyframeTrack, SkinnedMesh } from 'three';",
)
text = text.replace(
    "    point.fromBufferAttribute(position, vertex);",
    "    pointFrom(position, vertex, point);",
)
text = text.replace(
    "  skinIndex: BufferAttribute,\n  skinWeight: BufferAttribute,",
    "  skinIndex: BufferAttribute | InterleavedBufferAttribute,\n  skinWeight: BufferAttribute | InterleavedBufferAttribute,",
)
text = text.replace(
    "  const skinIndex = geometry.getAttribute('skinIndex') as BufferAttribute | undefined;\n  const skinWeight = geometry.getAttribute('skinWeight') as BufferAttribute | undefined;",
    "  const skinIndex = geometry.getAttribute('skinIndex');\n  const skinWeight = geometry.getAttribute('skinWeight');",
)
for old, new in [
    ("    a.fromBufferAttribute(position, ia);", "    pointFrom(position, ia, a);"),
    ("    b.fromBufferAttribute(position, ib);", "    pointFrom(position, ib, b);"),
    ("    c.fromBufferAttribute(position, ic);", "    pointFrom(position, ic, c);"),
    ("      neighbourPoint.fromBufferAttribute(position, neighbour);", "      pointFrom(position, neighbour, neighbourPoint);"),
]:
    text = text.replace(old, new)
text = text.replace(
    "  position: BufferAttribute,\n  vertex: number,",
    "  position: BufferAttribute | InterleavedBufferAttribute,\n  vertex: number,",
)
path.write_text(text, encoding='utf-8')
