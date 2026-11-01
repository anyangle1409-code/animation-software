# How a real body deforms in the Home Gym PT movements (reference notes, 1 Nov 2026)

**Purpose:** the owner asked for a review of how muscles and skin deform on real bodies in these movements, to guide
the remaining fixes. The notes below are the targets the model is judged against.

**What could be read from here:**

- **Blocked:** this session's network policy blocks the image and video hosts tried. These are Wikimedia Commons,
  Proko, Anatomy for Sculptors, ABMP and IFSSH. So no photograph or video was viewed in this review.
- **Earlier owner photos:** the owner's reference photos used on 20 and 30 Oct were seen in chat only and are not
  stored. That follows the rule that no reference photos go in git.
- **Basis:** the notes come from the anatomy and artist-anatomy sources that web search could reach, quoted below,
  and from standard surface anatomy where marked.
- **To unblock:** allowing those hosts in the environment's network settings would allow a real photo and video
  review.

## 1. Arms overhead (press lockout, pulldown top, overhead extension)

**What the sources say:**

- **Pectoralis major:**
  - "When the arm raises the muscle mass keeps its thickness near the armpit … More of the stretching happens closer
    to the sternum" (Proko, *How to draw pecs – form*).
  - "When the arm is raised, the lower mass of the pec thins, and the lower border becomes harder to distinguish"
    (Proko).
- **Fibre twist:** "Prior to inserting on the humerus, the fibers of the pectoralis major fold and twist, forming the
  thick anterior border of the axilla … Fully flexing the shoulder unwinds the twist" (ABMP, *Pectoralis major*).
- **Anterior axillary fold:** the lower margin of pectoralis major forms it (Elsevier anatomy;
  clinicalgate *Pectoral girdle, shoulder region and axilla*). With the arm raised, the lowest slip of pectoralis
  minor adds a bulge just beneath the fold, softening its edge (Wikibooks *MCEM anatomy: upper limb*).
- **Armpit hollow:** the axillary fascia hangs from the fascia around pectoralis minor; tension on it makes the
  hollow (Dartmouth *Human Anatomy*, ch. 8).
- **Folds relative to each other:** the anterior fold sits higher than the posterior fold (Mustansiriyah lecture,
  *Anatomy of axilla*).
- **Scapula and acromion:** above shoulder level, the scapula rotates with the humerus (Anatomy for Sculptors,
  *Shoulder bony landmarks*). Small dimples near the acromion can show with the arm raised (lower-authority source).

**Skin mechanics:** skin wrinkles when it is compressed or sheared (it buckles). Skin under tension does not
(Galway / Destrade group papers on skin buckling and shear instability; Binghamton study via New Atlas). The
inference used here, not stated by the sources in these words: **skin that is stretched in a pose should look smooth,
and wrinkles belong only where the skin is shortened.**

**What this means for the model at the press lockout:**

| Real body | Our candidate W5 at lockout | Verdict |
|---|---|---|
| Chest and upper-arm skin are stretched, so smooth | Chest smooth after W5; fine ripples left on the upper arms | Upper-arm ripples are wrong. W6 is under test |
| The anterior axillary fold is **one** rounded ridge, softened by the pectoralis minor bulge beneath it | Two or three thin parallel lines at each front armpit | Wrong. W7 (fairing) softens them a little. More needed |
| The pec's **lower mass thins and its lower border fades**. Stretch is concentrated near the sternum; thickness is kept near the armpit | The pecs keep a round, full standing shape with a crisp lower border | **Shape mismatch, not yet addressed** |
| The armpit hollow is a smooth, taut concavity | A deep hollow with fine webbing lines | Lines are wrong |
| The posterior fold (lat, teres major) sits lower than the anterior | The posterior fold is present, as judged on 30 Oct | OK |
| Clavicles elevate and their lower edges show | Clavicle edges visible below the neck | OK (expected) |

## 2. Closed fist (grip)

**What the sources say:**

- **Creases:** the palmar flexion creases are where skin is most tightly bound to the deep fascia. They let the skin
  fold without bunching when the hand closes (scienceabc; hand clinical anatomy lecture notes). The superficial fascia
  of the palm is dense fibrous bands anchoring skin to deep fascia. There are usually two creases per finger joint,
  the proximal one most prominent (IFSSH terminology, ch. 5).
- **Knuckles:** in a fist they form an arc with the middle finger's knuckle highest. The visible knuckles are the
  metacarpal heads. The first palm line runs along the border of the fat pad that covers the knuckles on the palm
  side (Anatomy for Sculptors / Proko hand notes, from search snippets).
- **Back of the hand:** the dorsal skin is thin and stretches tight over the metacarpal heads as the fingers curl
  (hand anatomy explainer). The metacarpal head is wider on its palmar side (orthopaedic reference).
- **Hypothenar side:** palmaris brevis corrugates the skin at the base of the hypothenar eminence in a grip (lecture
  slides).

**What this means for the model at the closed fist:**

| Real body | Our model (C1 / W5) | Verdict |
|---|---|---|
| The skin folds sharply **at** the crease lines and the folded sides press flat against each other; they do not pass through | 155 skin-through-skin pairs: thumb MCP crease 19 per hand, ring knuckle against the palm 12 per hand, smaller knuckle creases | The contact is right in kind, but the skin must meet, not overlap. A palm-crease contact corrective is needed |
| The fat pad at the base of the fingers (palm side) bulges and is pressed by the folded fingers | Not modelled as a separate shape | Part of the contact fix |
| Dorsal skin is tight and smooth over a knuckle arc, middle knuckle highest | Shape follows the bones (smooth) | Check in close-up |

## 3. Bent-over row (top of the pull)

The search found no surface-appearance description here. The sources cover only the action:

- rowing works the middle trapezius, rhomboids and latissimus, the aim being scapular retraction (Robertson Training
  Systems; Eric Cressey).
- the rhomboids lie deep between the shoulder blades and are hard to see; the trapezius and lats dominate the
  surface.

From standard surface anatomy, not sourced here: in retraction the medial borders of the scapulae approach the spine.
The skin between them shortens and bunches into soft vertical folds over the trapezius. The posterior deltoid
contracts into a rounded mass.

**What this means for the model:** compressed skin may fold here. The left posterior-shoulder crossing (57 pairs) is
the folded skin passing through itself, which is the same kind of fix as the fist: the skin should meet, not
overlap.

## Order of work from these notes

1. The pinched front-armpit lines and the upper-arm ripples (W6 / W7 under test).
2. **New:** the pec's lower mass thinning, with its lower border fading, at full elevation. A shape corrective on the
   lockout key, scaled into the pulldown and the overhead extension.
3. Fist palm-crease contact: skin meets skin.
4. Row posterior-shoulder contact: the same method.

## Sources (reached through web search snippets; the pages themselves were blocked)

- Proko, *How to Draw Pecs – Form*: https://proko.com/course-lesson/how-to-draw-pecs-form
- ABMP, *Pectoralis Major* (Jan/Feb 2015): https://www.abmp.com/massage-and-bodywork-magazine/issues/januaryfebruary-2015/pectoralis-major
- Elsevier, pectoralis major: https://www.elsevier.com/resources/anatomy/muscular-system/muscles-of-upper-limb/pectoralis-major-muscle/18194
- Clinicalgate, *Pectoral girdle, shoulder region and axilla*: https://clinicalgate.com/pectoral-girdle-shoulder-region-and-axilla/
- Wikibooks, *MCEM Part A: Upper limb*: https://en.wikibooks.org/wiki/MCEM_Part_A_Study_Guide/Anatomy/Upper_Limb
- Dartmouth, *Human Anatomy*, ch. 8: https://humananatomy.host.dartmouth.edu/BHA/public_html/part_2/chapter_8.html
- Mustansiriyah lecture, *Anatomy of axilla*: https://uomustansiriyah.edu.iq/media/lectures/2/2_2024_11_25!10_58_06_PM.pdf
- Anatomy for Sculptors, *Shoulder bony landmarks*: https://anatomy4sculptors.com/blog/shoulder-bony-landmarks/
- Anatomy for Sculptors, *Realistic hand*: https://anatomy4sculptors.com/blog/realistic-hand-tendons-veins-fat/
- Proko, *Realistic hands*: https://www.proko.com/course-lesson/how-to-draw-hands-details-for-realistic-hands/notes
- IFSSH terminology, ch. 5: https://www.ifssh.info/TerminologyPdfs/Chapter-5.pdf
- Springer, palmar creases: https://link.springer.com/article/10.1007/s00276-013-1211-4
- New Atlas, skin wrinkle mechanics: https://newatlas.com/aging/age-skin-wrinkles-mechanics
- Destrade et al., shear instability in skin: https://research.universityofgalway.ie/en/publications/shear-instability-in-skin-tissue-3/
- Eric Cressey, *How the rhomboids really work*: https://ericcressey.com/newsletter138html/
- Robertson Training Systems, *Row right*: https://robertsontrainingsystems.com/blog/row-right-get-more-bang-for-your-buck/
