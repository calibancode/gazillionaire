#!/usr/bin/env bash
#
# fetch_sdk.sh - download and install the build toolchain.
#
# Installs into $ROOT/sdk:
#   Apache Flex SDK 4.16.1  (compiler; matches the original's Flex 4.16.0)
#   Adobe AIR SDK 32.0      (airglobal.swc + adt; the app targets AIR 32)
#
# The AIR SDK is overlaid on top of the Flex SDK, exactly as the official
# Apache Flex SDK Installer does.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SDK="$ROOT/sdk"
CACHE="${TMPDIR:-/tmp}/gaz-sdk-cache"
FLEX_URL="https://archive.apache.org/dist/flex/4.16.1/binaries/apache-flex-sdk-4.16.1-bin.zip"
FLEX_MD5="8841c64bd5e32f8575eba86e2574873a"
AIR_URL="https://airdownload.adobe.com/air/win/download/32.0/AdobeAIRSDK.zip"

mkdir -p "$CACHE"

fetch() { # url file md5(optional)
  local url="$1" out="$2" md5="${3:-}"
  if [[ -f "$out" ]]; then echo "cached  $out"; return; fi
  echo "fetch   $url"
  curl -fL --retry 3 -o "$out.part" "$url"
  if [[ -n "$md5" ]]; then
    local got; got=$(md5sum "$out.part" | awk '{print $1}')
    [[ "$got" == "$md5" ]] || { echo "md5 mismatch for $out" >&2; exit 1; }
  fi
  mv "$out.part" "$out"
}

fetch "$FLEX_URL" "$CACHE/flex.zip" "$FLEX_MD5"
fetch "$AIR_URL"  "$CACHE/air.zip"

echo "install $SDK"
rm -rf "$SDK"; mkdir -p "$SDK"
unzip -q "$CACHE/flex.zip" -d "$SDK"
unzip -q "$CACHE/air.zip"  -d "$SDK"   # overlays AIR on Flex (official layout)
chmod +x "$SDK"/bin/* 2>/dev/null || true
command -v java >/dev/null || { echo "warning: 'java' not found on PATH" >&2; }

echo
echo "done. Build with:"
echo "  tools/build.sh"
