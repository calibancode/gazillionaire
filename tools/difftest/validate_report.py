"""Reject empty, partial, duplicate, or error-only runtime reports."""
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text()
lines = text.splitlines()
required = [
    "target=[%s]" % sys.argv[2], "defs ", "GameStrings keys=",
    "OpponentType.ser len=", "PlayerType.ser len=", "PlayerType.roundtrip hash=",
    "GameType.ser len=", "GameType.roundtrip hash=", "Mechanics.xml=",
    "Mechanics.status hash=", "Mechanics.commoditySound hash=", "Trading.buy cash=",
    "Trading.sell cash=", "Trading.roundtrip hash=", "Travel.order=",
    "AI.facilities cash=", "---8<---",
]
if (any(sum(line.startswith(prefix) for line in lines) != 1 for prefix in required)
        or any(line.startswith(("ERR ", "IOERROR ", "LOADERR ")) for line in lines)
        or "=false" in text or "=EX:" in text):
    raise SystemExit("FAIL: missing, duplicate, or unsuccessful runtime fixtures\n" + text)
