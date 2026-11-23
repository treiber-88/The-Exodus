"""Renders landscapes in the running Blender, then converts them to dithered
palette pixel art in assets/scenes.

Usage: python tools/build_scenes.py [--skip-render]
"""
import json
import socket
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "art" / "renders"
OUT = ROOT / "assets" / "scenes"
SIZE = (320, 136)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
PALETTE = [
    (16, 12, 20), (56, 36, 44), (84, 52, 28), (148, 96, 48), (196, 136, 100),
    (224, 196, 132), (244, 232, 196), (176, 124, 36), (232, 188, 60), (176, 72, 44),
    (112, 24, 32), (116, 56, 136), (60, 64, 132), (32, 52, 116), (60, 96, 188),
    (112, 188, 224), (196, 228, 236), (48, 96, 48), (92, 156, 64), (120, 84, 60), (204, 164, 104),
]


def render():
    code = "OUT_DIR = %r\n%s" % (str(RAW), (ROOT / "tools" / "blender" / "render_scenes.py").read_text(encoding="utf-8"))
    s = socket.create_connection(("127.0.0.1", 9876), timeout=600)
    s.settimeout(600)
    s.sendall(json.dumps({"type": "execute", "code": code, "strict_json": False}).encode() + b"\0")
    buf = b""
    while not buf.endswith(b"\0"):
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
    s.close()
    reply = json.loads(buf.rstrip(b"\0").decode())
    if reply.get("status") != "ok":
        sys.exit(str(reply)[:3000])
    print(reply.get("result"))


def nearest(r, g, b):
    return min(PALETTE, key=lambda c: 2 * (c[0] - r) ** 2 + 4 * (c[1] - g) ** 2 + 3 * (c[2] - b) ** 2)


def convert(path):
    im = Image.open(path).convert("RGB").resize(SIZE, Image.BOX)
    src, out = im.load(), Image.new("RGB", SIZE)
    dst = out.load()
    cache = {}
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            d = (BAYER[y % 4][x % 4] / 16 - 0.47) * 26
            r, g, b = src[x, y]
            key = (int(r + d) >> 2, int(g + d) >> 2, int(b + d) >> 2)
            if key not in cache:
                cache[key] = nearest(r + d, g + d, b + d)
            dst[x, y] = cache[key]
    return out


def main():
    if "--skip-render" not in sys.argv:
        render()
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("*.png"))
    for path in files:
        convert(path).save(OUT / path.name)
    cols = 4
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 324, rows * 140), (16, 12, 20))
    for i, path in enumerate(files):
        sheet.paste(Image.open(OUT / path.name), ((i % cols) * 324 + 2, (i // cols) * 140 + 2))
    sheet.save(ROOT / "assets" / "scenes_sheet.png")
    print("converted", len(files))


if __name__ == "__main__":
    main()
