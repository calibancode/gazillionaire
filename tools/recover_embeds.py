"""Recover the small embedded artwork library, without copying executable code."""
from pathlib import Path
import re
import struct
import zlib
from paths import DATA

# Bitmap, shape, sprite and scaling-grid definitions used by the eight
# synthetic embeds. Character definitions precede their dependants in this SWF.
ART_TAGS = {2, 6, 20, 21, 22, 32, 35, 36, 39, 46, 78, 83, 84, 90}
CODE_TAGS = {12, 59, 72, 82}


def tags(data: bytes, pos: int):
    while pos < len(data):
        start = pos
        head, = struct.unpack_from("<H", data, pos)
        pos += 2
        kind, size = head >> 6, head & 63
        if size == 63:
            size, = struct.unpack_from("<I", data, pos)
            pos += 4
        payload = data[pos:pos + size]
        if len(payload) != size:
            raise ValueError("truncated SWF tag")
        pos += size
        yield kind, payload, data[start:pos]


def tag(kind: int, payload: bytes) -> bytes:
    return struct.pack("<HI", kind << 6 | 63, len(payload)) + payload


def recover_embeds(root: Path) -> Path:
    scripts = DATA / "src/decompiled/scripts"
    symbols = set()
    for path in scripts.glob("_class_embed_css_*.as"):
        if "Assets_swf_" in path.name or "_f_fill" in path.name:
            symbols.update(map(int, re.findall(r'symbol="symbol(\d+)"', path.read_text())))
    data = (DATA / "original/Gazillionaire.swf").read_bytes()
    if data[:3] == b"CWS":
        data = data[:8] + zlib.decompress(data[8:])
    elif data[:3] != b"FWS":
        raise ValueError("unsupported SWF compression")
    header_end = 8 + (5 + 4 * (data[8] >> 3) + 7) // 8 + 4
    chunks = []
    recovered = set()
    for kind, payload, raw in tags(data, header_end):
        if kind not in ART_TAGS:
            continue
        character, = struct.unpack_from("<H", payload)
        if not 2 <= character <= max(symbols):
            continue
        if kind == 39 and any(k in CODE_TAGS for k, _, _ in tags(payload, 4)):
            raise ValueError("executable code in embedded sprite")
        chunks.append(raw)
        if kind != 78:
            recovered.add(character)
    if not symbols <= recovered:
        raise ValueError("missing embedded artwork symbols")
    exports = struct.pack("<H", len(symbols)) + b"".join(
        struct.pack("<H", i) + ("symbol%d" % i).encode() + b"\0" for i in sorted(symbols))
    # The library has one top-level frame; sprites retain their own timelines.
    frame_header = data[8:header_end - 2] + struct.pack("<H", 1)
    body = (frame_header + tag(69, struct.pack("<I", 8))
            + b"".join(chunks) + tag(56, exports) + tag(1, b"") + tag(0, b""))
    result = root / "build/embedded-art.swf"
    result.parent.mkdir(exist_ok=True)
    result.write_bytes(b"FWS" + data[3:4] + struct.pack("<I", len(body) + 8) + body)
    return result
