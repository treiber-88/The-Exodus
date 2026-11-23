"""Pixel-art compiler for The Exodus.

Sprites are drawn by hand as character grids in art/sprites/*.txt, one
character per pixel, using the fixed palette below. This keeps every pixel
deliberate and every sprite on one retro palette.

File format:
    @sprite moses_walk      starts a sprite
    @frame                  starts a frame; the grid rows follow

Usage:
    python tools/pixelart.py            build all sprites to assets/sprites
    python tools/pixelart.py --sheet    also write assets/contact_sheet.png
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "art" / "sprites"
OUT = ROOT / "assets" / "sprites"

PALETTE = {
    ".": (0, 0, 0, 0),
    "k": (16, 12, 20, 255),      # outline
    "W": (244, 240, 224, 255),   # linen
    "g": (164, 160, 152, 255),   # grey
    "G": (92, 90, 96, 255),      # dark grey
    "s": (236, 188, 148, 255),   # skin
    "S": (196, 136, 100, 255),   # skin shadow
    "b": (148, 96, 48, 255),     # wood
    "B": (84, 52, 28, 255),      # dark wood
    "r": (176, 40, 36, 255),     # red
    "R": (112, 24, 32, 255),     # dark red
    "y": (232, 188, 60, 255),    # gold
    "Y": (176, 124, 36, 255),    # sand shadow
    "t": (224, 196, 132, 255),   # sand
    "u": (60, 96, 188, 255),     # blue
    "U": (32, 52, 116, 255),     # deep blue
    "c": (112, 188, 224, 255),   # water
    "v": (92, 156, 64, 255),     # green
    "V": (48, 96, 48, 255),      # dark green
    "p": (116, 56, 136, 255),    # purple
}


def parse(path):
    sprites, name, frame = {}, None, None
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@recolor"):
            # @recolor new_name source_name r=u R=U
            _, new, source, *swaps = line.split()
            table = str.maketrans({a[0]: a[2] for a in swaps})
            sprites[new] = [[row.translate(table) for row in f] for f in sprites[source]]
            name, frame = None, None
        elif line.startswith("@sprite"):
            name = line.split()[1]
            sprites[name] = []
            frame = None
        elif line == "@frame":
            if name is None:
                sys.exit(f"{path.name}:{number}: @frame before @sprite")
            frame = []
            sprites[name].append(frame)
        else:
            if frame is None:
                sys.exit(f"{path.name}:{number}: pixels before @frame")
            bad = sorted(set(line) - set(PALETTE))
            if bad:
                sys.exit(f"{path.name}:{number}: unknown colours {bad}")
            if frame and len(line) != len(frame[0]):
                sys.exit(f"{path.name}:{number}: width {len(line)}, expected {len(frame[0])}")
            frame.append(line)
    return sprites


def render(frames):
    h = len(frames[0])
    w = len(frames[0][0])
    if any(len(f) != h or len(f[0]) != w for f in frames):
        raise ValueError("all frames in a sprite must be the same size")
    strip = Image.new("RGBA", (w * len(frames), h))
    px = strip.load()
    for i, frame in enumerate(frames):
        for y, row in enumerate(frame):
            for x, ch in enumerate(row):
                px[i * w + x, y] = PALETTE[ch]
    return strip


def contact_sheet(images, scale=6, columns=6):
    cell_w = max(im.width for im in images.values()) * scale + 12
    cell_h = max(im.height for im in images.values()) * scale + 12
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGBA", (cell_w * min(columns, len(images)), cell_h * rows), (224, 196, 132, 255))
    for i, im in enumerate(images.values()):
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        sheet.alpha_composite(big, ((i % columns) * cell_w + 6, (i // columns) * cell_h + 6))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    images = {}
    for path in sorted(SRC.glob("*.txt")):
        for name, frames in parse(path).items():
            images[name] = render(frames)
            images[name].save(OUT / f"{name}.png")
    if args.sheet and images:
        contact_sheet(images).save(ROOT / "assets" / "contact_sheet.png")
    print(f"built {len(images)} sprites")


if __name__ == "__main__":
    main()
