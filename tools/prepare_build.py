#!/usr/bin/env python3
"""
prepare_build.py - turn the raw JPEXS decompilation into a compilable Flex
source tree.

The decompiler emits [Embed(...)] metadata whose `source` points at its own
temporary extraction directory (`/_assets/...`).  This script rewrites those
paths to the real extracted assets and resolves the synthetic
`/_assets/assets.swf#symbolN` embeds (which ffdec invents for symbols that were
statically linked from the Flex framework / app assets).

Inputs
------
src/decompiled/scripts/*.as      raw decompiled game sources (156 files)
assets/main_embedded/**          assets extracted from Gazillionaire.swf
original/Gazillionaire.swf       artwork-only synthetic symbol library

Output
------
app/src/*.as                     buildable source tree
"""
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from clean_source import clean_initializers, clean_codegen
from recover_embeds import recover_embeds
from paths import DATA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(DATA, "src", "decompiled", "scripts")
OUT = os.path.join(ROOT, "app", "src")
EMBED_ROOT = os.path.join(DATA, "assets", "main_embedded")

EMBED_RE = re.compile(r"\[Embed\(([^]]*?)\)\]", re.S)
SOURCE_RE = re.compile(r'source="([^"]*)"')


def build_asset_map() -> dict[str, str]:
    """basename -> path relative to app/src."""
    out: dict[str, str] = {}
    for dirpath, _dirs, files in os.walk(EMBED_ROOT):
        for f in files:
            out.setdefault(f, os.path.relpath(os.path.join(dirpath, f), OUT))
    return out


def fix_mx_internal(text: str) -> str:
    """Qualified accesses need the namespace import, not a use directive."""
    if "mx_internal::" in text and "import mx.core.mx_internal;" not in text:
        text = text.replace(
            "package\n{\n",
            "package\n{\n   import mx.core.mx_internal;\n\n",
            1)
    return text


def transform(filename: str, text: str, asset_map: dict[str, str],
              missing: set[str]) -> str:
    is_mcl = "extends MovieClipLoaderAsset" in text
    is_sprite = "extends SpriteAsset" in text

    def repl(m: re.Match) -> str:
        attrs = m.group(1)
        src = SOURCE_RE.search(attrs)
        if not src:
            return m.group(0)
        source = src.group(1)

        if source == "/_assets/assets.swf":
            if is_mcl:
                # data comes from the overridden movieClipData/dataClass
                return ""
            if is_sprite:
                if "_f_fill" in filename or "Assets_swf_" in filename:
                    return "[Embed(%s)]" % SOURCE_RE.sub(
                        'source="../../build/embedded-art.swf"', attrs, count=1)
            missing.add(filename + " :: " + source)
            return m.group(0)

        base = os.path.basename(source)
        if base in asset_map:
            new_attrs = SOURCE_RE.sub(
                'source="%s"' % asset_map[base].replace("\\", "/"), attrs, count=1)
            return "[Embed(%s)]" % new_attrs
        missing.add(filename + " :: " + source)
        return m.group(0)

    text = EMBED_RE.sub(repl, text)

    return text


def main() -> int:
    if not os.path.isdir(SRC):
        print("error: %s not found (run tools/export_all.sh first)" % SRC,
              file=sys.stderr)
        return 1

    asset_map = build_asset_map()
    recover_embeds(Path(ROOT))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    missing: set[str] = set()
    count = 0
    for name in sorted(os.listdir(SRC)):
        if not name.endswith(".as"):
            continue
        with open(os.path.join(SRC, name), encoding="utf-8",
                  errors="replace") as fh:
            text = fh.read()
        if name == "Gazillionaire.as":
            text, removed = clean_initializers(text)
            print("removed %d redundant local initializers" % removed)
        text = clean_codegen(name, text)
        text = transform(name, text, asset_map, missing)
        text = fix_mx_internal(text)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        count += 1

    print("prepared %d source files in %s"
          % (count, os.path.relpath(OUT, ROOT)))
    if missing:
        print("\nUNRESOLVED embeds:")
        for m in sorted(missing):
            print("  " + m)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
