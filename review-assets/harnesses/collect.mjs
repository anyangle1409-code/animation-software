// Copy the existing review captures into one clearly named folder.
// Nothing is re-rendered and nothing is committed: the destination is inside
// the gitignored scratchpad.
import { copyFileSync, mkdirSync, writeFileSync } from 'node:fs';

const FROM = '/home/user/animation-software/scratchpad/repair';
const TO = '/home/user/animation-software/scratchpad/REVIEW_2026-09-15';
mkdirSync(TO, { recursive: true });

const files = [
  // --- hand/wrist candidate versus proven v5, matched frame and camera ------
  ['shots/v5_curl_peak_focus.png', 'A1_curlPeak_v5.png',
    'Curl Peak 2.00s, left hand, Focus camera, void backdrop — PROVEN v5'],
  ['shots/c035_curl_peak_focus.png', 'A1_curlPeak_candidate.png',
    'Curl Peak 2.00s, left hand, Focus camera, void backdrop — HAND/WRIST CANDIDATE'],
  ['shots/v5_curl_peak_under.png', 'A2_curlPeak_underside_v5.png',
    'Curl Peak 2.00s, left hand from underneath — PROVEN v5'],
  ['shots/c035_curl_peak_under.png', 'A2_curlPeak_underside_candidate.png',
    'Curl Peak 2.00s, left hand from underneath — HAND/WRIST CANDIDATE'],

  ['shots/v5_curl_bottom_L.png', 'B1_curlBottom_leftHand_v5.png',
    'Curl Bottom 0.00s, LEFT hand, Focus camera — PROVEN v5'],
  ['shots/c035_curl_bottom_L.png', 'B1_curlBottom_leftHand_candidate.png',
    'Curl Bottom 0.00s, LEFT hand, Focus camera — HAND/WRIST CANDIDATE'],
  ['shots/v5_curl_bottom_L_orbit.png', 'B2_curlBottom_leftHand_orbit_v5.png',
    'Curl Bottom 0.00s, LEFT hand, orbited round — PROVEN v5'],
  ['shots/c035_curl_bottom_L_orbit.png', 'B2_curlBottom_leftHand_orbit_candidate.png',
    'Curl Bottom 0.00s, LEFT hand, orbited round — HAND/WRIST CANDIDATE'],
  ['shots/v5_curl_bottom_R.png', 'B3_curlBottom_rightHand_v5.png',
    'Curl Bottom 0.00s, RIGHT hand, Focus camera — PROVEN v5'],
  ['shots/c035_curl_bottom_R.png', 'B3_curlBottom_rightHand_candidate.png',
    'Curl Bottom 0.00s, RIGHT hand, Focus camera — HAND/WRIST CANDIDATE'],

  ['shots/v5_press_hand.png', 'C1_shoulderPress_v5.png',
    'Shoulder press 2.35s of 4.70s, left hand, Focus camera — PROVEN v5'],
  ['shots/c035_press_hand.png', 'C1_shoulderPress_candidate.png',
    'Shoulder press 2.35s of 4.70s, left hand, Focus camera — HAND/WRIST CANDIDATE'],
  ['shots/v5_press_hand_orbit.png', 'C2_shoulderPress_orbit_v5.png',
    'Shoulder press 2.35s, left hand, orbited round — PROVEN v5'],
  ['shots/c035_press_hand_orbit.png', 'C2_shoulderPress_orbit_candidate.png',
    'Shoulder press 2.35s, left hand, orbited round — HAND/WRIST CANDIDATE'],

  ['shots/v5_pushup_hand.png', 'D1_pushUp_v5.png',
    'Push-up 1.58s of 3.50s (bottom), left hand, Focus camera — PROVEN v5'],
  ['shots/c035_pushup_hand.png', 'D1_pushUp_candidate.png',
    'Push-up 1.58s of 3.50s (bottom), left hand, Focus camera — HAND/WRIST CANDIDATE'],
  ['shots/v5_pushup_hand_orbit.png', 'D2_pushUp_orbit_v5.png',
    'Push-up 1.58s, left hand, orbited round — PROVEN v5'],
  ['shots/c035_pushup_hand_orbit.png', 'D2_pushUp_orbit_candidate.png',
    'Push-up 1.58s, left hand, orbited round — HAND/WRIST CANDIDATE'],

  ['shots/v5_pullup_hand.png', 'E1_pullUp_v5.png',
    'Pull-up 1.98s of 4.40s, left hand, Focus camera — PROVEN v5'],
  ['shots/c035_pullup_hand.png', 'E1_pullUp_candidate.png',
    'Pull-up 1.98s of 4.40s, left hand, Focus camera — HAND/WRIST CANDIDATE'],
  ['shots/v5_pullup_hand_orbit.png', 'E2_pullUp_orbit_v5.png',
    'Pull-up 1.98s, left hand, orbited round — PROVEN v5'],
  ['shots/c035_pullup_hand_orbit.png', 'E2_pullUp_orbit_candidate.png',
    'Pull-up 1.98s, left hand, orbited round — HAND/WRIST CANDIDATE'],

  ['shots/v5_rest_front.png', 'F1_wholeFigure_v5.png',
    'Whole figure, front camera, curl Bottom — PROVEN v5 (reference)'],
  ['shots/c035_rest_front.png', 'F1_wholeFigure_candidate.png',
    'Whole figure, front camera, curl Bottom — HAND/WRIST CANDIDATE (reference)'],
  ['shots/diff_rest_front.png', 'F2_wholeFigure_pixelDiff.png',
    'Pixel diff of the two above; red = changed. Solid red only at the two hands/wrists'],

  ['shots/compare_curl_peak.png', 'SHEET_1_curlPeak_v5_vs_candidate.png',
    'Contact sheet: curl Peak, v5 left / candidate right'],
  ['shots/compare_curl_bottom.png', 'SHEET_2_curlBottom_v5_vs_candidate.png',
    'Contact sheet: curl Bottom both hands, v5 left / candidate right'],
  ['shots/compare_cross.png', 'SHEET_3_press_pushUp_pullUp_v5_vs_candidate.png',
    'Contact sheet: press, push-up, pull-up, v5 left / candidate right'],

  // --- shorts, all on PROVEN v5 --------------------------------------------
  ['shorts/s3_air_squat_stand_front.png', 'G1_shorts_standing_front.png',
    'Shorts on v5 — standing (squat 0.00s of 4.40s), FRONT camera, studio backdrop'],
  ['shorts/s3_air_squat_stand_left.png', 'G2_shorts_standing_side.png',
    'Shorts on v5 — standing, SIDE (left) camera'],
  ['shorts/s3_air_squat_stand_rear.png', 'G3_shorts_standing_rear.png',
    'Shorts on v5 — standing, REAR camera (studio backdrop is backlit here)'],
  ['shorts/s3_air_squat_stand_front_hips.png', 'G4_shorts_standing_front_hips.png',
    'Shorts on v5 — standing, FRONT, hip/groin close crop'],

  ['shorts/s3_air_squat_half_front.png', 'H1_shorts_halfSquat_front.png',
    'Shorts on v5 — half-depth squat (1.10s of 4.40s), FRONT camera'],
  ['shorts/s3_air_squat_half_left.png', 'H2_shorts_halfSquat_side.png',
    'Shorts on v5 — half-depth squat, SIDE camera'],
  ['shorts/s3_air_squat_half_rear.png', 'H3_shorts_halfSquat_rear.png',
    'Shorts on v5 — half-depth squat, REAR camera'],

  ['shorts/s3_air_squat_deep_front.png', 'J1_shorts_deepSquat_front.png',
    'Shorts on v5 — DEEPEST squat (2.20s of 4.40s), FRONT camera'],
  ['shorts/s3_air_squat_deep_left.png', 'J2_shorts_deepSquat_side.png',
    'Shorts on v5 — DEEPEST squat, SIDE camera'],
  ['shorts/s3_air_squat_deep_rear.png', 'J3_shorts_deepSquat_rear.png',
    'Shorts on v5 — DEEPEST squat, REAR camera'],
  ['shorts/s3_air_squat_deep_front_hips.png', 'J4_shorts_deepSquat_front_hips_PENETRATION_VIEW.png',
    'Shorts on v5 — DEEPEST squat, FRONT, hip/groin close crop. This is the view used to '
      + 'judge the -15 mm front-of-pelvis reading; the reading is at the centre front panel'],
  ['shorts/s3_air_squat_deep_left_hips.png', 'J5_shorts_deepSquat_side_hips_PENETRATION_VIEW.png',
    'Shorts on v5 — DEEPEST squat, SIDE, hip/groin close crop. Second view used for the '
      + 'same -15 mm reading'],

  ['shorts/s3_dumbbell_bicep_curl_bottom_front.png', 'K1_shorts_curlBottom_front.png',
    'Shorts on v5 — dumbbell curl bottom (0.00s), FRONT camera'],
  ['shorts/s3_dumbbell_bicep_curl_bottom_left.png', 'K2_shorts_curlBottom_side.png',
    'Shorts on v5 — dumbbell curl bottom, SIDE camera'],
  ['shorts/s3_dumbbell_shoulder_press_mid_front.png', 'K3_shorts_shoulderPress_front.png',
    'Shorts on v5 — shoulder press (2.35s of 4.70s), FRONT camera'],
  ['shorts/s3_push_up_bottom_left.png', 'K4_shorts_pushUp_side.png',
    'Shorts on v5 — push-up bottom (1.58s of 3.50s), SIDE camera'],
  ['shorts/s3_push_up_bottom_front.png', 'K5_shorts_pushUp_front.png',
    'Shorts on v5 — push-up bottom, FRONT camera'],
  ['shorts/s3_pull_up_mid_front.png', 'K6_shorts_pullUp_front.png',
    'Shorts on v5 — pull-up (1.98s of 4.40s), FRONT camera'],
  ['shorts/s3_pull_up_mid_left.png', 'K7_shorts_pullUp_side.png',
    'Shorts on v5 — pull-up, SIDE camera'],

  ['shorts/shorts_squat.png', 'SHEET_4_shorts_squat_front_and_side.png',
    'Contact sheet: shorts through the squat, front and side'],
  ['shorts/shorts_hips.png', 'SHEET_5_shorts_hip_closeups.png',
    'Contact sheet: shorts hip/groin close-ups'],
  ['shorts/shorts_other.png', 'SHEET_6_shorts_other_exercises.png',
    'Contact sheet: shorts in curl, press, push-up, pull-up'],

  // --- accepted curl motion, for completeness ------------------------------
  ['shots/playback_cand_normal.png', 'M1_curlPlayback_1x_candidate.png',
    'Curl played at 1x on the HAND/WRIST CANDIDATE, 24 frames as a contact sheet'],
  ['shots/playback_cand_slow.png', 'M2_curlPlayback_quarterSpeed_candidate.png',
    'Curl played at 0.25x on the HAND/WRIST CANDIDATE, 24 frames as a contact sheet'],
];

const lines = ['# Review captures — 2026-09-15', ''];
lines.push('All images were captured earlier in this session; none was re-rendered for this folder.');
lines.push('');
lines.push('Bodies used:');
lines.push('  PROVEN v5             HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb        dfb0fea6…');
lines.push('  HAND/WRIST CANDIDATE  HomeGymPT_Male_HAND_WRIST_WEIGHT_CANDIDATE.glb  46180b57…');
lines.push('  SHORTS (on v5)        HomeGymPT_Male_SHORTS_CANDIDATE.glb             cdca3f3e…');
lines.push('');
lines.push('| file | what you are looking at |');
lines.push('|---|---|');

let copied = 0;
for (const [from, to, description] of files) {
  try {
    copyFileSync(`${FROM}/${from}`, `${TO}/${to}`);
    lines.push(`| \`${to}\` | ${description} |`);
    copied += 1;
  } catch (error) {
    lines.push(`| \`${to}\` | MISSING (${from}) |`);
    console.log('missing:', from);
  }
}

writeFileSync(`${TO}/INDEX.md`, `${lines.join('\n')}\n`);
console.log(`copied ${copied} of ${files.length} into ${TO}`);
