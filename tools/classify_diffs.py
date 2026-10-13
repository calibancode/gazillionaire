#!/usr/bin/env python3
"""
classify_diffs.py - automatically classify every differing method into the
known compiler/decompiler-artefact categories (or "unknown").

Works from the P-code cache produced by verify.sh (or verify_fast.sh):
  classify_diffs.py ORIG_PCODE_DIR NEW_PCODE_DIR [--worklist FILE]
                                    [--out FILE] [--examples DIR] [--show N]

Both sides are normalised exactly like verify_methods.py does (so what is
classified is precisely the residual that makes the method "differ"), then
the residual instruction lines are compared as multisets *and* in sequence:

  dbl_init    ffdec wrote `var _locN_:T = null;` where the original source
              said `var _locN_:T;` -> duplicated null-init code
              (pushnull / coerce T / setlocal) at method entry.
  tail_merge  ffdec folded `x = <expr>; return x;` into `return <expr>;`
              (and similar end-of-body assignment folding)
              -> missing coerce/setlocal/getlocal before returnvalue.
  alias_param ffdec renamed an original parameter (recovered name kept as a
              local) -> extra activation-object slot + copies for `paramN`.
  rtqname     namespace-qualified access originally written through the
              namespace *value* (RTQName sequence); rebuild emits a static
              QName.
  ns_kind     the original refers to a class through a plain
              Namespace("pkg") multiname, the rebuild through
              PackageNamespace("pkg").
  coercion    rebuild calls a global conversion (Number/int/String...) where
              the original folded it into convert_* / coerce_*.
  ordering    same instructions, different order (object literal key order).
  embed_stub  the two intentional f_fill cursor-art stubs (see BUILD.md).
  unknown     none of the above signatures matched.

Output: summary, plus a per-method TSV (--out) usable as an annotated
worklist for the source cleanup codemods.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_pcode as vp  # noqa: E402
import verify_methods as vm  # noqa: E402
from audit_residuals import explain  # noqa: E402

# canonical (post-normalisation) instruction shapes
SETLOCAL = re.compile(r"^setlocal L\d+$")
GETLOCAL = re.compile(r"^getlocal L\d+$")
KILL = re.compile(r"^kill L\d+$")
COERCE_LINE = re.compile(r"^coerce(?:_[abdibous])?(?:\s.*)?$")
CONVERT_LINE = re.compile(r"^convert_[a-z]+$")
INIT_LINE = re.compile(r"^(pushnull|pushbyte 0|pushnan|pushfalse|pushtrue|"
                       r"getscopeobject \d+|setlocal L\d+|setslot \d+|"
                       r"coerce(?:_[abdibous])?(?:\s.*)?)$")
LOCAL_OP = re.compile(r"^(coerce(?:_[abdibous])?(?:\s.*)?|convert_[a-z]+|"
                     r"setlocal L\d+|getlocal L\d+|kill L\d+)$")
# codegen-managed body numerics: legitimately shift with instruction changes
META_NUMERIC = re.compile(r"^(maxstack|localcount) \d+$")
SLOT_LINE = re.compile(r"^(trait slot|slotid \d+|type .+|end ; trait)$")
CONVERSION_NAMES = ("Number", "int", "uint", "String", "Boolean", "XML",
                    "XMLList", "Object", "Array")
CALLPROP_CONV = re.compile(
    r'^callproperty QName\(PackageNamespace\(""\),"(?:%s)"\), 1$'
    % "|".join(CONVERSION_NAMES))
FINDPROP_CONV = re.compile(
    r'^findpropstrict QName\(PackageNamespace\(""\),"(?:%s)"\)$'
    % "|".join(CONVERSION_NAMES))
INTENTIONAL_CLASSES = {
    "_class_embed_css_f_fillblue_png__944102544_696470983.pcode",
    "_class_embed_css_f_fillred_png_97191697_987149254.pcode",
}


def norm_block(text: str, class_name: str) -> list[str]:
    """Normalise a method block exactly like verify_methods.py compares it."""
    norm = vm.canon_locals(vp.normalize(text, class_name))
    return [l.strip() for l in norm.splitlines() if l.strip()]


def delta(a: list[str], b: list[str]):
    """(extra_in_b, missing_from_b) as Counters, ignoring maxstack/localcount."""
    ca = collections.Counter(l for l in a if not META_NUMERIC.match(l))
    cb = collections.Counter(l for l in b if not META_NUMERIC.match(l))
    return cb - ca, ca - cb


def classify_block(rel: str, a: list[str], b: list[str]) -> tuple[list[str], dict]:
    extra, missing = delta(a, b)
    exact = explain(a, b)
    if exact != "unexplained":
        return [exact], {"extra": sum(extra.values()), "missing": sum(missing.values())}
    cats: list[str] = []
    slot_ev = any(SLOT_LINE.match(l) for l in list(extra) + list(missing))

    if rel in INTENTIONAL_CLASSES:
        cats.append("embed_stub")

    if not extra and not missing and a != b:
        cats.append("ordering")

    # duplicated `= null` local declarations
    if extra and all(INIT_LINE.match(l) for l in extra):
        cats.append("dbl_init")

    # `x = expr; return x;` folded into `return expr;` (or end-of-body
    # assignment folds): the only thing the rebuild lacks is the store/load
    # pair (and its coercion) right before returnvalue.
    if missing and all(LOCAL_OP.match(l) for l in missing) and \
       any(l == "returnvalue" for l in a[-8:]):
        cats.append("tail_merge")

    # renamed parameter materialised as an alias local (activation slots)
    if slot_ev and any(l.startswith(("getslot", "setslot")) for l in extra):
        cats.append("alias_param")
    elif slot_ev and any(re.match(r"^param\d+$", l) for l in missing):
        cats.append("alias_param")

    # RTQName (namespace-value qualified) sequences in the original only
    if any("RTQName" in l for l in a) and not any("RTQName" in l for l in b):
        cats.append("rtqname")

    # plain Namespace("pkg") references replaced by PackageNamespace("pkg")
    # for the same (package, name) pair
    pair = re.compile(r'QName\((?:Package)?Namespace\("([^"]*)"\),"([^"]*)"\)')
    qn_orig = {(m.group(1), m.group(2)) for l in a for m in [pair.match(l)] if m}
    qn_new = {(m.group(1), m.group(2)) for l in b for m in [pair.match(l)] if m}
    if qn_orig & qn_new and any(l.startswith('QName(Namespace("') for l in missing):
        cats.append("ns_kind")

    # global conversion call vs folded convert_*/coerce_*
    if any(CONVERT_LINE.match(l) for l in missing) or \
       any(CALLPROP_CONV.match(l) or FINDPROP_CONV.match(l) for l in extra):
        cats.append("coercion")

    info = {"extra": sum(extra.values()), "missing": sum(missing.values())}
    return cats or ["unknown"], info


def read_worklist(path: str) -> list[tuple[str, int]]:
    entries = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            rel, idx = line.split("\t")
            entries.append((rel, int(idx)))
    return entries


def stream_class_pair(orig_dir, new_dir, rel, wanted: set[int]):
    """Yield (idx, lines_a, lines_b) for the wanted 1-based method indices."""
    cls = rel[:-len(".pcode")] if rel.endswith(".pcode") else rel
    pa = os.path.join(orig_dir, rel)
    pb = os.path.join(new_dir, rel)
    with open(pa, encoding="utf-8", errors="replace") as fa, \
         open(pb, encoding="utf-8", errors="replace") as fb:
        ia = vm.iter_blocks_from_lines(fa)
        ib = vm.iter_blocks_from_lines(fb)
        i = 0
        for ta, tb in zip(ia, ib):
            i += 1
            if i in wanted:
                yield i, norm_block(ta, cls), norm_block(tb, cls)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("orig")
    ap.add_argument("new")
    ap.add_argument("--worklist",
                    default="docs/reference/verification_diffs.tsv")
    ap.add_argument("--out",
                    default="build/verification_diffs_classified.tsv")
    ap.add_argument("--examples", default=None,
                    help="write an example diff per category here")
    ap.add_argument("--show", type=int, default=0,
                    help="print N example diffs per category")
    args = ap.parse_args()

    if not os.path.exists(args.worklist):
        print("worklist %s not found; run verify.sh first" % args.worklist,
              file=sys.stderr)
        return 1
    entries = read_worklist(args.worklist)

    by_class: dict[str, list[int]] = collections.defaultdict(list)
    for rel, idx in entries:
        by_class[rel].append(idx)

    results = []
    example_seen: collections.Counter = collections.Counter()
    for rel in sorted(by_class):
        wanted = set(by_class[rel])
        for idx, a, b in stream_class_pair(args.orig, args.new, rel, wanted):
            cats, info = classify_block(rel, a, b)
            results.append((rel, idx, cats, info["extra"], info["missing"]))
            key = "+".join(cats)
            if example_seen[key] < max(args.show, 1 if args.examples else 0):
                example_seen[key] += 1
                d = list(difflib.unified_diff(a, b, n=2, lineterm=""))
                if args.examples:
                    os.makedirs(args.examples, exist_ok=True)
                    with open(os.path.join(args.examples, "%s.txt" % key),
                              "w", encoding="utf-8") as fh:
                        fh.write("%s method#%d\n\n%s\n" % (rel, idx, "\n".join(d)))
                if args.show:
                    print("=" * 78)
                    print("%s method#%d  [%s]" % (rel, idx, key))
                    print("\n".join(d[:60]))

    cat_count = collections.Counter()
    combos = collections.Counter()
    for rel, idx, cats, _e, _m in results:
        combos["+".join(cats)] += 1
        for c in cats:
            cat_count[c] += 1
    print("methods classified : %d" % len(results))
    print("\nby category (a method may appear in several):")
    for c, n in cat_count.most_common():
        print("  %-12s %5d" % (c, n))
    print("\nby category combination:")
    for c, n in combos.most_common():
        print("  %-28s %5d" % (c, n))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("# class\tmethod_index\tcategory\textra_lines\tmissing_lines\n")
            for rel, idx, cats, e, m in results:
                fh.write("%s\t%d\t%s\t%d\t%d\n" % (rel, idx, "+".join(cats), e, m))
        print("\nclassified worklist written to %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
