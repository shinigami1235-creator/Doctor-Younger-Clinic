"""
One-off import of the 2017 site's text into content/th/.

Reads raw/doctoryounger-content.json (saved from doctoryounger.com on 20 Oct 2026)
and writes one YAML file per page. The Thai text is kept as the clinic wrote it,
except misspelled English words listed in TYPO_FIXES.

    python tools/import_legacy.py
"""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = json.loads((ROOT / "raw" / "doctoryounger-content.json").read_text(encoding="utf-8"))
OUT = ROOT / "content" / "th"

# Misspelled English inside the Thai pages. Thai text is never changed.
TYPO_FIXES = {
    "Dermatoloyg": "Dermatology",
    "Paris-Frace": "Paris-France",
    "Anerican Boavd": "American Board",
    "Cutaneans": "Cutaneous",
    "KERAROSIS": "KERATOSIS",
    "LENTIGENES": "LENTIGINES",
    "RECCOMMEND": "RECOMMEND",
    "Thanmasat": "Thammasat",
    "Astaxathin": "Astaxanthin",
}

SERVICE_SLUGS = {
    "2": "co2-laser", "3": "fractional-laser", "1": "aramis-laser", "5": "pigment-laser",
    "7": "active-bright", "9": "ultra-deep-lifting", "4": "aura-bright", "6": "monopolar-rf",
    "51": "vital-lift", "10": "ha", "14": "v-touch", "11": "diamond-toxin",
    "27": "acne-clear-light", "25": "phonophoresis", "19": "synergica", "20": "blue-mate",
    "16": "dermalift", "23": "grey-mate", "17": "cry-o-lift", "53": "dermalift-and-mask",
    "18": "ruby-mate", "21": "oxy-plus", "22": "iontophoresis", "26": "new-a-peel",
    "24": "peeling-treatment", "28": "endermologie", "31": "tks-laser", "54": "vita-bright",
}
# Skin layer shown on the diagram, only where the clinic's own text names the layer.
SERVICE_DEPTH = {"aramis-laser": "dermis", "pigment-laser": "dermis",
                 "ultra-deep-lifting": "smas", "monopolar-rf": "dermis"}

PRODUCT_SLUGS = {
    24: "ageless-essence", 1: "sunscreen-360", 10: "cleansing-mousse", 12: "deep-cleansing-water",
    2: "advance-glow-radiant-serum", 5: "anti-aging-serum", 11: "milky-cleanser",
    25: "asta-real", 14: "olivie-beauty-cream",
}
DOCTOR_IDS = {1: "wilai-thanasarnaksorn", 3: "nopadol-amornpinyokiat", 5: "patcharaporn-wachiranuntasin",
              12: "manika-napharat", 11: "nattawan-limcharoenwiriyakul", 10: "puntharika-apinoraset",
              9: "urairak-sapsarn"}
SKIP_REVIEWS = {"6", "40"}      # 6 is the disclaimer page, 40 is empty
SKIP_NEWS = {"6"}               # test post


def fix(text: str) -> str:
    for bad, good in TYPO_FIXES.items():
        text = text.replace(bad, good)
    return text


def tidy(html: str, drop=()) -> str:
    """Remove the title lines the old template repeated inside the body, and empty tags."""
    for d in drop:
        if d:
            html = html.replace(f"<h3>{d}</h3>", "", 1)
    html = re.sub(r"<h3>\s*(<em></em>)?\s*</h3>", "", html)
    html = re.sub(r"<(h3|p)>[^<]*ย้อนกลับหน้า[^<]*</\1>", "", html)
    html = re.sub(r"<p>\s*</p>", "", html)
    return fix(html.strip())


def first_text(html: str, n=160) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:n].rsplit(" ", 1)[0] if len(text) > n else text


def dump(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")


def main():
    # Services
    for s in RAW["services"]:
        slug = SERVICE_SLUGS[str(s["s"])]
        data = {
            "name": s["name"], "tagline": fix(s["tagline"] or ""),
            "body": tidy(s["html"]), "closing": s["closing"],
            "images": s["images"],
        }
        if slug in SERVICE_DEPTH:
            data["depth"] = SERVICE_DEPTH[slug]
        dump(OUT / "services" / f"{slug}.yaml", data)

    # Products: pull usage, size and price out of the body into their own fields
    short = {int(p["id"]): p["text"] for p in RAW["product_list"]}
    for p in RAW["products"]:
        html = tidy(p["html"], drop=p["h1"] + p["h2"])
        html = re.sub(r'<img [^>]+>', "", html, count=1)
        fields = {}
        for key, label in (("usage", "วิธีใช้"), ("size", "ปริมาณสุทธิ"), ("price", "ราคา")):
            m = re.search(rf"<strong>\s*{label}\s*:\s*</strong>\s*([^<]+)", html)
            if m:
                fields[key] = m.group(1).strip()
                html = html.replace(m.group(0), "")
        html = re.sub(r"(<br>\s*)+$", "", html).strip()
        name = p["h1"][0]
        dump(OUT / "products" / f"{PRODUCT_SLUGS[p['id']]}.yaml", {
            "name": name, "tagline": p["h2"][0] if p["h2"] else "",
            "short": short.get(p["id"], "").replace(name, "", 1).strip(),
            "body": html, **fields, "images": p["images"],
        })

    # Doctors: full profile body without the photo
    for d in RAW["doctors"]:
        html = re.sub(r'<img [^>]+>', "", tidy(d["html"]), count=1)
        dump(OUT / "doctors" / f"{DOCTOR_IDS[d['id']]}.yaml", {"body": html, "images": d["images"]})

    # Reviews
    for r in RAW["reviews"]:
        if str(r["id"]) in SKIP_REVIEWS or not r["h1"]:
            continue
        thumb = RAW["review_list"].get(str(r["id"]), {}).get("thumb", "")
        dump(OUT / "reviews" / f"{r['id']}.yaml", {
            "title": fix(r["h1"][0]), "by": r["h2"][0] if r["h2"] else "",
            "body": tidy(r["html"], drop=r["h1"] + r["h2"]), "images": r["images"], "thumb": thumb,
        })

    # Beauty's Talk: split the interview into question and answer turns
    names = {2: ("คุณไก่", "สุปราณี เจริญผล", "upload/beauty/big/2.jpg"),
             1: ("คุณหยาดทิพย์", "หยาดทิพย์ ราชปาล", "upload/beauty/big/1.jpg")}
    for t in RAW["talk"]:
        nick, name, photo = names[t["id"]]
        text = re.sub(r"<[^>]+>", " ", t["html"]).replace(name, "", 1)
        text = re.sub(r"\s+", " ", text).strip()
        parts = re.split(r"(Doctor Younger\s*:|" + re.escape(nick) + r"\s*:)", text)
        turns, who = [], None
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.endswith(":"):
                who = "q" if part.startswith("Doctor Younger") else "a"
            elif who:
                turns.append({who: part})
        # Pair questions with answers
        qa, cur = [], {}
        for turn in turns:
            if "q" in turn:
                cur = {"q": turn["q"]}
            else:
                cur["a"] = turn["a"]
                qa.append(cur)
                cur = {}
        slug = {2: "supranee-charoenphol", 1: "yardthip-rajpal"}[t["id"]]
        dump(OUT / "beauty-talk" / f"{slug}.yaml", {"nickname": nick, "name": name, "photo": photo,
                                                    "qa": qa, "images": t["images"]})

    # News
    for n in RAW["news"]:
        if str(n["id"]) in SKIP_NEWS:
            continue
        dump(OUT / "news" / f"{n['id']}.yaml", {
            "title": n["h1"][0], "date": n["h2"][0] if n["h2"] else "",
            "body": tidy(n["html"], drop=n["h1"] + n["h2"]), "images": n["images"],
        })

    # Tips
    for t in RAW["tips"]:
        if not t["h1"]:
            continue
        body = tidy(t["html"], drop=t["h1"] + t["h2"])
        m = re.search(r"<h3>\s*ที่มา\s*:?\s*([^<]+)</h3>", body) or re.search(r"<p>\s*ที่มา\s*:?\s*([^<]+)</p>", body)
        dump(OUT / "tips" / f"{t['id']}.yaml", {
            "title": fix(t["h1"][0]), "date": t["h2"][0] if t["h2"] else "",
            "source": m.group(1).strip() if m else "",
            "body": body, "images": t["images"],
            "thumb": RAW["tips_list"].get(str(t["id"]), {}).get("thumb", ""),
        })


if __name__ == "__main__":
    main()
