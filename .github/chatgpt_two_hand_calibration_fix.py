from pathlib import Path


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


p = 'src/equipment/twoHandAttachment.test.ts'
s = read(p)
s = replace_once(s, '  result.apply(restPose(canonicalSkeleton));', '  result.apply(restPose());', 'restPose signature')
s = replace_once(
    s,
    """    const rolled: EquipmentInstance = {
      ...calibrated,
      attachment: { ...calibrated.attachment, gripRoll: 17 },
    };
    const before = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const after = resolveEquipment(pose, [rolled]).get(base.id)!;
    const beforeFit = measureTwoHandFit(pose, calibrated, before)!;
    const afterFit = measureTwoHandFit(pose, rolled, after)!;""",
    """    if (calibrated.attachment.mode !== 'hands') throw new Error('Expected two-hand attachment');
    const rolled: EquipmentInstance = {
      ...calibrated,
      attachment: { ...calibrated.attachment, gripRoll: 17 },
    };
    const before = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const after = resolveEquipment(pose, [rolled]).get(base.id)!;
    const afterFit = measureTwoHandFit(pose, rolled, after)!;""",
    'narrow two-hand attachment',
)
write(p, s)

p = 'src/viewer/EquipmentView.tsx'
s = read(p)
s = replace_once(
    s,
    """        const local = twoHandAttachmentMatrix(leftHand, rightHand, instance);
        if (local) {
          group.visible = true;
          group.matrix.copy(local);
          group.matrixWorldNeedsUpdate = true;
          continue;
        }""",
    """        const local = leftHand && rightHand
          ? twoHandAttachmentMatrix(leftHand, rightHand, instance)
          : null;
        if (local) {
          group.visible = true;
          group.matrix.copy(local);
          group.matrixWorldNeedsUpdate = true;
          continue;
        }""",
    'nullable imported hand matrices',
)
write(p, s)

print('Applied two-hand calibration TypeScript fixes')
