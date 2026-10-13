#!/usr/bin/env bash
#
# build.sh - independently rebuild Gazillionaire.swf from the decompiled
# ActionScript.
#
#   1. regenerate app/src from src/decompiled + the extracted assets
#   2. compile it with the Flex 4.16.1 + AIR 32 toolchain
#
# Requirements: tools/fetch_sdk.sh has installed $ROOT/sdk, and Java is on PATH.
#
set -euo pipefail
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK="$ROOT/sdk"
OUT="$ROOT/build/Gazillionaire.swf"

[[ -x "$SDK/bin/amxmlc" ]] || {
  echo "error: $SDK/bin/amxmlc not found." >&2
  echo "run tools/fetch_sdk.sh first." >&2
  exit 1
}
command -v java >/dev/null || { echo "error: java not on PATH" >&2; exit 1; }

echo "==> preparing buildable source tree"
python3 "$ROOT/tools/prepare_build.py"

# The document class is the generated Flex SystemManager; the application class
# itself is only referenced by name at runtime, so force-link the entry points
# plus the classes named in SystemManager.info()'s mixins list.
INCLUDES="Gazillionaire,_Gazillionaire_FlexInit,_Gazillionaire_Styles,\
LoadScreen_LoadScreenGraphic,CustomPreloader,LoadScreen,\
mx.styles.StyleManagerImpl,mx.managers.systemClasses.ActiveWindowManager,\
mx.messaging.config.LoaderConfig"

echo "==> compiling $OUT"
mkdir -p "$ROOT/build"
# The Flex preloader runs on frame 1 and only hands off after the playhead
# advances to frame 2 (SystemManager.deferredNextFrame bails when
# `currentFrame + 1 > totalFrames`).  A normal MXML build gets this frame
# layout for free; because we compile the generated SystemManager directly we
# must place the application class on frame 2 explicitly, with the same
# FrameLabel the original binary has.
FLEX_HOME="$SDK" AIR_HOME="$SDK" "$SDK/bin/amxmlc" \
    -source-path "$ROOT/app/src" \
    "-includes=$INCLUDES" \
    "-frames.frame=Gazillionaire,Gazillionaire" \
    -default-size 760 570 \
    -default-background-color 0xFFFFFF \
    -target-player=32.0 \
    -swf-version=43 \
    -output "$OUT" \
    "$ROOT/app/src/_Gazillionaire_mx_managers_SystemManager.as"

echo "==> built $(stat -c '%s' "$OUT") bytes: $OUT"
