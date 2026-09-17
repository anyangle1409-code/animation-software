# Model phase B, item 7 — skin and material

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `ac4907b`
**Candidates only. Production v8 untouched. Not merged.**

Skin and material only, on top of the accepted Phase A normals repair. Nothing else in the
refinement list was touched: no geometry, proportions, rig, weights, curl mechanics, eyes, hair,
face shape or shorts.

## Diagnosis — why the body read as a grey mannequin

The body primitive carried **no material at all**. glTF's default then applies: base colour white,
**metallic 1.0, roughness 1.0** — a fully metallic, fully rough surface, which is exactly the dull
grey mannequin look. The shorts, which *do* carry a material (metallic 0, roughness 0.94), read as
believable dark fabric in the same frame. That contrast was the tell.

`COLOR_0` existed on the body but was uniformly white (65535 everywhere), contributing nothing.

## Where the change had to go, and why

`CharacterFigure` sets `material.color` from its own `colour` prop on every build, defaulting to
white, and documents the intent: *"multiplies the body's own vertex colours; white leaves them as
authored."* So a `baseColorFactor` would be overwritten at load. The tone therefore belongs in
`COLOR_0`, where the renderer leaves it alone. Roughness and metalness are never touched by the
app, so those belong on the material.

Working with that split rather than against it is what makes this a material change and not a
renderer change.

## What was applied

`scratchpad/repair/skinmaterial.mjs`, run identically on the bare and dressed candidates.

**Material** — one new `HomeGymPT_Skin`: `metallicFactor 0`, `roughnessFactor 0.5`,
`baseColorFactor [1,1,1,1]` (white on purpose, since the renderer overwrites it).

**Tone** — `COLOR_0` set to linear `0.5704, 0.3186, 0.2140`, which is sRGB `0.780, 0.600, 0.500`:
a medium, warm, believable tone rather than a saturated orange.

**Subtle anatomical definition, without geometry** — each vertex's tone is multiplied by a
curvature term derived from the mesh's own surface: the discrete mean-curvature sign, i.e. where
the neighbourhood centroid sits along the vertex normal, scaled by local edge length so a dense
region is not read as flatter than a coarse one. Valleys darken, ridges lighten slightly.
Neighbours are gathered **by position**, so a UV seam does not cut the surface and leave a bright
line down an arm. Measured 95th-percentile curvature 0.3624, gain 0.331, final multiplier range
**0.860 – 1.050** — a ±5–14% modulation, deliberately subtle.

## Verified material-and-colour only

Dressed candidate before and after, every buffer compared:

| Mesh | Result |
|---|---|
| Body: POSITION, NORMAL, TEXCOORD_0/1, JOINTS_0/1/2, WEIGHTS_0/1/2, indices | **identical** |
| Body: COLOR_0 | 32,517 components differ — 10,839 vertices × RGB, alpha untouched |
| **Shorts mesh: every attribute and its indices** | **identical** |
| **Shorts material** | **identical** |
| Inverse binds, nodes, scene extras, skin joints | identical |

`COLOR_0` is byte-identical between the bare and dressed candidates, so the pair stays equivalent.

## Candidate assets

| Role | File | SHA-256 |
|---|---|---|
| Bare | `scratchpad/reference-fit/HomeGymPT_Male_SKIN_CANDIDATE.glb` | `d71b70bc340eadad52a89d429c357e971509b69962d0bf14588a9ae86c18f2be` |
| Dressed | `scratchpad/reference-fit/HomeGymPT_Male_SKIN_CANDIDATE_SHORTS.glb` | `8d07100f007dd842a8f4a090a3476c07c32be701e7d19c0890370606f08f27ca` |

Rollback chain intact: Phase A candidates `b3dc70e1…89fdf09` / `71c5bdef…9fe42da9`, and production
v8 `951c2c39…963ee0` / `cc728366…5722e3`, all byte-identical.

## Review captures

Neutral review lighting — the `light` backdrop, which is the same key/ambient/rim rig as the
working studio on a neutral ground, so before and after are lit identically. No selection gizmo in
any frame: nothing is selected for the body views, and the upper-body close-up is framed with the
focus camera and then deselected, which drops the gizmo while leaving the camera where it was.

Matched pairs at front, 3/4, side, upper body, and the curl at Bottom and Peak.

### A capture bug I hit and had to fix

The first attempt produced before and after sets that were **pixel-identical** — `rgb(105,105,105)`
on the chest in both. Sampling the pixels rather than trusting the screenshots is what caught it.

The cause is in the app, not the asset: every import registers under the same `'import'` source id,
and the preserve branch of `registerImport` does not bump `deformationRevision`, so on a second
import into the same session `sourceId` is unchanged and the cached build is reused — the second
file never renders. I did not change that code; it is not a curl problem and it is outside this
item. The fix was to capture each asset in its own browser session.

After that, the same chest pixel reads `rgb(105,105,105)` before and **`rgb(178,142,121)`** after,
with the face going from `rgb(0,0,0)` — the metallic default rendered it black — to
`rgb(81,55,42)`.

Both sessions proved the bundled dressed v8 loaded first (`baseline-dressed`,
`206 …v8_SHORTS.glb`), then imported exactly one candidate and confirmed `import` became the active
source, in Character mode on the `light` backdrop. No page errors, no failed requests.

## Honest read of the result

What works: the body now reads as warm human skin. Pectoral separation, serratus, abdominal
segmentation, the deltoid head and the clavicles all read at close range, and the forearms stay
smooth after the Phase A repair. At full-body distance the tone and sheen look natural, and the
shorts still read as dark fabric beside it.

One judgement call for you: at the upper-body close-up, `roughness 0.5` gives a slightly **wet**
sheen across the clavicles and the tops of the shoulders, and those highlights follow the
underlying surface irregularities. Raising roughness to about 0.6 would broaden and dull them. I
left it at 0.5 because the reference board's own photographs show pronounced studio sheen on the
shoulders, chest and arms, so 0.5 is defensible against the target — but it is a taste call and one
number to change if you disagree.

Two limits worth stating: roughness is a single value for the whole body, because per-region
variation (oilier chest, drier forearms) needs a roughness texture, which is a texturing item
rather than this one; and the tone has no regional variation for the same reason — redder knuckles
and elbows would need a base-colour map.

## Status

Skin and material applied and verified as material-only. No other appearance item started.
Stopped for review. **Not merged.**
