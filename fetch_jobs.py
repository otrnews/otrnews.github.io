"""
Pulls CDL / truck driving jobs from the Adzuna API and writes data/jobs.json.
Runs daily via .github/workflows/update-jobs.yml. Needs repo secrets ADZUNA_APP_ID and ADZUNA_APP_KEY
(free keys at https://developer.adzuna.com).
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

APP_ID = os.environ.get("ADZUNA_APP_ID")
APP_KEY = os.environ.get("ADZUNA_APP_KEY")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jobs.json")

SEARCHES = [
    "cdl a truck driver",
    "otr truck driver",
    "regional cdl driver",
    "local cdl driver home daily",
    "owner operator truck",
    "lease purchase truck driver",
]
PAGES_PER_SEARCH = 2   # 50 results per page
MAX_AGE_DAYS = 21
MUST_MATCH = re.compile(r"\b(cdl|truck|tractor|owner[- ]operator|otr|driver)\b", re.I)

def tag(text):
    t = text.lower(); tags = []
    if re.search(r"\botr\b|over the road|long haul", t): tags.append("otr")
    if "regional" in t: tags.append("regional")
    if re.search(r"\blocal\b|home daily|home every night", t): tags.append("local")
    if re.search(r"owner[- ]operator|lease", t): tags.append("owner")
    return tags

def pay(j):
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if not lo and not hi: return ""
    fmt = lambda v: f"${v:,.0f}"
    s = fmt(lo) if lo == hi or not hi else (f"{fmt(lo)}–{fmt(hi)}" if lo else fmt(hi))
    return s + ("/yr" if (hi or lo) > 1000 else "/hr") + (" (est.)" if j.get("salary_is_predicted") == "1" else "")

def fetch(what, page):
    q = urllib.parse.urlencode({
        "app_id": APP_ID, "app_key": APP_KEY, "what": what,
        "results_per_page": 50, "max_days_old": MAX_AGE_DAYS,
        "sort_by": "date", "content-type": "application/json",
    })
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}?{q}"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "OTRNews-jobs/1.0"}), timeout=30) as r:
        return json.load(r).get("results", [])

def main():
    if not APP_ID or not APP_KEY:
        print("No ADZUNA_APP_ID / ADZUNA_APP_KEY secrets set; skipping the jobs update.")
        return
    if not os.environ.get("FORCE_JOBS"):
        try:
            last = json.load(open(OUT)).get("updated")
            if last and (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() < 20 * 3600:
                print("Jobs were refreshed in the last 20 hours; skipping.")
                return
        except Exception:
            pass
    seen, jobs = set(), []
    for what in SEARCHES:
        for page in range(1, PAGES_PER_SEARCH + 1):
            try:
                results = fetch(what, page)
            except Exception as e:
                print(f"warn: {what} p{page}: {e}"); break
            for j in results:
                title = j.get("title", ""); desc = j.get("description", "")
                company = (j.get("company") or {}).get("display_name", "Company not listed")
                key = (title.lower().strip(), company.lower().strip())
                if key in seen or not MUST_MATCH.search(title + " " + desc): continue
                seen.add(key)
                jobs.append({
                    "title": re.sub("<[^>]+>", "", title),
                    "company": company,
                    "location": (j.get("location") or {}).get("display_name", ""),
                    "pay": pay(j),
                    "id": str(j.get("id", "")),
                    "snippet": re.sub("<[^>]+>", "", desc)[:260].rstrip() + "…",
                    "description": re.sub("<[^>]+>", "", desc).strip(),
                    "url": j.get("redirect_url"),
                    "posted": j.get("created"),
                    "tags": tag(title + " " + desc),
                })
            time.sleep(1)  # be polite to the API
    jobs.sort(key=lambda x: x.get("posted") or "", reverse=True)
    if not jobs:
        print("No jobs fetched; keeping the existing jobs.json")
        return
    with open(OUT, "w") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(), "jobs": jobs}, f, indent=1)
    print(f"wrote {len(jobs)} jobs")

if __name__ == "__main__":
    main()
