# Shared local game-data location; override with an absolute path.
DATA="${GAZ_DATA_DIR:-$ROOT/.local-data}"
if [[ "$DATA" != /* ]]; then
  echo "error: GAZ_DATA_DIR must be an absolute path" >&2
  exit 1
fi
export GAZ_DATA_DIR="$DATA"
