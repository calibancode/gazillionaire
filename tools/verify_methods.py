#!/usr/bin/env python3
"""
verify_methods.py - method-level bytecode equivalence between the original SWF
and the independently rebuilt SWF.

Unlike verify_pcode.py (whole-class text diff, memory bound by class size) this
streams the P-code and compares the Nth top-level method block on each side.
Because both SWFs are compiled from the same source, method order is preserved.

Usage:
  tools/verify_methods.py ORIG_PCODE_DIR NEW_PCODE_DIR [--show N] [--all]

Exit status is non-zero if any game method differs.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from difflib import unified_diff

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_pcode as vp  # noqa: E402

METHOD_OPEN = re.compile(r"^(\s*)method$")
METHOD_CLOSE = re.compile(r"^(\s*)end ; method$")
COMPRESSED_LOCAL = re.compile(r"\b(setlocal|getlocal)([0-3])\b")
LOCAL_REF = re.compile(r"\b(setlocal|getlocal|kill) (\d+)\b")


def canon_locals(text: str) -> str:
    """Renumber local slots by order of first appearance.

    Two compilers (or two runs) can allocate the same locals to different slot
    numbers, or use the compressed `getlocal0..3` encodings; neither changes
    behaviour, so canonicalise the slot space before comparing.
    """
    text = COMPRESSED_LOCAL.sub(r"\1 \2", text)
    mapping: dict[int, int] = {}

    def repl(m: re.Match) -> str:
        n = int(m.group(2))
        if n not in mapping:
            mapping[n] = len(mapping)
        return "%s L%d" % (m.group(1), mapping[n])

    return LOCAL_REF.sub(repl, text)


def iter_blocks_from_lines(lines):
    """Yield the text of each top-level method block from a line iterator."""
    indent = None
    buf: list[str] = []
    in_block = False
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not in_block:
            m = METHOD_OPEN.match(line)
            if m:
                indent = len(m.group(1))
                in_block = True
                buf = []
            continue
        m = METHOD_CLOSE.match(line)
        if m and len(m.group(1)) == indent:
            in_block = False
            yield "\n".join(buf)
            continue
        buf.append(line)


def iter_blocks(path: str):
    """Yield the text of each top-level method block, in order."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        yield from iter_blocks_from_lines(fh)


def class_name(rel: str) -> str:
    base = os.path.basename(rel)
    return base[: -len(".pcode")] if base.endswith(".pcode") else base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("orig")
    ap.add_argument("new")
    ap.add_argument("--show", type=int, default=5,
                    help="number of differing methods to render")
    ap.add_argument("--all", action="store_true",
                    help="also compare bundled framework classes")
    ap.add_argument("--list", metavar="FILE",
                    help="write a worklist of differing methods (TSV)")
    args = ap.parse_args()

    files = []
    for dp, _dirs, fs in os.walk(args.orig):
        for f in fs:
            if f.endswith(".pcode"):
                rel = os.path.relpath(os.path.join(dp, f), args.orig)
                if args.all or vp.is_game_class(rel):
                    files.append(rel)
    files.sort()

    total_same = total_diff = total_missing = 0
    differing_classes = []
    worklist: list[tuple[str, int]] = []
    shown = 0

    for rel in files:
        a = os.path.join(args.orig, rel)
        b = os.path.join(args.new, rel)
        if not os.path.exists(b):
            continue
        cls = class_name(rel)
        it_a = iter_blocks(a)
        it_b = iter_blocks(b)
        i = 0
        cls_same = cls_diff = 0
        for ba, bb in zip(it_a, it_b):
            i += 1
            na = canon_locals(vp.normalize(ba, cls))
            nb = canon_locals(vp.normalize(bb, cls))
            if na == nb:
                cls_same += 1
            else:
                cls_diff += 1
                worklist.append((rel, i))
                if shown < args.show:
                    shown += 1
                    d = list(unified_diff(na.splitlines(), nb.splitlines(),
                                          n=2, lineterm=""))
                    print("=" * 78)
                    print("METHOD DIFF  %s  method#%d" % (rel, i))
                    print("=" * 78)
                    print("\n".join(d[:80]))
        # count unmatched tails
        extra_a = sum(1 for _ in it_a)
        extra_b = sum(1 for _ in it_b)
        total_missing += extra_a + extra_b
        total_same += cls_same
        total_diff += cls_diff
        if cls_diff:
            differing_classes.append((rel, cls_same, cls_diff))

    total = total_same + total_diff
    print()
    print("methods compared      : %d" % total)
    print("  bytecode-identical  : %d (%.2f%%)" %
          (total_same, 100.0 * total_same / max(total, 1)))
    print("  differing           : %d" % total_diff)
    if total_missing:
        print("  unmatched tail      : %d" % total_missing)
    if differing_classes:
        print("\nclasses with differing methods:")
        for rel, s, d in differing_classes:
            print("  %-58s %d/%d differ" % (rel, d, s + d))
    if args.list:
        with open(args.list, "w", encoding="utf-8") as fh:
            fh.write("# class\tmethod_index (1-based)\n")
            for rel, i in worklist:
                fh.write("%s\t%d\n" % (rel, i))
        print("\nworklist written to %s (%d entries)" % (args.list, len(worklist)))
    return 0 if total_diff == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
