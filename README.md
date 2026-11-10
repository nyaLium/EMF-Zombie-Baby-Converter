# EMF-Zombie-Baby-Converter
Convert adult Zombie models into baby Zombie models

Supported entities:

| Entity | Input | Output |
| --- | --- | --- |
| Zombie | `zombieX.jem` | `zombie_babyX.jem` |
| Drowned | `drownedX.jem`, `drowned_outerX.jem` | `drowned_babyX.jem`, `drowned_baby_outerX.jem` |
| Husk | `huskX.jem` | `husk_babyX.jem` |

```
ZombieBabyConverter\
├─ Transformer.bat               <- double-click this
├─ README - EN.md / README - CN.md
├─ _engine\                      <- internal, leave it alone
│   ├─ babyfy.py                 <- conversion logic (nothing to edit)
│   ├─ zombie_baby_template.jem  <- vanilla baby model, provides the part pivots (shared by all three)
│   └─ python\                   <- portable Python 3.12, so nothing has to be installed
└─ output\                       <- results land here (created automatically)
```

## Usage

**1** — put `zombie12.jem` next to the bat, double-click `Transformer.bat`.

**2** — drag one or several `.jem` files onto `Transformer.bat`.

**3 (batch)** — drag a whole folder onto the bat, or run
`_engine\python\python.exe _engine\babyfy.py --dir "some\cem\folder"`.
Batch mode only picks up `zombie*` / `drowned*` / `husk*`

Results go to `output\`:

| Input | Output |
| --- | --- |
| `zombie.jem` | `zombie_baby.jem` |
| `zombie12.jem` | `zombie_baby12.jem` |
| `drowned12.jem` | `drowned_baby12.jem` |
| `drowned_outer2.jem` | `drowned_baby_outer2.jem` |
| `my_zombie.jem` | `my_zombie_baby.jem` |

## What gets converted

| Step | Rule |
| --- | --- |
| Box scaling | head ×0.75, `y' = 0.75y - 9`; body/arms x,z ×0.5, y ×5/12, `y' = 5/12y - 1`; legs x,z ×0.5, `y' = y/3` |
| Per-face UVs | `textureOffset` is expanded into `uvNorth/East/South/West/Up/Down` using the **original** box dimensions, so the sampled texels do not move; `mirrorTexture: "u"` swaps east/west and reverses x |
| Top-level pivots | replaced by the vanilla baby pivots: head `[0,-8.75,0]`, body `[0,-6.5,0]`, arms `[±3,-8.5,0]`, legs `[±1,-4,0]`; `headwear` follows the head. Zombie, drowned and husk share one template because they share one skeleton |
| Sub-models | `translate`: level 1 is a model-space position (full affine), level 2 and deeper are relative to the parent (pure scaling). Boxes: absolute when the sub-model has no `translate`, local when it has one |
| Everything else | `sizeAdd` scales with x; `animations / rotate / invertAxis / mirrorTexture / texture / textureSize / id / credit` are preserved |

## Notes

* Part names must be `head` / `body` / `left_arm` / `right_arm` / `left_leg` / `right_leg`
  (plus optional `headwear`, `hat`). Anything else is reported and scaled like a body part —
  that fallback is meant for non-humanoid models and is not recommended.
* Boxes that already carry per-face UVs are not rewritten — only their coordinates scale.
* A `texture` field in the input is kept as-is (useful when the model forces a texture).
* **No Python installation needed.** `_engine\python\` is a portable Python 3.12.10 (the
  official embeddable build, with the modules a conversion never touches removed). The bat
  uses it first; only if that folder is missing does it fall back to `py -3`, then `python`,
  then the local `.dsh` runtime, and only then does it stop with an explanatory message.
* The portable runtime is the official python.org build, PSF licence
  (`_engine\python\LICENSE.txt`). Nothing is installed, no registry entries are written;
  the folder can be moved, renamed or put on a USB stick.
* On a machine that already has Python 3, deleting `_engine\python\` still works — it just
  makes the tool depend on that installation again.
