#!/usr/bin/env bash
#
# run.sh - assemble a runnable directory for the rebuilt SWF and launch it.
#
# Gazillionaire is NOT a self-contained SWF: it loads SWF/, MP3/, PNG/ and
# resources/ at runtime, relative to the SWF. Running build/Gazillionaire.swf by
# itself therefore shows only the app's white background.
#
# Usage:
#   tools/run.sh          # run under Ruffle (AIR runtime emulation)
#   tools/run.sh air      # run under the real Adobe AIR 32 runtime (Wine)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/tools/paths.sh"
MODE="${1:-ruffle}"
RUN="$ROOT/build/run"
SWF="$ROOT/build/Gazillionaire.swf"

[[ -f "$SWF" ]] || { echo "error: $SWF missing; run tools/build.sh" >&2; exit 1; }

# Assemble the directory the game expects: Gazillionaire.swf plus the four
# asset trees it loads from, resolved from the pristine copies.
mkdir -p "$RUN"
ln -sfn "$DATA/original/swf"       "$RUN/SWF"
ln -sfn "$DATA/original/resources" "$RUN/resources"
ln -sfn "$DATA/assets/audio"       "$RUN/MP3"
ln -sfn "$DATA/assets/images"      "$RUN/PNG"
cp -f "$SWF" "$RUN/Gazillionaire.swf"

case "$MODE" in
  ruffle)
    command -v ruffle >/dev/null || { echo "error: ruffle not found" >&2; exit 1; }
    echo "running rebuilt SWF under Ruffle (AIR)..."
    # AIR runtime + SWF v43; saves go under build/run/saves
    exec ruffle --player-runtime air --player-version 32 \
        --save-directory "$RUN/saves" "$RUN/Gazillionaire.swf"
    ;;
  air)
    SDK="$ROOT/sdk"
    [[ -f "$SDK/bin/adl.exe" ]] || { echo "error: SDK missing (tools/fetch_sdk.sh)" >&2; exit 1; }
    export WINEPREFIX="${WINEPREFIX:-$ROOT/build/wineprefix}"
    export WINEDEBUG="${WINEDEBUG:--all}"
    DESC="$(winepath -w "$ROOT/tools/app.xml")"
    APPDIR="$(winepath -w "$RUN")"
    echo "running rebuilt SWF under real AIR 32 (Wine)..."
    exec wine "$SDK/bin/adl.exe" -profile extendedDesktop "$DESC" "$APPDIR"
    ;;
  *)
    echo "usage: $0 [ruffle|air]" >&2; exit 2;;
esac
