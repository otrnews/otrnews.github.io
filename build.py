#!/usr/bin/env python3
"""
OTR News builder.
Pulls trucking headlines from feeds.txt, merges them into a rolling archive
(data/items.json), adds our own articles from posts/, and writes the site to ./site.
Standard library only.
"""
import base64
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime, format_datetime
from pathlib import Path

# ================== SETTINGS: edit these ==================
SITE_URL = "https://otrnews.com"
SITE_NAME = "OTR News"
TAGLINE = "Trucking news for owner-operators, small fleets, and drivers."
CONTACT_EMAIL = ""      # e.g. "news@otrnews.com" — turns on the Contact page
NEWSLETTER_URL = ""     # e.g. your Beehiiv signup link — turns on signup boxes
# ==========================================================

KEEP_DAYS = 30          # how long outside headlines stay in the archive
ON_PAGE = 100           # outside headlines on the homepage
ORIGINALS_ON_PAGE = 8   # our own articles leading the homepage

ROOT = Path(__file__).parent
SITE = ROOT / "site"
ARCHIVE = ROOT / "data" / "items.json"
POSTS = ROOT / "posts"
PAGES = ROOT / "pages"
UA = "Mozilla/5.0 (compatible; OTRNewsBot/1.0; +https://otrnews.com)"

# First match wins, so order matters.
CATEGORIES = [
    ("Regulations", r"\b(fmcsa|eld|elds|hours.of.service|hos|rulemaking|rule|rules|mandate|regulat\w*|exemption|waiver|clearinghouse|english.proficiency|non.domiciled|motus|usdot|congress|senate|bill|law|lawmakers)\b"),
    ("Fuel", r"\b(diesel|fuel|gas prices?|opec|crude|refiner\w*|oil prices?)\b"),
    ("Enforcement & safety", r"\b(crash\w*|rollover|fatal\w*|collision|safety|seiz\w*|cocaine|heroin|meth\w*|drugs?|smuggl\w*|troopers?|police|blitz|out.of.service|oos|inspections?|cargo theft|theft|stolen|arrest\w*|verdicts?|lawsuit|sues?|fraud\w*)\b"),
    ("Freight market", r"\b(freight|spot rates?|contract rates?|load posts?|load boards?|tenders?|capacity|shippers?|brokers?|brokerage|tariffs?|imports?|exports?|ports?|intermodal|dat|sonar)\b"),
    ("Equipment", r"\b(trailers?|engines?|electric trucks?|ev|evs|autonomous|driverless|hydrogen|used trucks?|truck sales|peterbilt|kenworth|freightliner|volvo|mack|navistar|daimler|tires?|nox|emissions)\b"),
    ("Drivers", r"\b(drivers?|truckers?|owner.operators?|cdl|cdls|truck parking|parking|driver pay|pay|wages?|recruit\w*|veterans?)\b"),
    ("Business", r"\b(bankrupt\w*|acquisitions?|acquires?|mergers?|layoffs?|earnings|revenue|profit|shuts? down|closes|headquarters|hq)\b"),
]

IMAGES = {'og.png': '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', 'icon.png': 'iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAAYFBMVEX////9/f34+vny9/Xq8u/j7urb6ePJ3da+1s2408m10Mapyb2awLKLt6bysB6AsJ54q5hmn4pUlHxIjXM4g2cse14oeVsneFogdFQYb04Ra0kQakgMaEUFYz8BYT0AYDyRNgOdAAAEHUlEQVR42u3d2ZLiIBQGYLLbMY5ZbaNZ3v8tp5cZyAIoJzhNpn4u2xT5mv2AJWzcYWJAAw000EADDfR/iGY/nYzRzI1kgmbupKfRjLmtZq6bZWrmvFmiZu6b12qmMf/0aKyUMOWTLkwiCgxTPObK3Cf1KNDuzNiP0c6Z5aT/B+3Wku4BmjmMZg/Qrq2egQYaaKCBBhpooIEGGmiggQYaaKCBBhpooIEGGmiggQbaDN2WpzQJA88PouSYV5376FueePNvYPhp2c+fqZ765kbx+eib9CMvjJL0XN7soNvMl70kKnqr6L/2VXEQ0EMeqPKP6xegl/lS0PdUk7ufvwTNvNOwBd3G+uxF7jbRjB0HOvoWP8r99Bo0O5PR/WHW1LKirKoyT/0Vwz7au1DR50kuqegdXRFN2nXz54/XaWr459Xs790MnV1EauoyP0wG1iMRfRFFGpSzDn0/ityTQTIh3PnHl/WHb5I28J2aRBTGnYYWA0fYLLOfVEJpDz12yTpbI7SoYq9ev1mUdTzYQ09eeiahs/UQMWWJdl1ZRI/JqlGboHs+E8a9bB1TSvqMBTSvwZSCFmNYLl18Dbyog94iOttU0ifej2/yJWPOYfUrSjqjoJNVPS3SVVMVdHS0ytQAPQS6rL9SqG7UZHS1rj4DdKsbHBbjeGIN3fKCDnsCuuavvarQvNWHttB1LFkxGaBFPSnjQdETBxp6uva41FUupkMW3ihoPgx7yoizUP9fz6E1qSQtTQt13a+nl5tt9JkWuXBR8AT6bhft5eNGtNc/bh6DVTQ9sK3Udb/qiMFoD+0dNmwhNLrXLoa82CK62rJZc19Fgat0UE/0dHTSb9lhinSr6a8UqJ8wnlwK9ULGBK2ZpL/Tu6YujNEDn1iC6wa0mO8aOZqHiV5rYRpvPFVjM0GLnpg9CAISK5FLpoqUjWLEWFlhi6klt4K+hZJ1hzFatI83WWDL3+G3dmLEQlG1RujW1416R23roaBFX5zHb2abNScxTZXqzRr/3dZmjeiLs/jfDC1a2ccSZra86DKm3RQhBgHZ1lXevK99DBFiSTDbgIw7e+hJP2no+9PZ7JAly9dbvYF8ECeGW4VsW9MU3T9aRXqKqJeInvTFgn580aVas6+K1KnRuOiLQUs/KOozjTmqR8voSYNM6eiP3hiqzNl9tI4WfZHP5qTDz+4kPUlMa83RMH1bTPTF6L7pmLkrlsfM0anRnmfT0cNhOdVaONAP40NWNPv4FsIPJqCBBhpooIEGGmiggQb6h9G/bCeggQYaaHfRmFyABhpooIEGGmiggQYaaKBp6H39/vQuf+kbPwT/z9C7vCdgnzcy7PLui33eMrLP+1z2eXPOPu8o2udtUPu8d2vc5Q1nbrjVsnGHCWiggQYaaKCB/ky/ASn6A695gGLnAAAAAElFTkSuQmCC'}


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
    text = (item["title"] + " " + item.get("summary", "")).lower()
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


def merge(old, new, allowed_sources):
    by_key = {}
    for i in old + new:
        if i.get("original") or i.get("source") not in allowed_sources:
            continue  # drops sources you've switched off in feeds.txt
        by_key.setdefault(key_for(i), i)
    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    now = datetime.now(timezone.utc) + timedelta(hours=1)
    items = [i for i in by_key.values() if cutoff <= datetime.fromisoformat(i["published"]) <= now]
    for i in items:
        i["category"] = categorize(i)
    items.sort(key=lambda i: i["published"], reverse=True)
    return items


# ---------- markdown ----------

def esc(s):
    return html.escape(s or "", quote=True)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def inline_md(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    def link(m):
        url = m.group(2)
        ext = not url.startswith("/") and not url.startswith("mailto:")
        return f'<a href="{url}"' + (' target="_blank" rel="noopener"' if ext else "") + f">{m.group(1)}</a>"
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]*|mailto:[^)\s]+)\)", link, t)
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


def split_front_matter(text):
    meta, body = {}, text
    if text.startswith("---"):
        _, head, body = text.split("---", 2)
        for line in head.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                meta[k.strip().lower()] = v
    return meta, body


# ---------- our own articles (posts/*.md) ----------

def load_posts():
    posts = []
    if not POSTS.exists():
        return posts
    for f in sorted(POSTS.glob("*.md")):
        meta, body = split_front_matter(f.read_text(encoding="utf-8"))
        if meta.get("draft", "").lower() == "true" or not meta.get("title"):
            continue
        date = parse_date(meta.get("date", "")) or datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)
        slug = meta.get("slug") or slugify(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", f.stem)) or slugify(meta["title"])
        words = len(re.findall(r"\w+", body))
        posts.append({
            "title": meta["title"], "link": f"/news/{slug}/", "slug": slug,
            "source": SITE_NAME, "author": meta.get("author", "OTR News Staff"),
            "summary": meta.get("summary", ""), "category": meta.get("category") or None,
            "published": date.isoformat(), "original": True,
            "minutes": max(1, round(words / 230)), "body": markdown(body),
        })
    posts.sort(key=lambda p: p["published"], reverse=True)
    return posts


# ---------- default pages (override by adding pages/about.md etc.) ----------

def default_pages():
    contact_line = (f"Send news tips, corrections, and advertising questions to [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})."
                    if CONTACT_EMAIL else "")
    pages = {
        "about": ("About OTR News", "Who we are and how we report.", f"""
OTR News covers the trucking industry for the people who keep it moving: owner-operators, small fleets, and company drivers.

## What we cover

Regulations and enforcement, freight rates, fuel, equipment, and the business of running trucks. We focus on the news that affects your money, your time, and your compliance, and we explain what it means and what to do about it.

## How we report

Every OTR News article is researched from primary sources, like FMCSA, DOT, the Federal Register, and the courts, along with reputable trade reporting. We link our sources at the end of each story so you can check them yourself.

We use AI tools to help research and draft articles. An editor reviews every story before it is published. When we get something wrong, we fix it and say so.

## Around the industry

Our homepage also links to headlines from other trucking news outlets. Those links go to the original publisher. We don't republish their articles.

{contact_line}
"""),
        "privacy": ("Privacy policy", "How OTR News handles information.", f"""
*Last updated {datetime.now(timezone.utc):%B %-d, %Y}*

OTR News is a news website. You can read everything on it without creating an account.

## What we collect

We don't ask for your name, email, or any other personal information to read the site, and we don't set advertising or tracking cookies.

## Services we rely on

- **Hosting.** The site is hosted on GitHub Pages. Like most web hosts, GitHub may log technical information such as IP addresses for security and reliability. See GitHub's privacy statement for details.
- **Fonts.** The site loads its typeface from Google Fonts, which means your browser connects to Google's servers. See Google's privacy policy for details.
- **Links to other sites.** Headlines and sources link to other publishers, whose own privacy policies apply once you leave OTR News.
{"- **Newsletter.** If you sign up for our newsletter, your email address is handled by our newsletter provider and used only to send you the newsletter. You can unsubscribe anytime." if NEWSLETTER_URL else ""}

## Changes

If we add features like a newsletter, analytics, or advertising, we'll update this page first.

{("## Contact" + chr(10) + chr(10) + f"Questions about this policy: [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL}).") if CONTACT_EMAIL else ""}
"""),
    }
    if CONTACT_EMAIL:
        pages["contact"] = ("Contact OTR News", "Send us news tips, corrections, and advertising questions.", f"""
We want to hear from drivers, owner-operators, and fleet owners.

- **News tips.** Seeing something on the road, at a shipper, or in your inbox that others should know about? Tell us.
- **Corrections.** If we got something wrong, let us know and we'll fix it.
- **Advertising.** Reach owner-operators and small fleets. Ask us about sponsorships.

Email: [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})
""")
    return pages


def load_pages():
    pages = default_pages()
    if PAGES.exists():
        for f in PAGES.glob("*.md"):
            meta, body = split_front_matter(f.read_text(encoding="utf-8"))
            name = f.stem.lower()
            old = pages.get(name, (name.title(), "", ""))
            pages[name] = (meta.get("title", old[0]), meta.get("summary", old[1]), body)
    return pages


# ---------- shared page shell ----------

def css_from(tpl):
    return re.search(r"<style>.*?</style>", tpl, re.S).group(0)


def footer_links(pages):
    links = [("/about/", "About")]
    if "contact" in pages:
        links.append(("/contact/", "Contact"))
    links += [("/privacy/", "Privacy"), ("/feed.xml", "RSS")]
    return "&ensp;".join(f'<a href="{u}">{t}</a>' for u, t in links)


def newsletter_box():
    if not NEWSLETTER_URL:
        return ""
    return f"""<aside class="signup">
<h2>Get the morning briefing</h2>
<p>The trucking news that matters to small carriers, in your inbox before you roll.</p>
<a class="btn" href="{esc(NEWSLETTER_URL)}" target="_blank" rel="noopener">Sign up free</a>
</aside>"""


PAGE_CSS = """<style>
.mast.small{padding-top:1.25rem}
.mast.small .sign-inner{padding:.8rem 1.1rem .7rem}
.mast.small .logo{font-size:2rem}
.doc{padding-top:1.5rem;padding-bottom:2rem}
.doc h1{font-weight:900;font-size:clamp(1.9rem,6.5vw,2.8rem);line-height:1.1;margin:.3rem 0 .6rem}
.doc .deck{font-size:1.2rem;color:var(--muted);margin:0 0 1rem}
.byline{font-size:.9rem;color:var(--muted);padding-bottom:1rem;border-bottom:1px solid var(--line);margin:0 0 1.2rem;display:flex;flex-wrap:wrap;gap:.3rem 1rem}
.body p,.body li{font-size:1.1rem;line-height:1.65}
.body h2{font-weight:800;font-size:1.45rem;margin:2rem 0 .4rem}
.body h3{font-weight:800;font-size:1.2rem;margin:1.5rem 0 .3rem}
.body a{color:var(--sign);text-underline-offset:2px}
@media (prefers-color-scheme:dark){.body a{color:#5CC795}}
.share{display:flex;flex-wrap:wrap;gap:.5rem;margin:2rem 0 0;padding-top:1.25rem;border-top:1px solid var(--line)}
.share span{width:100%;font-weight:800;margin-bottom:.1rem}
.share a,.share button{font:600 .95rem var(--font);color:var(--ink);background:var(--card);border:1.5px solid var(--line);border-radius:999px;padding:.45rem 1rem .35rem;text-decoration:none;cursor:pointer}
.more{margin-top:2.5rem}
.more h2{font-weight:900;font-size:1.3rem;margin:0 0 .25rem;padding-top:1rem;border-top:4px solid var(--sign)}
.back{display:inline-block;margin-top:1.5rem;font-weight:700}
</style>"""


def shell(tpl, pages, *, title, description, path, body, og_type="website", ld=None):
    ld_html = f'<script type="application/ld+json">{json.dumps(ld)}</script>' if ld else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE_URL}{path}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#00603C">
<link rel="icon" href="/icon.png"><link rel="apple-touch-icon" href="/icon.png">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Overpass:wght@400;600;800;900&display=swap" rel="stylesheet">
{ld_html}
{css_from(tpl)}
{PAGE_CSS}
</head><body>
<header class="mast small wrap"><div class="sign"><div class="sign-inner"><p class="logo"><a href="/">{SITE_NAME}</a></p></div></div></header>
<main class="wrap doc">
{body}
</main>
<footer class="wrap"><p>{footer_links(pages)}</p><p>&copy; {datetime.now(timezone.utc).year} {SITE_NAME}</p></footer>
</body></html>"""


def render_article(p, posts, tpl, pages):
    d = datetime.fromisoformat(p["published"])
    url = SITE_URL + p["link"]
    q = urllib.parse.quote
    share = f"""<div class="share"><span>Share this story</span>
<a href="https://www.facebook.com/sharer/sharer.php?u={q(url, safe='')}" target="_blank" rel="noopener">Facebook</a>
<a href="https://twitter.com/intent/tweet?url={q(url, safe='')}&text={q(p['title'], safe='')}" target="_blank" rel="noopener">X</a>
<a href="mailto:?subject={q(p['title'], safe='')}&body={q(url, safe='')}">Email</a>
<button type="button" onclick="navigator.clipboard&&navigator.clipboard.writeText('{url}').then(()=>{{this.textContent='Link copied'}})">Copy link</button>
</div>"""
    others = [o for o in posts if o is not p][:4]
    more = ""
    if others:
        more = '<section class="more"><h2>More from OTR News</h2>' + "".join(story_html(o) for o in others) + "</section>"
    body = f"""<article>
<p class="meta"><span class="cat">{esc(p['category'])}</span></p>
<h1>{esc(p['title'])}</h1>
<p class="deck">{esc(p['summary'])}</p>
<p class="byline"><span>By {esc(p['author'])}</span><time datetime="{p['published']}">{d.strftime('%B %-d, %Y')}</time><span>{p['minutes']} min read</span></p>
<div class="body">
{p['body']}
</div>
{share}
</article>
{newsletter_box()}
{more}
<a class="back" href="/">All trucking news</a>"""
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": p["title"],
          "datePublished": p["published"], "dateModified": p["published"],
          "author": {"@type": "Organization", "name": p["author"]},
          "publisher": {"@type": "Organization", "name": SITE_NAME,
                        "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/icon.png"}},
          "image": [f"{SITE_URL}/og.png"], "description": p["summary"], "mainEntityOfPage": url}
    return shell(tpl, pages, title=p["title"], description=p["summary"], path=p["link"],
                 body=body, og_type="article", ld=ld)


def render_page(name, page, tpl, pages):
    title, desc, md = page
    body = f'<h1>{esc(title)}</h1>\n<div class="body">\n{markdown(md)}\n</div>\n<a class="back" href="/">All trucking news</a>'
    return shell(tpl, pages, title=title, description=desc or title, path=f"/{name}/", body=body)


# ---------- homepage ----------

def fmt_date(iso):
    return datetime.fromisoformat(iso).strftime("%b %-d, %Y")


def story_html(i, lead=False):
    cls = ("story lead" if lead else "story") + (" original" if i.get("original") else "")
    summary = f'<p class="dek">{esc(i["summary"])}</p>' if i.get("summary") else ""
    tag = "h2" if lead else "h3"
    target = "" if i.get("original") else ' target="_blank" rel="noopener"'
    return f"""<article class="{cls}" data-cat="{esc(i["category"])}">
  <p class="meta"><span class="cat">{esc(i["category"])}</span><span class="src">{esc(i["source"])}</span><time datetime="{esc(i["published"])}">{fmt_date(i["published"])}</time></p>
  <{tag}><a href="{esc(i["link"])}"{target}>{esc(i["title"])}</a></{tag}>
  {summary}
</article>"""


def render(items, originals, sources_ok, pages):
    updated = datetime.now(timezone.utc)
    originals = originals[:ORIGINALS_ON_PAGE]
    feed = items[:ON_PAGE]
    cats = [c for c, _ in CATEGORIES] + ["Industry"]
    present = [c for c in cats if any(i["category"] == c for i in feed)]
    tpl = (ROOT / "template.html").read_text()
    chips = "".join(f'<button type="button" class="chip" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in present)
    if originals:
        ours = story_html(originals[0], True) + "\n".join(story_html(i) for i in originals[1:])
        industry_intro = '<h2 class="section-title" id="industry">Around the industry</h2>'
        feed_html = "\n".join(story_html(i) for i in feed)
    else:
        ours, industry_intro = "", ""
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
               .replace("{{NEWSLETTER}}", newsletter_box())
               .replace("{{INDUSTRY_TITLE}}", industry_intro)
               .replace("{{STORIES}}", feed_html)
               .replace("{{FOOTER_LINKS}}", footer_links(pages))
               .replace("{{JSONLD}}", json.dumps(ld))
               .replace("{{YEAR}}", str(updated.year)))


def render_rss(entries):
    out = []
    for i in entries[:50]:
        d = format_datetime(datetime.fromisoformat(i["published"]))
        link = SITE_URL + i["link"] if i["link"].startswith("/") else i["link"]
        out.append(f"<item><title>{esc(i['title'])}</title><link>{esc(link)}</link><guid isPermaLink=\"true\">{esc(link)}</guid><pubDate>{d}</pubDate><category>{esc(i['category'])}</category><description>{esc(i['summary'])}</description></item>")
    now = format_datetime(datetime.now(timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{SITE_URL}</link><description>{esc(TAGLINE)}</description><lastBuildDate>{now}</lastBuildDate>
{''.join(out)}
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
        except Exception as e:
            print(f"  skip {name}: {e.__class__.__name__}: {e}", file=sys.stderr)

    items = merge(load_archive(), fresh, {n for n, _ in feeds})
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(json.dumps(items, indent=1))

    SITE.mkdir(exist_ok=True)
    tpl = (ROOT / "template.html").read_text()
    pages = load_pages()
    posts = load_posts()
    for p in posts:
        p["category"] = p["category"] or categorize(p)
    for p in posts:
        out = SITE / "news" / p["slug"]
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render_article(p, posts, tpl, pages))
    for name, page in pages.items():
        out = SITE / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(render_page(name, page, tpl, pages))
    (SITE / "404.html").write_text(shell(tpl, pages, title="Page not found", description="Page not found", path="/404.html",
        body='<h1>That page isn\'t here</h1><div class="body"><p>It may have moved. The latest trucking news is on the homepage.</p></div><a class="back" href="/">All trucking news</a>'))
    for name, data in IMAGES.items():
        (SITE / name).write_bytes(base64.b64decode(data))

    (SITE / "index.html").write_text(render(items, posts, ok, pages))
    everything = sorted(posts + items, key=lambda i: i["published"], reverse=True)
    (SITE / "feed.xml").write_text(render_rss(everything))
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = [f"<url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq></url>"]
    urls += [f'<url><loc>{SITE_URL}{p["link"]}</loc><lastmod>{p["published"][:10]}</lastmod></url>' for p in posts]
    urls += [f"<url><loc>{SITE_URL}/{n}/</loc></url>" for n in pages]
    (SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(urls) + "</urlset>")
    print(f"Built site: {len(posts)} articles, {len(items)} headlines in archive, {ok}/{len(feeds)} sources up.")


if __name__ == "__main__":
    main()
