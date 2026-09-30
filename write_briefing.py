#!/usr/bin/env python3
"""
OTR News weekly briefing writer. Runs every Monday (.github/workflows/write-briefing.yml).

Writes two files:
  briefings/YYYY-MM-DD.md            the newsletter issue, published at otrnews.com/briefing/
  briefings/community/YYYY-MM-DD.md  5 ready-to-paste community posts on different topics

To send it: open the issue at otrnews.com/briefing/, copy it into a new Kajabi email broadcast,
then paste the community posts into your Kajabi community. Needs the ANTHROPIC_API_KEY secret.
"""
import json
import os
import random
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import build  # reuses the site's settings, question bank, jobs, and posts

MODEL = os.environ.get("OTR_MODEL", "claude-sonnet-5-5")
OUT = build.ROOT / "briefings"


def parse(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def gather():
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    try:
        items = json.loads(build.ARCHIVE.read_text())
    except Exception:
        items = []
    recent = [i for i in items if not i.get("original") and (parse(i.get("published")) or now) >= week_ago]
    # a spread of topics: up to 2 per category, newest first
    stories, per_cat = [], {}
    for i in sorted(recent, key=lambda x: x.get("published", ""), reverse=True):
        cat = i.get("category") or "Industry"
        if per_cat.get(cat, 0) >= 2:
            continue
        per_cat[cat] = per_cat.get(cat, 0) + 1
        stories.append({"title": i.get("title"), "source": i.get("source"), "url": i.get("link"),
                        "category": cat, "summary": (i.get("summary") or "")[:400]})
        if len(stories) >= 10:
            break
    posts = build.load_posts()
    ours = [{"title": p["title"], "url": build.SITE_URL + p["link"], "summary": p.get("summary", ""),
             "guide": bool(p.get("section"))} for p in posts[:12]]
    _, jobs = build.load_jobs()
    picked = [j for j in jobs if j.get("pay")][:5] or jobs[:5]
    job_list = [{"title": j["title"], "company": j.get("company", ""), "location": j.get("location", ""),
                 "pay": (("Est. " + j["pay"].replace(" (est.)", "")) if "(est.)" in j.get("pay", "") else j.get("pay", "")),
                 "url": f'{build.SITE_URL}/jobs/{j["slug"]}/'} for j in picked]
    q = random.Random(now.strftime("%G-%V")).choice(build.QUIZ) if build.QUIZ else None
    question = {"topic": q[0], "question": q[1], "choices": q[2], "correct": q[2][0], "why": q[3]} if q else None
    return stories, ours, job_list, question


PROMPT = """You write the OTR News Briefing, a weekly email for truck drivers, owner-operators, and small fleet owners.
OTR News ({site}) is a MyCDLCoach company. Write in plain, friendly, direct English. Short sentences. No hype, no emoji.

Use ONLY the facts in the data below. Do not add numbers, names, or claims that are not in the data.
Summarize stories in your own words; never copy sentences from the summaries.

DATA (JSON):
{data}

Write two things.

PART 1, the newsletter issue, in Markdown:
- A 2-3 sentence opening that sets up the week.
- "## Top stories": 5 or 6 bullets. Each: **headline in your own words** ([Source](url)): one sentence on why it matters to drivers or small carriers.
- "## New jobs on the OTR News Job Board": one bullet per job: [job title](url), company, location, pay if given. Then a line linking to {site}/jobs/ for all jobs.
- "## From OTR News": 1-3 of our own articles or guides with links and one sentence each.
- "## CDL question of the week": the question and the choices as bullets, then "**Answer:**" with the correct answer and the explanation.
- A closing line inviting readers to the free CDL courses at {site}/courses/ and, for new drivers, MyCDLCoach's online ELDT theory course at {training}.

PART 2, community posts: 5 short posts for our driver community, each on a DIFFERENT topic:
1. A discussion question about one of this week's stories.
2. The CDL question of the week, asking members to answer before checking.
3. A job-hunting tip that links to {site}/jobs/.
4. A money or business tip for owner-operators that links to one of our articles if one fits.
5. A safety or health tip for life on the road.
Each post: 2-5 sentences, conversational, ends with a question or call to action.

Reply in exactly this format:
SUBJECT: <email subject line, under 60 characters>
PREVIEW: <preview text, under 110 characters>
===ISSUE===
<the Markdown issue>
===COMMUNITY===
### Post 1: <topic>
<text>
### Post 2: <topic>
<text>
(and so on through Post 5)
"""


def call_claude(prompt, key):
    body = json.dumps({"model": MODEL, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Anthropic API error {e.code}: {e.read().decode()[:500]}")
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def main():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        print("No ANTHROPIC_API_KEY secret set; skipping the briefing.")
        return
    stories, ours, jobs, question = gather()
    if not stories and not ours:
        print("Not enough news this week to write a briefing.")
        return
    data = json.dumps({"stories": stories, "our_articles": ours, "jobs": jobs, "cdl_question": question}, indent=1)
    text = call_claude(PROMPT.format(site=build.SITE_URL, training=build.TRAINING_URL, data=data), key)
    subject = (re.search(r"^SUBJECT:\s*(.+)$", text, re.M) or [None, ""])[1].strip()
    preview = (re.search(r"^PREVIEW:\s*(.+)$", text, re.M) or [None, ""])[1].strip()
    if "===ISSUE===" not in text or "===COMMUNITY===" not in text:
        sys.exit("The briefing came back in the wrong format; nothing saved. It will try again next week, or run it again by hand.")
    issue = text.split("===ISSUE===", 1)[1].split("===COMMUNITY===", 1)[0].strip()
    community = text.split("===COMMUNITY===", 1)[1].strip()
    today = datetime.now(timezone.utc)
    stamp = today.strftime("%Y-%m-%d")
    title = subject or f"OTR News Briefing, {today:%B %-d, %Y}"
    OUT.mkdir(exist_ok=True)
    (OUT / f"{stamp}.md").write_text(
        f'---\ntitle: {title.replace(chr(10), " ")}\ndate: {today.isoformat()}\npreview: {preview.replace(chr(10), " ")}\n---\n\n{issue}\n',
        encoding="utf-8")
    (OUT / "community").mkdir(exist_ok=True)
    (OUT / "community" / f"{stamp}.md").write_text(
        f"# Community posts for the week of {today:%B %-d, %Y}\n\nCopy each post into your community, one or two a day.\n\n{community}\n",
        encoding="utf-8")
    print(f"Briefing saved: briefings/{stamp}.md and briefings/community/{stamp}.md")


if __name__ == "__main__":
    main()
