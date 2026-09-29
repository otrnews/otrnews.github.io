#!/usr/bin/env python3
"""
OTR News builder.
Pulls the latest trucking headlines from the feeds in feeds.txt, merges them
into a rolling archive (data/items.json), and writes a static site to ./site.
Standard library only — no installs needed.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime, format_datetime
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
ARCHIVE = ROOT / "data" / "items.json"
SITE_URL = "https://otrnews.com"
SITE_NAME = "OTR News"
TAGLINE = "Trucking news from across the industry, updated all day."
KEEP_DAYS = 30          # how long stories stay in the archive
ON_PAGE = 120           # how many stories the homepage shows
UA = "Mozilla/5.0 (compatible; OTRNewsBot/1.0; +https://otrnews.com)"

CATEGORIES = [
    ("Regulations", r"\b(fmcsa|dot|eld|hours.of.service|hos|rule|rulemaking|mandate|regulat|compliance|clearinghouse|cvsa|inspection|english.proficiency|non.domiciled|cdl rule|congress|senate|bill|law)\b"),
    ("Freight market", r"\b(freight|spot rate|contract rate|load|tender|capacity|volume|shipper|broker|brokerage|tariff|import|export|port|intermodal|rates?)\b"),
    ("Fuel", r"\b(diesel|fuel|gas price|opec|crude|refiner)\b"),
    ("Safety", r"\b(crash|safety|fatal|accident|collision|verdict|lawsuit|nuclear verdict|speed limiter|insurance)\b"),
    ("Equipment", r"\b(truck maker|freightliner|peterbilt|kenworth|volvo|mack|international|navistar|trailer|engine|electric truck|ev|hydrogen|autonomous|driverless|tesla semi|tire)\b"),
    ("Drivers", r"\b(driver|drivers|owner.operator|trucker|truckers|cdl|parking|pay|wage|recruit)\b"),
    ("Business", r"\b(bankrupt|acquisition|acquire|merger|layoff|earnings|revenue|profit|closes|shutdown|carrier|fleet)\b"),
]


# ---------- fetching & parsing ----------

def read_feeds():
    feeds = []
    for line in (ROOT / "feeds.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        name, url = [p.strip() for p in line.split("|", 1)]
        feeds.append((name, url))
    return feeds


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def strip_ns(tag):
    return tag.rsplit("}", 1)[-1].lower()


def child_text(el, *names):
    for c in el:
        if strip_ns(c.tag) in names and (c.text or "").strip():
            return c.text.strip()
    return ""


def parse_date(s):
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def clean(text, limit=None):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(The post .*? appeared first on .*?\.?$)", "", text).strip()
    if limit and len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return text


def parse_feed(source, raw):
    root = ET.fromstring(raw)
    items = []
    for el in root.iter():
        kind = strip_ns(el.tag)
        if kind not in ("item", "entry"):
            continue
        title = clean(child_text(el, "title"))
        link = child_text(el, "link")
        if not link:  # Atom
            for c in el:
                if strip_ns(c.tag) == "link" and c.get("href") and c.get("rel", "alternate") == "alternate":
                    link = c.get("href")
                    break
        date = parse_date(child_text(el, "pubdate", "published", "updated", "date"))
        summary = clean(child_text(el, "description", "summary", "encoded"), 240)
        src = source
        if "news.google.com" in (link or ""):
            publisher = child_text(el, "source")
            if publisher:
                src = publisher
                title = re.sub(r"\s+-\s+" + re.escape(publisher) + r"$", "", title)
            summary = ""  # Google's summaries just repeat the headline
        if not title or not link or not link.startswith("http"):
            continue
        items.append({
            "title": title,
            "link": link,
            "source": src,
            "summary": summary,
            "published": (date or datetime.now(timezone.utc)).isoformat(),
        })
    return items


def categorize(item):
    text = (item["title"] + " " + item["summary"]).lower()
    for name, pattern in CATEGORIES:
        if re.search(pattern, text):
            return name
    return "Industry"


def key_for(item):
    return re.sub(r"[^a-z0-9]", "", item["title"].lower())[:80]


# ---------- archive ----------

def load_archive():
    if ARCHIVE.exists():
        try:
            return json.loads(ARCHIVE.read_text())
        except json.JSONDecodeError:
            pass
    return []


def merge(old, new):
    by_key = {key_for(i): i for i in old}
    for i in new:
        k = key_for(i)
        if k not in by_key:
            by_key[k] = i
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    items = [i for i in by_key.values() if cutoff <= datetime.fromisoformat(i["published"]) <= now]
    for i in items:
        i["category"] = categorize(i)
    items.sort(key=lambda i: i["published"], reverse=True)
    return items


# ---------- rendering ----------

def esc(s):
    return html.escape(s or "", quote=True)


def fmt_date(iso):
    d = datetime.fromisoformat(iso)
    return d.strftime("%b %-d, %Y")


def story_html(i, lead=False):
    cls = "story lead" if lead else "story"
    summary = f'<p class="dek">{esc(i["summary"])}</p>' if i["summary"] else ""
    return f'''<article class="{cls}" data-cat="{esc(i["category"])}">
  <p class="meta"><span class="cat">{esc(i["category"])}</span><span class="src">{esc(i["source"])}</span><time datetime="{esc(i["published"])}">{fmt_date(i["published"])}</time></p>
  <h{2 if lead else 3}><a href="{esc(i["link"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></h{2 if lead else 3}>
  {summary}
</article>'''


def render(items, sources_ok):
    shown = items[:ON_PAGE]
    cats = [c for c, _ in CATEGORIES] + ["Industry"]
    present = [c for c in cats if any(i["category"] == c for i in shown)]
    updated = datetime.now(timezone.utc)
    lead = shown[0] if shown else None
    rest = shown[1:]
    tpl = (ROOT / "template.html").read_text()
    chips = "".join(f'<button type="button" class="chip" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in present)
    body = (story_html(lead, True) if lead else '<p class="empty">No stories yet. The next update will fill this page.</p>')
    body_rest = "\n".join(story_html(i) for i in rest)
    ld = {
        "@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL,
        "description": TAGLINE,
    }
    out = (tpl.replace("{{SITE_NAME}}", esc(SITE_NAME))
              .replace("{{TAGLINE}}", esc(TAGLINE))
              .replace("{{SITE_URL}}", SITE_URL)
              .replace("{{UPDATED_ISO}}", updated.isoformat())
              .replace("{{UPDATED_TEXT}}", updated.strftime("%b %-d, %Y at %H:%M UTC"))
              .replace("{{SOURCE_COUNT}}", str(sources_ok))
              .replace("{{CHIPS}}", chips)
              .replace("{{LEAD}}", body)
              .replace("{{STORIES}}", body_rest)
              .replace("{{JSONLD}}", json.dumps(ld))
              .replace("{{YEAR}}", str(updated.year)))
    return out


def render_rss(items):
    entries = []
    for i in items[:50]:
        d = format_datetime(datetime.fromisoformat(i["published"]))
        entries.append(f"""<item><title>{esc(i['title'])}</title><link>{esc(i['link'])}</link><guid isPermaLink="true">{esc(i['link'])}</guid><pubDate>{d}</pubDate><category>{esc(i['category'])}</category><description>{esc(i['summary'])}</description></item>""")
    now = format_datetime(datetime.now(timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}</link><description>{esc(TAGLINE)}</description><lastBuildDate>{now}</lastBuildDate>
{''.join(entries)}
</channel></rss>"""


def main():
    feeds = read_feeds()
    fresh, ok = [], 0
    for name, url in feeds:
        try:
            got = parse_feed(name, fetch(url))
            fresh.extend(got)
            ok += 1
            print(f"  ok   {name}: {len(got)} stories")
        except Exception as e:  # keep going if one source is down
            print(f"  skip {name}: {e.__class__.__name__}: {e}", file=sys.stderr)

    items = merge(load_archive(), fresh)
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(json.dumps(items, indent=1))

    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(render(items, len(feeds)))
    (SITE / "feed.xml").write_text(render_rss(items))
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq></url></urlset>')
    print(f"Built site: {len(items)} stories in archive, {min(len(items), ON_PAGE)} on page, {ok}/{len(feeds)} sources up.")


if __name__ == "__main__":
    main()
