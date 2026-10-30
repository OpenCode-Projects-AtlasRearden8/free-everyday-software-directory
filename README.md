# Free Every-Day Software Directory

A static, single-file HTML directory of **genuinely free software** every household deserves —
free software, not just "free tools." LibreOffice, GIMP, Audacity, VLC, Syncthing-style file
sync, compression tools, a plain-English PDF reader, password management, and more — each with
what it does, whether it is *truly* free, install difficulty and safe first steps, honest
limits, and dates for when its free license was last verified and when to recheck.

Written plain-English, step by step, never condescending — like a friend would.

**An open project by Asdale Dynamics, LLC.** MIT Licensed — see [LICENSE](LICENSE).

## The one-file you hand to people: `index.html`

`index.html` is fully self-contained — styles, data, and JavaScript are all embedded.
Double-click it or email it to someone; it works offline, on any browser, with no internet,
no accounts, no tracking, and **no affiliate links** — nothing to buy, no upsells.

## Project layout

| File | What it is |
|---|---|
| `apps.json` | The data: one object per program (name, category, what it does, truly free, install difficulty, install steps, honest limits, verified-free date, recheck date...). |
| `template.html` | The page template with a `{{APPS_JSON}}` placeholder. Edit UI/wording here, not in `index.html`. |
| `build.py` | Validates `apps.json` and embeds it into the template to produce `index.html`. |
| `index.html` | **Generated.** The offline single file people receive. Do not hand-edit; regenerate. |
| `test.py` | Test suite: JSON schema, build integrity, no-affiliate checks, and an actual page render (via Node + a tiny DOM shim). |

## Day-to-day use

```bash
# build the single-file page (index.html) from the data + template
python3 build.py

# validate the data without writing anything
python3 build.py --check

# run every test
python3 test.py
```

Requirements: Python 3.9+ (any OS). The render tests additionally need Node.js if present;
without Node, test.py still runs the JSON and build checks and reports the skip accordingly.

## How to add or update a program

1. Add an object to `apps.json` with **all** required fields:

   `id` (lowercase-with-dashes, unique), `name`, `category` (see below), `tagline`,
   `whatItDoes`, `trulyFree` (`"yes"`), `installDifficulty` (`easy` | `medium` | `hard`),
   `installSteps` (numbered plain sentences), `honestLimits`, `verifiedFreeOn` (YYYY-MM-DD),
   `recheckDate` (YYYY-MM-DD, after the verified date), `license` (SPDX-style), `website`
   (**https:// official site only**), `platforms` (array), `sizeEstimate`.

   Valid categories: `office`, `photos`, `audio`, `media`, `files`, `documents`, `security`
   (declared in `build.py` `REQUIRED_FIELDS`/category logic; the page groups unknown ones
   under their raw key, so extend deliberately).

2. Run `python3 test.py`. Fix anything it flags.

3. Run `python3 build.py` and open `index.html` in your browser to eyeball the new card.

### Six-month maintenance rhythm

Every entry carries `verifiedFreeOn` and `recheckDate`. **Every six months**:

```bash
python3 build.py --check   # any stale-date or schema problem appears here?
```

Then, for each app whose `recheckDate` has passed:

- Visit the **official website** and confirm the software still ships under a free
  (OSI-approved or equivalent) license and that the URL is still good.
- Look for any license change or "new monetization" (ads, data collection, account walls).
- Update `verifiedFreeOn` to today and set `recheckDate` to today + 6 months.
- Re-check `honestLimits` — does it still say the true thing?

Search the repo for `recheckDate` values older than six months; that is exactly what the
fields are designed to surface.

### House rules

- **No affiliate links, no referral tags (`ref=`, `utm_`, `tag=`), no promo codes**, ever.
  `test.py` checks the generated file for pulled URLs. Keep all `website` values as
  official-homepage HTTPS URLs.
- **Never link a download mirror**; always the official site. A big part of staying safe
  is learning to type the real address ourselves.
- Plain English: if a sentence sounds like a manual for experts, rewrite it.
- No secrets, API keys, or personal data in any file — this is a public-friendly artifact.

## Verification

`test.py` covers three layers:

1. **Data** — `apps.json` parses, every required field is present and correctly typed,
   dates are real and ordered, IDs unique, anchored apps present (LibreOffice, GIMP,
   Audacity, VLC, syncthing, Sumatra PDF...), no affiliate-shaped fields.
2. **Build** — `build.py` runs clean; `index.html` is self-contained (no external scripts
   or stylesheets), embeds the exact current `apps.json`, leaves no placeholders, and the
   anti-injection escaping neutralizes `</script>`.
3. **Render** — the page's JavaScript actually runs (Node + minimal DOM shim): all cards
   render, category filtering narrows, search matches, nonsense search shows the
   friendly empty state, and cards carry their install steps, honest limits, and
   verified-free dates. The un-built template degrades to a friendly "run build.py"
   message instead of crashing.

## License

MIT — Copyright (c) 2026 Asdale Dynamics, LLC. See [LICENSE](LICENSE).
