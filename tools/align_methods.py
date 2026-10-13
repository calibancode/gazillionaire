#!/usr/bin/env python3
"""
align_methods.py - map (class, method_index) from the P-code worklist to the
function declarations in the decompiled ActionScript source.

JPEXS P-code blocks and the decompiled .as both preserve the class trait
order, so the Nth method block corresponds to the Nth function declaration,
up to a small leading offset (the class iinit/cinit blocks have no source
declaration).  Because this SWF carries no method names (built without
debug info), the offset is detected per class by correlating the block's
`pushstring` literals with the source function text, and reported with a
confidence score.

Usage:
  align_methods.py PCODE_FILE AS_FILE [--json OUT]

Output (stdout): one line per method, tab-separated
  index, offset, pcode-name, src-name, src_line, confidence
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_methods as vm  # noqa: E402

FUNC_RE = re.compile(
    r"^\s*(?:[a-z_]+(?:\s+[a-z_]+)*\s+)?"          # modifiers (public etc.)
    r"(?:static\s+|final\s+|override\s+)*"          # ASC modifiers
    r"function\s+(get\s+|set\s+)?([A-Za-z_$][\w$]*)\s*\(")
PUSHSTRING = re.compile(r'^\s*pushstring "(.*)"\s*$')
SRC_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')

MAX_OFFSET = 3


def src_functions(text: str):
    """Yield (name, line_no) for top-level function declarations."""
    depth = 0
    class_seen = class_open = False
    target = None
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not class_seen and re.match(
                r"(?:public |internal |final |dynamic )*class\s", stripped):
            class_seen = True
        if class_seen and not class_open and stripped == "{":
            class_open = True
            target = depth + 1
        if target is not None and depth == target:
            m = FUNC_RE.match(line)
            if m:
                kind = ("get_" if m.group(1) == "get " else
                        "set_" if m.group(1) == "set " else "")
                yield kind + m.group(2), n
        depth += line.count("{") - line.count("}")
        if depth < 0:
            depth = 0


def load_pcode(path: str):
    """[(name, [string literals])] per top-level method block."""
    out = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for block in vm.iter_blocks_from_lines(fh):
            first = block.splitlines()[0] if block else ""
            m = re.match(r"\s*name\s+(.+)$", first)
            name = m.group(1).strip() if m else "?"
            strings = [mm.group(1)
                       for mm in (PUSHSTRING.match(l) for l in block.splitlines())
                       if mm]
            out.append((name, strings))
    return out


def align(pcode_path: str, as_path: str):
    blocks = load_pcode(pcode_path)
    with open(as_path, encoding="utf-8", errors="replace") as fh:
        src_lines = fh.read().splitlines()
    funcs = list(src_functions("\n".join(src_lines)))

    # source text slice per function (declaration line .. next declaration)
    slices = []
    for k, (_name, line) in enumerate(funcs):
        end = funcs[k + 1][1] - 1 if k + 1 < len(funcs) else len(src_lines)
        slices.append(set(m.group(1) for m in
                          SRC_STRING.finditer("\n".join(src_lines[line - 1:end]))))

    def score(offset: int) -> tuple[int, int]:
        hit = miss = 0
        for i in range(offset, len(blocks)):
            _n, strings = blocks[i]
            k = i - offset
            if k >= len(slices):
                break
            if not strings:
                continue
            if any(s in slices[k] for s in strings):
                hit += 1
            else:
                miss += 1
        return hit, miss

    best_offset, best = 0, (-1, 10**9)
    for off in range(MAX_OFFSET + 1):
        if len(blocks) - off < 10 or len(funcs) < 10:
            break
        h, m = score(off)
        if h > best[0] or (h == best[0] and m < best[1]):
            best_offset, best = off, (h, m)
    hit, miss = best
    conf = hit / max(hit + miss, 1)
    rows = []
    for i, (name, strings) in enumerate(blocks):
        k = i - best_offset
        if 0 <= k < len(funcs):
            rows.append({"index": i + 1, "pcode_name": name,
                         "src_name": funcs[k][0], "src_line": funcs[k][1],
                         "has_strings": bool(strings)})
    return {"pcode_blocks": len(blocks), "src_functions": len(funcs),
            "offset": best_offset, "string_hits": hit, "string_misses": miss,
            "confidence": round(conf, 4), "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pcode")
    ap.add_argument("asfile")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    result = align(args.pcode, args.asfile)
    print("pcode blocks : %d" % result["pcode_blocks"])
    print("src functions: %d" % result["src_functions"])
    print("offset       : %d" % result["offset"])
    print("string match : %d hit / %d miss (confidence %.2f)" % (
        result["string_hits"], result["string_misses"], result["confidence"]))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh)
        print("mapping written to %s" % args.json)
    else:
        for r in result["rows"][:20]:
            print("  idx %-5d src=%r line %d" %
                  (r["index"], r["src_name"], r["src_line"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())