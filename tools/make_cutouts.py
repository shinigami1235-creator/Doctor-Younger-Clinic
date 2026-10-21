"""Cut the white background out of each product photo for the 3D showroom.

The clinic's product photos are 300 x 300 JPGs on plain white. The showroom stands each
product on a pedestal, so it needs the product alone on a transparent background.

    pip install rembg onnxruntime          # only needed for this script, not for the build
    python tools/make_cutouts.py --media path/to/static/media

--media is a folder holding the downloaded photos and manifest.json (made by fetch_media.py).
Output: static/img/products/<slug>.png at 600 x 600, committed to the repo so the
showroom works even when the media download fails. The first run downloads the
isnet-general-use model (about 180 MB) into ~/.rembg.

Steps for each photo:
1. Enlarge to 600 x 600 and let the isnet-general-use model find the product.
2. Keep only the largest shape, so stray specks of background are dropped.
3. Fill any holes inside it, so white labels and caps are never cut away.
4. Pull the edge in by one pixel and soften it, so there is no rough or white rim.
5. Remove the white that bled into the soft edge, so the product sits cleanly on any colour.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageFilter
from rembg import new_session, remove
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SIZE = 600


def clean_mask(alpha: np.ndarray) -> np.ndarray:
    """Return a smooth 0..1 mask holding only the product."""
    solid = alpha > 128
    labels, count = ndimage.label(solid)
    if count > 1:
        sizes = ndimage.sum(solid, labels, range(1, count + 1))
        solid = labels == (int(np.argmax(sizes)) + 1)
    solid = ndimage.binary_fill_holes(solid)
    solid = ndimage.binary_opening(solid, iterations=1)
    solid = ndimage.binary_erosion(solid, iterations=1)
    soft = Image.fromarray((solid * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
    return np.asarray(soft, dtype=np.float32) / 255.0


def cutout(src: Path, session) -> Image.Image:
    rgb = Image.open(src).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=2))
    model_alpha = np.asarray(remove(rgb, session=session, only_mask=True), dtype=np.float32)
    a = clean_mask(model_alpha)
    px = np.asarray(rgb, dtype=np.float32)
    # Edge pixels are a mix of product and white background; take the white back out.
    edge = (a > 0.02) & (a < 0.98)
    safe = np.clip(a, 0.02, 1.0)[..., None]
    unmixed = np.clip((px - (1.0 - safe) * 255.0) / safe, 0, 255)
    px = np.where(edge[..., None], unmixed, px)
    out = np.dstack([px, a * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", required=True)
    args = ap.parse_args()
    media = Path(args.media)
    manifest = json.loads((media / "manifest.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "static" / "img" / "products"
    out_dir.mkdir(parents=True, exist_ok=True)
    session = new_session("isnet-general-use")
    for f in sorted((ROOT / "content" / "th" / "products").glob("*.yaml")):
        product = yaml.safe_load(f.read_text(encoding="utf-8"))
        local = manifest.get(product["images"][0])
        if not local:
            print("no photo for", f.stem)
            continue
        cutout(media / local, session).save(out_dir / f"{f.stem}.png", optimize=True)
        print("made", f.stem)


if __name__ == "__main__":
    main()
