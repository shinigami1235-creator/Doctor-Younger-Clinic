# Doctor Younger Clinic website rebuild

This is the plan for rebuilding doctoryounger.com, which was built in 2017. Thai is the main language and every page also gets an English version. The clinic's own Thai text stays as written, and only the design, layout and code change. The crawl below was done on 20 October 2026.

## Decisions (20 October 2026)

- Design direction: Quiet luxury, with the skin layer diagram on laser and RF pages.
- 21 October 2026: people who know the doctor describe her brand as simple yet timeless elegance, so the design was pared back. Soft white page, near-black text, bronze only for thin lines, square buttons, labels in normal case. The intro splash, gold dust, rotating badge, marquee, count-up numbers, custom cursor, magnetic buttons, tilt and word-by-word headings were removed. Motion is now one soft fade per block, plus the skin diagram, the treatment finder and a slower product showroom.
- Logo: the Instagram serif wordmark. A vector file is still needed from the clinic.
- Promotion and Q&A are empty and hidden. Products, Reviews, News and Tips load their lists by script on the old site, which the first crawl missed; they are now imported in full (9 products, 21 reviews, 3 news posts, 85 Tips articles).
- Thai text is kept as written except misspelled English words, which are corrected.

## 1. What the current site has

### Pages

| Page | State |
|---|---|
| Home (index.php) | Reviews strip, 8 feature tiles, branch phones, 3 trust badges |
| About us (about-us.php) | Serves the homepage again since it has no content of its own |
| Promotion | Empty |
| Doctor's Profile | 7 doctors, each with a detail page |
| Beauty's Talk | 2 presenter interviews (คุณไก่ สุปราณี เจริญผล, คุณหยาดทิพย์ ราชปาล) |
| Services | 6 categories, 30 treatments, each with a detail page |
| Products | 9 products, each with size, price and how to use (loaded by script) |
| Q&A | Empty |
| Review list | 23 entries, 21 real reviews (loaded by script) |
| News & Event | 3 posts and 1 test post (loaded by script) |
| Tips | 85 articles, every one credited to another publisher such as Sanook or Kapook (loaded by script) |
| Review detail | 3 reviews (Rattanaporn, ต้อม ภาวนา, Apple) |
| Contact us | Both branches with address, phones and a map image |
| Booking | Form: name, phone, email, branch, service type |
| Register | Member form with a 20% discount offer |
| Privacy policy | Full PDPA text |

### Services (6 categories, 30 treatments)

- **LASER & RF:** CO2 Laser, Fractional Laser, Aramis Laser, Pigment Laser, Active Bright, Ultra Deep Lifting, Aura Bright, Monopolar RF
- **FACIAL DESIGN:** Vital Lift, HA, V-Touch, Diamond Toxin
- **FACIAL TREATMENT:** Acne Clear Light, Phonophoresis, Synergica, Blue Mate, Dermalift, Grey Mate, Cry-O Lift, Dermalift & Mask, Ruby Mate, Oxy Plus, Iontophoresis, New A Peel, Peeling Treatment
- **BODY TREATMENT:** Endermologie
- **HAIR REMOVAL:** TKS Laser
- **OTHERS:** Vita Bright

Each detail page follows the same pattern: headline, one-line benefit, results list, how it works, when results show, who it suits, and a closing line with the phone and LINE ID. Only Acne Clear Light lists a price (800 baht per session, 7,200 baht for 10).

### Doctors

พญ.วิไล ธนสารอักษร, นพ.นพดล อมรภิญโญเกียรติ (หมอบอย), พญ.พัชราภรณ์ วชิรนันทศิลป์ (หมอบี), พญ.มานิกา นภารัตน์ (หมอปาล์ม), พญ.ณัฐวรรณ ลิ้มเจริญวิริยกุล (หมอมะปราง), พญ.ปุณฑริกา อภินรเศรษฐ์ (หมอพิ้งค์), พญ.อุไรรักษ์ ทรัพย์สาร (หมอเตย). Every profile has education, training and a weekly schedule for each branch.

### Branches

| | Sukhumvit 23 | Thanya Park Srinakarin |
|---|---|---|
| Address | อาคารจัสมินซิตี้ ชั้น 18 ซอยประสานมิตร (สุขุมวิท 23) ถ.สุขุมวิท แขวงคลองเตยเหนือ เขตวัฒนา กรุงเทพฯ 10110 | ธัญญาพาร์ค ศรีนครินทร์ อาคาร C ชั้น 2 ถนนศรีนครินทร์ แขวงสวนหลวง เขตสวนหลวง กรุงเทพฯ 10250 |
| Phone on contact page | 02-665-7057-8, 081-4245008 | 02-108-6168-9, 081-2058322 |
| Hours on site | 10.00 to 20.00 daily | 10.00 to 20.00 daily |
| Google listing | None | Exists with no reviews, hours 10:30 to 19:30, phone 02 108 6168 |

The call centre number 02-261-3697-8 sits in the header and at the end of every service page. Instagram lists 02-261-3697-8 as the Sukhumvit 23 number.

### Brand assets

- Logo file: images/shared/logo.png, the 2017 mark with "Always Younger" script beside a gold leaf and "Doctor YOUNGER" wordmark.
- Instagram uses a newer mark: "DOCTOR YOUNGER" in a serif wordmark on a bronze circle, with a campaign line "LOOK YOUNGER / FEEL YOUNGER / BE YOUNGER" over a team photo of the doctors in white coats.
- Colours in the 2017 CSS: bronze gold #B69E59 (used 50 times), brighter gold #D1AB2B, grey #58595B, light grey #CED0D4.
- Fonts in the 2017 CSS: Century Gothic, RSU, Prompt Light.

### Social accounts

- Instagram @doctor_younger: 4,758 followers, 1,386 posts, active.
- Facebook DoctorYoungerFan: shows "This content isn't available at the moment". The site, Instagram bio and every service page link to it.
- YouTube @doctoryounger4713: channel description says the clinic's serum won a Cosmopolitan award in 2015.
- LINE: @DoctorYounger.

## 2. Problems found

### Code and SEO

1. Every page has the same title, "Doctor Younger | Always Younger", and the same meta description.
2. The menu uses `onclick="window.location.href=..."` in place of links, so Google cannot follow the menu to reach the inner pages.
3. Any address that does not exist returns the homepage with status 200. robots.txt, sitemap.xml, /en/ and /demo2017/ all return the homepage, so the site has no robots file and no sitemap.
4. A copy of the site lives in /demo2017/ and is reachable, which gives Google duplicate pages.
5. No `lang` attribute, no canonical tags, no hreflang, no structured data.
6. Phone numbers and branch names are marked as `<h1>`, so the homepage has seven h1 tags and none of them say what the clinic does.
7. Images have no alt text.
8. jQuery is loaded twice (jquery.js and jquery-1.9.1.min.js) with bxSlider and Fancybox from 2013.
9. Footer reads "© 2017 Doctoryounger".

### Content

1. Sukhumvit 23 has three phone numbers in use (02-665-7057-8, 02-261-3697-8, 081-4245008).
2. The register form still lists เทอมินอล 21 as a branch.
3. Google Maps has a separate "Doctor Younger Clinic" walk-in clinic at 309/26-27 Phatthanakan Road, Prawet, phone 02 722 0708.
4. Promotion and Q&A are empty.
5. Each Beauty's Talk interview repeats the first question twice with slightly different answers.
6. English inside the Thai pages has misspellings: RECCOMMEND, Paris-Frace, Dermatoloyg, Anerican Boavd, Cutaneans, KERAROSIS, LENTIGENES.

## 3. Why Google shows J Young for Sukhumvit 23

The Sukhumvit 23 branch has no Google Business Profile. A search for "Doctor Younger Clinic สุขุมวิท 23" fills the gap with เจยัง คลินิก (สาขา อโศก), which has 143 reviews at 4.9 and sits close by in the Times Square building (246, room 321, 3rd floor). Its panel links to jyounggroup.com and its phone is 02 116 4251. Google matches "Younger" to "J YOUNG" and the location to Asok, and with no Doctor Younger listing to compete, J Young wins.

The website alone cannot fix this since the knowledge panel comes from Google Business Profile. The fix has two parts.

### Off the site (the clinic does these)

1. Create and verify a Google Business Profile for "Doctor Younger Clinic สาขาสุขุมวิท 23" at Jasmine City, 18th floor, with the pin on the Jasmine City building. Category: Skin care clinic, with Dermatologist as a second category.
2. Pick one phone number per branch and use it everywhere: website, both Google profiles, LINE, Instagram, Wongnai, GoWabi, ThaiClinics.
3. Correct the Thanya Park profile: hours to match the site, website link to the branch page, photos of the branch.
4. Check the Prawet listing. If it is an old Doctor Younger branch, mark it permanently closed. If it is another clinic, leave it.
5. Ask regular patients at each branch for Google reviews once the profiles exist.

### On the site (we build these)

1. One page per branch: /th/branches/sukhumvit-23/ and /th/branches/thanya-park-srinakarin/, each with the full address, the one chosen phone, hours, a live map embed with the exact pin, how to get there (BTS Asok, MRT Sukhumvit for Sukhumvit 23), and the doctors on duty there.
2. Structured data on each branch page: `MedicalClinic` with its own `@id`, name including the branch, address, `geo` coordinates, `openingHoursSpecification`, `telephone`, `hasMap`, and `parentOrganization` pointing at one `Organization` for Doctor Younger.
3. The branch name, address and phone written the same way in the footer, the branch page, the schema and the Google profile.
4. The building name "Jasmine City" / "จัสมินซิตี้" in titles and headings, which J Young does not have.

## 4. Design direction

The goal is a premium clinic that still reads as a doctor-led dermatology practice. Three directions to choose from:

**A. Quiet luxury (recommended).** Warm ivory background, deep espresso text, the clinic's own bronze gold #B69E59 for lines and accents. Serif display type matching the Instagram wordmark. Large photos of the clinic and doctors with generous space around them. Motion is slow: fades, gold hairlines drawing in, images easing into place.

**B. Clinical precision.** White and champagne with a cooler grey. Each laser page carries a diagram of skin layers showing the depth the device reaches, taken from the clinic's own text (CO2 10,600 nm, Aramis 1540 nm at 200 to 500 µm, Ultra Deep Lifting to the SMAS layer). Feels like a dermatology institute.

**C. Editorial.** Laid out like a beauty magazine. Beauty's Talk interviews become feature spreads and services read like articles.

The skin layer diagram from B works inside A, which is the combination I would build.

### Type

| Use | Thai | English |
|---|---|---|
| Headings | Noto Serif Thai or Trirong | Cormorant Garamond |
| Body | Prompt Light (already in use) or IBM Plex Sans Thai | Jost, the closest free match to Century Gothic |

### Logo

The 2017 logo and the Instagram wordmark differ. The site needs the current one as a vector file (SVG, AI or PDF) from the clinic. Until then the build uses logo.png from the current site.

### Motion

Motion follows the simple, timeless direction set on 21 October 2026.

- Each block fades in once as it scrolls into view. The hero lines fade in one after another on load, which is the only staged moment.
- The skin layer diagram draws the beam down to the depth of each device.
- The treatment finder slides cards to their new places when a concern is picked.
- The product showroom turns on its own every 8 seconds and stops while someone is using it.
- Hovers change a colour or a border, nothing moves.
- Every animation switches off when the visitor's device asks for reduced motion.

## 5. Features to add

1. **Sticky contact bar on mobile:** Call, LINE, Book. Most visitors arrive on a phone.
2. **Branch selector:** remembered between visits, and it changes the phone, map and doctor schedule shown across the site.
3. **Doctor on duty today:** built from the schedules already on each profile. Pick a branch and a day to see who is in.
4. **Treatment finder by concern:** acne, melasma and spots, wrinkles, sagging, pores, scars, unwanted hair, body contour. Each concern lists the clinic's existing treatments that mention it. The concern names are new labels and need the clinic's OK.
5. **Skin layer diagram** on each laser and RF page.
6. **Booking that works:** the form sends to the clinic by email and LINE now, and to the backend later. LINE stays the main channel since the clinic already runs everything through @DoctorYounger.
7. **Instagram feed** on the homepage, which keeps the site current without anyone editing it.
8. **Language switch** that stays on the same page.
9. **Hide empty sections** (Promotion, Q&A, Tips, News, Products) until they have content. Empty pages hurt search ranking.
10. **PDPA cookie banner** rebuilt so Google Analytics only loads after consent. The existing GA4 tag G-0PRF2YXPYW is kept.

## 6. Site map and URLs

Thai sits at the root and English under /en/.

```
/                                   หน้าแรก
/about/                             เกี่ยวกับเรา
/services/                          บริการ (6 categories)
/services/laser-rf/                 category page
/services/laser-rf/ultra-deep-lifting/
/doctors/                           แพทย์
/doctors/wilai-thanasarnaksorn/
/branches/sukhumvit-23/
/branches/thanya-park-srinakarin/
/beauty-talk/
/beauty-talk/supranee-charoenphol/
/reviews/
/booking/
/privacy-policy/
/en/...                             same tree in English
```

Every old .php address gets a 301 redirect to its new address, kept in `redirects.csv`, so the rankings the old pages have are carried over.

## 7. English version

- Thai text is kept exactly as the clinic wrote it.
- English is translated from the Thai, with grammar corrected and the meaning and tone kept. Promotional phrasing stays promotional. Doctor nicknames are kept (Dr. Boy, Dr. Bee).
- Treatment and device names stay in English as the clinic writes them.
- Each English page is marked as a translation of its Thai page with hreflang, so Google shows the right one to each visitor.

## 8. Code

Python, written so another programmer can pick it up without asking.

```
Doctor Younger Clinic/
  content/
    th/            one YAML file per page, the clinic's own text
    en/            the same files in English
  data/
    branches.yaml  name, address, phone, hours, coordinates per branch
    doctors.yaml   names, education, schedule per branch
    services.yaml  category, slug, images per treatment
  templates/       Jinja2 HTML templates
  static/          CSS, JS, fonts, images
  build.py         turns content + templates into the finished site
  dist/            the finished site, the only folder that goes online
  redirects.csv    old .php address to new address
  README.md        how to edit text, add a doctor, add a service, build
```

- `build.py` writes the pages, sitemap.xml, robots.txt, hreflang tags, structured data and an .htaccess with the 301 redirects.
- Text lives in YAML files, never inside the HTML, so changing a doctor's schedule means editing one line in `doctors.yaml`.
- Images are converted to WebP at build time and served at the size the screen needs.
- No jQuery and no framework. Plain HTML, CSS and a small JS file.
- The GitHub Pages preview is built with `noindex` so it never competes with doctoryounger.com in Google. The production build turns `noindex` off.

### Backend later

The content files are already shaped like database records, so a backend reads them without a rewrite. Two routes:

1. **Admin on top of the static site.** Decap CMS gives staff an edit screen in the browser, saves to GitHub, and the site rebuilds itself. No server to pay for.
2. **Python server.** Flask with SQLite and an admin panel, using the same templates. Needed if the clinic wants member accounts, live booking slots or a promotions system.

## 9. Thai advertising rules

A clinic website counts as advertising a medical facility under the Medical Facilities Act and needs approval from สบส. before it is published. Before-and-after photos, patient reviews, presenter endorsements and discount offers are the areas most often restricted. The clinic should confirm which of the current content (the 3 reviews, the 2 presenter interviews, the 20% register discount) its current approval covers before the new site goes live. The footer can show the clinic's facility licence and advertising approval numbers once the clinic provides them.

## 10. Needed from the clinic

- Logo as a vector file, and which logo is current
- The one phone number to use for each branch
- Opening hours for each branch
- Photos and video of both branches and the doctors, at full size
- Current Facebook page address
- Facility licence numbers and the advertising approval number
- Whether the Prawet listing is theirs
- Whether the doctor list and schedules are current
- Products to list, if any

## 11. Build order

1. Save every page's text and images from the current site into the content folder.
2. Build the homepage, one service page and one branch page in the chosen direction for review.
3. Build the rest of the Thai site.
4. Translate and build the English site.
5. Schema, sitemap, redirects, speed and accessibility checks.
6. Publish the preview on GitHub Pages.
