#!/usr/bin/env python3
"""
OTR News daily article writer.
Asks Claude (via the Anthropic API, with web search) to research the most important
trucking story for owner-operators and small fleets and write an original article.
The article is saved to posts/ as a DRAFT. To publish it, edit the file on GitHub
and change `draft: true` to `draft: false`.
Needs the ANTHROPIC_API_KEY secret. Standard library only.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
POSTS = ROOT / "posts"
IMAGES = ROOT / "images"
ARCHIVE = ROOT / "data" / "items.json"
GUIDE = ROOT / "style-guide.md"   # optional: your own voice and rules
MODEL = os.environ.get("OTR_MODEL", "claude-sonnet-5-5")
MAX_SEARCHES = 8

PROMPT = """You are the staff writer for OTR News (otrnews.com), a trucking news site for
truck drivers, owner-operators, and small fleets. Today is {today}.

{assignment}

Recent OTR News articles (do not repeat these topics unless there is major new news):
{recent}

Today's industry headlines, as leads (verify everything yourself; do not rely on these):
{headlines}

Rules:
- Write every sentence in your own words. Never copy or closely paraphrase another
  outlet's sentences or structure. Report the facts, then explain what they mean.
- Only state facts you found in your research. If something is unclear or unconfirmed,
  say so. Never invent quotes, numbers, names, or dates.
- Prefer primary sources (FMCSA, DOT, Federal Register, courts, company statements).
- Plain, direct language a driver would use. No hype, no filler.
- Write as a newsroom, in the third person. Never use "I" or "we", never address the
  editor, and never mention your research process, searches, or what you could not find.
  If a detail is unconfirmed, say so in reader-facing terms, for example
  "FMCSA had not published the notice as of Tuesday."
- The headline must not contain a colon. Use plain words instead.
- Structure: a short opening that says what happened and why it matters; sections with
  "## " headings; a "## What to do" section with practical steps when relevant; a one-line
  **Bottom line:**; then "## Sources" with 2-5 markdown links you actually used.
- 450-800 words.
{guide}
Output ONLY the finished file, starting with the front matter, exactly in this format:

---
title: <headline, specific and plain, under 90 characters>
date: {iso}
summary: <one or two sentences, under 200 characters>
category: <{categories}>
author: OTR News Staff
draft: true
photo_idea: <3 to 6 words for a stock photo search that includes a truck, a generic trucking scene such as "semi truck at fuel pump" or "truck parking lot at night"; no identifiable people, logos, or specific real events>
---

<article body in markdown>
"""



NEWS_ASSIGNMENT = """Your job: find the single most useful trucking story from the last 48 hours for
truck drivers and owner-operators, research it with web search, and write an ORIGINAL article.

Write for the driver in the cab: what happened, how it affects their pay, time, safety, or
compliance, and what to do about it. Good picks: FMCSA/DOT rules and enforcement blitzes,
inspections and out-of-service trends, driver pay and jobs, parking, diesel prices and state
fuel relief, weather and road closures affecting freight, broker and freight-rate changes,
fraud and cargo theft, registration and authority. Skip stories only executives or investors care about."""

GUIDE_TOPICS = {
    "training": [
        "How to pass the CDL permit (knowledge) test on the first try",
        "The CDL pre-trip inspection, step by step",
        "Air brakes: what the CDL test expects you to know",
        "Class A vs. Class B CDL: which one do you need?",
        "CDL endorsements explained (H, N, P, S, T, X) and when they are worth getting",
        "Combination vehicles: tips for the CDL knowledge and skills tests",
        "How to choose a CDL school or training program without getting burned",
        "Backing and parking: skills test maneuvers and how to practice them",
        "Getting a hazmat endorsement: the steps, background check, and test",
    ],
    "finance": [
        "Truck factoring explained: how it works, what it costs, and when it makes sense",
        "Financing your first semi truck: what lenders look at and how to prepare",
        "How to calculate your cost per mile and set a profitable rate",
        "Owner-operator taxes 101: per diem, deductions, and quarterly estimates",
        "Lease-purchase programs: the questions to ask before you sign",
    ],
    "health": [
        "The DOT physical: what to expect and how to prepare",
        "Your medical examiner's certificate: how long it lasts and how to keep it current",
        "Sleep apnea and truck drivers: what the rules actually say",
        "Staying healthy on the road: realistic food and exercise habits for drivers",
        "High blood pressure and your DOT medical card: what drivers should know",
    ],
    "repairs": [
        "Preventive maintenance schedule for owner-operators",
        "What to do when your truck breaks down on the highway",
        "Tire care for truckers: tread, pressure, and inspection basics",
        "Reading your truck's warning lights and fault codes: when to stop and when to keep going",
        "DPF and emissions system problems: causes, prevention, and costs",
    ],
    "insurance": [
        "Commercial truck insurance explained: the coverages owner-operators need",
        "Why truck insurance costs so much, and how to lower your premium",
        "Getting your own authority: insurance requirements and filings",
    ],
    "jobs": [
        "How to read a trucking job ad: pay, home time, and red flags",
        "Driver pay explained: cents per mile, percentage, and hourly",
        "Your first year as a truck driver: what to expect and how to survive it",
        "Company driver, lease-purchase, or owner-operator: comparing the paths",
    ],
}
SECTION_CATEGORY = {"training": "Training", "finance": "Business", "insurance": "Business",
                    "health": "Drivers", "repairs": "Equipment", "jobs": "Drivers"}

GUIDE_ASSIGNMENT = """Your job today: write an evergreen CDL STUDY GUIDE for new and future truck drivers on
this topic: "{topic}"

Research it with web search, using primary sources first (FMCSA, the federal regulations in
49 CFR, IRS, state CDL manuals, and other official sources). Be accurate: note where rules differ by state and tell readers
to check their own state's rules where relevant. Be practical: checklists, common mistakes, and
test-day tips. Do not promise that anyone will pass, and do not mention any specific
training company by name."""


def pick_assignment(now):
    """Mondays and Thursdays are guide days, rotating through the guide sections; other days are news."""
    if now.weekday() in (0, 3):
        done = [f.read_text(encoding="utf-8").lower() for f in POSTS.glob("*.md")]
        guides_so_far = sum(1 for d in done if "guide_topic:" in d)
        order = list(GUIDE_TOPICS)
        for step in range(len(order)):
            section = order[(guides_so_far + step) % len(order)]
            for topic in GUIDE_TOPICS[section]:
                if not any(topic.lower()[:40] in d for d in done):
                    extra = ("\nThis is general health information, not medical advice. Tell readers to talk to a "
                             "certified medical examiner or their doctor about their own situation." if section == "health" else "")
                    extra += ("\nExplain options neutrally. Never promise approval, rates, or savings." if section in ("finance", "insurance") else "")
                    return GUIDE_ASSIGNMENT.format(topic=topic) + extra, SECTION_CATEGORY[section], topic, section
    return NEWS_ASSIGNMENT, "Regulations, Freight market, Fuel, Enforcement & safety, Equipment, Drivers, Business", None, None

TRUCK_WORDS = re.compile(r"\b(truck\w*|semi|trailer\w*|tractor|freight|highway|trucker\w*|rig|big rig|18.wheeler|diesel)\b", re.I)
# Backup searches by topic, so every article gets a real trucking photo
TOPIC_PHOTO = {
    "Regulations": "semi truck weigh station", "Fuel": "semi truck diesel fuel pump",
    "Enforcement & safety": "semi truck highway safety", "Freight market": "semi trucks loading dock freight",
    "Equipment": "semi truck engine repair shop", "Drivers": "truck driver in cab",
    "Business": "semi truck fleet parked", "Training": "truck driving school tractor trailer",
    "Industry": "semi truck on highway",
}
SECTION_PHOTO = {"finance": "semi truck fleet parked", "insurance": "semi truck on highway", "health": "trucks parked at truck stop night",
                 "repairs": "semi truck engine repair shop", "jobs": "truck driver in cab", "training": "truck driving school tractor trailer"}


def used_photo_urls():
    used = set()
    for f in POSTS.glob("*.md"):
        m = re.search(r"^credit_url:\s*(\S+)", f.read_text(encoding="utf-8"), re.M)
        if m:
            used.add(m.group(1))
    return used


def search_photos(query):
    """Search Pixabay first (PIXABAY_API_KEY), then Pexels (PEXELS_API_KEY). Returns a list of candidate photos."""
    out = []
    pix = os.environ.get("PIXABAY_API_KEY", "").strip()
    if pix:
        url = "https://pixabay.com/api/?" + urllib.parse.urlencode(
            {"key": pix, "q": query[:100], "image_type": "photo", "orientation": "horizontal",
             "safesearch": "true", "per_page": 20})
        req = urllib.request.Request(url, headers={"User-Agent": "OTRNewsBot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            for h in json.loads(r.read()).get("hits", []):
                out.append({"src": h.get("largeImageURL") or h.get("webformatURL"), "page": h.get("pageURL", "https://pixabay.com"),
                            "alt": h.get("tags", ""), "credit": f"Image by {h.get('user', 'Pixabay')} from Pixabay"})
    pex = os.environ.get("PEXELS_API_KEY", "").strip()
    if pex and not out:
        url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
            {"query": query, "per_page": 20, "orientation": "landscape"})
        req = urllib.request.Request(url, headers={"Authorization": pex, "User-Agent": "OTRNewsBot/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            for p in json.loads(r.read()).get("photos", []):
                out.append({"src": p["src"].get("large") or p["src"]["original"], "page": p.get("url", "https://www.pexels.com"),
                            "alt": p.get("alt", ""), "credit": f"Photo by {p.get('photographer', 'Pexels')} on Pexels"})
    return [p for p in out if p.get("src")]


def fetch_photo(query, slug, backup=""):
    """Find a free trucking photo that matches the story. Needs PIXABAY_API_KEY (or PEXELS_API_KEY); skipped if neither is set."""
    if not (os.environ.get("PIXABAY_API_KEY", "").strip() or os.environ.get("PEXELS_API_KEY", "").strip()):
        print("No PIXABAY_API_KEY secret set; the article will use the topic card image.")
        return None
    query = (query or "").strip()
    if query and not TRUCK_WORDS.search(query):
        query += " semi truck"   # keep results trucking-related, not generic office stock
    used = used_photo_urls()
    try:
        for q in [x for x in (query, backup, "semi truck highway") if x]:
            photos = [p for p in search_photos(q) if p["page"] not in used]
            if photos:
                break
        else:
            return None
        ph = photos[0]
        req = urllib.request.Request(ph["src"], headers={"User-Agent": "OTRNewsBot/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        IMAGES.mkdir(exist_ok=True)
        name = f"{slug}.jpg"
        (IMAGES / name).write_bytes(data)
        return {"image": f"/images/{name}",
                "image_alt": (ph["alt"] or query).replace("\n", " ")[:150],
                "credit": ph["credit"],
                "credit_url": ph["page"]}
    except Exception as e:
        print(f"Photo search skipped: {e}")
        return None


def add_photo_lines(article, photo):
    end = article.find("---", 3)
    lines = "".join(f'{k}: {v.replace(chr(10), " ")}\n' for k, v in photo.items())
    return article[:end].rstrip("\n") + "\n" + lines + article[end:]


def backfill_photos(limit=8):
    """Give older articles and guides without a photo a matching trucking photo, a few per run."""
    done = 0
    for f in sorted(POSTS.glob("*.md"), reverse=True):
        if done >= limit:
            break
        text = f.read_text(encoding="utf-8")
        head = text[:text.find("---", 3)] if text.startswith("---") else ""
        if not head or re.search(r"^image:", head, re.M):
            continue
        get = lambda k: (re.search(rf"^{k}:\s*(.+)$", head, re.M) or [None, ""])[1].strip().strip('"')
        backup = SECTION_PHOTO.get(get("section").lower()) or TOPIC_PHOTO.get(get("category"), "")
        photo = fetch_photo(get("photo_idea") or backup, f.stem, backup)
        if not photo:
            break
        f.write_text(add_photo_lines(text, photo), encoding="utf-8")
        print(f"Photo added: {f.name}")
        done += 1


def recent_posts(n=10):
    titles = []
    for f in sorted(POSTS.glob("*.md"), reverse=True)[:n]:
        m = re.search(r"^title:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        if m:
            titles.append("- " + m.group(1).strip())
    return "\n".join(titles) or "- (none yet)"


def headlines(n=25):
    try:
        items = json.loads(ARCHIVE.read_text())
    except Exception:
        return "- (none available)"
    return "\n".join(f"- {i['title']} ({i['source']})" for i in items[:n] if not i.get("original")) or "- (none available)"


def call_claude(messages, key):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "messages": messages,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_SEARCHES}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Anthropic API error {e.code}: {e.read().decode()[:500]}")


def main():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("No ANTHROPIC_API_KEY secret set; skipping the daily article.")
        return

    now = datetime.now(timezone.utc)
    guide = ""
    if GUIDE.exists():
        guide = "\nHouse style from the publisher (follow it):\n" + GUIDE.read_text(encoding="utf-8") + "\n"
    assignment, categories, guide_topic, section = pick_assignment(now)
    if guide_topic:
        categories = categories  # fixed category for guides
    else:
        categories = "one of: " + categories
    prompt = PROMPT.format(today=now.strftime("%A, %B %-d, %Y"), iso=now.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                           recent=recent_posts(), headlines=headlines(), guide=guide,
                           assignment=assignment, categories=categories)
    messages = [{"role": "user", "content": prompt}]

    for _ in range(5):  # server-side search can pause a long turn; continue it
        resp = call_claude(messages, key)
        if resp.get("stop_reason") != "pause_turn":
            break
        messages += [{"role": "assistant", "content": resp["content"]}]

    text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    start = text.find("---")
    if start == -1 or "title:" not in text:
        sys.exit("The reply didn't contain an article. Raw reply:\n" + text[:2000])
    article = text[start:].strip() + "\n"

    # Always save as a draft, whatever the model wrote
    head_end = article.find("---", 3)
    head = article[:head_end]
    head = re.sub(r"^draft:.*$", "draft: true", head, flags=re.M)
    if "draft:" not in head:
        head = head.rstrip() + "\ndraft: true\n"
    if guide_topic:
        head = head.rstrip() + f"\nguide_topic: {guide_topic}\nsection: {section}\n"
    article = head + article[head_end:]

    # House-style cleanup: no colons in the headline/summary, no notes to the editor
    def no_colon(m):
        return m.group(1) + m.group(2).replace(": ", " — ")
    article = re.sub(r"^(title:\s*|summary:\s*)(.+)$", no_colon, article, flags=re.M)
    head_end = article.find("---", 3)
    body = article[head_end + 3:]
    paras = re.split(r"\n\s*\n", body)
    note = re.compile(r"^(I|We)\b|\b(I (did|could|was|found|searched|couldn't|didn't))\b|\bmy (research|search)", re.I)
    kept = [p for p in paras if not note.search(p.strip())]
    article = article[:head_end + 3] + "\n\n".join(kept)

    title = re.search(r"^title:\s*(.+)$", article, re.M).group(1).strip().strip('"')
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60].rstrip("-")
    idea = re.search(r"^photo_idea:\s*(.+)$", article, re.M)
    cat = re.search(r"^category:\s*(.+)$", article, re.M)
    backup = SECTION_PHOTO.get(section or "") or TOPIC_PHOTO.get(cat.group(1).strip() if cat else "", "")
    photo = fetch_photo(idea.group(1).strip().strip('"') if idea else "", f"{now:%Y-%m-%d}-{slug}", backup)
    if photo:
        article = add_photo_lines(article, photo)
    POSTS.mkdir(exist_ok=True)
    path = POSTS / f"{now:%Y-%m-%d}-{slug}.md"
    path.write_text(article, encoding="utf-8")
    print(f"Draft saved: {path.relative_to(ROOT)}")
    backfill_photos()


if __name__ == "__main__":
    main()
