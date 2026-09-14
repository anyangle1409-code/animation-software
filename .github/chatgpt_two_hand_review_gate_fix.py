from pathlib import Path


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# A push-up is the better fixture for a rigid two-hand bar review because both
# hands are world-locked throughout the rep. The curl intentionally allows small
# natural upper-arm motion, so its hand separation is not a rigid-bar invariant.
p = 'src/editor/review.test.ts'
s = read(p)
s = replace_once(
    s,
    "const exercise = clone(getExercise('dumbbell_bicep_curl'));\n    const bar: EquipmentInstance = {",
    "const exercise = clone(getExercise('push_up'));\n    const bar: EquipmentInstance = {",
    'stable push-up fixture',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
s = replace_once(
    s,
    'Regression coverage appends a synthetic rigid barbell to the retained curl only inside the test: default 80 cm sockets correctly block automated approval, then the test measures the actual hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. No accepted exercise definition or curl animation was changed.',
    'Regression coverage appends a synthetic rigid barbell to the push-up only inside the test because its two hands are world-locked throughout the rep. Default 80 cm sockets correctly block automated approval; the test then measures the actual locked-hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. The earlier curl-based fixture was deliberately rejected because the curl allows small natural bilateral hand-spacing changes across the rep, which the new gate correctly detected. No accepted exercise definition or animation was changed.',
    'changelog stable fixture',
)
write(p, s)

print('Switched two-hand review regression to stable locked-hand fixture')
