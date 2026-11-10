#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
babyfy.py -- 僵尸系 CEM 模型（.jem）-> 幼年 CEM 模型 转换器

支持的实体（三者成年/幼年骨架完全一致，溺尸与尸壳只是换皮）：

    zombie        僵尸
    drowned       溺尸（另有外层模型 drowned_outer）
    husk          尸壳

`*_outer` 只对溺尸有效（drowned_outer -> drowned_baby_outer）；husk_outer /
zombie_outer 在 vanilla 与 EMF 里都不存在。

配套 `Transformer.bat` 使用，不依赖任何第三方库。

把成人模型放到工具目录下，双击 bat（或把 .jem / 文件夹拖到 bat 上），
就会在 output\ 里生成 <原名>_baby.jem：

    zombie.jem          -> zombie_baby.jem
    zombie12.jem        -> zombie_baby12.jem
    drowned12.jem       -> drowned_baby12.jem
    drowned_outer2.jem  -> drowned_baby_outer2.jem
    my_zombie.jem       -> my_zombie_baby.jem

注意：只有溺尸有外层模型（drowned_outer）。husk_outer / zombie_outer 在
vanilla 与 EMF 里都不存在，这类文件名会被当作不支持的模型跳过。

转换内容：
  1. 盒体缩放（原版幼体比例）
        head        x/z/y x0.75       y' = 0.75y - 9
        body/arm    x/z x0.5  y x5/12 y' = 5/12 y - 1
        leg         x/z x0.5  y x1/3  y' = y/3
  2. textureOffset（箱式 UV）展开成逐面 UV，面区域按**原始**盒体尺寸算，
     所以贴图采样位置不变；mirrorTexture: "u" 会交换 east/west 并对调 x
  3. 顶层部件的 translate（= 旋转枢纽）改用原版 zombie_baby 模板的值
     （溺尸 / 尸壳与僵尸同骨架，共用同一份模板）
  4. 子模型的 translate：第 1 层（顶层部件的直接子级）按绝对坐标走完整仿射，
     第 2 层及更深按相对父级做纯缩放

其余键（animations / rotate / invertAxis / mirrorTexture / texture /
textureSize / credit / id / sizeAdd）原样保留或按比例缩放。
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))      # ...\ZombieBabyConverter\_engine
ROOT = os.path.dirname(HERE)                            # ...\ZombieBabyConverter
TEMPLATE = os.path.join(HERE, "zombie_baby_template.jem")
OUT_DIR = os.path.join(ROOT, "output")

# 支持的实体：这三者的成年/幼年骨架完全一致（溺尸、尸壳只是换皮 + 外层）
ENTITIES = ("zombie", "drowned", "husk")

# 每个实体允许的附层后缀：只有溺尸有外层模型（drowned_outer）。
# husk_outer / zombie_outer 在 vanilla 与 EMF 里都不存在，不接受。
ENTITY_SUFFIXES = {
    "zombie": ("",),
    "drowned": ("", "_outer"),
    "husk": ("",),
}

# part -> (sx, sy, sz, b)      y' = sy*y + b
PARTS = {
    "head": (0.75, 0.75, 0.75, -9.0),
    "headwear": (0.75, 0.75, 0.75, -9.0),
    "body": (0.50, 5.0 / 12.0, 0.50, -1.0),
    "left_arm": (0.50, 5.0 / 12.0, 0.50, -1.0),
    "right_arm": (0.50, 5.0 / 12.0, 0.50, -1.0),
    "left_leg": (0.50, 1.0 / 3.0, 0.50, 0.0),
    "right_leg": (0.50, 1.0 / 3.0, 0.50, 0.0),
}
FALLBACK = "body"
UV_KEYS = ("uvNorth", "uvEast", "uvSouth", "uvWest", "uvUp", "uvDown")
UV_ALIASES = ("uvFront", "uvBack", "uvLeft", "uvRight")
SKIP_NAMES = {"zombie_baby_template.jem"}

# ------------------------------------------------------------------ language
# Console text is English by default so the tool can be shared as-is;
# pass --zh to get the Chinese wording back.
LANG = "en"


def t(en: str, zh: str) -> str:
    return en if LANG == "en" else zh


def num(v):
    v = round(float(v), 5)
    return int(v) if abs(v - int(v)) < 1e-9 else v


# ------------------------------------------------------------------ 枢轴模板
def load_template(path: str) -> dict:
    if not os.path.exists(path):
        raise SystemExit(t("Pivot template not found: %s" % path,
                           "找不到枢轴模板：%s" % path))
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    piv = {m["part"]: [float(v) for v in m.get("translate", [0, 0, 0])]
           for m in doc.get("models", []) if m.get("part")}
    if "head" in piv:
        piv.setdefault("headwear", list(piv["head"]))
    return piv


# ------------------------------------------------------------------- 逐面 UV
def face_uv(offset, dims, mirror: bool) -> dict:
    u, v = offset
    w, h, d = dims
    north = (u + d, v + d, u + d + w, v + d + h)
    east = (u, v + d, u + d, v + d + h)
    south = (u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h)
    west = (u + d + w, v + d, u + 2 * d + w, v + d + h)
    up = (u + d, v, u + d + w, v + d)
    down = (u + d + w, v, u + 2 * w + d, v + d)
    if mirror:
        return {
            "uvNorth": [num(north[2]), num(north[1]), num(north[0]), num(north[3])],
            "uvEast": [num(west[2]), num(west[1]), num(west[0]), num(west[3])],
            "uvSouth": [num(south[2]), num(south[1]), num(south[0]), num(south[3])],
            "uvWest": [num(east[2]), num(east[1]), num(east[0]), num(east[3])],
            "uvUp": [num(up[0]), num(up[3]), num(up[2]), num(up[1])],
            "uvDown": [num(down[0]), num(down[1]), num(down[2]), num(down[3])],
        }
    return {
        "uvNorth": [num(x) for x in north],
        "uvEast": [num(x) for x in east],
        "uvSouth": [num(x) for x in south],
        "uvWest": [num(x) for x in west],
        "uvUp": [num(up[2]), num(up[3]), num(up[0]), num(up[1])],
        "uvDown": [num(down[2]), num(down[1]), num(down[0]), num(down[3])],
    }


# -------------------------------------------------------------------- 转换
def convert_box(box: dict, scale, off: float, absolute: bool, mirror: bool) -> dict:
    sx, sy, sz = scale
    x, y, z, dx, dy, dz = [float(v) for v in box["coordinates"]]
    out = {"coordinates": [num(sx * x), num(sy * y + (off if absolute else 0.0)),
                           num(sz * z), num(sx * dx), num(sy * dy), num(sz * dz)]}
    if "textureOffset" in box:
        out.update(face_uv([float(v) for v in box["textureOffset"]], [dx, dy, dz],
                           mirror))
    else:
        for k in UV_KEYS + UV_ALIASES:
            if k in box:
                out[k] = box[k]
    if "sizeAdd" in box:
        out["sizeAdd"] = num(float(box["sizeAdd"]) * sx)
    if "sizesAdd" in box:
        out["sizesAdd"] = [num(float(v) * sx) for v in box["sizesAdd"]]
    for k, v in box.items():
        if k not in out and k not in ("coordinates", "textureOffset", "sizeAdd",
                                      "sizesAdd") + UV_KEYS + UV_ALIASES:
            out[k] = v
    return out


def convert_sub(model: dict, scale, off: float, level: int) -> dict:
    sx, sy, sz = scale
    absolute = "translate" not in model
    mirror = "u" in str(model.get("mirrorTexture", ""))
    out = {}
    for key, val in model.items():
        if key == "translate":
            t = [float(v) for v in val]
            if level == 1:
                out[key] = [num(sx * t[0]), num(sy * t[1] + off), num(sz * t[2])]
            else:
                out[key] = [num(sx * t[0]), num(sy * t[1]), num(sz * t[2])]
        elif key == "boxes":
            out[key] = [convert_box(b, scale, off, absolute, mirror) for b in val]
        elif key == "submodels":
            out[key] = [convert_sub(s, scale, off, level + 1) for s in val]
        else:
            out[key] = val
    return out


def convert_part(model: dict, pivots: dict, warnings: list) -> dict:
    part = model.get("part") or ""
    if part not in PARTS:
        warnings.append(t("unknown part %r -> treated as body" % part,
                          "部件名 %r 不在标准列表里，按 body 处理" % part))
    sx, sy, sz, off = PARTS.get(part, PARTS[FALLBACK])
    mirror = "u" in str(model.get("mirrorTexture", ""))
    out = {}
    for key, val in model.items():
        if key == "translate":
            out[key] = [num(v) for v in pivots.get(part, val)]
        elif key == "boxes":
            out[key] = [convert_box(b, (sx, sy, sz), off, True, mirror)
                        for b in val]
        elif key == "submodels":
            out[key] = [convert_sub(s, (sx, sy, sz), off, 1) for s in val]
        else:
            out[key] = val
    return out


def convert_document(doc: dict, pivots: dict, warnings: list) -> dict:
    return {k: ([convert_part(m, pivots, warnings) for m in v]
                if k == "models" else v) for k, v in doc.items()}


# ----------------------------------------------------------------------- 输出
def fmt(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        v = num(v)
        if isinstance(v, int):
            return str(v)
        s = ("%.5f" % v).rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join("%s: %s" % (json.dumps(k, ensure_ascii=False), fmt(x))
                               for k, x in v.items()) + "}"
    raise TypeError(type(v))


def dump_box(box: dict, ind: str) -> list:
    lines = [ind + "{"]
    items = list(box.items())
    for i, (k, v) in enumerate(items):
        lines.append("%s\t%s: %s%s" % (ind, json.dumps(k), fmt(v),
                                       "," if i < len(items) - 1 else ""))
    lines.append(ind + "}")
    return lines


def dump_model(m: dict, ind: str) -> list:
    lines = [ind + "{"]
    keys = [k for k in m if not (k == "boxes" and not m[k])]
    for i, k in enumerate(keys):
        v = m[k]
        comma = "," if i < len(keys) - 1 else ""
        if k == "boxes":
            lines.append('%s\t"boxes": [' % ind)
            for j, b in enumerate(v):
                bl = dump_box(b, ind + "\t\t")
                if j < len(v) - 1:
                    bl[-1] += ","
                lines.extend(bl)
            lines.append("%s\t]%s" % (ind, comma))
        elif k == "submodels":
            lines.append('%s\t"submodels": [' % ind)
            for j, s in enumerate(v):
                sl = dump_model(s, ind + "\t\t")
                if j < len(v) - 1:
                    sl[-1] += ","
                lines.extend(sl)
            lines.append("%s\t]%s" % (ind, comma))
        else:
            lines.append("%s\t%s: %s%s" % (ind, json.dumps(k), fmt(v), comma))
    lines.append(ind + "}")
    return lines


def dump(doc: dict) -> str:
    lines = ["{"]
    keys = list(doc)
    for i, k in enumerate(keys):
        v = doc[k]
        comma = "," if i < len(keys) - 1 else ""
        if k == "models":
            lines.append('\t"models": [')
            for j, m in enumerate(v):
                ml = dump_model(m, "\t\t")
                if j < len(v) - 1:
                    ml[-1] += ","
                lines.extend(ml)
            lines.append("\t]%s" % comma)
        else:
            lines.append('\t%s: %s%s' % (json.dumps(k), fmt(v), comma))
    lines.append("}")
    return "\n".join(lines) + "\n"


NAME_RE = re.compile(r"^(%s)(_[a-z]+)?(\d*)\.jem$" % "|".join(ENTITIES), re.I)


def parse_name(name: str):
    """zombie12.jem -> ('zombie','','12') ; drowned_outer2.jem -> ('drowned','_outer','2')

    只有 drowned 允许 `_outer`；husk_outer / zombie_outer 一律视为不支持。
    """
    m = NAME_RE.match(os.path.basename(name))
    if not m:
        return None
    entity = m.group(1).lower()
    suffix = (m.group(2) or "").lower()
    if suffix not in ENTITY_SUFFIXES.get(entity, ("",)):
        return None
    return entity, suffix, m.group(3)


def is_target_model(name: str) -> bool:
    stem = os.path.splitext(os.path.basename(name))[0]
    if re.match(r"^(%s)_baby" % "|".join(ENTITIES), stem, re.I):
        return False
    return parse_name(name) is not None


def baby_name(name: str) -> str:
    """zombie.jem -> zombie_baby.jem ; drowned_outer2.jem -> drowned_baby_outer2.jem"""
    parsed = parse_name(name)
    if parsed:
        entity, suffix, index = parsed
        return "%s_baby%s%s.jem" % (entity, suffix, index)
    return "%s_baby.jem" % os.path.splitext(os.path.basename(name))[0]


def convert_file(path: str, out_dir: str, pivots: dict) -> str:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    warnings = []
    out_doc = convert_document(doc, pivots, warnings)
    dst = os.path.join(out_dir, baby_name(path))
    os.makedirs(out_dir, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dump(out_doc))
    n_boxes = sum(len(m.get("boxes", [])) for m in doc.get("models", []))
    print("  %-28s -> %-28s %s"
          % (os.path.basename(path), os.path.basename(dst),
             t("(%d top-level boxes)" % n_boxes, "(%d 个顶层盒体)" % n_boxes)))
    for w in sorted(set(warnings)):
        print("      ! %s" % w)
    return dst


def is_zombie_model(name: str) -> bool:
    return is_target_model(name)


def pick_lang(argv) -> str:
    """--zh / --en, last one wins; English otherwise."""
    lang = "en"
    for a in argv:
        low = a.lower()
        if low in ("--zh", "-zh", "--chinese"):
            lang = "zh"
        elif low in ("--en", "-en", "--english"):
            lang = "en"
    return lang


def main() -> int:
    global LANG
    LANG = pick_lang(sys.argv[1:])
    args = [a for a in sys.argv[1:] if not a.lower().startswith("-")]

    print("=" * 68)
    print(t(" Zombie / Drowned / Husk  ->  Baby   CEM model converter",
            " 僵尸 / 溺尸 / 尸壳  ->  幼年模型  转换器"))
    print("=" * 68)

    pivots = load_template(TEMPLATE)

    dropped_dirs = [a for a in args if os.path.isdir(a)]
    if dropped_dirs:
        args = ["--dir", dropped_dirs[0]] + [a for a in args if a not in dropped_dirs]
    if args and args[0].lower() == "--dir" and len(args) > 1:
        folder = args[1]
        if not os.path.isdir(folder):
            print(t("Folder not found: %s" % folder, "目录不存在：%s" % folder))
            return 2
        files = [os.path.join(folder, n) for n in sorted(os.listdir(folder))
                 if n.lower().endswith(".jem") and is_zombie_model(n)]
        skipped = [n for n in sorted(os.listdir(folder))
                   if n.lower().endswith(".jem") and not is_zombie_model(n)
                   and n not in SKIP_NAMES]
        if skipped:
            print(t("\nSkipping %d unsupported model(s) (this tool handles "
                    "zombie / drowned / husk; only drowned has _outer): %s",
                    "\n跳过 %d 个不支持的模型（本工具处理 zombie / drowned / husk；外层只有 drowned 有）：%s")
                  % (len(skipped),
                     ", ".join(skipped[:6]) + ("..." if len(skipped) > 6 else "")))
        if not files:
            print(t("No supported models (zombie*.jem / drowned*.jem / husk*.jem) in: %s" % folder,
                    "目录里没有可转换的模型（zombie*.jem / drowned*.jem / husk*.jem）：%s" % folder))
            return 1
        args = []
        print(t("\nBatch mode: %s" % folder, "\n批量模式：%s" % folder))
    elif args:
        files = [a for a in args if a.lower().endswith(".jem")]
        for s in [a for a in args if not a.lower().endswith(".jem")]:
            print(t("  skipped (not a .jem): %s" % s, "  跳过（不是 .jem）：%s" % s))
        keep = [f for f in files if is_zombie_model(os.path.basename(f))]
        for s in [f for f in files if f not in keep]:
            print(t("  skipped (already a baby model, or not zombie/drowned/husk): %s"
                    % os.path.basename(s),
                    "  跳过（已经是幼年模型，或不是 zombie/drowned/husk）：%s"
                    % os.path.basename(s)))
        files = keep
        if not files:
            print(t("\nNothing to convert.", "\n没有可转换的模型。"))
            return 1
    else:
        all_jem = [n for n in sorted(os.listdir(ROOT)) if n.lower().endswith(".jem")
                   and n not in SKIP_NAMES]
        files = [os.path.join(ROOT, n) for n in all_jem if is_zombie_model(n)]
        skipped = [n for n in all_jem if not is_zombie_model(n)]
        if skipped:
            print(t("\nSkipping %d unsupported model(s) (only drowned has _outer): %s",
                    "\n跳过 %d 个不支持的模型（外层只有 drowned 有）：%s")
                  % (len(skipped),
                     ", ".join(skipped[:6]) + ("..." if len(skipped) > 6 else "")))
        if not files:
            print(t("\nNo convertible .jem file in this folder.",
                    "\n本目录下没有可转换的 .jem 文件。"))
            print(t("Put your model (zombie / drowned / husk, e.g. zombie12.jem) here:\n  %s" % ROOT,
                    "把模型（zombie / drowned / husk，如 zombie12.jem）放到：\n  %s" % ROOT))
            print(t("then run the bat again. You can also drag .jem files onto the bat.",
                    "再双击本 bat 即可。也可以把 .jem 直接拖到 bat 上。"))
            return 1

    print(t("\n%d model(s), output folder: %s\n" % (len(files), OUT_DIR),
            "\n共 %d 个模型，输出到：%s\n" % (len(files), OUT_DIR)))
    ok = 0
    for f in files:
        if not os.path.exists(f):
            print(t("  not found: %s" % f, "  找不到：%s" % f))
            continue
        try:
            convert_file(f, OUT_DIR, pivots)
            ok += 1
        except Exception as exc:                      # noqa: BLE001
            print(t("  failed: %s -> %s" % (os.path.basename(f), exc),
                    "  失败：%s -> %s" % (os.path.basename(f), exc)))
    print(t("\nDone: %d/%d. Results are in the output folder." % (ok, len(files)),
            "\n完成：%d/%d。结果在 output\\ 里。" % (ok, len(files))))
    return 0 if ok == len(files) else 2


if __name__ == "__main__":
    sys.exit(main())
