#!/usr/bin/env python3
"""
Big-story alert. Runs with every site update (update.yml).

When 3 or more different outlets cover the same story within a few hours, it writes an OTR News
explainer draft right away (instead of waiting for the next scheduled article) and opens a GitHub
issue so you get a phone notification to review it.

Limits: at most MAX_PER_DAY big-story drafts per day, and never the same story twice.
"""
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = ROOT / "data" / "items.json"
STATE = ROOT / "data" / "big_stories.json"
POSTS = ROOT / "posts"

MIN_SOURCES = 3        # different outlets covering the same story
WINDOW_HOURS = 6       # how recent the coverage must be
MAX_PER_DAY = 2        # most big-story drafts per day

STOP = set("""the and for with from that this will have has had are was were into over after about their they them
what when where which while than then more most just also says said new news report reports amid could would should
truck trucks trucking trucker truckers driver drivers freight carrier carriers industry fmcsa""".split())


def words(text):
    return {w for w in re.findall(r"[a-z0-9$]+", (text or "").lower()) if len(w) > 3 and w not in STOP}


def parse(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def clusters(items):
    n = len(items)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    ws = [words(i["title"]) for i in items]
    for a in range(n):
        for b in range(a + 1, n):
            shared = ws[a] & ws[b]
            union = ws[a] | ws[b]
            if len(shared) >= 3 or (union and len(shared) >= 2 and len(shared) / len(union) >= 0.3):
                parent[find(a)] = find(b)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(items[i])
    return list(groups.values())


def main():
    now = datetime.now(timezone.utc)
    try:
        items = json.loads(ITEMS.read_text())
    except Exception:
        print("No headlines yet.")
        return
    try:
        state = json.loads(STATE.read_text())
    except Exception:
        state = {"handled": []}
    today = now.strftime("%Y-%m-%d")
    if sum(1 for h in state["handled"] if h.get("date") == today) >= MAX_PER_DAY:
        print("Big-story limit reached for today.")
        return
    recent = [i for i in items if not i.get("original") and (parse(i.get("published")) or now) >= now - timedelta(hours=WINDOW_HOURS)]
    handled_links = {l for h in state["handled"] for l in h.get("links", [])}
    handled_words = [set(h.get("words", [])) for h in state["handled"][-50:]]
    # our own recent articles, so we don't repeat a story we already covered
    own = []
    for f in sorted(POSTS.glob("*.md"), reverse=True)[:30] if POSTS.exists() else []:
        m = re.search(r"^title:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        if m:
            own.append(words(m.group(1)))
    best = None
    for g in clusters(recent):
        sources = {i["source"] for i in g}
        if len(sources) < MIN_SOURCES:
            continue
        if any(i["link"] in handled_links for i in g):
            continue
        key = set.intersection(*[words(i["title"]) for i in g]) or words(g[0]["title"])
        allw = set().union(*[words(i["title"]) for i in g])
        if any(len(allw & hw) >= 4 for hw in handled_words) or any(len(allw & ow) >= 4 for ow in own):
            continue
        if not best or len(sources) > len({i["source"] for i in best}):
            best = g
    if not best:
        print("No big story right now.")
        return
    coverage = "\n".join(f"- {i['source']}: {i['title']} ({i['link']})" for i in best[:8])
    print("Big story found:\n" + coverage)
    before = set(POSTS.glob("*.md")) if POSTS.exists() else set()
    os.environ["BIG_STORY"] = coverage
    import write_article
    write_article.main()
    new = sorted(set(POSTS.glob("*.md")) - before)
    state["handled"].append({"date": today, "links": [i["link"] for i in best],
                             "words": sorted(set().union(*[words(i["title"]) for i in best]))})
    state["handled"] = state["handled"][-200:]
    STATE.write_text(json.dumps(state, indent=1))
    if new:
        f = new[0]
        m = re.search(r"^title:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        title = (m.group(1).strip().strip('"') if m else f.stem)
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a") as fh:
                fh.write(f"draft=posts/{f.name}\n")
                fh.write("title=" + title.replace("\n", " ")[:200] + "\n")
        print(f"Draft saved: posts/{f.name}")


if __name__ == "__main__":
    main()
