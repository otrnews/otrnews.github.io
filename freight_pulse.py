#!/usr/bin/env python3
"""
Freight Pulse: hot and cold freight zones by truck type, built from free data.
Called by build.py on every run. Standard library only.

Signals (each region x van/reefer/flatbed gets a 1-5 score):
  Driver reports      35%  readers tap Dead / Normal / Hot (needs 3+ this week)
  Rate trend          25%  median rate per loaded mile on opt-in load checks, this week vs last
  Load activity       15%  load checks from the region this week vs the usual
  USDA availability   15%  reefer only: USDA truck shortage/surplus by shipping district
  Seasonal pattern    10%  built-in calendar, always on, only nudges (2-4)
Signals without enough data are skipped and the rest re-weighted.

Driver reports and load checks come from the free Cloudflare Worker in
cloudflare-worker/. Until it's set up, the map runs on USDA + seasonal.
"""
import base64
import json
import os
import re
import statistics
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ================== SETTINGS ==================
# Your Cloudflare Worker address once it's set up, e.g. "https://freight-pulse.yourname.workers.dev"
FREIGHT_PULSE_URL = os.environ.get("FREIGHT_PULSE_URL", "")
# Free key from https://mymarketnews.ams.usda.gov/mymarketnews-api . Put it in GitHub:
# Settings > Secrets and variables > Actions > New repository secret, name USDA_API_KEY.
USDA_API_KEY = os.environ.get("USDA_API_KEY", "")
USDA_REPORT_ID = os.environ.get("USDA_TRUCK_REPORT_ID", "")   # optional; found automatically
USDA_REFRESH_HOURS = 12                                          # USDA updates about weekly; don't ask every run
# ==============================================

ROOT = Path(__file__).parent
DATA = ROOT / "data"
USDA_CACHE = DATA / "freight-pulse-usda.json"
OUT_JSON = DATA / "freight-pulse.json"
UA = "Mozilla/5.0 (compatible; OTRNewsBot/1.0; +https://otrnews.com)"

REGIONS = {
    "northeast":    ("Northeast",              ["ME", "NH", "VT", "MA", "RI", "CT", "NY", "NJ", "PA"]),
    "midatlantic":  ("Mid-Atlantic",           ["MD", "DE", "DC", "VA", "WV"]),
    "carolinas":    ("Carolinas",              ["NC", "SC"]),
    "southeast":    ("Southeast",              ["GA", "AL", "MS", "TN"]),
    "florida":      ("Florida",                ["FL"]),
    "ohioriver":    ("Ohio River",             ["OH", "KY", "IN"]),
    "greatlakes":   ("Great Lakes",            ["MI", "IL", "WI"]),
    "uppermidwest": ("Upper Midwest",          ["MN", "IA", "ND", "SD", "NE"]),
    "southcentral": ("South Central",          ["TX", "OK", "AR", "LA", "KS", "MO"]),
    "mountain":     ("Mountain West",          ["MT", "WY", "CO", "UT", "ID", "NM"]),
    "southwest":    ("California & Southwest", ["CA", "AZ", "NV"]),
    "pacificnw":    ("Pacific Northwest",      ["WA", "OR"]),
}
STATE_NAMES = {"AL": "Alabama", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut",
               "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "ID": "Idaho", "IL": "Illinois",
               "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
               "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
               "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
               "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
               "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
               "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}
STATE_REGION = {s: r for r, (_, states) in REGIONS.items() for s in states}
EQUIPMENT = ["van", "reefer", "flatbed"]
EQ_NAMES = {"van": "Dry van", "reefer": "Reefer", "flatbed": "Flatbed"}

WEIGHTS = {"drivers": .35, "rates": .25, "activity": .15, "usda": .15, "seasonal": .10}
MIN_REPORTS, MIN_CHECKS = 3, 5


# ---------- seasonal baseline (edit as you learn your readers' lanes) ----------
BUSY = {
    "reefer": [("florida", [12, 1, 2, 3, 4, 5]), ("southcentral", [11, 12, 1, 2, 3, 4, 5]),
               ("southwest", list(range(1, 13))), ("southeast", [5, 6, 7]), ("carolinas", [6, 7, 8]),
               ("pacificnw", [8, 9, 10, 11]), ("mountain", [9, 10, 11]), ("uppermidwest", [9, 10, 11]),
               ("greatlakes", [8, 9, 10])],
    "flatbed": [("*", [3, 4, 5, 6, 7, 8, 9, 10]), ("uppermidwest", [3, 4, 5]), ("southcentral", list(range(1, 13)))],
    "van": [("*", [9, 10, 11, 12])],
}
SLOW = {"flatbed": ([12, 1, 2], ["northeast", "greatlakes", "uppermidwest", "mountain", "ohioriver"]),
        "van": ([1, 2], ["*"])}


def seasonal_score(region, eq, month):
    s = 3.0
    for r, months in BUSY.get(eq, []):
        if r in ("*", region) and month in months:
            s += .5
    if eq in SLOW:
        months, regions = SLOW[eq]
        if month in months and ("*" in regions or region in regions):
            s -= 1
    return max(2.0, min(4.0, s))


# ---------- helpers ----------
def _get_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _level(score):
    if score is None:
        return "No data"
    if score >= 4.2: return "Hot"
    if score >= 3.4: return "Warm"
    if score > 2.6: return "Normal"
    if score > 1.8: return "Cool"
    return "Cold"


def iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


# ---------- USDA (reefer truck availability) ----------
AVAIL = [(r"slight\s*shortage", 4, "Slight shortage"), (r"shortage", 5, "Shortage"),
         (r"slight\s*surplus", 2, "Slight surplus"), (r"surplus", 1, "Surplus"), (r"adequate", 3, "Adequate")]
PLACE_HINTS = [(r"rio grande|lower valley|south texas", "TX"),
               (r"salinas|san joaquin|imperial|coachella|oxnard|santa maria|kern|central coast|sacramento", "CA"),
               (r"yuma|nogales", "AZ"), (r"yakima|wenatchee|columbia basin", "WA"),
               (r"upper valley|twin falls|snake river", "ID"), (r"red river valley", "ND"),
               (r"san luis valley", "CO"), (r"delmarva", "DE"), (r"vidalia", "GA")]


def _avail(v):
    if not isinstance(v, str):
        return None
    for pat, score, label in AVAIL:
        if re.search(pat, v, re.I):
            return score, label
    return None


def _district_state(text):
    if not text:
        return None
    for pat, st in PLACE_HINTS:
        if re.search(pat, text, re.I):
            return st
    for code, name in sorted(STATE_NAMES.items(), key=lambda kv: -len(kv[1])):
        if re.search(r"\b" + re.escape(name) + r"\b", text, re.I):
            return code
    return None


def _usda_regions(rows):
    """Find availability and district fields without assuming exact names (USDA varies them)."""
    by = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        av = None
        for k, v in row.items():
            if re.search(r"avail|trend|truck", k, re.I):
                av = _avail(v)
                if av:
                    break
        if not av:
            for v in row.values():
                av = _avail(v)
                if av:
                    break
        if not av:
            continue
        district = next((v for k, v in row.items()
                         if re.search(r"district|region|origin|location|loc_name|market", k, re.I) and isinstance(v, str)), None)
        reg = STATE_REGION.get(_district_state(district) or "")
        if reg:
            by.setdefault(reg, []).append(av)
    out = {}
    for reg, lst in by.items():
        s = sum(a for a, _ in lst) / len(lst)
        label = lst[0][1] if len(lst) == 1 else _level_usda(s) + f" (avg of {len(lst)} districts)"
        out[reg] = {"score": round(s, 2), "label": label}
    return out


def _level_usda(s):
    return "Shortage" if s >= 4.5 else "Slight shortage" if s >= 3.5 else "Adequate" if s > 2.5 else "Slight surplus" if s > 1.5 else "Surplus"


def refresh_usda():
    """Pull USDA at most every USDA_REFRESH_HOURS; keep the cached copy otherwise."""
    cache = {}
    try:
        cache = json.loads(USDA_CACHE.read_text())
    except Exception:
        pass
    fetched = cache.get("fetched")
    if fetched and datetime.now(timezone.utc) - datetime.fromisoformat(fetched) < timedelta(hours=USDA_REFRESH_HOURS):
        return cache
    if not USDA_API_KEY:
        return cache
    auth = {"Authorization": "Basic " + base64.b64encode(f"{USDA_API_KEY}:".encode()).decode()}
    base = "https://marsapi.ams.usda.gov/services/v1.2"
    try:
        rid = USDA_REPORT_ID
        if not rid:
            lst = _get_json(f"{base}/reports", auth)
            lst = lst if isinstance(lst, list) else lst.get("results", [])
            hit = next((r for r in lst if re.search(r"truck\s*rate", str(r.get("report_title") or r.get("report_name") or ""), re.I)), None)
            if not hit:
                raise RuntimeError("truck rate report not found; set USDA_TRUCK_REPORT_ID")
            rid = hit.get("slug_id") or hit.get("slug_name")
        data = _get_json(f"{base}/reports/{rid}?lastReports=1", auth, timeout=40)
        rows = data if isinstance(data, list) else data.get("results", [])
        regions = _usda_regions(rows)
        cache = {"fetched": datetime.now(timezone.utc).isoformat(), "report_id": rid,
                 "report_date": (rows[0].get("report_date") if rows and isinstance(rows[0], dict) else None),
                 "regions": regions, "rows": len(rows),
                 "sample_fields": sorted(rows[0].keys()) if rows and isinstance(rows[0], dict) else []}
        DATA.mkdir(exist_ok=True)
        USDA_CACHE.write_text(json.dumps(cache, indent=1))
        print(f"  freight pulse: USDA report {rid}, {len(regions)} regions from {len(rows)} rows")
        if rows and not regions:
            print(f"  freight pulse: USDA fields not matched, check sample_fields in {USDA_CACHE.name}")
    except Exception as e:
        print(f"  freight pulse: USDA skipped ({e.__class__.__name__}: {e})")
    # usable for 10 days even if a refresh fails
    if cache.get("fetched") and datetime.now(timezone.utc) - datetime.fromisoformat(cache["fetched"]) > timedelta(days=10):
        return {}
    return cache


# ---------- driver reports + load checks (Cloudflare Worker) ----------
def fetch_worker():
    if not FREIGHT_PULSE_URL:
        return {}
    try:
        return _get_json(FREIGHT_PULSE_URL.rstrip("/") + "/summary", timeout=20)
    except Exception as e:
        print(f"  freight pulse: worker skipped ({e.__class__.__name__}: {e})")
        return {}


# ---------- scoring ----------
def _rate_score(p):
    return 5 if p >= 4 else 4 if p >= 1.5 else 3 if p > -1.5 else 2 if p > -4 else 1


def _activity_score(r):
    return 5 if r >= 1.3 else 4 if r >= 1.1 else 3 if r > .9 else 2 if r > .7 else 1


def score_region(votes, checks, usda, seasonal):
    sig = {}
    n = votes.get("hot", 0) + votes.get("normal", 0) + votes.get("dead", 0)
    if n >= MIN_REPORTS:
        sig["drivers"] = (votes.get("hot", 0) * 5 + votes.get("normal", 0) * 3 + votes.get("dead", 0) * 1) / n
    now_n, prev_n = checks.get("n7", 0), checks.get("nprev", 0)
    med, medp = checks.get("med7"), checks.get("medprev")
    pct = None
    if now_n >= MIN_CHECKS and prev_n >= MIN_CHECKS and med and medp:
        pct = (med - medp) / medp * 100
        sig["rates"] = _rate_score(pct)
    ratio = None
    if now_n >= MIN_CHECKS and checks.get("weekly_avg", 0) > 0:
        ratio = now_n / checks["weekly_avg"]
        sig["activity"] = _activity_score(ratio)
    if usda:
        sig["usda"] = usda["score"]
    sig["seasonal"] = seasonal
    wsum = sum(WEIGHTS[k] for k in sig)
    score = round(sum(WEIGHTS[k] * v for k, v in sig.items()) / wsum, 2)
    return {"score": score, "level": _level(score), "basis": [k for k in sig if k != "seasonal"],
            "drivers": {"reports": n, "hot": votes.get("hot", 0), "normal": votes.get("normal", 0), "dead": votes.get("dead", 0)},
            "rates": ({"median": round(med, 2), "change": None if pct is None else round(pct, 1), "checks": now_n} if med and now_n else None),
            "activity": None if ratio is None else round(ratio, 2),
            "usda": usda["label"] if usda else None}


def build_data():
    now = datetime.now(timezone.utc)
    usda = refresh_usda()
    w = fetch_worker()
    out = {"updated": now.isoformat(), "week": iso_week(now), "usda_date": usda.get("report_date"),
           "reports": w.get("total_votes", 0), "checks7": w.get("total_checks7", 0),
           "live": bool(FREIGHT_PULSE_URL), "regions": {}}
    for reg in REGIONS:
        out["regions"][reg] = {}
        for eq in EQUIPMENT:
            out["regions"][reg][eq] = score_region(
                ((w.get("votes") or {}).get(reg) or {}).get(eq) or {},
                ((w.get("checks") or {}).get(reg) or {}).get(eq) or {},
                (usda.get("regions") or {}).get(reg) if eq == "reefer" else None,
                seasonal_score(reg, eq, now.month))
    DATA.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=1))
    return out


# ---------- page section ----------
FP_CSS = """<style>
.fp-seg{display:grid;grid-template-columns:repeat(3,1fr);gap:.35rem;padding:.3rem;margin:.6rem 0 1rem;background:var(--card);border:1px solid var(--line);border-radius:999px}
.fp-seg button{font:800 .95rem var(--font);padding:.55rem .3rem .45rem;border:0;border-radius:999px;background:none;color:var(--ink);cursor:pointer}
.fp-seg button[aria-pressed="true"]{background:var(--sign);color:#fff}
.fp-map{display:grid;grid-template-columns:repeat(12,1fr);gap:3px}
.fp-map button{aspect-ratio:1;border:0;border-radius:4px;padding:0;font:800 clamp(8px,2.3vw,12px) var(--font);cursor:pointer}
.fp-map button:disabled{opacity:.4;cursor:default}
.fp-map button.sel{box-shadow:inset 0 0 0 2px var(--ink)}
.fp-legend{display:flex;gap:4px;margin:.6rem 0 .1rem}.fp-legend span{flex:1;height:10px;border-radius:2px}
.fp-legend-l{display:flex;justify-content:space-between;font-size:.8rem;color:var(--muted)}
.fp-card{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:.9rem 1rem;margin:1rem 0}
.fp-card h3{margin:0;font-size:1.15rem}
.fp-top{display:flex;justify-content:space-between;align-items:baseline;gap:.5rem}
.fp-pill{border-radius:999px;padding:.1rem .7rem;font-weight:800;font-size:.9rem}
.fp-card dl{display:grid;grid-template-columns:1fr auto;gap:.3rem 1rem;margin:.6rem 0 0}.fp-card dt{color:var(--muted)}.fp-card dd{margin:0;font-weight:700;text-align:right}
.fp-rank{list-style:none;margin:0;padding:0}.fp-rank li{border-top:1px solid var(--line)}.fp-rank li:first-child{border-top:0}
.fp-rank button{all:unset;box-sizing:border-box;display:flex;gap:.6rem;align-items:center;width:100%;padding:.5rem 0;cursor:pointer}
.fp-rank button:focus-visible,.fp-map button:focus-visible{outline:3px solid var(--amber)}
.fp-dot{width:14px;height:14px;border-radius:3px;flex:none}.fp-rank .nm{flex:1}
.fp-vote label{display:block;font-weight:700;margin:.6rem 0 .25rem}
.fp-vote select{width:100%;font:600 1rem var(--font);padding:.5rem .6rem;border:1.5px solid var(--line);border-radius:8px;background:var(--paper);color:var(--ink)}
.fp-choices{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem}
.fp-choices button{font:800 1rem var(--font);padding:.7rem .3rem;border:2px solid var(--line);border-radius:10px;background:var(--paper);color:var(--ink);cursor:pointer}
.fp-choices button[aria-pressed="true"][data-r="1"]{background:#2D6AA8;border-color:#2D6AA8;color:#fff}
.fp-choices button[aria-pressed="true"][data-r="3"]{border-color:var(--ink)}
.fp-choices button[aria-pressed="true"][data-r="5"]{background:#CF4330;border-color:#CF4330;color:#fff}
.fp-vote .btn{border:0;cursor:pointer;font:800 1rem var(--font);margin-top:.8rem}.fp-vote .btn:disabled{opacity:.5;cursor:default}
</style>"""

_FP_JS = r"""<script>(function(){
var D=__DATA__,API=__API__,R=__REGIONS__,SN=__STATES__,EQ={van:'Dry van',reefer:'Reefer',flatbed:'Flatbed'};
var G={WA:[1,0],ID:[2,0],MT:[3,0],ND:[4,0],MN:[5,0],WI:[6,0],MI:[7,0],VT:[10,0],NH:[11,0],ME:[11,-1],
OR:[1,1],NV:[2,1],WY:[3,1],SD:[4,1],IA:[5,1],IL:[6,1],IN:[7,1],OH:[8,1],NY:[9,1],MA:[10,1],
CA:[1,2],UT:[2,2],CO:[3,2],NE:[4,2],MO:[5,2],KY:[6,2],WV:[7,2],PA:[8,2],NJ:[9,2],CT:[10,2],RI:[11,2],
AZ:[2,3],NM:[3,3],KS:[4,3],AR:[5,3],TN:[6,3],VA:[7,3],MD:[8,3],DE:[9,3],DC:[10,3],
OK:[4,4],LA:[5,4],MS:[6,4],AL:[7,4],NC:[8,4],SC:[9,4],TX:[4,5],GA:[8,5],FL:[9,6]};
var SR={};Object.keys(R).forEach(function(r){R[r][1].forEach(function(s){SR[s]=r;});});
var C=['#D9D7CF','#2D6AA8','#86B1D8','#E4E1D6','#F0A458','#CF4330'],I=['#58625C','#fff','#1B211E','#1B211E','#1B211E','#fff'];
var K={'No data':0,Cold:1,Cool:2,Normal:3,Warm:4,Hot:5},eq='van',sel=null,$=function(i){return document.getElementById(i);};
function el(t,a,x){var e=document.createElement(t);for(var k in a||{})e.setAttribute(k,a[k]);if(x!=null)e.textContent=x;return e;}
function g(r){return D.regions[r]&&D.regions[r][eq];}
var map=$('fp-map'),tiles={};
Object.keys(G).forEach(function(s){var b=el('button',{type:'button'},s);b.style.gridColumn=G[s][0]+1;b.style.gridRow=G[s][1]+2;
b.addEventListener('click',function(){sel=SR[s];draw();$('fp-detail').scrollIntoView({block:'nearest'});});map.appendChild(b);tiles[s]=b;});
function draw(){
document.querySelectorAll('.fp-seg button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.eq===eq);});
Object.keys(tiles).forEach(function(s){var d=g(SR[s]),l=d?d.level:'No data',k=K[l];tiles[s].style.background=C[k];tiles[s].style.color=I[k];
tiles[s].classList.toggle('sel',sel===SR[s]);tiles[s].setAttribute('aria-label',SN[s]+', '+R[SR[s]][0]+': '+l);});
var det=$('fp-detail');det.textContent='';
if(!sel){det.appendChild(el('p',{},'Tap a state to see its region.'));}else{
var d=g(sel),l=d?d.level:'No data',k=K[l],top=el('div',{class:'fp-top'});top.appendChild(el('h3',{},R[sel][0]));
var p=el('span',{class:'fp-pill'},l);p.style.background=C[k];p.style.color=I[k];top.appendChild(p);det.appendChild(top);
det.appendChild(el('p',{class:'fine'},EQ[eq]+' · '+R[sel][1].join(', ')));var dl=el('dl');function row(a,b){dl.appendChild(el('dt',{},a));dl.appendChild(el('dd',{},b));}
if(d){row('Driver reports this week',d.drivers.reports?String(d.drivers.reports):'None yet');
if(d.drivers.reports)row('Hot / Normal / Dead',d.drivers.hot+' / '+d.drivers.normal+' / '+d.drivers.dead);
if(d.rates){row('Typical rate offered','$'+d.rates.median.toFixed(2)+'/loaded mi');if(d.rates.change!=null)row('Change from last week',(d.rates.change>0?'+':'')+d.rates.change.toFixed(1)+'%');row('Loads checked this week',String(d.rates.checks));}
if(d.activity!=null)row('Load activity vs usual',Math.round(d.activity*100)+'%');if(eq==='reefer'&&d.usda)row('USDA truck availability',d.usda);}
det.appendChild(dl);var nm={drivers:'driver reports',rates:'rate trend',activity:'load activity',usda:'USDA data'};
det.appendChild(el('p',{class:'fine'},!d||!d.basis.length?'Based on the usual pattern for this time of year. Driver reports and load checks will sharpen it.':'Based on '+d.basis.map(function(b){return nm[b];}).join(', ')+', plus the seasonal pattern.'));}
$('fp-ranktitle').textContent='Hottest to coldest: '+EQ[eq];var rk=$('fp-rank');rk.textContent='';
Object.keys(R).sort(function(a,b){return (g(b)?g(b).score:0)-(g(a)?g(a).score:0);}).forEach(function(r){var d=g(r),l=d?d.level:'No data',li=el('li'),b=el('button',{type:'button'}),dot=el('span',{class:'fp-dot'});
dot.style.background=C[K[l]];b.appendChild(dot);b.appendChild(el('span',{class:'nm'},R[r][0]));b.appendChild(el('span',{class:'fine'},l));
b.addEventListener('click',function(){sel=r;draw();$('fp-detail').scrollIntoView({block:'nearest'});});li.appendChild(b);rk.appendChild(li);});}
document.querySelectorAll('.fp-seg button').forEach(function(b){b.addEventListener('click',function(){eq=b.dataset.eq;var v=$('fp-veq');if(v)v.value=eq;draw();});});
draw();
if(!API)return;
var dev;try{dev=localStorage.getItem('fp_device');}catch(e){}
if(!dev){dev=(window.crypto&&crypto.randomUUID)?crypto.randomUUID():Date.now()+'-'+Math.random().toString(16).slice(2)+Math.random().toString(16).slice(2);try{localStorage.setItem('fp_device',dev);}catch(e){}}
var st=$('fp-vstate'),ve=$('fp-veq'),send=$('fp-send'),msg=$('fp-msg'),rating=null;
Object.keys(SN).filter(function(s){return SR[s];}).sort(function(a,b){return SN[a]<SN[b]?-1:1;}).forEach(function(s){st.appendChild(el('option',{value:s},SN[s]));});
function pick(r){rating=r;document.querySelectorAll('.fp-choices button').forEach(function(b){b.setAttribute('aria-pressed',+b.dataset.r===r);});ok();}
function ok(){send.disabled=!(st.value&&rating);}
document.querySelectorAll('.fp-choices button').forEach(function(b){b.addEventListener('click',function(){pick(+b.dataset.r);});});st.addEventListener('change',ok);
fetch(API+'/my-vote?deviceId='+encodeURIComponent(dev)).then(function(r){return r.ok?r.json():null;}).then(function(v){if(!v)return;st.value=v.state;ve.value=v.equipment;pick(v.rating);send.textContent='Update my report';msg.textContent="You've already reported this week. Change it any time.";}).catch(function(){});
send.addEventListener('click',function(){send.disabled=true;msg.textContent='Sending…';
fetch(API+'/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({deviceId:dev,state:st.value,equipment:ve.value,rating:rating})})
.then(function(r){return r.json().then(function(j){return {ok:r.ok,j:j};});}).then(function(x){
msg.textContent=x.ok?'Report sent for '+SN[st.value]+', '+EQ[ve.value]+'. The map updates within 30 minutes.':(x.j.error||'Report not sent. Try again.');if(x.ok)send.textContent='Update my report';ok();})
.catch(function(){msg.textContent='Report not sent. Check your connection and try again.';ok();});});
})();</script>"""


def section_html(data):
    wk = data["week"].split("-W")
    upd = datetime.fromisoformat(data["updated"]).strftime("%b %-d at %H:%M UTC")
    src = f' Reefer truck availability from USDA Specialty Crops Truck Rate Report{", " + data["usda_date"] if data.get("usda_date") else ""}.' if data.get("usda_date") else ""
    counts = (f'{data["reports"]} driver report{"s" if data["reports"] != 1 else ""} this week · {data["checks7"]} loads checked in 7 days. '
              if data.get("live") else "")
    vote = ""
    if FREIGHT_PULSE_URL:
        vote = """<section class="fp-card fp-vote"><h3>How's freight where you are?</h3>
<p class="fine">One report per driver per week. You can change it until the week ends. No sign-in, nothing personal stored.</p>
<label for="fp-vstate">Your state</label><select id="fp-vstate"><option value="">Choose a state</option></select>
<label for="fp-veq">You pull</label><select id="fp-veq"><option value="van">Dry van</option><option value="reefer">Reefer</option><option value="flatbed">Flatbed</option></select>
<span style="display:block;font-weight:700;margin:.6rem 0 .25rem" id="fp-rlbl">Freight this week</span>
<div class="fp-choices" role="group" aria-labelledby="fp-rlbl"><button type="button" data-r="1" aria-pressed="false">Dead</button><button type="button" data-r="3" aria-pressed="false">Normal</button><button type="button" data-r="5" aria-pressed="false">Hot</button></div>
<button type="button" class="btn" id="fp-send" disabled>Send my report</button><p class="fine" id="fp-msg" role="status"></p></section>"""
    js = (_FP_JS.replace("__DATA__", json.dumps(data, separators=(",", ":")))
               .replace("__API__", json.dumps(FREIGHT_PULSE_URL.rstrip("/")))
               .replace("__REGIONS__", json.dumps({k: [v[0], v[1]] for k, v in REGIONS.items()}, separators=(",", ":")))
               .replace("__STATES__", json.dumps(STATE_NAMES, separators=(",", ":"))))
    return f"""<h2 class="section-title" id="freight-pulse">Freight Pulse: hot and cold zones</h2>
<p class="fine">Where freight is hot and where it's dead right now, by truck type. Week {wk[1]}. {counts}Updated {upd}.</p>
<div class="fp-seg" role="group" aria-label="Truck type"><button type="button" data-eq="van" aria-pressed="true">Dry van</button><button type="button" data-eq="reefer" aria-pressed="false">Reefer</button><button type="button" data-eq="flatbed" aria-pressed="false">Flatbed</button></div>
<div class="fp-map" id="fp-map" role="group" aria-label="Freight map by state. Tap a state to see its region."></div>
<div class="fp-legend" aria-hidden="true"><span style="background:#2D6AA8"></span><span style="background:#86B1D8"></span><span style="background:#E4E1D6"></span><span style="background:#F0A458"></span><span style="background:#CF4330"></span></div>
<div class="fp-legend-l"><span>Cold</span><span>Normal</span><span>Hot</span></div>
<section class="fp-card" id="fp-detail" aria-live="polite"></section>
<section class="fp-card"><h3 id="fp-ranktitle">Hottest to coldest</h3><ul class="fp-rank" id="fp-rank"></ul></section>
{vote}
<details class="fp-card"><summary><strong>How the score works</strong></summary>
<p class="fine">Each region gets a score from 1 (cold) to 5 (hot) for each truck type, from driver reports this week, the trend in rates offered on loads checked in our <a href="/tools/load-calculator/">load calculator</a>, how many loads were checked compared with usual, USDA truck availability for reefer, and the usual pattern for this time of year. Signals without enough data are left out. Scores are a planning guide, not a promise of loads.{src}</p></details>
{js}"""


def write_section():
    """Build the data and return (html, css) for the Road conditions page. Never breaks the build."""
    try:
        return section_html(build_data()), FP_CSS
    except Exception as e:
        print(f"  freight pulse: section skipped ({e.__class__.__name__}: {e})")
        return "", ""
