# Zombie-family → Baby model converter

Turns an adult zombie-family CEM model into the matching baby model. Model authors only
have to make the adult model — this tool derives the child version, including the
proportion change, the per-face UVs and all part pivots.

Supported entities (their adult and baby skeletons are identical; drowned and husk are
just re-skins with an extra outer layer):

| entity | input | output |
| --- | --- | --- |
| zombie | `zombieX.jem` | `zombie_babyX.jem` |
| drowned | `drownedX.jem`, `drowned_outerX.jem` | `drowned_babyX.jem`, `drowned_baby_outerX.jem` |
| husk | `huskX.jem` | `husk_babyX.jem` |

Only **drowned** has an outer-layer model in vanilla; `husk_outer` / `zombie_outer` do not
exist and such files are skipped.

```
ZombieBabyConverter\
├─ Transformer.bat                <- double-click this (the entry point)
├─ README - EN.md / README - CN.md
├─ _engine\                       <- internal, leave it alone
│   ├─ babyfy.py                  <- conversion logic, no dependencies
│   ├─ zombie_baby_template.jem   <- vanilla baby model (part pivots; shared by all three)
│   └─ python\                    <- portable Python 3.12, so nothing has to be installed
└─ output\                        <- results land here (created automatically)
```

Only `Transformer.bat` and the models you want converted belong in the top folder;
`_engine\` is deliberately kept separate so it cannot be picked up or edited by accident.
Keep `_engine\python\` next to `babyfy.py` — that is the portable interpreter which makes
the tool work on a PC without Python.

## Usage

**1. Drop-in (most common)** — put `zombie12.jem` (or `drowned12.jem` / `husk12.jem`)
next to the bat, double-click `Transformer.bat`.

**2. Drag & drop** — drag one or several `.jem` files onto `Transformer.bat`.

**3. Batch** — drag a whole folder onto the bat, or run
`_engine\python\python.exe _engine\babyfy.py --dir "some\cem\folder"`.
Batch mode only picks up `zombie*` / `drowned*` / `husk*` models; other entities
(bee, cat, …) are skipped automatically.

Results go to `output\`:

| input | output |
| --- | --- |
| `zombie.jem` | `zombie_baby.jem` |
| `zombie12.jem` | `zombie_baby12.jem` |
| `drowned12.jem` | `drowned_baby12.jem` |
| `drowned_outer2.jem` | `drowned_baby_outer2.jem` |
| `my_zombie.jem` | `my_zombie_baby.jem` |

Copy the result — plus the matching `.properties` file — into
`assets/minecraft/optifine/cem/`.

Console output is English by default. On a Chinese Windows the bat switches to Chinese
by itself; pass `--zh` / `--en` to force one.

## What is converted

| Step | Rule |
| --- | --- |
| Box scaling | head ×0.75, `y' = 0.75y − 9`; body/arms x,z ×0.5, y ×5/12, `y' = 5/12y − 1`; legs x,z ×0.5, `y' = y/3` |
| Per-face UV | `textureOffset` is expanded into `uvNorth/East/South/West/Up/Down` using the **original** box dimensions, so the sampled texels do not move; `mirrorTexture: "u"` swaps east/west and reverses x |
| Part pivots | replaced by the vanilla baby pivots: head `[0,-8.75,0]`, body `[0,-6.5,0]`, arms `[±3,-8.5,0]`, legs `[±1,-4,0]`; `headwear` follows the head. Zombie, drowned and husk share these (same skeleton), so all three use the same template file |
| Sub-models | `translate`: level 1 is a model-space position (full affine), level 2+ is relative to its parent (pure scaling). Boxes: absolute when the sub-model has no `translate`, local otherwise |
| Everything else | `sizeAdd` scales with x; `animations / rotate / invertAxis / mirrorTexture / texture / textureSize / id / credit` are preserved |

## Notes

* Part names must be `head` / `body` / `left_arm` / `right_arm` / `left_leg` / `right_leg`
  (optionally `headwear`, `hat`). Anything else is reported and scaled like a body part.
* Boxes that already carry per-face UVs are not rewritten — only their coordinates scale.
* A `texture` field in the input is kept as-is (useful when the model forces a texture).
* `*_outer` models are supported for **drowned only** (EMF's `drowned_baby_outer`); the
  `_outer` part is kept in the output name. `husk_outer` / `zombie_outer` do not exist in
  vanilla or EMF and are skipped.
* **No Python installation needed.** `_engine\python\` is a portable Python 3.12.10
  (original embeddable build, trimmed to what the converter uses). The bat uses it first;
  if that folder is missing it falls back to `py -3`, then `python`, then the local `.dsh`
  runtime, and only then gives up with an explanatory message.
* The portable runtime is the official python.org build, PSF licence (`_engine\python\
  LICENSE.txt`). Nothing is installed and nothing is written outside this folder; the
  folder can be moved, renamed or put on a USB stick.
* Deleting `_engine\python\` does not break the tool on a machine that already has
  Python 3 — it just makes the tool depend on that installation again.

## Portable runtime

`_engine\python\` is the official `python-3.12.10-embed-amd64.zip` from python.org, with
the modules a `.jem` conversion never touches removed (SSL, SQLite, ctypes, unicodedata,
compression, …). That takes it from 21 MB to 11 MB. Checked by converting the pack's
331 adult zombie models once with this runtime and once with a normal Python 3.12: the
331 output files are byte-identical.
