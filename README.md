# Walkersville Lions Boys Soccer · 2026

A family & friends site for the 2026 boys varsity and JV seasons: next game with countdown and
ticket links, latest-result highlights, full schedule/results, roster + coaches, and a searchable
photo catalog (filter by game, team, jersey number, or free-text search).

Plain static site in `site/`: no framework and no build step to view it.

## View
`python3 -m http.server -d site 8000` → http://localhost:8000 (or just open `site/index.html`)

## Where the data comes from
| What | Source | File |
|---|---|---|
| Games, times, varsity + JV scores, rosters, coaches | ArbiterLive team pages (auto) | fetched by `scripts/build.py` (URLs in `data/roster.json`) |
| Backup varsity league scores | MPSSAA scores API (auto) | fetched by `scripts/build.py` |
| GoFan ticket links, game notes, opponent mascots | hand-maintained | `data/schedule.json` |
| Coach bios | old lionssoccer.org staff page | `data/roster.json` |
| Photos | shared Google Drive, hand-picked | `scripts/cache/picks.txt` → `data/photos.json` |

## Update
```sh
python3 scripts/build.py                 # refresh games/scores/rosters + rebuild site/data.js (run after any data edit)
```

### Adding photos
1. `python3 scripts/drive_index.py <drive-folder-id> scripts/cache/drive.json`: index the Drive folders
2. Map any new folder to its game in `data/photo_folders.json`
3. Add picks to `scripts/cache/picks.txt` as `tag|jersey numbers|caption|featured`
   (tags come from the contact-sheet step; `cand.json` maps tag → Drive file)
4. `.venv/bin/python scripts/photos.py` downloads only the picks at web size (WebP), then run `build.py`

Pillow is needed for `photos.py`: `python3 -m venv .venv && .venv/bin/pip install pillow`

### Picking good photos
`scripts/curate/score.py` scores 320px previews for sharpness/exposure and collapses burst shots;
`scripts/curate/sheets.py` then builds numbered contact sheets of the top candidates per game for
eyeballing. The sheet tags (e.g. `02-41`) are what go in `picks.txt`.

## History section (`/history/`)
Program history since 1928: trophy case, great teams, coaches, a season-by-season timeline, a page per season
(`/history/1972`), stats (`/history/stats`: win % by season, coaching records, head-to-head, record book) and a
searchable list of every rostered player (`/history/players`).

- Data: `data/history.json`, hand-maintained. Seasons 1928-2019 were extracted from Spencer Shortt's history PDF on
  lionssoccer.org; 2020-2025 were pieced together from ArbiterLive (past seasons), walkersvillelions.com (scores and
  rosters), lionssoccer.org (team photos, 2024 roster) and MaxPreps. Game scores are Walkersville first; `est` marks a
  score the PDF filled in as 1-0/0-1/0-0, `pk` the result after penalty kicks, and `status: "partial"` a season with
  missing results.
- Photos: `site/history/img/<year>.webp` (1600px) with thumbnails in `img/t/`. Add a season's photo there and list it
  under the season's `photos`.
- Build: `python3 scripts/history.py` writes `site/history/*.html` (run it after editing the JSON). The nightly
  workflow doesn't touch these pages; the 2026 card and page read the live record from `site/data.js`.

## Hosting
Live at https://wvlions.com (www redirects to it). Cloudflare Pages project `wvlions`, connected to this repo:
it publishes `site/` on every push to `main`, with no build step. `.github/workflows/deploy.yml` runs nightly and on every
push: it refreshes games/scores with `scripts/build.py` and commits `site/data.js` (that commit is what Cloudflare
publishes). It also still deploys a copy to GitHub Pages (https://edwurtle.github.io/wvlions/). If ArbiterLive is
unreachable it deploys the last good data.
Refresh on demand: `gh workflow run deploy.yml`.

### NFHS Network affiliate links
Every nfhsnetwork.com watch/replay link (game streams from the NFHS search API and `links.watch` in `data/schedule.json`)
is wrapped by `affiliate()` in `scripts/build.py`, which routes it through the Impact tracking link for media property
wvlions.com (`AFFILIATE`). The site's Impact verification tag is in the `<head>` of `site/index.html`.

### Analytics
GoatCounter (cookie-free), dashboard at https://wvlions.goatcounter.com. The script tag is in the `<head>` of both pages;
page views are automatic, each photo opened in the lightbox counts as a view of `/photo/<id>`, and `app.js` (`track`)
records taps as events: `nfhs/replay`, `nfhs/live`, `nfhs/channel`, `tickets`, `directions`, `download/*`, `share`,
`calendar`, `drive`. GoatCounter ignores localhost.

### Photo URLs
`/photos[/varsity|jv][/<jersey #>][/<date>-<opponent>]` (e.g. `/photos/varsity/12/2026-10-15-south-carroll`) filters
the catalog; `/photo/<id>` opens one photo. Both are served by Cloudflare Pages functions in `functions/` (limited to
those paths by `site/_routes.json`, so images don't count against the free quota). `/photo/<id>` also gets link-preview
tags from `site/photo-meta.json`, which `build.py` writes. These paths only work on Cloudflare, not the GitHub Pages copy.
