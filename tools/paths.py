"""Shared location for user-supplied game data."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("GAZ_DATA_DIR", ROOT / ".local-data"))
if not DATA.is_absolute():
    raise ValueError("GAZ_DATA_DIR must be an absolute path")
