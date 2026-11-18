#!/usr/bin/env python3
"""Copy the entry image to the output directory.

The entry image is entry.png beside this file. The program checks it
is a whole JPEG (SOI marker at the start, EOI marker at the end),
copies it to MAKEFUN_OUTPUT_DIR (or /output), then reads the copy
back and verifies it is byte-identical to the source.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")


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
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SRC, dst)
    if sha256_of(dst) != hashlib.sha256(data).hexdigest():
        print("copy is not byte-identical to entry.png", file=sys.stderr)
        return 1
    print("wrote", dst, "(%d bytes, sha256 %s)"
          % (len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
