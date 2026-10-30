# STATUS.md — Free Every-Day Software Directory

_Last updated: 2026-10-30. Maintained by Asdale Dynamics, LLC._

## What was built

A static, offline, single-file HTML directory of genuinely free (not just
free-of-charge-looking) software every household deserves, in Asdale Dynamics LLC's
plain-English, never-condescending house style:

- **13 data fields per app**, kept in `apps.json`: id, name, category, tagline,
  what it does, **truly free yes/no**, install difficulty, numbered safe first
  steps, honest limits, license (SPDX-style), official HTTPS website, platforms,
  size estimate, plus **verified-free-on and recheck dates** for the six-month
  maintenance rhythm.
- **12 apps at launch**: LibreOffice, GIMP, Audacity, VLC, Syncthing (file sync),
  7-Zip, Keka/The Unarchiver (the macOS compression pair), Sumatra PDF
  (plain-English PDF reader), KeePassXC, Inkscape, Darktable, Thunderbird.
- **index.html** — a fully self-generated, self-contained single file
  (embedded CSS + JSON + JS; zero network requests; no affiliate links, no
  tracking, no external image or font assets). Works by double-clicking from a
  USB stick or email attachment.
- **Category filter chips + live text search** with a friendly empty state;
  cards surface "Truly free" badges, install difficulty, expandable "Safe first
  steps" and "Honest limits" sections, and verified/recheck dates.
- **build.py** — validates `apps.json` (schema, date logic, unique ids, HTTPS-only
  official websites, no affiliate-shaped fields) and embeds it into
  `template.html` → `index.html`, neutralizing `</script>` injection from data.
- **test.py** — three-layer test suite (data / build / runtime render).
- **README.md** — maintenance guide including the six-month recheck rhythm and
  house rules; **LICENSE** — MIT, Copyright (c) 2026 Asdale Dynamics, LLC.

## How to run it

Open `index.html` in any browser — nothing else needed. To develop:

```bash
python3 build.py      # regenerate index.html from apps.json + template.html
python3 build.py --check
python3 test.py       # full validation, includes a real JS render test
```

Optional preview over localhost: `python3 -m http.server`, then visit
http://localhost:8000. (Optional — the file also just opens directly.)

## Verification results (final run: 2026-10-30)

- `python3 build.py` → `OK: built index.html with 12 apps.`
- `python3 build.py --check` → `OK: 12 apps validated (check-only...)`
- `python3 test.py` → **20 passed, 0 failed**, covering:
  - JSON parses; ≥10 entries; full schema/type/date validation; anchored apps
    (LibreOffice, GIMP, Audacity, VLC, syncthing, Sumatra PDF) present.
  - Build clean; `index.html` self-contained (no external script/style/img);
    embedded JSON byte-equal to `apps.json`; no leftover placeholder.
  - No affiliate-shaped URLs (`affiliate`, `ref=`, `utm_`, `tag=`) anywhere.
  - Runtime render (Node + DOM shim): all 12 cards render; search "vlc"/
    "passwords" narrows correctly; nonsense search shows empty-state message;
    category "files" narrows and badges carry; "All" restores everything;
    cards include install steps, honest limits, and verified-free dates.
  - Fail-path: opening the raw template shows a friendly "run build.py"
    message instead of crashing (two real crash bugs were found and fixed by
    these tests during development).

## Known gaps / future ideas

- **Render tests use a minimal DOM shim**, not a full browser: real-browser
  visual/layout behavior (responsive grid widths, details toggling animation)
  is verified by hand with `python3 -m http.server` + a real browser, not
  automatically. A Playwright/puppeteer pass could tighten this later.
- `trulyFree` only supports `"yes"` today; if a future honest entry is
  "mostly (with caveats)", add the label to the validator, page badge, and CSS
  in one small change.
- The Keka entry notes its App Store variant costs a few dollars by Apple's
  rules — the directory points at the free keka.io download; keep an eye on it
  at recheck time.
- Two apps are Windows-only by design (7-Zip, Sumatra PDF); macOS/Linux
  equivalents are noted inside those cards. A per-platform filter chip could
  be added if the directory grows much larger.
- The iOS story for Syncthing is essentially nonexistent (sandboxing); the
  card says "Android" only, which is honest but worth rechecking twice a year.
- No automated license-text verification against OSI’s database; recheck dates
  schedule the human visit instead.
