# Third-party assets

## MakeHuman anatomical base

The built-in character in the split `src/body/anatomical*.ts` modules is
generated from the MakeHuman project's CC0 data files:

- `makehuman/data/3dobjs/base.obj`
- `makehuman/data/rigs/default_weights.mhw`
- `makehuman/data/rigs/default.mhskel`
- `makehuman/data/targets/macrodetails/caucasian-male-young.target`
- `makehuman/data/targets/macrodetails/universal-male-young-maxmuscle-averageweight.target`

Upstream repository: <https://github.com/makehumancommunity/makehuman>

The source OBJ identifies the asset as CC0, and the weights and skeleton files
declare their licence as CC0. The generated geometry contains no MakeHuman
application code. `scripts/generate-anatomical-body.mjs` records the complete
conversion and accepts the directory containing those five files through the
`MAKEHUMAN_SOURCE_DIR` environment variable.
