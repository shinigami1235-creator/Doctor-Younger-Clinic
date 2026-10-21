"""Cut the white background out of each product photo for the 3D showroom.

The clinic's product photos are 300 x 300 JPGs on plain white. The showroom stands each
product on a pedestal, so it needs the product alone on a transparent background.

    python tools/make_cutouts.py --media path/to/static/media

--media is a folder holding the downloaded photos and manifest.json (made by fetch_media.py).
Output: static/img/products/<slug>.png at 600 x 600, committed to the repo so the
showroom works even when the media download fails.

How it works: white pixels touching the edge of the photo are flooded as background,
the flood edge is softened over two pixels, and the result is enlarged 2x with a light sharpen.
White inside a bottle is kept, since only white connected to the photo's edge is removed.
"""
import argparse
import json
from collections import deque
from pathlib import Path

import yaml
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
WHITE = 244          # a pixel counts as background when every channel is at least this
SCALE = 2


def cutout(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    px = im.load()
    bg = [[False] * w for _ in range(h)]
    q = deque((x, y) for x in range(w) for y in (0, h - 1))
    q.extend((x, y) for y in range(h) for x in (0, w - 1))
    while q:
        x, y = q.popleft()
        if bg[y][x] or min(px[x, y]) < WHITE:
            continue
        bg[y][x] = True
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx]:
                q.append((nx, ny))
    mask = Image.new("L", (w, h), 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            mp[x, y] = 0 if bg[y][x] else 255
    big = (w * SCALE, h * SCALE)
    mask = mask.resize(big, Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
    rgb = im.resize(big, Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    out = rgb.convert("RGBA")
    out.putalpha(mask)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", required=True)
    args = ap.parse_args()
    media = Path(args.media)
    manifest = json.loads((media / "manifest.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "static" / "img" / "products"
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / "content" / "th" / "products").glob("*.yaml")):
        product = yaml.safe_load(f.read_text(encoding="utf-8"))
        local = manifest.get(product["images"][0])
        if not local:
            print("no photo for", f.stem)
            continue
        cutout(media / local).save(out_dir / f"{f.stem}.png", optimize=True)
        print("made", f.stem)


if __name__ == "__main__":
    main()
