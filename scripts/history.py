"""Build the history section (site/history/) from data/history.json.

Writes the main page (trophy case, great teams, coaches, season timeline), one page per season (/history/<year>),
the stats page (win % by season, coaches, head-to-head, record book) and the players page (every rostered name, searchable).
The current season's page and card read the live record from site/data.js, so the nightly refresh keeps them current.
Run after any edit to data/history.json:  python3 scripts/history.py
"""
import datetime
import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "history"
CURRENT = 2026
CONTACT = "edwurtle@gmail.com"  # where missing photos, scores and records get sent
HONORS = ["State Champions", "State Finalist", "Region Champions", "Region Finalist", "County Champions", "County Finalist",
          "Division Champions"]
BIG = {"State Champions", "Region Champions"}  # gold chips; everything else is outlined
GREAT = [1928, 1972, 1975, 1982, 2004, 2018]  # featured on the main page

esc = html.escape


def rec_str(r):
    return f"{r[0]}-{r[1]}-{r[2]}" if r else "—"


def pct(r):
    n = sum(r)
    return (r[0] + r[2] / 2) / n if n else None


def results(games):
    """W/L/T per game; a game settled on penalty kicks counts the way the PDF counted it."""
    for g in games:
        if g.get("gf") is None:
            yield g, None
        else:
            yield g, g.get("pk") or ("W" if g["gf"] > g["ga"] else "L" if g["gf"] < g["ga"] else "T")


def load():
    data = json.loads((ROOT / "data" / "history.json").read_text())
    seasons = sorted(data["seasons"], key=lambda s: s["year"])
    return data, seasons


def stats(data, seasons):
    honors = {h: [s["year"] for s in seasons if h in s.get("titles", [])] for h in HONORS}
    total = [0, 0, 0]
    gf = ga = 0
    for s in seasons:
        if s.get("record") and s.get("status") != "partial":
            total = [a + b for a, b in zip(total, s["record"])]
    eras = []
    for c in data["coaches"]:
        end = c["end"] or CURRENT
        ss = [s for s in seasons if c["start"] <= s["year"] <= end and s["year"] < CURRENT]
        r = [0, 0, 0]
        for s in ss:
            if s.get("record") and s.get("status") != "partial":
                r = [a + b for a, b in zip(r, s["record"])]
        titles = [(t, s["year"]) for s in ss for t in s.get("titles", [])]
        eras.append(dict(c, end=end, record=r if sum(r) else None, titles=titles,
                         years=f"{c['start']}" + (f"–{c['end']}" if c["end"] != c["start"] else "") if c["end"] else f"{c['start']}–"))
    h2h = defaultdict(lambda: dict(w=0, l=0, t=0, gf=0, ga=0, est=0, first=9999, last=0, best=None))
    for s in seasons:
        for g, res in results(s.get("games", [])):
            if res is None or g["opp"] in ("Unknown", "Region playoff opponent"):
                continue
            o = h2h[g["opp"]]
            o[res.lower()] += 1
            o["first"], o["last"] = min(o["first"], s["year"]), max(o["last"], s["year"])
            if g.get("est"):
                o["est"] += 1
            else:
                o["gf"] += g["gf"]
                o["ga"] += g["ga"]
                if g["gf"] > g["ga"] and (not o["best"] or g["gf"] - g["ga"] > o["best"][0] - o["best"][1]):
                    o["best"] = (g["gf"], g["ga"], s["year"])
    players = defaultdict(list)
    for s in seasons + [dict(year=CURRENT, players=current_roster())]:
        for p in s.get("players", []):
            seen = next((x for x in players[p["name"]] if x["y"] == s["year"]), None)  # a few rosters list a name twice
            if seen:
                seen["c"] |= 1 if p.get("captain") else 0
            else:
                players[p["name"]].append(dict(y=s["year"], c=1 if p.get("captain") else 0, n=p.get("num", "")))
    return dict(honors=honors, total=total, eras=eras, h2h=dict(h2h), players=dict(players))


# ---------- page shell ----------

STAMP = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
NAV = [("./", "History", "index"), ("stats", "Stats", "stats"), ("players", "Players", "players")]


def page(title, desc, body, active="", scripts=""):
    nav = "".join(f'<a href="{href}"{" aria-current=page" if key == active else ""}>{label}</a>' for href, label, key in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0a1433">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="../favicon.ico?v=2" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32.png?v=2">
<link rel="apple-touch-icon" href="../img/apple-touch-icon.png?v=2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../styles.css?v={STAMP}">
<link rel="stylesheet" href="history.css?v={STAMP}">
<script data-goatcounter="https://wvlions.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</head>
<body class="hist" data-page="{active or 'season'}">

<header class="top">
  <div class="wrap">
    <a class="brand" href="/"><img class="ball" src="../img/w-logo.svg" alt="Walkersville W"><span>Lions Soccer<small>wvlions.com</small></span></a>
    <nav class="nav">
      {nav}
      <a class="cta" href="/">{CURRENT} Season</a>
    </nav>
  </div>
</header>

{body}

<footer>
  <div class="wrap">
    <div><b>WV Lions</b> · <a href="https://wvlions.com">wvlions.com</a><br>Walkersville boys soccer history, 1928 to today. Not an official school site.</div>
    <div>Seasons through 2019 researched and compiled by Spencer Shortt, WHS class of 2018:
      <a href="https://www.lionssoccer.org/_docs/The%20History%20of%20Walkersville%20HS%20Boys%20Soccer.pdf" target="_blank" rel="noopener">the original history (PDF, 40 MB)</a>.
      <br>Have a photo, roster or score from a missing season? Email <a href="mailto:{CONTACT}?subject=Lions%20soccer%20history">{CONTACT}</a>.</div>
  </div>
</footer>

<div class="h-lb" id="h-lb" hidden><button type="button" aria-label="Close">×</button><img alt=""><p></p></div>
{scripts}<script src="history.js?v={STAMP}"></script>
</body>
</html>
"""


# ---------- pieces ----------

def chips(titles, linked_year=None):
    out = []
    for t in titles:
        cls = "chip big" if t in BIG else "chip"
        out.append(f'<span class="{cls}">{esc(t)}</span>')
    return "".join(out)


def thumb(s, cls="thumb"):
    p = (s.get("photos") or [None])[0]
    if not p:
        return f'<div class="{cls} none"><span>No team photo</span></div>'
    return f'<div class="{cls}"><img src="img/t/{p["src"]}" alt="{s["year"]} Walkersville boys soccer team" loading="lazy"></div>'


def season_card(s, partial_label=True):
    y = s["year"]
    if s.get("end"):  # gap years with nothing recorded
        return f"""<div class="card gap" id="y{y}"><div class="yr">{y}–{str(s['end'])[2:]}</div>
  <p>{esc(s['notes'][0])}</p></div>"""
    r = s.get("record")
    status = s.get("status")
    rec = (f'<b class="rec">{rec_str(r)}</b>' if r and status != "partial"
           else f'<b class="rec dim">{esc(s["reported"].split(" (")[0]) if s.get("reported") else "Record unknown"}</b>')
    sub = []
    if s.get("coach") and s["coach"] not in ("Unknown", "Unconfirmed"):
        sub.append(esc(s["coach"]))
    if r and s.get("gf") is not None and status != "partial" and not s.get("goals_est"):
        sub.append(f'{s["gf"]} GF · {s["ga"]} GA')
    if status == "partial":
        sub.append("partial results")
    title_cls = " champ" if "State Champions" in s.get("titles", []) else ""
    return f"""<a class="card{title_cls}" id="y{y}" href="{y}">
  {thumb(s)}
  <div class="body">
    <div class="row"><span class="yr">{y}</span>{rec}</div>
    <div class="meta">{' · '.join(sub)}</div>
    {f'<div class="chips">{chips(s["titles"])}</div>' if s.get("titles") else ''}
  </div>
</a>"""


TROPHY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4h8v5a4 4 0 0 1-8 0V4z"/><path d="M8 6H5a2 2 0 0 0 0 4c1 0 2-.5 3-1M16 6h3a2 2 0 0 1 0 4c-1 0-2-.5-3-1"/><path d="M12 13v4M8.5 20h7M9.5 17h5v3h-5z"/></svg>'


def index_page(data, seasons, st):
    by = {s["year"]: s for s in seasons}
    t = st["total"]
    h = st["honors"]
    tiles = [("First season", "1928", "State champions that year"),
             ("State titles", str(len(h["State Champions"])), " · ".join(map(str, h["State Champions"]))),
             ("Region titles", str(len(h["Region Champions"])), " · ".join(map(str, h["Region Champions"]))),
             ("All-time wins", str(t[0]), f"{rec_str(t)} in recorded seasons")]
    tiles_html = "".join(f'<div class="record"><span>{a}</span><b>{b}</b><small>{c}</small></div>' for a, b, c in tiles)

    trophies = []
    for name in HONORS:
        ys = h[name]
        if not ys:
            continue
        links = "".join(f'<a href="{y}">{y}</a>' for y in ys)
        trophies.append(f"""<div class="trophy{' gold' if name == 'State Champions' else ' medal' if name in BIG else ''}">
  <div class="ic">{TROPHY}</div>
  <div><div class="n">{len(ys)}<span>{esc(name)}</span></div><div class="yrs">{links}</div></div>
</div>""")

    greats = []
    for y in GREAT:
        s = by[y]
        p = (s.get("photos") or [None])[0]
        bg = f' style="background-image:url(img/t/{p["src"]})"' if p else ""
        greats.append(f"""<a class="great" href="{y}">
  <div class="ph{'' if p else ' none'}"{bg}>{'' if p else '<span>No photo found</span>'}</div>
  <div class="body">
    <div class="row"><span class="yr">{y}</span><b class="rec">{rec_str(s.get("record")) if s.get("record") else "Record unknown"}</b></div>
    <div class="chips">{chips(s.get("titles", []))}</div>
    <p>{esc(s.get("story", ""))}</p>
  </div>
</a>""")

    eras = []
    for e in st["eras"]:
        if e["name"] in ("Unknown", "Unconfirmed") and not e["titles"]:
            continue
        cur = e["end"] == CURRENT
        r = e["record"]
        ts = sorted({t for t, _ in e["titles"] if t in BIG or t == "State Finalist"}, key=HONORS.index)
        title_line = " · ".join(f"{sum(1 for x, _ in e['titles'] if x == t)}× {t}" for t in ts)
        eras.append(f"""<div class="era{' now' if cur else ''}">
  <div class="yrs">{e['years']}</div>
  <h3>{esc(e['name'])}</h3>
  <div class="rec" {'data-live="record"' if cur else ''}>{rec_str(r) if r else ('2026 season' if cur else 'Record not recorded')}</div>
  {f'<div class="t">{title_line}</div>' if title_line else ''}
  {f'<p>{esc(e["note"])}</p>' if e.get('note') else ''}
</div>""")

    decades = defaultdict(list)
    for s in seasons:
        decades[s["year"] // 10 * 10].append(s)
    decades[CURRENT // 10 * 10].append(dict(year=CURRENT, current=True))
    jump = "".join(f'<a href="#d{d}">{d}s</a>' for d in sorted(decades))
    tl = []
    for d in sorted(decades):
        cards = []
        for s in decades[d]:
            if s.get("current"):
                cards.append(f"""<a class="card now" id="y{CURRENT}" href="/">
  <div class="thumb live"><span>Now playing</span></div>
  <div class="body"><div class="row"><span class="yr">{CURRENT}</span><b class="rec" data-live="record">In progress</b></div>
  <div class="meta">Zach Hommey · current season, live from the schedule</div><div class="chips"><span class="chip big">Season in progress</span></div></div>
</a>""")
            else:
                cards.append(season_card(s))
        tl.append(f'<section class="decade" id="d{d}"><h3 class="dh">{d}s</h3><div class="cards">{"".join(cards)}</div></section>')

    body = f"""<section class="hero h-hero">
  <div class="hero-bg" style="background-image:url(img/1972.webp)"></div>
  <div class="wrap">
    <div>
      <div class="eyebrow">Walkersville High School · Boys Soccer · Since 1928</div>
      <h1>Lions <span>History</span></h1>
      <p class="lead">Nearly a century of Walkersville boys soccer: two state championships, four region titles, a dozen county crowns, and every season we could find.</p>
      <div class="records">{tiles_html}</div>
    </div>
  </div>
</section>

<section class="block" id="trophies">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">Trophy case</div><h2>Championships</h2></div>
      <p>Tap a year to open that season.</p></div>
    <div class="trophies">{''.join(trophies)}</div>
  </div>
</section>

<section class="block alt" id="greats">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">The best of the Lions</div><h2>Great Teams</h2></div></div>
    <div class="greats">{''.join(greats)}</div>
  </div>
</section>

<section class="block" id="coaches">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">On the sideline</div><h2>Head Coaches</h2></div>
      <a class="btn ghost" href="stats#coaches">Coaching records →</a></div>
    <div class="eras">{''.join(eras)}</div>
  </div>
</section>

<section class="block alt" id="timeline">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">Every season</div><h2>Timeline</h2>
      <p>Records are wins-losses-ties. Tap a season for the team photo, roster and every score.</p></div></div>
  </div>
  <nav class="jump" aria-label="Jump to decade"><div class="wrap">{jump}</div></nav>
  <div class="wrap">{''.join(tl)}</div>
</section>

<section class="block" id="more">
  <div class="wrap more">
    <a class="morecard" href="stats"><div class="eyebrow">Stats</div><h3>Records &amp; rivalries</h3><p>Win % by season, every coach, the record book, and how the Lions have fared against {len(st['h2h'])} opponents.</p><span>Open stats →</span></a>
    <a class="morecard" href="players"><div class="eyebrow">Players</div><h3>Find a Lion</h3><p>Search {len(st['players']):,} names from every roster we have, 1928 to today. Look up a parent, grandparent or old teammate.</p><span>Search players →</span></a>
  </div>
</section>"""
    return page("Lions History · Walkersville Boys Soccer", "The history of Walkersville High School boys soccer since 1928: championships, great teams, coaches and every season.",
                body, "index", '<script src="../data.js?v=' + STAMP + '"></script>\n')


def season_page(s, prev, nxt, st):
    y = s["year"]
    r = s.get("record")
    status = s.get("status")
    tiles = []
    if r and status != "partial":
        tiles.append(("Record", rec_str(r), "wins · losses · ties"))
        if s.get("gf") is not None:
            tiles.append(("Goals for", str(s["gf"]), "estimated" if s.get("goals_est") else ""))
            tiles.append(("Goals against", str(s["ga"]), "estimated" if s.get("goals_est") else ""))
    elif s.get("reported"):
        tiles.append(("Reported", s["reported"].split(" (")[0], s["reported"].split(" (")[1].rstrip(")") if " (" in s["reported"] else ""))
    else:
        tiles.append(("Record", "Unknown", "not yet found"))
    tiles_html = "".join(f'<div class="record"><span>{a}</span><b>{b}</b><small>{c}</small></div>' for a, b, c in tiles)
    nav = (f'<a href="{prev}">← {prev}</a>' if prev else "<span></span>") + (f'<a href="{nxt}">{nxt} →</a>' if nxt else "")

    photos = s.get("photos", [])
    ph_html = "".join(f"""<figure class="tp"><button type="button" data-full="img/{p['src']}" data-cap="{esc(p.get('caption') or f'{y} team')}">
  <img src="img/{p['src']}" alt="{esc(p.get('caption') or f'{y} Walkersville boys soccer team')}" loading="lazy" width="{p.get('w', '')}" height="{p.get('h', '')}"></button>
  {f'<figcaption>{esc(p["caption"])}</figcaption>' if p.get('caption') else ''}</figure>""" for p in photos)
    if not photos:
        ph_html = '<div class="nophoto">No team photo has been found for this season.</div>'

    roster = ""
    if s.get("roster"):
        rows = "".join(f'<li>{f"<b>{esc(row["label"])}:</b> " if row["label"] else ""}{esc(", ".join(row["names"]))}</li>' for row in s["roster"] if row["names"])
        roster = f'<div class="rows"><h3>Team photo, left to right{" (partial)" if s.get("roster_partial") else ""}</h3><ul>{rows}</ul></div>'
    elif s.get("players"):
        roster = f'<div class="rows"><h3>Roster</h3>{player_list(s["players"])}</div>'

    staff = ""
    if s.get("staff"):
        staff = '<div class="staff">' + "".join(f'<span><b>{esc(x["name"])}</b> {esc(x["role"])}</span>' for x in s["staff"]) + "</div>"

    callouts = ""
    if s.get("story"):
        callouts += f'<div class="story">{esc(s["story"])}</div>'
    for n in s.get("notes", []):
        callouts += f'<div class="note">{esc(n)}</div>'
    if s.get("school_records"):
        callouts += '<div class="srec"><h3>School records set</h3><ul>' + "".join(f"<li>{esc(x)}</li>" for x in s["school_records"]) + "</ul></div>"

    games = ""
    if s.get("games"):
        rows = []
        est_any = False
        dated = any(g.get("date") for g in s["games"])
        for g, res in results(s["games"]):
            when = datetime.date.fromisoformat(g["date"]).strftime("%b %-d") if g.get("date") else ""
            if res is None:
                score = '<span class="res none">Score not found</span>'
            else:
                est_any = est_any or g.get("est")
                score = f'<span class="res {res}"><i>{res}</i>{g["gf"]}–{g["ga"]}{"*" if g.get("est") else ""}</span>'
            tags = []
            if g.get("playoff"):
                tags.append('<span class="pill">Playoff</span>')
            if g.get("note"):
                tags.append(f'<span class="gnote">{esc(g["note"])}</span>')
            rows.append(f'<li>{f"<span class=d>{when}</span>" if dated else ""}<span class="o">{esc(g["opp"])}</span>{score}<span class="x">{"".join(tags)}</span></li>')
        foot = '<p class="fine">* Score not recorded. The PDF counts these as 1-0 wins, 0-1 losses or 0-0 ties.</p>' if est_any else ""
        games = f'<section class="games"><h2>Results</h2><ul class="glist{"" if dated else " nodate"}">{"".join(rows)}</ul>{foot}</section>'
    elif r:
        games = '<section class="games"><h2>Results</h2><p class="fine">The season record survives, but game-by-game scores haven’t been found.</p></section>'

    src = {"pdf": "The History of Walkersville HS Boys Soccer (Spencer Shortt, 2020)"}.get(s.get("source"), s.get("source", ""))
    coach = {"Unknown": "Head coach unknown", "Unconfirmed": "Head coach unconfirmed", None: "Head coach unknown"}.get(s.get("coach"), s.get("coach"))
    body = f"""<section class="s-hero">
  <div class="wrap">
    <div class="crumbs"><a href="./">History</a> / <a href="./#d{y // 10 * 10}">{y // 10 * 10}s</a></div>
    <div class="s-top">
      <div>
        <h1>{y}</h1>
        <div class="s-coach">{esc(coach)}</div>
        {f'<div class="chips">{chips(s["titles"])}</div>' if s.get("titles") else ''}
      </div>
      <div class="records">{tiles_html}</div>
    </div>
    <div class="pn">{nav}</div>
  </div>
</section>

<section class="block s-body">
  <div class="wrap">
    <div class="s-grid">
      <div class="s-photo">{ph_html}{roster}{staff}</div>
      <div class="s-side">{callouts}{games}</div>
    </div>
    <p class="src">Source: {esc(src)}</p>
  </div>
</section>"""
    return page(f"{y} Lions Soccer · History", f"The {y} Walkersville boys soccer season: record, roster and results.", body)


def current_roster():
    """This season's varsity roster from data/roster.json (the same list the home page uses)."""
    roster = json.loads((ROOT / "data" / "roster.json").read_text())
    return [dict(name=p["name"], num=str(p["num"]), cls=p.get("grade") or "") for p in roster["players"]["varsity"]]


def player_list(players):
    def pl(p):
        bits = [p.get("num") and f'<i>{esc(p["num"])}</i>', esc(p["name"]),
                p.get("cls") and f'<small>{esc(p["cls"])}</small>', p.get("grad") and f'<small>’{str(p["grad"])[2:]}</small>']
        return f'<li><a href="players?q={esc(p["name"])}">{"".join(b for b in bits if b)}</a></li>'
    ordered = sorted(players, key=lambda p: (len(p.get("num") or "zz"), p.get("num") or "zz"))
    return f'<ul class="plist">{"".join(pl(p) for p in ordered)}</ul>'


def current_page(prev):
    body = f"""<section class="s-hero">
  <div class="wrap">
    <div class="crumbs"><a href="./">History</a> / <a href="./#d{CURRENT // 10 * 10}">{CURRENT // 10 * 10}s</a></div>
    <div class="s-top">
      <div><h1>{CURRENT}</h1><div class="s-coach">Zach Hommey</div><div class="chips"><span class="chip big">Season in progress</span></div></div>
      <div class="records"><div class="record"><span>Varsity record</span><b data-live="record">—</b><small data-live="gfga"></small></div></div>
    </div>
    <div class="pn"><a href="{prev}">← {prev}</a><a href="/">Full {CURRENT} season →</a></div>
  </div>
</section>
<section class="block s-body">
  <div class="wrap">
    <div class="s-grid">
      <div class="s-photo"><div class="rows"><h3>Varsity roster</h3>{player_list(current_roster())}</div></div>
      <div class="s-side"><section class="games"><h2>Results so far</h2><ul class="glist" data-live="games"></ul>
        <p class="fine">Live from the <a href="/">{CURRENT} season page</a>, which has photos, the full schedule and both teams.</p></section></div>
    </div>
  </div>
</section>"""
    return page(f"{CURRENT} Lions Soccer · History", f"The {CURRENT} Walkersville boys soccer season so far.", body, "",
                '<script src="../data.js?v=' + STAMP + '"></script>\n')


def chart(seasons, eras, honors):
    """Win % by season as an inline SVG bar chart, coaching eras shaded behind."""
    first, last = 1928, CURRENT - 1
    W, H, L, R, T, B = 1100, 300, 40, 10, 34, 28
    n = last - first + 1
    sw = (W - L - R) / n
    y = lambda v: T + (1 - v) * (H - T - B)
    by = {s["year"]: s for s in seasons}
    out = [f'<svg class="wchart" viewBox="0 0 {W} {H}" role="img" aria-label="Win percentage by season, 1928 to {last}">']
    for i, e in enumerate(eras):
        x0 = L + (max(e["start"], first) - first) * sw
        x1 = L + (min(e["end"], last) - first + 1) * sw
        if x1 <= x0:
            continue
        if i % 2 == 0:
            out.append(f'<rect class="band" x="{x0:.1f}" y="{T - 22}" width="{x1 - x0:.1f}" height="{H - T - B + 22}"/>')
        label = e["name"].split()[-1] if e["name"] not in ("Unknown", "Unconfirmed") else ""
        if label and x1 - x0 > 44:
            out.append(f'<text class="era" x="{(x0 + x1) / 2:.1f}" y="{T - 8}" text-anchor="middle">{esc(label)}</text>')
    for v in (0, .25, .5, .75, 1):
        out.append(f'<line class="{"mid" if v == .5 else "grid"}" x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                   f'<text class="ax" x="{L - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{int(v * 100)}%</text>')
    for yr in range(first, last + 1, 10):
        out.append(f'<text class="ax" x="{L + (yr - first + .5) * sw:.1f}" y="{H - 8}" text-anchor="middle">{yr}</text>')
    for yr in range(first, last + 1):
        s = by.get(yr)
        x = L + (yr - first) * sw
        r = s.get("record") if s and s.get("status") != "partial" else None
        p = pct(r) if r else None
        titles = (s or {}).get("titles", [])
        tip = f"{yr} · {rec_str(r)} ({p:.0%})" if p is not None else f"{yr} · no record found"
        if titles:
            tip += " · " + ", ".join(titles)
        if p is not None:
            top = y(max(p, .012))
            out.append(f'<path class="bar" d="M{x + 1:.1f},{y(0):.1f}V{top + 2:.1f}q0,-2 2,-2h{sw - 6:.1f}q2,0 2,2V{y(0):.1f}z"/>')
            if "State Champions" in titles or "Region Champions" in titles:
                big = "State Champions" in titles
                out.append(f'<circle class="ttl{" st" if big else ""}" cx="{x + sw / 2:.1f}" cy="{top - 8:.1f}" r="{4.5 if big else 3.5}"/>')
        else:
            out.append(f'<rect class="nodata" x="{x + 1:.1f}" y="{y(0) - 3:.1f}" width="{sw - 2:.1f}" height="3"/>')
            if "State Champions" in titles:  # 1928: a state title with no surviving record
                out.append(f'<circle class="ttl st" cx="{x + sw / 2:.1f}" cy="{y(0) - 14:.1f}" r="4.5"/>')
        out.append(f'<rect class="hit" x="{x:.1f}" y="{T}" width="{sw:.1f}" height="{H - T - B}" data-tip="{esc(tip)}"><title>{esc(tip)}</title></rect>')
    out.append("</svg>")
    return "".join(out)


def stats_page(data, seasons, st):
    t = st["total"]
    done = [s for s in seasons if s.get("record") and s.get("status") != "partial" and s["year"] < CURRENT]
    gf = sum(s.get("gf", 0) for s in done if not s.get("goals_est"))
    ga = sum(s.get("ga", 0) for s in done if not s.get("goals_est"))
    tiles = [("All-time record", rec_str(t), f"{pct(t):.1%} win rate"), ("Seasons with a record", str(len(done)), f"of {CURRENT - 1928} since 1928"),
             ("Winning seasons", str(sum(1 for s in done if s["record"][0] > s["record"][1])), "more wins than losses"),
             ("Unbeaten seasons", str(len(unbeaten := [s["year"] for s in done if s["record"][1] == 0])), " · ".join(map(str, unbeaten)))]
    tiles_html = "".join(f'<div class="record"><span>{a}</span><b>{b}</b><small>{c}</small></div>' for a, b, c in tiles)

    crow = []
    for e in st["eras"]:
        r = e["record"]
        if not r and e["name"] in ("Unconfirmed",):
            continue
        n = len([s for s in done if e["start"] <= s["year"] <= e["end"]])
        big = [f"{y} {t.replace(' Champions', '').replace('Finalist', 'finalist')}" for t, y in e["titles"] if t in BIG or t == "State Finalist"]
        crow.append(f"""<tr><td><b>{esc(e['name'])}</b></td><td>{e['years']}</td><td class="num">{n or '—'}</td><td class="num">{rec_str(r) if r else '—'}</td>
  <td class="num">{f'{pct(r):.3f}'.lstrip('0') if r else '—'}</td><td class="t">{esc(' · '.join(big)) or ''}</td></tr>""")

    hrows = []
    for opp, o in sorted(st["h2h"].items(), key=lambda kv: -(kv[1]["w"] + kv[1]["l"] + kv[1]["t"])):
        gp = o["w"] + o["l"] + o["t"]
        p = (o["w"] + o["t"] / 2) / gp
        best = f'{o["best"][0]}-{o["best"][1]} ({o["best"][2]})' if o["best"] else "—"
        span = f'{o["first"]}' + (f'–{o["last"]}' if o["last"] != o["first"] else "")
        hrows.append(f"""<tr data-opp="{esc(opp.lower())}"><td data-v="{esc(opp)}"><b>{esc(opp)}</b></td><td class="num" data-v="{gp}">{gp}</td>
  <td class="num" data-v="{o['w']}">{o['w']}</td><td class="num" data-v="{o['l']}">{o['l']}</td><td class="num" data-v="{o['t']}">{o['t']}</td>
  <td class="num" data-v="{p:.4f}"><span class="bar-in" style="--p:{p * 100:.0f}%"></span>{f'{p:.3f}'.lstrip('0') if p < 1 else '1.000'}</td>
  <td class="num" data-v="{o['gf'] - o['ga']}">{o['gf']}–{o['ga']}</td><td data-v="{o['last']}">{span}</td><td class="num">{best}</td></tr>""")

    groups = defaultdict(list)
    for r in data["record_book"]:
        groups[r["group"]].append(r)
    book = "".join(f"""<div class="bookgrp"><h3>{esc(g)}</h3>{''.join(f'<div class="rb"><b>{esc(r["value"])}</b><div><span>{esc(r["label"])}</span><small>{esc(" · ".join(x for x in (r["who"], r["year"]) if x))}</small></div></div>' for r in rs)}</div>"""
                   for g, rs in groups.items())

    best = sorted([s for s in done if sum(s["record"]) >= 8], key=lambda s: (-pct(s["record"]), -s["record"][0]))[:10]
    brows = "".join(f'<li><a href="{s["year"]}"><b>{s["year"]}</b><span>{rec_str(s["record"])}</span><em>{pct(s["record"]):.3f}</em><small>{esc(s["coach"] if s["coach"] not in ("Unknown",) else "")}</small></a></li>'.replace("<em>0.", "<em>.").replace("<em>1.000", "<em>1.000") for s in best)
    goals = sorted([s for s in done if s.get("gf") is not None and not s.get("goals_est")], key=lambda s: -s["gf"])[:10]
    grows = "".join(f'<li><a href="{s["year"]}"><b>{s["year"]}</b><span>{s["gf"]} goals</span><em>{s["gf"] / sum(s["record"]):.1f}/gm</em><small>{rec_str(s["record"])}</small></a></li>' for s in goals)

    body = f"""<section class="ph-hero h-sub">
  <div class="wrap">
    <div class="eyebrow">Lions History</div>
    <h1>Stats &amp; Records</h1>
    <p>Every recorded season since 1928. Records count games settled on penalty kicks as wins or losses, the way the original history does.</p>
    <div class="records">{tiles_html}</div>
  </div>
</section>

<section class="block">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">Win % by season</div><h2>Ups &amp; Downs</h2>
      <p>Bars are win percentage (ties count half). Shaded bands are coaching eras. <span class="key"><i class="k st"></i>State champions <i class="k rg"></i>Region champions <i class="k nd"></i>No record found</span></p></div></div>
    <div class="chartbox"><div class="chart-scroll">{chart(seasons, st['eras'], st['honors'])}</div><div class="tip" hidden></div></div>
  </div>
</section>

<section class="block alt" id="coaches">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">By coach</div><h2>Coaching Records</h2>
      <p>Seasons with a recorded result only. Pct counts ties as half a win.</p></div></div>
    <div class="tbl"><table><thead><tr><th>Coach</th><th>Years</th><th class="num">Seasons</th><th class="num">W-L-T</th><th class="num">Pct</th><th>Titles</th></tr></thead>
      <tbody>{''.join(crow)}</tbody></table></div>
  </div>
</section>

<section class="block" id="h2h">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">Head to head</div><h2>Rivalries</h2>
      <p>Every opponent in a game with a known result. Goals leave out games whose score wasn’t recorded. Tap a column to sort.</p></div>
      <div class="search h2h-q"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input type="search" placeholder="Find an opponent" aria-label="Find an opponent"></div></div>
    <div class="tbl"><table class="sortable"><thead><tr><th data-k="0">Opponent</th><th class="num" data-k="1" aria-sort="descending">GP</th><th class="num" data-k="2">W</th><th class="num" data-k="3">L</th>
      <th class="num" data-k="4">T</th><th class="num" data-k="5">Pct</th><th class="num" data-k="6">Goals</th><th data-k="7">Years</th><th class="num">Biggest win</th></tr></thead>
      <tbody>{''.join(hrows)}</tbody></table></div>
  </div>
</section>

<section class="block alt" id="book">
  <div class="wrap">
    <div class="head"><div><div class="eyebrow" style="color:var(--blue)">Record book</div><h2>School Records</h2><p>As of the 2019 history. Know of a newer record? <a href="mailto:{CONTACT}?subject=Lions%20soccer%20record%20book">Email {CONTACT}</a>.</p></div></div>
    <div class="book">{book}</div>
  </div>
</section>

<section class="block">
  <div class="wrap tops">
    <div><h2 class="subhead">Best seasons</h2><p class="fine">By win %, eight or more games.</p><ol class="toplist">{brows}</ol></div>
    <div><h2 class="subhead">Most goals</h2><p class="fine">Seasons with full scores.</p><ol class="toplist">{grows}</ol></div>
  </div>
</section>"""
    return page("Stats & Records · Lions History", "Walkersville boys soccer all-time stats: win % by season, coaching records, head-to-head results and the school record book.", body, "stats")


def players_page(st):
    idx = [[n, [[p["y"], p["c"], p["n"]] for p in v]] for n, v in sorted(st["players"].items(), key=lambda kv: (kv[0].split()[-1].lower(), kv[0].lower()))]
    body = f"""<section class="ph-hero h-sub">
  <div class="wrap">
    <div class="eyebrow">Lions History</div>
    <h1>Find a Lion</h1>
    <p>{len(idx):,} names from every Walkersville roster we have, 1928 to {CURRENT}. Older names are spelled as they appear in the yearbook captions, sometimes with only an initial.</p>
  </div>
</section>
<div class="filters">
  <div class="wrap">
    <div class="search"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input type="search" id="pq" placeholder="Search a last name, first name or year" aria-label="Search players" autocomplete="off"></div>
    <span class="count" id="pcount"></span>
  </div>
</div>
<section class="block">
  <div class="wrap"><div class="az" id="paz"></div><div id="plist" class="players"></div></div>
</section>"""
    return page("Find a Lion · Lions History", "Search every Walkersville boys soccer roster since 1928.", body, "players",
                f'<script>window.PLAYERS = {json.dumps(idx, separators=(",", ":"), ensure_ascii=False)};</script>\n')


def main():
    data, seasons = load()
    st = stats(data, seasons)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(index_page(data, seasons, st))
    pages = [s for s in seasons if not s.get("end")]
    years = [s["year"] for s in pages]
    for i, s in enumerate(pages):
        nxt = years[i + 1] if i + 1 < len(years) else CURRENT
        (OUT / f"{s['year']}.html").write_text(season_page(s, years[i - 1] if i else None, nxt, st))
    (OUT / f"{CURRENT}.html").write_text(current_page(years[-1]))
    (OUT / "stats.html").write_text(stats_page(data, seasons, st))
    (OUT / "players.html").write_text(players_page(st))
    t = st["total"]
    print(f"{len(pages) + 1} season pages · all-time {rec_str(t)} · {len(st['h2h'])} opponents · {len(st['players'])} players -> site/history/")


if __name__ == "__main__":
    main()
