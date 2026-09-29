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
TAGLINE = "Trucking news for owner-operators, small fleets, and drivers."
KEEP_DAYS = 30          # how long stories stay in the archive
ON_PAGE = 100           # how many outside headlines the homepage shows
ORIGINALS_ON_PAGE = 8   # how many of our own articles lead the homepage
POSTS = ROOT / "posts"
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



# ---------- our own articles (posts/*.md) ----------

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def inline_md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*)\)",
               lambda m: f'<a href="{m.group(2)}"' + ('' if m.group(2).startswith('/') else ' target="_blank" rel="noopener"') + f'>{m.group(1)}</a>', t)
    return t


def markdown(md):
    out, para, lst = [], [], None
    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>"); para = []
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline_md(x)}</li>" for x in lst) + "</ul>"); lst = None
    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush(); continue
        if s.startswith("### "):
            flush(); out.append(f"<h3>{inline_md(s[4:])}</h3>")
        elif s.startswith("## "):
            flush(); out.append(f"<h2>{inline_md(s[3:])}</h2>")
        elif s[:2] in ("- ", "* "):
            if para: flush()
            lst = (lst or []) + [s[2:]]
        else:
            if lst: flush()
            para.append(s)
    flush()
    return "\n".join(out)


def load_posts():
    posts = []
    if not POSTS.exists():
        return posts
    for f in sorted(POSTS.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        meta, body = {}, text
        if text.startswith("---"):
            _, head, body = text.split("---", 2)
            for line in head.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip().strip('"')
        if meta.get("draft", "").lower() == "true" or not meta.get("title"):
            continue
        date = parse_date(meta.get("date", "")) or datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
        slug = meta.get("slug") or slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)) or slugify(meta["title"])
        posts.append({
            "title": meta["title"],
            "link": f"/news/{slug}/",
            "slug": slug,
            "source": "OTR News",
            "author": meta.get("author", "OTR News Staff"),
            "summary": meta.get("summary", ""),
            "category": meta.get("category") or None,
            "published": date.isoformat(),
            "original": True,
            "body": markdown(body),
        })
    return posts


def render_article(p, tpl):
    style = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
    d = datetime.fromisoformat(p["published"])
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"],
          "datePublished": p["published"], "author": {"@type": "Organization", "name": p["author"]},
          "publisher": {"@type": "Organization", "name": SITE_NAME}, "description": p["summary"],
          "mainEntityOfPage": SITE_URL + p["link"]}
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(p['title'])} | {SITE_NAME}</title>
<meta name="description" content="{esc(p['summary'])}">
<link rel="canonical" href="{SITE_URL}{p['link']}">
<meta property="og:title" content="{esc(p['title'])}">
<meta property="og:description" content="{esc(p['summary'])}">
<meta property="og:type" content="article">
<meta property="og:url" content="{SITE_URL}{p['link']}">
<meta name="theme-color" content="#00603C">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800;900&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(ld)}</script>
{style}
<style>
.mast.small .sign-inner{{padding:.8rem 1.1rem .7rem}}
.mast.small .logo{{font-size:2rem}}
.article{{padding-top:1.5rem;padding-bottom:3rem}}
.article h1{{font-weight:900;font-size:clamp(1.9rem,6.5vw,2.8rem);line-height:1.1;margin:.3rem 0 .6rem}}
.article .deck{{font-size:1.2rem;color:var(--muted);margin:0 0 1rem}}
.byline{{font-size:.9rem;color:var(--muted);padding-bottom:1rem;border-bottom:1px solid var(--line);margin:0 0 1.2rem}}
.body p,.body li{{font-size:1.1rem;line-height:1.65}}
.body h2{{font-weight:800;font-size:1.45rem;margin:2rem 0 .4rem}}
.body h3{{font-weight:800;font-size:1.2rem;margin:1.5rem 0 .3rem}}
.body a{{color:var(--sign);text-underline-offset:2px}}
@media (prefers-color-scheme:dark){{.body a{{color:#5CC795}}}}
.back{{display:inline-block;margin-top:2rem;font-weight:700}}
</style>
</head><body>
<header class="mast small wrap"><div class="sign"><div class="sign-inner"><p class="logo"><a href="/">{SITE_NAME}</a></p></div></div></header>
<main class="wrap article">
<p class="meta"><span class="cat">{esc(p['category'])}</span></p>
<h1>{esc(p['title'])}</h1>
<p class="deck">{esc(p['summary'])}</p>
<p class="byline">By {esc(p['author'])}&ensp;<time datetime="{p['published']}">{d.strftime('%B %-d, %Y')}</time></p>
<div class="body">
{p['body']}
</div>
<a class="back" href="/">All trucking news</a>
</main>
<footer class="wrap"><p>&copy; {d.year} {SITE_NAME}</p></footer>
</body></html>"""


# ---------- rendering ----------

def esc(s):
    return html.escape(s or "", quote=True)


def fmt_date(iso):
    d = datetime.fromisoformat(iso)
    return d.strftime("%b %-d, %Y")


def story_html(i, lead=False):
    cls = ("story lead" if lead else "story") + (" original" if i.get("original") else "")
    summary = f'<p class="dek">{esc(i["summary"])}</p>' if i["summary"] else ""
    return f'''<article class="{cls}" data-cat="{esc(i["category"])}">
  <p class="meta"><span class="cat">{esc(i["category"])}</span><span class="src">{esc(i["source"])}</span><time datetime="{esc(i["published"])}">{fmt_date(i["published"])}</time></p>
  <h{2 if lead else 3}><a href="{esc(i["link"])}"{'' if i.get("original") else ' target="_blank" rel="noopener"'}>{esc(i["title"])}</a></h{2 if lead else 3}>
  {summary}
</article>'''


def render(items, sources_ok):
    updated = datetime.now(timezone.utc)
    originals = [i for i in items if i.get("original")][:ORIGINALS_ON_PAGE]
    feed = [i for i in items if not i.get("original")][:ON_PAGE]
    cats = [c for c, _ in CATEGORIES] + ["Industry"]
    present = [c for c in cats if any(i["category"] == c for i in feed)]
    tpl = (ROOT / "template.html").read_text()
    chips = "".join(f'<button type="button" class="chip" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in present)

    if originals:
        ours = story_html(originals[0], True) + "\n".join(story_html(i) for i in originals[1:])
        industry_intro = '<h2 class="section-title" id="industry">Around the industry</h2>'
        feed_html = "\n".join(story_html(i) for i in feed)
    else:  # no articles of our own yet: lead with the newest headline
        ours = ""
        industry_intro = ""
        feed_html = (story_html(feed[0], True) + "\n".join(story_html(i) for i in feed[1:])) if feed else \
            '<p class="empty">No stories yet. The next update will fill this page.</p>'

    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL, "description": TAGLINE}
    return (tpl.replace("{{SITE_NAME}}", esc(SITE_NAME))
               .replace("{{TAGLINE}}", esc(TAGLINE))
               .replace("{{SITE_URL}}", SITE_URL)
               .replace("{{UPDATED_ISO}}", updated.isoformat())
               .replace("{{UPDATED_TEXT}}", updated.strftime("%b %-d, %Y at %H:%M UTC"))
               .replace("{{SOURCE_COUNT}}", str(sources_ok))
               .replace("{{CHIPS}}", chips)
               .replace("{{ORIGINALS}}", ours)
               .replace("{{INDUSTRY_TITLE}}", industry_intro)
               .replace("{{STORIES}}", feed_html)
               .replace("{{JSONLD}}", json.dumps(ld))
               .replace("{{YEAR}}", str(updated.year)))


def render_rss(items):
    entries = []
    for i in items[:50]:
        d = format_datetime(datetime.fromisoformat(i["published"]))
        link = SITE_URL + i["link"] if i["link"].startswith("/") else i["link"]
        entries.append(f"""<item><title>{esc(i['title'])}</title><link>{esc(link)}</link><guid isPermaLink="true">{esc(link)}</guid><pubDate>{d}</pubDate><category>{esc(i['category'])}</category><description>{esc(i['summary'])}</description></item>""")
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
    posts = load_posts()
    for p in posts:
        p["category"] = p["category"] or categorize(p)
    tpl = (ROOT / "template.html").read_text()
    for p in posts:
        out = SITE / "news" / p["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render_article(p, tpl))
    posted = [{k: v for k, v in p.items() if k != "body"} for p in posts]
    items = sorted(posted + items, key=lambda i: i["published"], reverse=True)

    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(render(items, len(feeds)))
    (SITE / "feed.xml").write_text(render_rss(items))
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    (SITE / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq></url>'
        + "".join(f'<url><loc>{SITE_URL}{p["link"]}</loc><lastmod>{p["published"][:10]}</lastmod></url>' for p in posts)
        + '</urlset>')
    print(f"Built site: {len(items)} stories in archive, {min(len(items), ON_PAGE)} on page, {ok}/{len(feeds)} sources up.")


if __name__ == "__main__":
    main()
