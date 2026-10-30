#!/usr/bin/env python3
"""Build the single-file Free Every-Day Software Directory.

Reads apps.json, validates it, and embeds it into template.html to produce
a fully self-contained, offline index.html (no network, no dependencies).

Usage:
    python3 build.py            # build index.html from apps.json + template.html
    python3 build.py --check    # validate only, do not write
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APPS_JSON = HERE / "apps.json"
TEMPLATE = HERE / "template.html"
OUTPUT = HERE / "index.html"

REQUIRED_FIELDS = {
    "id": str,
    "name": str,
    "category": str,
    "tagline": str,
    "whatItDoes": str,
    "trulyFree": str,
    "installDifficulty": str,
    "installSteps": str,
    "honestLimits": str,
    "verifiedFreeOn": str,
    "recheckDate": str,
    "license": str,
    "website": str,
    "platforms": list,
}

VALID_TRULY_FREE = ("yes",)
VALID_DIFFICULTY = ("easy", "medium", "hard")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(apps):
    errors = []
    if not isinstance(apps, list) or not apps:
        return ["apps.json must be a non-empty array of app objects."]

    seen_ids = set()
    schema_ok = all(
        isinstance(a, dict) for a in apps
    ) if isinstance(apps, list) else False
    if not schema_ok:
        return ["apps.json must be a non-empty array of app objects."]

    for i, app in enumerate(apps):
        label = f"app[{i}] ({app.get('name', 'unnamed')})"
        for field, typ in REQUIRED_FIELDS.items():
            if field not in app:
                errors.append(f"{label}: missing required field '{field}'.")
            elif not isinstance(app[field], typ):
                errors.append(
                    f"{label}: field '{field}' must be {typ.__name__}, "
                    f"got {type(app[field]).__name__}."
                )
        if app.get("trulyFree") not in VALID_TRULY_FREE:
            errors.append(
                f"{label}: trulyFree must be one of {VALID_TRULY_FREE}, "
                f"got {app.get('trulyFree')!r}."
            )
        if app.get("installDifficulty") not in VALID_DIFFICULTY:
            errors.append(
                f"{label}: installDifficulty must be one of {VALID_DIFFICULTY}, "
                f"got {app.get('installDifficulty')!r}."
            )
        for date_field in ("verifiedFreeOn", "recheckDate"):
            value = app.get(date_field, "")
            if not DATE_RE.match(value) or not _is_date(value):
                errors.append(
                    f"{label}: {date_field} must be a valid YYYY-MM-DD date, got {value!r}."
                )
        if DATE_RE.match(app.get("verifiedFreeOn", "")) and DATE_RE.match(
            app.get("recheckDate", "")
        ):
            if app["recheckDate"] <= app["verifiedFreeOn"]:
                errors.append(
                    f"{label}: recheckDate must be after verifiedFreeOn."
                )
        website = app.get("website", "")
        if not website.startswith("https://"):
            errors.append(f"{label}: website must be an https:// URL, got {website!r}.")
        app_id = app.get("id", "")
        if re.match(r"^[a-z0-9-]+$", app_id) is None:
            errors.append(
                f"{label}: id must be lowercase letters, digits, and dashes, got {app_id!r}."
            )
        if app_id in seen_ids:
            errors.append(f"{label}: duplicate id '{app_id}'.")
        seen_ids.add(app_id)
        for text_field in ("tagline", "whatItDoes", "honestLimits", "installSteps"):
            value = app.get(text_field, "")
            if isinstance(value, str) and len(value.strip()) < 20:
                errors.append(f"{label}: {text_field} looks too short to be useful.")
    return errors


def _is_date(value):
    try:
        from datetime import date

        year, month, day = (int(p) for p in value.split("-"))
        date(year, month, day)
        return True
    except ValueError:
        return False


def escape_for_script_tag(text):
    """Keep '[' characters intact but neutralize '</script' and JSON string hazards."""
    # Split on '<', reattach with safe encoding only for '</' sequences.
    # Escapes '<' in '</...' so the script tag cannot be terminated by app data.
    out = []
    idx = 0
    for match in re.finditer(r"</", text):
        out.append(text[idx:match.start()])
        out.append("<\\/")
        idx = match.end()
    out.append(text[idx:])
    return "".join(out)


def build():
    apps_raw = APPS_JSON.read_text(encoding="utf-8")
    apps = json.loads(apps_raw)
    errors = validate(apps)
    if errors:
        for e in errors:
            print("VALIDATION ERROR:", e, file=sys.stderr)
        sys.exit(1)

    template = TEMPLATE.read_text(encoding="utf-8")
    if "{{APPS_JSON}}" not in template:
        print("BUILD ERROR: template.html is missing the {{APPS_JSON}} placeholder.",
              file=sys.stderr)
        sys.exit(1)

    compact = json.dumps(apps, ensure_ascii=False, separators=(",", ":"))
    html = template.replace("{{APPS_JSON}}", escape_for_script_tag(compact))
    OUTPUT.write_text(html, encoding="utf-8")
    return apps


def main():
    if "--check" in sys.argv[1:]:
        apps = json.loads(APPS_JSON.read_text(encoding="utf-8"))
        errors = validate(apps)
        if errors:
            for e in errors:
                print("VALIDATION ERROR:", e, file=sys.stderr)
            sys.exit(1)
        print(f"OK: {len(apps)} apps validated (check-only, nothing written).")
        return
    apps = build()
    print(f"OK: built {OUTPUT.name} with {len(apps)} apps.")


if __name__ == "__main__":
    main()
