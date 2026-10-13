#!/usr/bin/env bash
#
# verify_runtime.sh - runtime differential test under the *real* Adobe AIR 32
# runtime (via Wine) and, optionally, Ruffle.
#
# It builds the Probe driver, runs it once against the original SWF and once
# against the rebuilt SWF, and diffs the observed behaviour of GameStrings /
# GameType / PlayerType / OpponentType.
#
# Requirements: wine (any recent version), the SDK from tools/fetch_sdk.sh.
#
# Uses a dedicated WINEPREFIX (default build/wineprefix) because it runs
# `wineserver -k` between cases.  Do not point WINEPREFIX at a prefix where you
# have other applications running.
#
set -euo pipefail
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/tools/paths.sh"
SDK="$ROOT/sdk"
WINE="${WINE:-wine}"
export WINEPREFIX="${WINEPREFIX:-$ROOT/build/wineprefix}"
export WINEDEBUG="${WINEDEBUG:--all}"
ADL_TIMEOUT="${ADL_TIMEOUT:-120}"

[[ -x "$SDK/bin/adl.exe" ]] && [[ -x "$SDK/bin/amxmlc" ]] || {
  echo "error: SDK missing; run tools/fetch_sdk.sh" >&2; exit 1; }
command -v "$WINE" >/dev/null || { echo "error: wine not found" >&2; exit 1; }
[[ -f "$ROOT/build/Gazillionaire.swf" ]] || {
  echo "error: build/Gazillionaire.swf missing; run tools/build.sh" >&2; exit 1; }

WORK="$(mktemp -d)"
COLLECT="$WORK/collect"
cleanup() { [[ -n "${COLLECTOR_PID:-}" ]] && kill "$COLLECTOR_PID" 2>/dev/null || true; rm -f "$ROOT/build/probe-target.txt"; rm -rf "$WORK"; }
trap cleanup EXIT

echo "==> building probe driver"
FLEX_HOME="$SDK" AIR_HOME="$SDK" "$SDK/bin/amxmlc" \
    -target-player=32.0 -swf-version=43 \
    -output "$ROOT/build/probe.swf" "$ROOT/tools/difftest/Probe.as" >/dev/null

echo "==> starting collector"
: > "$COLLECT"
python3 "$ROOT/tools/difftest/collector.py" "$COLLECT" &
COLLECTOR_PID=$!
sleep 1
if ! kill -0 "$COLLECTOR_PID" 2>/dev/null; then
  echo "error: collector could not start (port 8765 already in use?)" >&2
  exit 1
fi

DESC="$(winepath -w "$ROOT/tools/difftest/probe-app.xml")"
APPROOT="$(winepath -w "$ROOT")"

run_case() { # <app:/target> <outfile>
  local target="$1" out="$2"
  : > "$COLLECT"
  # the probe resolves this relative to its own SWF (build/probe.swf)
  printf '%s' "$target" > "$ROOT/build/probe-target.txt"
  local status=0
  timeout "$ADL_TIMEOUT" "$WINE" "$SDK/bin/adl.exe" -nodebug \
      -profile extendedDesktop "$DESC" "$APPROOT" >"$WORK/adl.log" 2>&1 || status=$?
  # `timeout` only kills the wine wrapper; tear the prefix down so the next
  # case cannot inherit a still-running adl process.
  wineserver -k 2>/dev/null || true
  sleep 1
  cp "$COLLECT" "$out"
  if (( status != 0 )); then
    echo "error: AIR launch/probe failed (exit $status)" >&2
    cat "$WORK/adl.log" >&2
    return 1
  fi
  python3 "$ROOT/tools/difftest/validate_report.py" "$out" "$target"
}

echo "==> running ORIGINAL   ($ADL_TIMEOUT s budget)"
ln -sfn "$DATA/original" "$ROOT/build/runtime-original"
run_case "app:/build/runtime-original/Gazillionaire.swf" "$WORK/orig.txt"
echo "==> running REBUILT"
run_case "app:/build/Gazillionaire.swf" "$WORK/new.txt"
rm -f "$ROOT/build/probe-target.txt"

echo
echo "================= ORIGINAL ================="
cat "$WORK/orig.txt"
echo "================= REBUILT  ================="
cat "$WORK/new.txt"

# the first line names the loaded file; everything else must match exactly
if diff <(grep -v '^target=' "$WORK/orig.txt") \
        <(grep -v '^target=' "$WORK/new.txt") >/dev/null; then
  echo
  echo "PASS: state/localization and deterministic gameplay-handler fixtures are identical."
  exit 0
else
  echo
  echo "FAIL: runtime behaviour differs:"
  diff <(grep -v '^target=' "$WORK/orig.txt") \
       <(grep -v '^target=' "$WORK/new.txt") || true
  exit 1
fi
