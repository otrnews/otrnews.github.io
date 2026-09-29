# OTR News — auto-updating trucking news site

Every 30 minutes this site pulls the newest headlines from trucking news sources,
sorts them by topic (Regulations, Freight market, Fuel, Safety, Equipment, Drivers,
Business), and republishes otrnews.com. Stories stay on the archive for 30 days.
Nothing to run on your own computer, and hosting is free.

## What's in here

| File | What it does |
|---|---|
| `feeds.txt` | The news sources. Add or remove one per line. |
| `build.py` | Pulls the feeds and builds the site. |
| `template.html` | The page design. Edit wording or colors here. |
| `.github/workflows/update.yml` | The timer that rebuilds and publishes the site. |

## Go live (about 15 minutes, one time)

1. **Create a free GitHub account** at github.com if you don't have one.
2. **New repository** → name it `otrnews` → Public → Create.
3. **Upload the files**: on the repo page click *Add file → Upload files*, drag in
   everything from this folder (including the `.github` folder — on a Mac press
   Cmd+Shift+. to show hidden folders), then *Commit changes*.
4. **Turn on publishing**: *Settings → Pages → Build and deployment → Source:*
   choose **GitHub Actions**.
5. **Run it once**: *Actions* tab → *Update OTR News* → *Run workflow*. After ~1 minute
   your site is live at `https://<your-username>.github.io/otrnews/`.
6. **Connect otrnews.com**: *Settings → Pages → Custom domain* → type `otrnews.com` → Save.
   Then at your domain registrar, set these DNS records:
   - `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `CNAME` record for `www` → `<your-username>.github.io`

   DNS can take up to a day. Once the domain shows as verified, tick **Enforce HTTPS**.

From then on it updates itself every 30 minutes.

## Changing things

- **Add a source**: edit `feeds.txt` on GitHub (pencil icon), add `Name | feed URL`, commit.
  The site rebuilds right away.
- **Change the tagline**: edit `TAGLINE` near the top of `build.py`.
- **Update speed**: change the `cron` line in the workflow (`*/15 * * * *` = every 15 min).
- **See what happened on a run**: *Actions* tab → click a run. Sources that were down
  show as `skip`; the site still publishes with the rest.

## Notes

- The site shows headlines, a short excerpt, and links to the original article —
  the standard way news aggregators work. It doesn't copy full articles.
- GitHub pauses scheduled runs on repos with no activity for 60 days. The archive
  commits the site makes each run count as activity, so this shouldn't happen, but if
  updates ever stop, open *Actions* and re-enable the workflow.
