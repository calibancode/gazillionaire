"""Explain residuals by exact structural checks; never change the verifier."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import re

def explain(a: list[str], b: list[str]) -> str:
    if a == b:
        return "identical"
    namespace = re.compile(r'QName\(Namespace\("(mx.core|mx.styles)"\),')
    if [namespace.sub(r'QName(PackageNamespace("\1"),', line) for line in a] == b:
        return "namespace_kind"
    without_jumps = [line for i, line in enumerate(a)
                     if not (line.startswith("jump ") and i + 1 < len(a)
                             and a[i + 1] == line[5:] + ":")]
    if without_jumps == b:
        return "jump_to_next_instruction"
    folded = re.sub(r'greaterequals\niffalse (off#\d+)', r'ifnge \1', "\n".join(a))
    if folded == "\n".join(b):
        return "folded_boolean_branch"
    # Verify complete key/value pairs, not merely the instruction multiset.
    def object_literal(lines):
        first = next((i for i, line in enumerate(lines) if line.startswith('pushstring ')), -1)
        end = next((i for i, line in enumerate(lines) if line.startswith('newobject ')), -1)
        middle = lines[first:end]
        if first < 0 or end < 0 or len(middle) % 2 or not all(line.startswith('pushstring ') for line in middle):
            return None
        pairs = list(zip(middle[::2], middle[1::2]))
        if len(pairs) != int(lines[end].split()[1]):
            return None
        return lines[:first], Counter(pairs), lines[end:]
    if object_literal(a) is not None and object_literal(a) == object_literal(b):
        return "object_member_order"
    return "unexplained"


def main():
    from classify_diffs import read_worklist, stream_class_pair

    ap = argparse.ArgumentParser()
    ap.add_argument("orig")
    ap.add_argument("new")
    ap.add_argument("--worklist", default="docs/reference/verification_diffs.tsv")
    ap.add_argument("--out", default="docs/reference/residual_audit.tsv")
    args = ap.parse_args()
    by_class = defaultdict(set)
    for cls, idx in read_worklist(args.worklist):
        by_class[cls].add(idx)
    rows = []
    for cls, indices in sorted(by_class.items()):
        for idx, a, b in stream_class_pair(args.orig, args.new, cls, indices):
            rows.append((cls, idx, explain(a, b)))
    if len(rows) != sum(map(len, by_class.values())):
        raise SystemExit("missing method pairs in residual audit")
    Path(args.out).write_text("# class\tmethod_index\texact_residual_shape\n" + "".join(
        "%s\t%d\t%s\n" % row for row in rows))
    counts = Counter(row[2] for row in rows)
    print(dict(counts))
    raise SystemExit(1 if counts["unexplained"] else 0)


if __name__ == "__main__":
    main()
