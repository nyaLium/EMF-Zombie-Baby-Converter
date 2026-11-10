# 僵尸系 → 幼年模型 转换器

> English version: see `README - EN.md`（英文说明，便于对外交流）。
> 命令行输出默认**英文**；在中文 Windows 上 bat 会自动切成中文，
> 也可以手动加 `--zh` / `--en` 指定。

把一份成人僵尸系 CEM 模型转成对应的幼年模型。开发者只需要做成人模型，其余交给这个工具。

支持的实体（三者成年/幼年骨架完全一致，溺尸与尸壳只是换皮）：

| 实体 | 输入 | 输出 |
| --- | --- | --- |
| 僵尸 zombie | `zombieX.jem` | `zombie_babyX.jem` |
| 溺尸 drowned | `drownedX.jem`、`drowned_outerX.jem` | `drowned_babyX.jem`、`drowned_baby_outerX.jem` |
| 尸壳 husk | `huskX.jem` | `husk_babyX.jem` |

外层模型只有溺尸有（`drowned_outer`）；`husk_outer` / `zombie_outer` 在 vanilla 与 EMF 里都不存在，
这类文件会被当作不支持的模型跳过。

```
ZombieBabyConverter\
├─ Transformer.bat               ← 双击这个
├─ README - CN.md / README - EN.md
├─ _engine\                      ← 内部文件，别动
│   ├─ babyfy.py                 ← 转换逻辑（不用改）
│   ├─ zombie_baby_template.jem  ← 原版小僵尸模型，提供各部件枢轴（三者共用）
│   └─ python\                   ← 便携版 Python 3.12，装了它就不需要装 Python
└─ output\                       ← 结果输出到这里（自动创建）
```

外层只放 `Transformer.bat` 和要转的模型；`babyfy.py`、模板和便携 Python 放进了 `_engine\`，
免得被误删、误改，或被当成待转换的模型扫进去。`_engine\python\` 要和 `babyfy.py` 放在一起
——它就是让这个工具在没有 Python 的电脑上也能跑的东西。

## 怎么用

**方式一（最常用）**：把 `zombie12.jem` 放到本文件夹（和 bat 同级），双击 `Transformer.bat`。

**方式二**：把一个或多个 `.jem` 直接拖到 `Transformer.bat` 上。

**方式三（批量）**：把一个文件夹拖到 bat 上，或命令行
`_engine\python\python.exe _engine\babyfy.py --dir "某个\cem\文件夹"`。
批量模式只处理 `zombie*` / `drowned*` / `husk*`，其它实体（bee、cat…）自动跳过。

结果统一在 `output\` 里，文件名：

| 输入 | 输出 |
| --- | --- |
| `zombie.jem` | `zombie_baby.jem` |
| `zombie12.jem` | `zombie_baby12.jem` |
| `drowned12.jem` | `drowned_baby12.jem` |
| `drowned_outer2.jem` | `drowned_baby_outer2.jem` |
| `my_zombie.jem` | `my_zombie_baby.jem` |

把结果连同原来的 `.properties` 一起放进 `assets/minecraft/optifine/cem/` 即可。

## 转换了什么

| 步骤 | 规则 |
| --- | --- |
| 盒体缩放 | head ×0.75、`y' = 0.75y − 9`；body/arm x,z ×0.5、y ×5/12、`y' = 5/12y − 1`；leg x,z ×0.5、`y' = y/3` |
| 逐面 UV | 用**原始**盒体尺寸把 `textureOffset` 展开成 `uvNorth/East/South/West/Up/Down`，贴图采样位置不变；`mirrorTexture: "u"` 会交换 east/west 并对调 x |
| 顶层枢轴 | 换成原版小僵尸的枢轴：head `[0,-8.75,0]`、body `[0,-6.5,0]`、arm `[±3,-8.5,0]`、leg `[±1,-4,0]`，`headwear` 跟随 head。僵尸/溺尸/尸壳同骨架，共用同一份模板 |
| 子模型 | `translate`：第 1 层按绝对坐标走完整仿射，第 2 层及更深按相对父级纯缩放；盒体：没有 `translate` 的按模型空间（绝对）处理，有的按局部处理 |
| 其它 | `sizeAdd` 按 x 比例缩放；`animations / rotate / invertAxis / mirrorTexture / texture / textureSize / id / credit` 原样保留 |

## 注意

* 部件名必须是 `head` / `body` / `left_arm` / `right_arm` / `left_leg` / `right_leg`（可加 `headwear`、`hat`）。
  出现别的名字会提示，并按 body 的比例处理 —— 那是给非人形模型用的，不建议。
* 已经有逐面 UV 的盒子不会被改写，只缩放坐标。
* 输入里的 `texture` 字段会原样保留（该模型强制指定贴图时有用）。
* 外层模型只有溺尸有：`drowned_outer` → `drowned_baby_outer`，输出保留 `_outer` 位置，与 EMF 命名一致。
  `husk_outer` / `zombie_outer` 不存在，这类文件会被跳过并提示。
* **不需要装 Python**：`_engine\python\` 是便携版 Python 3.12.10（官方 embeddable 包，
  去掉了转换用不到的模块）。bat 优先用它；这个文件夹被删了才会回退到 `py -3`、`python`、
  本机 `.dsh` 内置的 Python，都没有时给出一条说明性的报错。
* 便携运行时是 python.org 的官方构建，PSF 许可（`_engine\python\LICENSE.txt`）。不写注册表、
  不装任何东西，整个文件夹可以随便移动、改名、放 U 盘。
* 如果对方的电脑本来就有 Python 3，删掉 `_engine\python\` 也能继续用（只是又变成依赖本机 Python）。

## 便携运行时

`_engine\python\` 来自 python.org 的 `python-3.12.10-embed-amd64.zip`，删掉了 `.jem` 转换
根本不会碰的模块（SSL、SQLite、ctypes、unicodedata、压缩库等），体积从 21 MB 降到 11 MB。
用这套运行时和一台机器上正常的 Python 3.12 分别转包里的 331 个成人僵尸模型，
331 个输出文件**逐字节相同**。
