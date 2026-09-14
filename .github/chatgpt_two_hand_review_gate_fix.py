from pathlib import Path


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# A push-up is the better fixture for a rigid two-hand bar review because both
# hand joints are world-locked throughout the rep. The synthetic bar also uses
# the hand origins rather than an in-palm offset so wrist orientation cannot
# change the bilateral test separation.
p = 'src/editor/review.test.ts'
s = read(p)
s = replace_once(
    s,
    "const exercise = clone(getExercise('dumbbell_bicep_curl'));\n    const bar: EquipmentInstance = {",
    "const exercise = clone(getExercise('push_up'));\n    const bar: EquipmentInstance = {",
    'stable push-up fixture',
)
s = replace_once(
    s,
    """      attachment: {
        mode: 'hands',
        leftSocket: 'grip_l',
        rightSocket: 'grip_r',
      },""",
    """      attachment: {
        mode: 'hands',
        leftSocket: 'grip_l',
        rightSocket: 'grip_r',
        gripOffset: { x: 0, y: 0, z: 0 },
      },""",
    'origin grip point for rigid fixture',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
s = replace_once(
    s,
    'Regression coverage appends a synthetic rigid barbell to the retained curl only inside the test: default 80 cm sockets correctly block automated approval, then the test measures the actual hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. No accepted exercise definition or curl animation was changed.',
    'Regression coverage appends a synthetic rigid barbell to the push-up only inside the test because its hand joints are world-locked throughout the rep. The synthetic bar deliberately uses the hand origins as its grip targets, avoiding normal in-palm offsets whose world position changes as the wrist rotates. Default 80 cm sockets correctly block automated approval; the test then measures the actual locked-hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. Earlier curl and in-palm fixtures were deliberately rejected because the new gate correctly detected their changing bilateral grip-point spacing. No accepted exercise definition or animation was changed.',
    'changelog stable fixture',
)
write(p, s)

print('Stabilized two-hand review regression at world-locked hand origins')
