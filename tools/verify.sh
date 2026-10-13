#!/usr/bin/env bash
#
# verify.sh - measure how faithfully the rebuilt SWF reproduces the original.
#
# Disassembles both SWFs to JPEXS P-code and runs the two comparison tools:
#   * verify_methods.py - per-method bytecode equivalence (streamed; scales to
#                         the 1.2 GB P-code of the main class)
#   * verify_pcode.py   - whole-class summary
#
# NOTE: P-code for Gazillionaire.pcode is ~1.2 GB per side, so this needs a few
# GB of scratch space.  Set KEEP=1 to keep the scratch tree for inspection.
#
set -euo pipefail
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/tools/paths.sh"
ORIG="$DATA/original/Gazillionaire.swf"
NEW="$ROOT/build/Gazillionaire.swf"
WORK="${TMPDIR:-/tmp}/gaz-verify"

[[ -f "$NEW" ]] || { echo "error: build first (tools/build.sh)" >&2; exit 1; }
command -v ffdec >/dev/null || { echo "error: ffdec not on PATH" >&2; exit 1; }

rm -rf "$WORK"; mkdir -p "$WORK/orig" "$WORK/new"

echo "==> disassembling original"
ffdec -format script:pcode -export script "$WORK/orig" "$ORIG" >/dev/null
echo "==> disassembling rebuilt"
ffdec -format script:pcode -export script "$WORK/new" "$NEW" >/dev/null

echo
echo "================= per-method equivalence ================="
python3 "$ROOT/tools/verify_methods.py" "$WORK/orig/scripts" "$WORK/new/scripts" \
    --show 0 --list "$ROOT/docs/reference/verification_diffs.tsv" || true

echo
echo "================= per-class summary ======================"
python3 "$ROOT/tools/verify_pcode.py" "$WORK/orig/scripts" "$WORK/new/scripts" --show 0 || true

[[ "${KEEP:-0}" == "1" ]] || rm -rf "$WORK"
