"""
Copy every photo the site uses from the current doctoryounger.com into static/media/.

The 3D product showroom needs the photos on the same site, since browsers block
WebGL from reading pictures hosted elsewhere. The preview workflow runs this before
build.py. Photos that fail to download keep loading from doctoryounger.com.

    python tools/fetch_media.py
"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT / "static" / "media"
LEGACY = "https://www.doctoryounger.com/"
PATTERN = re.compile(r"https://www\.doctoryounger\.com/[^\s\"'<>]+\.(?:jpe?g|png|gif|webp)|(?<![\w/])upload/[^\s\"'<>]+\.(?:jpe?g|png|gif|webp)|img-uploads/[^\s\"'<>]+\.(?:jpe?g|png|gif|webp)", re.I)


def collect() -> set[str]:
    urls = set()
    for f in list((ROOT / "content").rglob("*.yaml")) + list((ROOT / "data").glob("*.yaml")):
        for m in PATTERN.findall(f.read_text(encoding="utf-8")):
            urls.add(m if m.startswith("http") else LEGACY + m)
    return urls


def download(url: str):
    """Fetch one photo. Returns (url, relative path) or (url, None) when it fails."""
    rel = urllib.request.unquote(url[len(LEGACY):]).replace(" ", "-")
    target = MEDIA / rel
    if target.exists():
        return url, rel
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site rebuild media copy)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(r.read())
        return url, rel
    except Exception as e:  # the page falls back to the live URL
        print(f"skip {url}: {e}")
        return url, None


def main():
    MEDIA.mkdir(parents=True, exist_ok=True)
    manifest_path = MEDIA / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    urls = sorted(collect())

    # Try a few first, so a site that blocks the request does not stall the build for an hour.
    probe = [download(u) for u in urls[:5]]
    if not any(rel for _, rel in probe):
        print("doctoryounger.com refused the first 5 photos. Photos will load from the live site.")
        return
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = probe + list(pool.map(download, urls[5:]))
    for url, rel in results:
        if rel:
            manifest[url] = rel
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"{sum(1 for _, r in results if r)} photos copied, {sum(1 for _, r in results if not r)} skipped.")


if __name__ == "__main__":
    main()
