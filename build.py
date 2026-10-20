"""
Build the Doctor Younger Clinic website.

Reads the text in content/ and the shared data in data/, fills the HTML templates
in templates/, and writes the finished site into dist/.

    python build.py                                   # preview build for GitHub Pages
    python build.py --mode production                 # build for www.doctoryounger.com

Preview builds carry a noindex tag so Google never indexes the preview copy, and
they skip Google Analytics so test visits do not reach the clinic's reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
LANGS = ["th", "en"]          # Thai is the main language and sits at the site root
DEFAULT_LANG = "th"
PREVIEW_BASE = "/Doctor-Younger-Clinic"   # GitHub Pages serves the preview from this folder

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data():
    data = {name: load(ROOT / "data" / f"{name}.yaml")
            for name in ("site", "branches", "doctors", "services")}
    data["content"] = {}
    for lang in LANGS:
        folder = ROOT / "content" / lang
        data["content"][lang] = {
            "ui": load(folder / "ui.yaml"),
            "home": load(folder / "home.yaml"),
            "services": {p.stem: load(p) for p in sorted((folder / "services").glob("*.yaml"))},
        }
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
        """Site-relative link, e.g. page('/services/', 'en') -> '/en/services/'."""
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
        "sameAs": [v for v in site["social"].values()],
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
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(crumbs)
        ],
    }


def graph(*nodes) -> str:
    return json.dumps({"@context": "https://schema.org", "@graph": list(nodes)},
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

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.globals.update(site=site, preview=preview, paths=paths, branches=data["branches"],
                       doctors=data["doctors"], categories=data["services"], year=date.today().year,
                       maps_link=maps_link, directions_link=directions_link, map_embed=map_embed,
                       service_path=service_path, branch_path=branch_path, describe_shift=describe_shift)
    env.filters["media"] = lambda p: p if p.startswith("http") else site["legacy_media"] + p
    # Adds the is-th class to any label containing Thai, which turns off wide letter-spacing.
    env.filters["th"] = lambda text: " is-th" if any("\u0e00" <= ch <= "\u0e7f" for ch in str(text)) else ""

    def doctors_for(lang):
        """Doctor list with schedules, in the shape site.js reads for the duty widget."""
        return [{
            "name": d["title"][lang] + ("" if lang == "th" else " ") + d["name"][lang],
            "nickname": d["nickname"][lang],
            "photo": env.filters["media"](d["photo"]),
            "shifts": [{"branch": s["branch"], "days": [WEEKDAY_KEYS.index(x) for x in s["days"]],
                        "weeks": s.get("weeks"), "except": s.get("except_weeks"),
                        "from": s["from"], "to": s["to"]} for s in d["schedule"]],
        } for d in data["doctors"]]
    env.globals["doctors_for"] = doctors_for

    sitemap: list[dict] = []

    def write(path: str, lang: str, template: str, **ctx):
        """Render one page in one language and note it for the sitemap."""
        ui = data["content"][lang]["ui"]
        alternates = {l: paths.absolute(path, l) for l in LANGS}
        html = env.get_template(template).render(
            lang=lang, ui=ui, path=path,
            canonical=paths.absolute(path, lang),
            alternates=alternates,
            switch_url=paths.page(path, "en" if lang == "th" else "th"),
            url=lambda p, l=lang: paths.page(p, l),
            built_services=built_services,
            **ctx)
        out = DIST / (path.strip("/") if lang == DEFAULT_LANG else f"{lang}/{path.strip('/')}") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        if lang == DEFAULT_LANG:
            sitemap.append({"path": path, "alternates": alternates})

    # Treatments that have text in every language get their own page.
    built_services = {
        item["slug"]
        for cat in data["services"] for item in cat["items"]
        if all(item["slug"] in data["content"][l]["services"] for l in LANGS)
    }

    for lang in LANGS:
        c = data["content"][lang]
        home_url = paths.absolute("/", lang)

        # Homepage
        featured_slug = c["home"]["services"]["featured"]
        featured_cat = next(cat for cat in data["services"]
                            if any(i["slug"] == featured_slug for i in cat["items"]))
        write("/", lang, "home.html", page=c["home"],
              featured=c["services"][featured_slug], featured_cat=featured_cat,
              featured_slug=featured_slug,
              schema=graph(org_schema(data, paths, lang),
                           {"@type": "WebSite", "@id": f"{origin}/#website", "url": home_url,
                            "name": site["name"], "inLanguage": lang},
                           *[clinic_schema(b, data, paths, lang) for b in data["branches"]]))

        # Treatment pages
        for cat in data["services"]:
            for item in cat["items"]:
                if item["slug"] not in built_services:
                    continue
                path = service_path(cat["id"], item["slug"])
                svc = c["services"][item["slug"]]
                write(path, lang, "service.html", page=svc, category=cat, item=item,
                      schema=graph(
                          {"@type": "MedicalProcedure", "name": svc["name"],
                           "description": svc["meta"]["description"],
                           "url": paths.absolute(path, lang),
                           "procedureType": "https://schema.org/NoninvasiveProcedure",
                           "provider": {"@id": f"{origin}/#organization"}},
                          breadcrumb_schema([(c["ui"]["nav"]["home"], home_url),
                                             (c["ui"]["nav"]["services"], home_url + "#services"),
                                             (svc["name"], paths.absolute(path, lang))])))

        # Branch pages
        for b in data["branches"]:
            path = branch_path(b["id"])
            here = [d for d in data["doctors"] if any(s["branch"] == b["id"] for s in d["schedule"])]
            write(path, lang, "branch.html", branch=b, doctors_here=here, page=c["home"],
                  schema=graph(org_schema(data, paths, lang), clinic_schema(b, data, paths, lang),
                               breadcrumb_schema([(c["ui"]["nav"]["home"], home_url),
                                                  (b["name"][lang], paths.absolute(path, lang))])))

    # 404 page for GitHub Pages and Apache
    (DIST / "404.html").write_text(
        env.get_template("404.html").render(lang="th", ui=data["content"]["th"]["ui"], path="/",
                                            canonical=origin + "/", alternates={},
                                            switch_url=paths.page("/", "en"),
                                            url=lambda p: paths.page(p, "th"), schema=None),
        encoding="utf-8")

    write_sitemap(sitemap, preview)
    write_robots(origin, preview)
    write_redirects(data)
    print(f"Built {len(sitemap) * len(LANGS)} pages into {DIST} ({mode}).")


def write_sitemap(entries, preview):
    rows = []
    for e in entries:
        links = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{u}"/>'
                        for l, u in e["alternates"].items())
        links += f'<xhtml:link rel="alternate" hreflang="x-default" href="{e["alternates"][DEFAULT_LANG]}"/>'
        for url in e["alternates"].values():
            rows.append(f"<url><loc>{url}</loc>{links}</url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")
    (DIST / "sitemap.xml").write_text(xml, encoding="utf-8")


def write_robots(origin, preview):
    if preview:
        text = "User-agent: *\nDisallow: /\n"
    else:
        text = f"User-agent: *\nAllow: /\n\nSitemap: {origin}/sitemap.xml\n"
    (DIST / "robots.txt").write_text(text, encoding="utf-8")


def write_redirects(data):
    """301 redirects from every old .php address to its new page.

    Written twice: redirects.csv for people to read, and .htaccess for an Apache server.
    """
    rows = [("index.php", "/"), ("about-us.php", "/about/"), ("doctor-profile.php", "/doctors/"),
            ("beauty-talk.php", "/beauty-talk/"), ("services.php", "/services/"),
            ("review.php", "/reviews/"), ("contact-us.php", "/branches/sukhumvit-23/"),
            ("booking.php", "/booking/"), ("privacy-policy.php", "/privacy-policy/")]
    for cat in data["services"]:
        rows.append((cat["legacy"], f"/services/{cat['id']}/"))
        for item in cat["items"]:
            rows.append((item["legacy"], service_path(cat["id"], item["slug"])))
    for d in data["doctors"]:
        rows.append((f"doctor-profile-detail.php?doctor={d['legacy_id']}", f"/doctors/{d['id']}/"))

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
