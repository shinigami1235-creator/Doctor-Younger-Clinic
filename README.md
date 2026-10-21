# Doctor Younger Clinic website

This is the rebuild of doctoryounger.com. Thai is the main language at the site root and English sits under `/en/`. All text lives in YAML files, and `build.py` turns them into plain HTML pages in `dist/`.

## Build

You need Python 3.10 or newer.

```
pip install -r requirements.txt
python build.py                      # preview build, served from /Doctor-Younger-Clinic/ on GitHub Pages
python build.py --mode production    # build for www.doctoryounger.com
```

Upload the contents of `dist/` to the web server. The preview build is marked `noindex` and blocks crawlers in `robots.txt` so Google never indexes the preview copy. The production build allows crawling, adds the Search Console verification tag and loads Google Analytics after the visitor accepts cookies.

## Folders

| Folder | What it holds |
|---|---|
| `data/site.yaml` | Clinic name, call centre number, LINE, social links, Analytics ID |
| `data/branches.yaml` | Address, phone, hours and map pin for each branch |
| `data/doctors.yaml` | Doctors with their weekly schedule at each branch |
| `data/services.yaml` | Service categories and treatments, with their old addresses |
| `data/concerns.yaml` | Skin concerns for the treatment finder and which treatments belong to each |
| `content/th/`, `content/en/` | Page text in each language: `services/`, `products/`, `doctors/`, `reviews/`, `beauty-talk/`, `news/`, plus `tips/` in Thai only |
| `raw/` | The old site's text as saved on 20 October 2026, kept as the source of the import |
| `tools/import_legacy.py` | One-off script that turned `raw/` into the Thai content files |
| `tools/fetch_media.py` | Copies the clinic's photos from the old site into `static/media/` |
| `tools/make_cutouts.py` | Cuts the white background out of each product photo for the 3D showroom, saved to `static/img/products/` |
| `templates/` | Jinja2 HTML templates |
| `static/` | CSS, JavaScript and self-hosted fonts |
| `dist/` | The finished site. Created by `build.py`, never edited by hand |

## Common edits

**Change a phone number or opening hours.** Edit the branch in `data/branches.yaml` and build again. The footer, branch page and the structured data Google reads all update together. Keep the values identical to the branch's Google Business Profile.

**Change a doctor's schedule.** Edit the `schedule` lines under that doctor in `data/doctors.yaml`. Each line is one shift:

```yaml
- {branch: sukhumvit-23, days: [sat], weeks: [1, 3], from: "12:00", to: "18:00"}
```

`weeks` limits a shift to certain weeks of the month and `except_weeks` skips weeks. The "Doctors on duty" panel and the branch pages read from this file.

**Add a treatment page.** Add the treatment to `data/services.yaml`, then copy any file in `content/th/services/` to a new file named after its `slug`, replace the text, and do the same in `content/en/services/`. A treatment gets its own page once it has a file in both languages. `body` is HTML, and `depth` (epidermis, dermis, fat, smas or muscle) adds the skin layer diagram.

**Add it to the treatment finder.** List its slug under each matching concern in `data/concerns.yaml`.

**Add a doctor.** Add an entry to `data/doctors.yaml` and build again.

## Google

- Each branch page carries `MedicalClinic` structured data with its own address, phone, map pin and hours, linked to one `Organization` for the clinic. This keeps Google from merging Sukhumvit 23 with J Young Clinic Asok, which sits nearby.
- `sitemap.xml` lists every page with its Thai and English versions.
- `.htaccess` and `redirects.csv` send every old `.php` address to its new page with a 301 redirect so the old pages pass their ranking on. `.htaccess` works on Apache. On another server, copy the rules from `redirects.csv`.

## Tips

Every one of the 85 Tips articles credits another publisher (Sanook, Kapook, Mthai and others). They are built in Thai only, kept out of the sitemap and marked `noindex`, since Google ranks copied articles poorly and can mark the whole site down for them. Replace them with the clinic's own articles before removing the `noindex`.

## Images

Run `python tools/fetch_media.py` before `build.py` to copy every photo from the old site into `static/media/`. The preview workflow does this on GitHub. Any photo not copied still loads from doctoryounger.com. The 3D product showroom uses its own cutouts in `static/img/products/`, which are kept in the repo since browsers block WebGL from reading photos hosted on another site. When a product photo changes, run `python tools/fetch_media.py` and then `python tools/make_cutouts.py --media static/media`, and commit the new PNG. The homepage photo comes from Unsplash and should be replaced with a photo of the clinic.

## Backend later

The YAML files are shaped like database records. Two routes are open:

1. Decap CMS gives staff an editing screen in the browser that saves to the YAML files on GitHub, and the site rebuilds itself. No server is needed.
2. A Flask app with SQLite and an admin panel, using the same templates, if the clinic wants member accounts or live booking slots.
