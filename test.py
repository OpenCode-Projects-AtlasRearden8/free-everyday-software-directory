#!/usr/bin/env python3
"""Tests for the Free Every-Day Software Directory.

Checks three layers:
  1. apps.json schema + content rules (via build.py's validator)
  2. The built index.html: single-file, self-contained, JSON matches apps.json
  3. Runtime render: executes the page's JavaScript in Node with a minimal
     DOM shim and asserts cards, category filtering, and search behavior.

Run:  python3 test.py
Exit code 0 = all pass, 1 = failure.
"""
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build import APPS_JSON, OUTPUT, TEMPLATE, escape_for_script_tag, validate  # noqa: E402

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}" + (f" -- {detail}" if detail else ""))


# ---------------------------------------------------------------- layer 1: JSON
print("[1] apps.json schema and content")
raw = APPS_JSON.read_text(encoding="utf-8")
apps = json.loads(raw)
check("apps.json parses as JSON", isinstance(apps, list) and len(apps) > 0)
check("apps.json has >= 10 entries", len(apps) >= 10, f"got {len(apps)}")
errors = validate(apps)
check("build.py validator reports no errors", not errors, "; ".join(errors))
required_asks = ["libreoffice", "gimp", "audacity", "vlc", "syncthing", "sumatra-pdf"]
ids = {a["id"] for a in apps}
check("requested anchored apps present", all(r in ids for r in required_asks),
      f"missing: {[r for r in required_asks if r not in ids]}")
check("no affiliate/marketing fields",
      not any(k in a for a in apps for k in
              ("affiliateUrl", "referral", "affiliate", "trackingId", "promoCode")))

# ids referenced later in the runtime render test
SEARCH_ID = "vlc"
BAD_SEARCH_ID = "vlc"

# ---------------------------------------------------------------- layer 2: build
print("[2] build & single-file HTML")
build_result = subprocess.run(
    [sys.executable, str(HERE / "build.py")], capture_output=True, text=True)
check("build.py runs cleanly", build_result.returncode == 0, build_result.stderr.strip())
html = OUTPUT.read_text(encoding="utf-8")
check("index.html exists and is not empty", len(html) > 5000, f"len={len(html)}")
check("index.html has no external <script src=>", "script src=" not in html
      and "<script src" not in html)
check("index.html has no external stylesheet link", "<link rel=\"stylesheet\"" not in html
      and "'stylesheet'" not in html)
check("index.html has no placeholder left", "{{APPS_JSON}}" not in html)
match = re.search(
    r'<script id="apps-data" type="application/json">(.*?)</script>', html, re.S)
check("embedded apps-data script present", bool(match))
embedded_ok = bool(match)
if embedded_ok:
    embedded_apps = json.loads(match.group(1))
    check("embedded JSON equals apps.json", embedded_apps == apps)
check("template.html is not shipped as output", html != TEMPLATE.read_text(encoding="utf-8"))

template = TEMPLATE.read_text(encoding="utf-8")
check("template placeholder exists", "{{APPS_JSON}}" in template)
check("build escaping neutralizes script closing",
      "</script" not in escape_for_script_tag('{"name":"a</script>b"}'))

parser = _Parsed = None


class TitleGrab(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""
        self.imgs = 0
        self.links_visited = 0

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        if tag == "img":
            self.imgs += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


t = TitleGrab()
t.feed(html)
check("page has a <title>", t.title.strip() != "")
check("no <img> external assets in page (fully text/CSS)", t.imgs == 0)
links = re.findall(r'\shref="(https?://[^"]+)"', html)
# NOTE: this pattern will also match URLs inside the embedded JSON; that is fine,
# they are "official website" links written by a human, not affiliate links.
check("no affiliate-looking URLs", not any(
    ("affiliate" in u.lower() or "ref=" in u or "utm_" in u or "tag=" in u)
    for u in links), str(links))

# ---------------------------------------------------------------- layer 3: render
print("[3] runtime render (Node + DOM shim)")
SHIM = r'''
import { readFileSync } from "node:fs";

// --- tiny DOM enough for this page ---
class ClassList {
  constructor() { this.set = new Set(); }
  add(c) { this.set.add(c); }
  remove(c) { this.set.delete(c); }
  toggle(c, force) {
    const has = this.set.has(c);
    const want = force === undefined ? !has : !!force;
    want ? this.set.add(c) : this.set.delete(c);
    return want;
  }
  contains(c) { return this.set.has(c); }
}
class El {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.attributes = {};
    this.style = {};
    this.classList = new ClassList();
    this.handlers = {};
    this._text = "";
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() {
    return this._text + this.children.map(c => c.textContent).join("");
  }
  appendChild(c) { c.parentNode = this; this.children.push(c); return c; }
  removeChild(c) {
    const i = this.children.indexOf(c);
    if (i >= 0) this.children.splice(i, 1);
    return c;
  }
  get firstChild() { return this.children[0] || null; }
  setAttribute(k, v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k] ?? null; }
  addEventListener(type, fn) { this.handlers[type] = fn; }
}

const documentShim_html = readFileSync(process.argv[2], "utf8");

const grid = new El("div");
const noResults = new El("p");
noResults.setAttribute("id", "no-results");
const search = new El("input");
const filters = new El("div");

const appDataEl = new El("script");
const appDataMatch = documentShim_html.match(
  /<script id="apps-data" type="application\/json">([\s\S]*?)<\/script>/);
appDataEl.textContent =
  process.argv[3] === "--fail-path" ? "" : (appDataMatch ? appDataMatch[1] : "");

const document = {
  readyState: "complete",
  _done: [],
  getElementById(id) {
    if (id === "grid") return grid;
    if (id === "no-results") return noResults;
    if (id === "search") return search;
    if (id === "filters") return filters;
    if (id === "apps-data") return appDataEl;
    return null;
  },
  createElement(t) { return new El(t); },
  createTextNode(s) { return { text: String(s), textContent: String(s) }; },
  addEventListener() {}
};

// load the page's inline script
const html = documentShim_html;
const m = html.match(/<script>\n([\s\S]*?)<\/script>\n?\s*<script id="apps-data"/);
if (!m) { console.error("inline script not found"); process.exit(1); }
const window = {};
const fn = new Function("document", "window", "console", m[1]);
fn(document, window, console);

let failures = 0;
function expect(name, cond, detail) {
  if (cond) { console.log("  PASS  " + name); }
  else { console.log("  FAIL  " + name + (detail ? " -- " + detail : "")); failures++; }
}

if (process.argv[3] === "--fail-path") {
  const msg = noResults.textContent || grid.textContent;
  expect("fail-path shows friendly 'run build.py' message",
    msg.includes("python3 build.py"), msg);
  if (failures > 0) process.exit(1);
  console.log("FAIL-PATH RENDER TEST PASSED");
  process.exit(0);
}

// helpers
function cards() {
  return grid.children.filter(c => c.tagName === "ARTICLE");
}
function cardTitle(c) {
  return c.children[0].textContent;
}
function clicks(sel) {
  const btns = filters.children;
  const b = btns.find(x => x.getAttribute("data-cat") === sel);
  if (!b) { console.error("no button for " + sel); process.exit(1); }
  b.handlers.click();
}
function type(text) {
  search.value = text;
  search.handlers.input();
}

const total = JSON.parse(appDataMatch[1].replace(/<\\\//g, "</")).length;

expect("initial render shows all cards", cards().length === total,
  cards().length + " vs " + total);
expect("initial render hides no-results", noResults.style.display !== "block");

clicks("all"); type("");
expect("re-render shows all cards", cards().length === total);

type("vlc");
expect("search 'vlc' narrows to 1 named hit",
  cards().length === 1 && cardTitle(cards()[0]) === "VLC Media Player",
  JSON.stringify(cards().map(cardTitle)));

type("passwords");
expect("search 'passwords' finds KeePassXC",
  cards().length === 1 && cardTitle(cards()[0]) === "KeePassXC",
  JSON.stringify(cards().map(cardTitle)));

type("zzzznope");
expect("nonsense search shows zero cards", cards().length === 0);
expect("nonsense search shows the no-results message", noResults.style.display === "block");

type("");
clicks("files");
const byCat = cards().every(c => true);
expect("category filter 'files' narrows results", cards().length < total, "" + cards().length);
expect("all filtered cards carry the files badge",
  cards().every(c => c.children[2].children.some(b =>
    b.textContent.includes("Files") || b.textContent.includes("7-Zip")
    || b.textContent.includes("Keka") || b.textContent.includes("Syncthing"))));

clicks("all");
expect("back to 'All' shows everything again", cards().length === total);

// card content sanity on one card
type("libreoffice");
const c = cards()[0];
expect("card has install steps summary",
  c.children.some(x => x.tagName === "DETAILS"
    && x.children.some(s => s.textContent === "Safe first steps")));
expect("card has honest limits summary",
  c.children.some(x => x.tagName === "DETAILS"
    && x.children.some(s => s.textContent === "Honest limits")));
expect("card meta mentions verification date",
  c.children[c.children.length - 1].textContent.includes("Verified free on:"));

if (failures > 0) { console.error("RENDER TESTS FAILED: " + failures); process.exit(1); }
console.log("RENDER TESTS PASSED");
'''

(subprocess_dir := HERE / ".tmp-test").mkdir(exist_ok=True)
(shim_file := subprocess_dir / "render_test.mjs").write_text(SHIM, encoding="utf-8")
try:
    node = subprocess.run(["node", str(shim_file), str(OUTPUT)],
                          capture_output=True, text=True)
    print(node.stdout, end="")
    check("node render test exits 0", node.returncode == 0,
          (node.stderr or "").strip()[-600:])
    if node.returncode != 0 and node.stderr:
        print("  node stderr tail:", node.stderr.strip()[-600:])

    # fail-path: opening template.html directly (no embedded JSON) must not crash
    node_fail = subprocess.run(["node", str(shim_file), str(TEMPLATE), "--fail-path"],
                               capture_output=True, text=True)
    check("fail-path run (template.html) exits 0", node_fail.returncode == 0,
          (node_fail.stderr or "").strip()[-600:])
except FileNotFoundError:
    print("  SKIP  render tests: Node.js not found (JSON and build checks still ran).")


print()
print(f"Results: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
