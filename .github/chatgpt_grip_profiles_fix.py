from pathlib import Path

# The current canonical thumb base has a hard -14 degree anatomical limit.
# Keep all cylindrical profiles inside that actual limit; differentiate them
# through the finger and distal-thumb joints that have usable range.
p = Path('src/exercises/gripProfiles.ts')
s = p.read_text()
s = s.replace("thumbOppositionX: -16,", "thumbOppositionX: -14,")
s = s.replace("thumbOppositionX: -18,", "thumbOppositionX: -14,")
s = s.replace("thumbOppositionX: -20,", "thumbOppositionX: -14,")
p.write_text(s)

p = Path('src/exercises/gripProfiles.test.ts')
s = p.read_text().replace(
    "expect(deg(rope.rotations.thumb_01_l?.x)).toBeCloseTo(-20 * 0.85, 8);",
    "expect(deg(rope.rotations.thumb_01_l?.x)).toBeCloseTo(-14 * 0.85, 8);\n"
    "    expect(deg(rope.rotations.thumb_02_l?.z)).toBeCloseTo(70 * 0.85, 8);",
)
p.write_text(s)

p = Path('AI_CHANGELOG.md')
s = p.read_text().replace(
    "Bar/pull-up, neutral handle and rope profiles now have distinct finger/thumb closure and opposition values;",
    "Bar/pull-up, neutral handle and rope profiles now have distinct finger/distal-thumb closure values; thumb-base opposition stays at the canonical rig's real -14° limit rather than asking the joint for impossible extra travel;",
)
p.write_text(s)

print('Calibrated grip profiles to canonical thumb opposition limit')
