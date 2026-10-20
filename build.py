"""
Build the Doctor Younger Clinic website.

Reads the text in content/ and the shared data in data/, fills the HTML templates
in templates/, and writes the finished site into dist/.

    python build.py                                   # preview build for GitHub Pages
    python build.py --mode production                 # build for www.doctoryounger.com

Preview builds carry a noindex tag so Google never indexes the preview copy, and
they skip Google Analytics so test visits do not reach the clinic's reports.

Images: run `python tools/fetch_media.py` first to copy the clinic's photos into
static/media/. Any photo not copied yet still loads from the current site.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
LANGS = ["th", "en"]          # Thai is the main language and sits at the site root
DEFAULT_LANG = "th"
PREVIEW_BASE = "/Doctor-Younger-Clinic"   # GitHub Pages serves the preview from this folder
LEGACY = "https://www.doctoryounger.com/"

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Product order on the current products page.
PRODUCT_ORDER = ["ageless-essence", "sunscreen-360", "cleansing-mousse", "deep-cleansing-water",
                 "advance-glow-radiant-serum", "anti-aging-serum", "milky-cleanser", "asta-real",
                 "olivie-beauty-cream"]

# Words that tie a review to a treatment or product page.
REVIEW_KEYWORDS = {
    "co2-laser": ["co2 laser", "co2"], "fractional-laser": ["fractional"], "aramis-laser": ["aramis"],
    "pigment-laser": ["pigment laser"], "active-bright": ["active bright"], "ultra-deep-lifting": ["ultra deep"],
    "aura-bright": ["aura bright"], "monopolar-rf": ["monopolar"], "vital-lift": ["vital lift"],
    "v-touch": ["v-touch"], "diamond-toxin": ["diamond toxin"], "acne-clear-light": ["acne clear"],
    "phonophoresis": ["phonophoresis"], "synergica": ["synergica"], "blue-mate": ["blue mate"],
    "dermalift": ["dermalift"], "grey-mate": ["grey mate"], "cry-o-lift": ["cry-o"],
    "ruby-mate": ["ruby mate"], "oxy-plus": ["oxy plus"], "iontophoresis": ["iontophoresis"],
    "new-a-peel": ["new a peel"], "peeling-treatment": ["peeling"], "endermologie": ["endermologie"],
    "tks-laser": ["tks"], "vita-bright": ["vita bright"],
    "sunscreen-360": ["sunscreen"], "ageless-essence": ["ageless"], "asta-real": ["asta real"],
}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_folder(folder: Path) -> dict:
    if not folder.exists():
        return {}
    return {p.stem: load(p) for p in sorted(folder.glob("*.yaml"))}


def load_data():
    data = {name: load(ROOT / "data" / f"{name}.yaml")
            for name in ("site", "branches", "doctors", "services", "concerns")}
    data["content"] = {}
    for lang in LANGS:
        folder = ROOT / "content" / lang
        data["content"][lang] = {
            "ui": load(folder / "ui.yaml"),
            "home": load(folder / "home.yaml"),
            "services": load_folder(folder / "services"),
            "products": load_folder(folder / "products"),
            "doctors": load_folder(folder / "doctors"),
            "reviews": load_folder(folder / "reviews"),
            "talk": load_folder(folder / "beauty-talk"),
            "news": load_folder(folder / "news"),
            "tips": load_folder(folder / "tips"),
        }
    # Doctor profiles: the weekly schedule is shown from data/doctors.yaml as a table,
    # so the schedule paragraph copied from the old profile page is left out.
    for lang in LANGS:
        for doc in data["content"][lang]["doctors"].values():
            doc["body"] = re.split(r"<h3>[^<]*(ตารางออกตรวจ|[Ss]chedule)[^<]*</h3>", doc["body"])[0]
    manifest = ROOT / "static" / "media" / "manifest.json"
    data["media"] = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    return data


# --------------------------------------------------------------------------- #
# Addresses
# --------------------------------------------------------------------------- #

class Paths:
    """Builds every link on the site so the base folder and language prefix live in one place."""

    def __init__(self, base: str, origin: str):
        self.base = base.rstrip("/")
        self.origin = origin.rstrip("/")

    def page(self, path: str, lang: str) -> str:
        prefix = "" if lang == DEFAULT_LANG else f"/{lang}"
        return f"{self.base}{prefix}{path}"

    def absolute(self, path: str, lang: str) -> str:
        prefix = "" if lang == DEFAULT_LANG else f"/{lang}"
        return f"{self.origin}{prefix}{path}"

    def static(self, path: str) -> str:
        return f"{self.base}/static/{path}"


def service_path(category_id: str, slug: str) -> str:
    return f"/services/{category_id}/{slug}/"


def branch_path(branch_id: str) -> str:
    return f"/branches/{branch_id}/"


# --------------------------------------------------------------------------- #
# Structured data for Google (JSON-LD)
# --------------------------------------------------------------------------- #

def org_schema(data, paths: Paths, lang: str) -> dict:
    site = data["site"]
    return {
        "@type": "Organization",
        "@id": f"{paths.origin}/#organization",
        "name": site["name"],
        "alternateName": ["Doctor Younger", "ด็อกเตอร์ ยังเกอร์ คลินิก"],
        "url": paths.absolute("/", lang),
        "slogan": site["tagline"],
        "telephone": site["call_center_tel"],
        "sameAs": list(site["social"].values()),
        "department": [{"@id": f"{paths.origin}{branch_path(b['id'])}#clinic"} for b in data["branches"]],
    }


def clinic_schema(branch: dict, data, paths: Paths, lang: str) -> dict:
    site = data["site"]
    return {
        "@type": ["MedicalClinic", "MedicalBusiness"],
        "@id": f"{paths.origin}{branch_path(branch['id'])}#clinic",
        "name": f"{site['name']} {branch['name'][lang]}",
        "url": paths.absolute(branch_path(branch["id"]), lang),
        "telephone": branch["phone_tel"],
        "medicalSpecialty": "Dermatology",
        "parentOrganization": {"@id": f"{paths.origin}/#organization"},
        "address": {
            "@type": "PostalAddress",
            "streetAddress": branch["postal"]["street"],
            "addressLocality": branch["postal"]["locality"],
            "addressRegion": branch["postal"]["region"],
            "postalCode": branch["postal"]["code"],
            "addressCountry": "TH",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": branch["lat"], "longitude": branch["lng"]},
        "hasMap": maps_link(branch),
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "opens": branch["opens"],
            "closes": branch["closes"],
        }],
    }


def breadcrumb_schema(crumbs: list[tuple[str, str]]) -> dict:
    return {"@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(crumbs)]}


def graph(*nodes) -> str:
    return json.dumps({"@context": "https://schema.org", "@graph": [n for n in nodes if n]},
                      ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------- #
# Helpers used in templates
# --------------------------------------------------------------------------- #

def maps_link(branch: dict) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={branch['lat']},{branch['lng']}"


def directions_link(branch: dict) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={branch['lat']},{branch['lng']}"


def map_embed(branch: dict) -> str:
    return f"https://maps.google.com/maps?q={branch['lat']},{branch['lng']}&z=17&output=embed"


def describe_shift(shift: dict, ui: dict) -> str:
    """Turn one schedule line into readable text, e.g. 'เสาร์ (สัปดาห์ที่ 3) 13.00 - 16.00 น.'"""
    days = ", ".join(ui["weekdays"][WEEKDAY_KEYS.index(d)] for d in shift["days"])
    if shift.get("weeks"):
        days += f" ({ui['duty_weeks']} {', '.join(map(str, shift['weeks']))})"
    if shift.get("except_weeks"):
        days += f" ({ui['duty_except']} {', '.join(map(str, shift['except_weeks']))})"
    t = f"{shift['from'].replace(':', '.')} - {shift['to'].replace(':', '.')}"
    return f"{days} {t} {ui['time_suffix']}".strip()


def plain(html: str, n: int | None = None) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    if n and len(text) > n:
        text = text[:n].rsplit(" ", 1)[0] + "…"
    return text


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

def build(mode: str, base: str):
    data = load_data()
    site = data["site"]
    preview = mode == "preview"
    origin = site["production_url"]
    paths = Paths(base, origin)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "static", DIST / "static")
    (DIST / ".nojekyll").write_text("")

    # Photos copied by tools/fetch_media.py are served locally, the rest from the current site.
    def media(p: str) -> str:
        if not p:
            return ""
        url = p if p.startswith("http") else LEGACY + p
        local = data["media"].get(url)
        return paths.static("media/" + local) if local else url

    def media_html(html: str) -> Markup:
        html = re.sub(r'src="(https://www\.doctoryounger\.com/[^"]+)"',
                      lambda m: f'src="{media(m.group(1))}" loading="lazy"', html or "")
        return Markup(html)

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters["media"] = media
    env.filters["media_html"] = media_html
    env.filters["plain"] = plain
    env.filters["th"] = lambda text: " is-th" if any("฀" <= ch <= "๿" for ch in str(text)) else ""
    env.globals.update(site=site, preview=preview, paths=paths, branches=data["branches"],
                       doctors=data["doctors"], categories=data["services"], concerns=data["concerns"],
                       year=date.today().year, maps_link=maps_link, directions_link=directions_link,
                       map_embed=map_embed, service_path=service_path, branch_path=branch_path,
                       describe_shift=describe_shift, product_order=PRODUCT_ORDER)

    def doctors_for(lang):
        """Doctor list with schedules, in the shape site.js reads for the duty widget."""
        return [{
            "name": d["title"][lang] + ("" if lang == "th" else " ") + d["name"][lang],
            "nickname": d["nickname"][lang],
            "photo": media(d["photo"]),
            "url": paths.page(f"/doctors/{d['id']}/", lang),
            "shifts": [{"branch": s["branch"], "days": [WEEKDAY_KEYS.index(x) for x in s["days"]],
                        "weeks": s.get("weeks"), "except": s.get("except_weeks"),
                        "from": s["from"], "to": s["to"]} for s in d["schedule"]],
        } for d in data["doctors"]]

    # Category of every treatment, and which treatments have text in every language.
    cat_of = {i["slug"]: c for c in data["services"] for i in c["items"]}
    built_services = {s for s in cat_of if all(s in data["content"][l]["services"] for l in LANGS)}
    env.globals.update(built_services=built_services, cat_of=cat_of)

    # Reviews that mention each treatment or product, matched on the Thai text.
    th_reviews = data["content"]["th"]["reviews"]
    mentions = {key: [rid for rid, r in th_reviews.items()
                      if any(w in (r["title"] + " " + plain(r["body"])).lower() for w in words)]
                for key, words in REVIEW_KEYWORDS.items()}
    review_order = sorted(th_reviews, key=lambda k: -int(k))
    tip_order = sorted(data["content"]["th"]["tips"], key=lambda k: -int(k))
    env.globals.update(mentions=mentions, review_order=review_order, tip_order=tip_order)

    sitemap: list[dict] = []

    def write(path: str, lang: str, template: str, langs=LANGS, noindex=False, **ctx):
        """Render one page in one language and note it for the sitemap."""
        c = data["content"][lang]
        alternates = {l: paths.absolute(path, l) for l in langs}
        other = "en" if lang == "th" else "th"
        html = env.get_template(template).render(
            lang=lang, ui=c["ui"], c=c, path=path, noindex=noindex,
            canonical=paths.absolute(path, lang), alternates=alternates,
            switch_url=paths.page(path if other in langs else "/", other),
            url=lambda p, l=lang: paths.page(p, l),
            doctors_json=doctors_for(lang), **ctx)
        out = DIST / (path.strip("/") if lang == DEFAULT_LANG else f"{lang}/{path.strip('/')}") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        if lang == DEFAULT_LANG and not noindex:
            sitemap.append({"path": path, "alternates": alternates})

    for lang in LANGS:
        c = data["content"][lang]
        ui = c["ui"]
        home_url = paths.absolute("/", lang)
        crumb_home = (ui["nav"]["home"], home_url)

        # Homepage
        write("/", lang, "home.html", page=c["home"],
              schema=graph(org_schema(data, paths, lang),
                           {"@type": "WebSite", "@id": f"{origin}/#website", "url": home_url,
                            "name": site["name"], "inLanguage": lang},
                           *[clinic_schema(b, data, paths, lang) for b in data["branches"]]))

        # Services: index, categories, treatments
        write("/services/", lang, "services.html", page=c["home"],
              schema=graph(breadcrumb_schema([crumb_home, (ui["nav"]["services"], paths.absolute("/services/", lang))])))
        for cat in data["services"]:
            cpath = f"/services/{cat['id']}/"
            write(cpath, lang, "category.html", category=cat,
                  schema=graph(breadcrumb_schema([crumb_home, (ui["nav"]["services"], paths.absolute("/services/", lang)),
                                                  (cat["name"], paths.absolute(cpath, lang))])))
            items = [i for i in cat["items"] if i["slug"] in built_services]
            for n, item in enumerate(items):
                path = service_path(cat["id"], item["slug"])
                svc = c["services"][item["slug"]]
                write(path, lang, "service.html", page=svc, category=cat, item=item,
                      prev_item=items[n - 1] if n else None, next_item=items[n + 1] if n + 1 < len(items) else None,
                      schema=graph(
                          {"@type": "MedicalProcedure", "name": svc["name"],
                           "description": svc["tagline"], "url": paths.absolute(path, lang),
                           "procedureType": "https://schema.org/NoninvasiveProcedure",
                           "provider": {"@id": f"{origin}/#organization"}},
                          breadcrumb_schema([crumb_home, (cat["name"], paths.absolute(f"/services/{cat['id']}/", lang)),
                                             (svc["name"], paths.absolute(path, lang))])))

        # Products
        write("/products/", lang, "products.html",
              schema=graph(breadcrumb_schema([crumb_home, (ui["nav"]["products"], paths.absolute("/products/", lang))])))
        for n, slug in enumerate(PRODUCT_ORDER):
            p = c["products"][slug]
            path = f"/products/{slug}/"
            write(path, lang, "product.html", page=p, slug=slug,
                  next_slug=PRODUCT_ORDER[(n + 1) % len(PRODUCT_ORDER)],
                  schema=graph({"@type": "Product", "name": p["name"], "description": p.get("tagline", ""),
                                "image": media(p["images"][0]) if p.get("images") else None,
                                "brand": {"@type": "Brand", "name": "Doctor Younger"}},
                               breadcrumb_schema([crumb_home, (ui["nav"]["products"], paths.absolute("/products/", lang)),
                                                  (p["name"], paths.absolute(path, lang))])))

        # Doctors
        write("/doctors/", lang, "doctors.html", page=c["home"],
              schema=graph(breadcrumb_schema([crumb_home, (ui["nav"]["doctors"], paths.absolute("/doctors/", lang))])))
        for d in data["doctors"]:
            path = f"/doctors/{d['id']}/"
            write(path, lang, "doctor.html", doctor=d, page=c["doctors"].get(d["id"], {}),
                  schema=graph({"@type": "Physician", "name": d["title"][lang] + " " + d["name"][lang],
                                "medicalSpecialty": "Dermatology", "image": media(d["photo"]),
                                "worksFor": {"@id": f"{origin}/#organization"}},
                               breadcrumb_schema([crumb_home, (ui["nav"]["doctors"], paths.absolute("/doctors/", lang)),
                                                  (d["name"][lang], paths.absolute(path, lang))])))

        # Reviews
        write("/reviews/", lang, "reviews.html")
        for rid in review_order:
            write(f"/reviews/{rid}/", lang, "review.html", page=c["reviews"][rid], rid=rid)

        # Beauty's Talk
        write("/beauty-talk/", lang, "talk_index.html", page=c["home"])
        for slug, t in c["talk"].items():
            write(f"/beauty-talk/{slug}/", lang, "talk.html", page=t, slug=slug)

        # News
        write("/news/", lang, "news.html")
        for nid, n in c["news"].items():
            write(f"/news/{nid}/", lang, "news_item.html", page=n, nid=nid)

        # Branches
        for b in data["branches"]:
            path = branch_path(b["id"])
            here = [d for d in data["doctors"] if any(s["branch"] == b["id"] for s in d["schedule"])]
            write(path, lang, "branch.html", branch=b, doctors_here=here, page=c["home"],
                  schema=graph(org_schema(data, paths, lang), clinic_schema(b, data, paths, lang),
                               breadcrumb_schema([crumb_home, (b["name"][lang], paths.absolute(path, lang))])))

    # Tips: Thai only. Every article credits another publisher (Sanook, Kapook, ...), so the
    # pages are kept out of Google with noindex until the clinic replaces them with its own.
    write("/tips/", "th", "tips.html", langs=["th"], noindex=True)
    for tid in tip_order:
        write(f"/tips/{tid}/", "th", "tip.html", langs=["th"], noindex=True,
              page=data["content"]["th"]["tips"][tid], tid=tid)

    # 404 page for GitHub Pages and Apache
    th = data["content"]["th"]
    (DIST / "404.html").write_text(
        env.get_template("404.html").render(lang="th", ui=th["ui"], c=th, path="/", noindex=True,
                                            canonical=origin + "/", alternates={},
                                            switch_url=paths.page("/", "en"), doctors_json=[],
                                            url=lambda p: paths.page(p, "th"), schema=None),
        encoding="utf-8")

    write_sitemap(sitemap)
    write_robots(origin, preview)
    write_redirects(data, review_order, tip_order)
    count = sum(1 for _ in DIST.rglob("index.html"))
    print(f"Built {count} pages into {DIST} ({mode}).")


def write_sitemap(entries):
    rows = []
    for e in entries:
        links = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>' for l, u in e["alternates"].items())
        links += f'<xhtml:link rel="alternate" hreflang="x-default" href="{e["alternates"][DEFAULT_LANG]}"/>'
        for url in e["alternates"].values():
            rows.append(f"<url><loc>{url}</loc>{links}</url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")
    (DIST / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots(origin, preview):
    text = "User-agent: *\nDisallow: /\n" if preview else f"User-agent: *\nAllow: /\n\nSitemap: {origin}/sitemap.xml\n"
    (DIST / "robots.txt").write_text(text, encoding="utf-8")


def write_redirects(data, review_order, tip_order):
    """301 redirects from every old .php address to its new page.

    Written twice: redirects.csv for people to read, and .htaccess for an Apache server.
    """
    rows = [("index.php", "/"), ("about-us.php", "/"), ("doctor-profile.php", "/doctors/"),
            ("beauty-talk.php", "/beauty-talk/"), ("services.php", "/services/"),
            ("products.php", "/products/"), ("review.php", "/reviews/"), ("tips.php", "/tips/"),
            ("news-events.php", "/news/"), ("contact-us.php", "/branches/sukhumvit-23/"),
            ("booking.php", "/"), ("register.php", "/"), ("promotion.php", "/"), ("faq.php", "/")]
    for cat in data["services"]:
        rows.append((cat["legacy"], f"/services/{cat['id']}/"))
        for item in cat["items"]:
            rows.append((item["legacy"], service_path(cat["id"], item["slug"])))
    product_ids = {"ageless-essence": 24, "sunscreen-360": 1, "cleansing-mousse": 10, "deep-cleansing-water": 12,
                   "advance-glow-radiant-serum": 2, "anti-aging-serum": 5, "milky-cleanser": 11,
                   "asta-real": 25, "olivie-beauty-cream": 14}
    rows += [(f"products-detail.php?pd={pid}", f"/products/{slug}/") for slug, pid in product_ids.items()]
    rows += [(f"doctor-profile-detail.php?doctor={d['legacy_id']}", f"/doctors/{d['id']}/") for d in data["doctors"]]
    rows += [(f"review-detail.php?review={r}", f"/reviews/{r}/") for r in review_order]
    rows += [(f"tips-detail.php?tips={t}", f"/tips/{t}/") for t in tip_order]
    rows += [("beauty-talk-detail.php?celeb=2", "/beauty-talk/supranee-charoenphol/"),
             ("beauty-talk-detail.php?celeb=1", "/beauty-talk/yardthip-rajpal/")]
    rows += [(f"news-detail.php?news={n}", f"/news/{n}/") for n in (1, 2, 3)]

    with open(ROOT / "redirects.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["old", "new"])
        w.writerows(rows)

    lines = ["RewriteEngine On", "ErrorDocument 404 /404.html", ""]
    for old, new in rows:
        page, _, query = old.partition("?")
        if query:
            lines.append(f"RewriteCond %{{QUERY_STRING}} ^{query}$")
        lines.append(f"RewriteRule ^{page.replace('.', '[.]')}$ {new}? [R=301,L]")
    lines += ["", "# The 2017 demo copy of the site", "RewriteRule ^demo2017/ / [R=301,L]"]
    (DIST / ".htaccess").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["preview", "production"], default="preview")
    parser.add_argument("--base", default=None,
                        help="Folder the site is served from. Defaults to the GitHub Pages folder for previews.")
    args = parser.parse_args()
    base = args.base if args.base is not None else (PREVIEW_BASE if args.mode == "preview" else "")
    build(args.mode, base)
