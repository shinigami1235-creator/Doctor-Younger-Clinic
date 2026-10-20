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
| `content/th/`, `content/en/` | Page text in each language, one file per page |
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

**Add a treatment page.** Copy `content/th/services/ultra-deep-lifting.yaml` to a new file named after the treatment's `slug` in `data/services.yaml`, replace the text, and do the same in `content/en/services/`. A treatment gets its own page once it has a file in both languages. Until then it shows as a name in the menu without a link.

**Add a doctor.** Add an entry to `data/doctors.yaml` and build again.

## Google

- Each branch page carries `MedicalClinic` structured data with its own address, phone, map pin and hours, linked to one `Organization` for the clinic. This keeps Google from merging Sukhumvit 23 with J Young Clinic Asok, which sits nearby.
- `sitemap.xml` lists every page with its Thai and English versions.
- `.htaccess` and `redirects.csv` send every old `.php` address to its new page with a 301 redirect so the old pages pass their ranking on. `.htaccess` works on Apache. On another server, copy the rules from `redirects.csv`.

## Images

Photos still load from the current doctoryounger.com while the clinic gathers full-size files. Once they arrive, put them in `static/img/` and change the paths in the YAML files. The homepage photo comes from Unsplash and should be replaced with a photo of the clinic.

## Backend later

The YAML files are shaped like database records. Two routes are open:

1. Decap CMS gives staff an editing screen in the browser that saves to the YAML files on GitHub, and the site rebuilds itself. No server is needed.
2. A Flask app with SQLite and an admin panel, using the same templates, if the clinic wants member accounts or live booking slots.
