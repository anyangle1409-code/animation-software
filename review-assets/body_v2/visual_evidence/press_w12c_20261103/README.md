# Shoulder press: W11 vs W12c (3 Nov 2026)

**Status:** review candidate. W11 and W5 are unchanged, and nothing is merged or deployed.

**What W12c adds to W11:**

1. **The armpit hollow (W12a):** the hollow is faired at the lockout. That is a 4.5 cm bi-Laplacian patch at
   (0.21, −0.015, 1.39) m, mirrored, in the lockout key. It removes fine radial lines in the hollow and softens the
   hard line on the anterior fold.
2. **The lower press angles (W12c):** the two fixes W5 and W7 made at the lockout are now made at 120° and 150° too.
   - The fixes are the guarded delta mush (pec wood-grain ripples) and the front-armpit fairing.
   - They live in their own keys, `R121_ARMBAND120_<s>` and `R121_ARMBAND150_<s>`. Each follows its press key and fades
     out above 50–70° of elbow flexion and towards forward raises (plane factor 0.3–0.6).
   - Without the gates (W12b) the same patch put 14 folds into the overhead extension, whose arms rise in the forward
     plane, and changed the squat.

**Stills:** `STILLS_press_<view>.jpg` show the rack (90°), intermediate (125°), near lockout (149°) and lockout (160°),
from three-quarter, front, side and back. Skeleton motion and cameras are identical in both columns.

**What to look at:**

- **At 125° and 149°:** the pecs are free of the wood-grain ripples, the pinched notch at the front armpit is
  softened, and the clavicle region is cleaner.
- **At lockout:** the armpit hollow is smoother.

**Metrics against W11** (17-frame harness):

- **Press and pulldown:** self-intersections and folds unchanged; stretched edges 8798 → 8734.
- **Overhead extension:** folds 59 → 51, self-intersections 365 → 338, edges over 35° 697 → 678.
- **Unchanged:** lateral raise, curl and squat are identical.
- **Worse:** collapsed edges +11 (press) and +40 (overhead extension). This is the faired hollow's skin shortening.
