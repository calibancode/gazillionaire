#!/usr/bin/env bash
#
# export_all.sh - Reproduce the decompilation of the Steam release of
#                 Gazillionaire (Lavamind / Adobe AIR) with JPEXS Free Flash
#                 Decompiler (ffdec).
#
# Usage:
#   tools/export_all.sh [PATH_TO_GAME_DIR]
#
# The default game dir is the Linux Steam install location. The script is
# idempotent: re-running it overwrites the generated source/assets but leaves
# the hand-written documentation alone.
#
# Requires: ffdec (JPEXS Free Flash Decompiler) on PATH, Java 8+.

set -euo pipefail
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

GAME="${1:-$HOME/.local/share/Steam/steamapps/common/Gazillionaire}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/tools/paths.sh"

if [[ ! -f "$GAME/Gazillionaire.swf" ]]; then
  echo "error: Gazillionaire.swf not found in '$GAME'" >&2
  echo "usage: $0 [PATH_TO_GAME_DIR]" >&2
  exit 1
fi

command -v ffdec >/dev/null 2>&1 || { echo "error: ffdec not on PATH" >&2; exit 1; }

mkdir -p "$DATA/src" "$DATA/assets" "$DATA/original"

echo "==> Application ActionScript from the main Flex application"
ffdec -export script "$DATA/src/decompiled" "$GAME/Gazillionaire.swf"

echo "==> Steam extension ActionScript from the bundled FRESteamWorks Steam ANE"
if [[ -f "$GAME/META-INF/AIR/extensions/com.amanitadesign.steam.FRESteamWorks/library.swf" ]]; then
  ffdec -export script "$DATA/src/steam_ane" \
    "$GAME/META-INF/AIR/extensions/com.amanitadesign.steam.FRESteamWorks/library.swf"
fi

echo "==> Embedded assets"
ffdec -format sprite:gif,shape:svg,image:png_gif_jpeg,font:ttf,sound:mp3,movie:flv \
  -export image,shape,sprite,font,sound,movie,binaryData \
  "$DATA/assets/main_embedded" "$GAME/Gazillionaire.swf"

echo "==> External graphics movies"
ffdec -format sprite:gif,shape:svg,image:png_gif_jpeg,font:ttf,sound:mp3,movie:flv \
  -export image,shape,sprite,font,sound,movie \
  "$DATA/assets/swf" "$GAME/SWF"

echo "==> Shared graphics resources"
ffdec -format sprite:gif,shape:svg,image:png_gif_jpeg,font:ttf,sound:mp3 \
  -export image,shape,sprite,font,sound \
  "$DATA/assets/resources" "$GAME/resources"

echo "==> Preserving original binaries and copying raw audio/images"
mkdir -p "$DATA/original/swf" "$DATA/original/resources" "$DATA/assets/audio" "$DATA/assets/images"
cp "$GAME/Gazillionaire.swf" "$DATA/original/"
if [[ -d "$GAME/META-INF/AIR" ]]; then
  mkdir -p "$DATA/original/AIR"
  cp -a "$GAME/META-INF/AIR/." "$DATA/original/AIR/"
fi
cp "$GAME"/SWF/*.SWF          "$DATA/original/swf/"
cp "$GAME"/resources/*        "$DATA/original/resources/"
cp "$GAME"/MP3/*.MP3          "$DATA/assets/audio/" 2>/dev/null || true
cp "$GAME"/PNG/*.PNG          "$DATA/assets/images/" 2>/dev/null || true

echo "done. Source: $DATA/src; game data: $DATA/{assets,original}."
