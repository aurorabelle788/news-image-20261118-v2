#!/usr/bin/env python3
"""Copy the entry image to the output directory.

The entry image is entry.png beside this file. The program checks it
is a whole JPEG (SOI marker at the start, EOI marker at the end),
reads the JPEG frame header to confirm it is exactly 1024x1024,
copies it to MAKEFUN_OUTPUT_DIR (or /output), then reads the copy
back and verifies it is byte-identical to the source and still
1024x1024. A one-line verification summary goes to stderr.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
EXPECTED_SIZE = (1024, 1024)

# Markers with no length field (standalone): TEM, RST0-RST7, SOI, EOI.
_STANDALONE = {0x01} | set(range(0xD0, 0xD8)) | {0xD8, 0xD9}
# Start-of-frame markers that carry width/height (baseline + progressive).
_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_dimensions(data):
    """Return (width, height) from the JPEG frame header, or None.

    Walks the marker segments without decoding any pixels, so a
    truncated or non-image file is caught even when SOI/EOI look fine.
    """
    pos = 2  # skip the SOI marker
    n = len(data)
    while pos + 1 < n:
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker == 0xFF:  # fill byte, stay on the marker run
            pos += 1
            continue
        if marker in _STANDALONE:
            pos += 2
            continue
        if marker == 0xDA:  # SOS: compressed scan data follows, no SOF left
            return None
        if pos + 4 > n:
            return None
        seg_len = (data[pos + 2] << 8) | data[pos + 3]
        if seg_len < 2 or pos + 2 + seg_len > n:
            return None
        if marker in _SOF:
            if seg_len < 8:  # need precision + height + width bytes
                return None
            height = (data[pos + 5] << 8) | data[pos + 6]
            width = (data[pos + 7] << 8) | data[pos + 8]
            return (width, height)
        pos += 2 + seg_len
    return None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(SRC, "rb") as f:
        data = f.read()
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        print("entry.png is not a JPEG (missing SOI marker)", file=sys.stderr)
        return 1
    if data[-2:] != b"\xff\xd9":
        print("entry.png is not whole (missing EOI marker)", file=sys.stderr)
        return 1
    dims = jpeg_dimensions(data)
    if dims is None:
        print("entry.png has no readable JPEG frame header", file=sys.stderr)
        return 1
    if dims != EXPECTED_SIZE:
        print("entry.png is %dx%d, expected 1024x1024" % dims, file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dst)
    digest = hashlib.sha256(data).hexdigest()
    if sha256_of(dst) != digest:
        print("copy is not byte-identical to entry.png", file=sys.stderr)
        return 1
    with open(dst, "rb") as f:
        copy_dims = jpeg_dimensions(f.read())
    if copy_dims != EXPECTED_SIZE:
        print("copied entry.png is not 1024x1024", file=sys.stderr)
        return 1
    print("wrote", dst, "(%d bytes, sha256 %s)" % (len(data), digest))
    print("verified entry.png: %d bytes, sha256 %s…, %dx%d, byte-identical"
          % (len(data), digest[:12], dims[0], dims[1]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
