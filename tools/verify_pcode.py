#!/usr/bin/env python3
"""
verify_pcode.py - compare the ActionScript bytecode (ffdec P-code) of the
original SWF against the independently rebuilt SWF, method by method.

The original was compiled with Flex 4.16; the rebuild uses Flex 4.16.1, so the
AVM2 code that each method compiles to is expected to be identical up to a small
set of compiler-assigned identifiers and one codegen preference.  Any remaining
difference is a candidate decompilation error and is reported for review.

Normalisations applied to both sides:
  * PrivateNamespace(null,"<n>")  - compiler-assigned private namespace ids
  * initproperty / setproperty    - codegen preference for `this.x = ...`

Usage:
  tools/verify_pcode.py ORIG.pcode_dir NEW.pcode_dir [--show N]

Generate the inputs with:
  ffdec -format script:pcode -export script OUT ORIGINAL.swf
  ffdec -format script:pcode -export script OUT BUILT.swf
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from difflib import unified_diff

PRIVATE_NS = re.compile(r'PrivateNamespace\(null,"\d+"\)')
# per-ABC constant-pool / class indices and the decompiler's embed placeholders
INDEX_OPS = re.compile(r"\b(newclass|newfunction|newcatch)\s+\d+")
EMBED_ATTRS = re.compile(r"\[Embed\([^]]*\)\]")
OPCODE_ALIASES = {
    "initproperty": "setproperty",   # codegen preference for `this.x = ...`
}
# Multiname/namespace-set operands are enormous and contain the compiler's
# private-namespace ids; collapse them to a placeholder.
MULTINAME_L = re.compile(r"MultinameL\(\[[^\]]*\]\)")
MULTINAME = re.compile(r'(Multiname\("[^"]*",)\[[^\]]*\]\)')
# ffdec inserts redundant Number(x) coercions that the original compiler folded
# into convert_* opcodes.
NUMBER_COERCE = re.compile(
    r'^[ \t]*findpropstrict QName\(PackageNamespace\(""\),"Number"\)\r?\n'
    r'[ \t]*callproperty QName\(PackageNamespace\(""\),"Number"\), 1\r?\n',
    re.M)
# branch targets: `ofs00ab:` / `ofs00ab` -> appearance-ordered `off#N`
LABEL = re.compile(r"\bofs([0-9a-fA-F]+)(:?)")


def canon_labels(text: str) -> str:
    mapping: dict[str, int] = {}

    def repl(m: re.Match) -> str:
        k = m.group(1)
        if k not in mapping:
            mapping[k] = len(mapping)
        return "off#%d%s" % (mapping[k], m.group(2))

    return LABEL.sub(repl, text)


def normalize(text: str, class_name: str = "") -> str:
    text = MULTINAME_L.sub("MultinameL([NS])", text)
    text = MULTINAME.sub(r"\1[NS])", text)
    text = PRIVATE_NS.sub('PrivateNamespace(null,"N")', text)
    text = INDEX_OPS.sub(r"\1 N", text)
    text = EMBED_ATTRS.sub("[Embed]", text)
    text = NUMBER_COERCE.sub("", text)
    # AVM2 instance scope setup: `findpropstrict <own class>` and
    # `getscopeobject 0` are two encodings of the same thing.  The namespace
    # set may already have been collapsed to [NS] above, so match both forms.
    if class_name:
        text = text.replace(
            'findpropstrict Multiname("%s",[PackageNamespace("")])' % class_name,
            "getscopeobject 0")
        text = text.replace(
            'findpropstrict Multiname("%s",[NS])' % class_name,
            "getscopeobject 0")
    for src, dst in OPCODE_ALIASES.items():
        text = re.sub(r"\b%s\b" % src, dst, text)
    return canon_labels(text)


def is_game_class(rel: str) -> bool:
    """True for decompiled game classes, False for bundled SDK framework."""
    parts = rel.replace("\\", "/").split("/")
    return not any(p in ("mx", "spark", "flashx") for p in parts)


def method_names(text: str) -> list[str]:
    """Extract method names from a P-code file (best effort)."""
    names = []
    for m in re.finditer(r"method\s*\n\s*name ([^\n]*)", text):
        n = m.group(1).strip()
        if n and n != "null":
            names.append(n)
    return names


def read_norm(path: str, rel: str) -> str:
    cls = os.path.basename(rel)
    if cls.endswith(".pcode"):
        cls = cls[: -len(".pcode")]
    return normalize(open(path, encoding="utf-8", errors="replace").read(), cls)


def diff_of(a: str, b: str) -> list[str]:
    return list(unified_diff(a.splitlines(), b.splitlines(), lineterm=""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("orig")
    ap.add_argument("new")
    ap.add_argument("--show", type=int, default=3,
                    help="how many differing files to dump")
    ap.add_argument("--all", action="store_true",
                    help="also compare bundled framework classes (noisy)")
    args = ap.parse_args()

    orig_root = args.orig
    new_root = args.new
    files = []
    for dp, _dirs, fs in os.walk(orig_root):
        for f in fs:
            if f.endswith(".pcode"):
                rel = os.path.relpath(os.path.join(dp, f), orig_root)
                if args.all or is_game_class(rel):
                    files.append(rel)
    files.sort()

    same = diff = missing = 0
    differing = []
    for rel in files:
        a = os.path.join(orig_root, rel)
        b = os.path.join(new_root, rel)
        if not os.path.exists(b):
            missing += 1
            continue
        na, nb = read_norm(a, rel), read_norm(b, rel)
        if na == nb:
            same += 1
        else:
            diff += 1
            differing.append((rel, len(na), na, nb))

    total = same + diff + missing
    print("P-code files compared : %d" % total)
    print("  bytecode-identical  : %d (%.1f%%)" % (same, 100.0 * same / max(total, 1)))
    print("  differing           : %d" % diff)
    print("  only in original    : %d" % missing)
    if differing:
        differing.sort(key=lambda t: t[1])  # smallest first: easiest to inspect
        print("\ndiffering classes (by size):")
        for rel, size, _na, _nb in differing:
            print("  %8d  %s" % (size, rel))
        if args.show:
            for rel, size, na, nb in differing[:args.show]:
                if size > 2_000_000:
                    print("\n(skipping diff render of large class %s)" % rel)
                    continue
                d = diff_of(na, nb)
                print("\n" + "=" * 78)
                print("DIFF " + rel + "  (%d hunks/lines)" % len(d))
                print("=" * 78)
                print("\n".join(d[:120]))
    return 0 if diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
