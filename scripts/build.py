#!/usr/bin/env python3
"""Build site/data.js: schedule, results, rosters and coaches from ArbiterLive, plus the photo catalog.

ArbiterLive team pages give both levels' games (times, home/away, scores, league vs non-league),
the player rosters and coaches. The MPSSAA scores API (same source as ../soccer) fills any varsity
league score Arbiter hasn't posted yet; MPSSAA lists games from the home school's side, so scores
are flipped when Walkersville isn't the listed school.
"""
import datetime, html, json, pathlib, re, subprocess, urllib.parse

API = "https://www.mpssaa.org/wp-json/smartsheet-sports/v1/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
US = "Walkersville"
RES = {"Win": "W", "Forfeit-Win": "W", "Loss": "L", "Forfeit-Loss": "L", "Tie": "T"}
FLIP = {"W": "L", "L": "W", "T": "T"}
# NFHS Network affiliate program (Impact, media property wvlions.com, id 9025280): every NFHS watch link goes through
# this tracking link; &u= tells Impact which nfhsnetwork.com page to land on
AFFILIATE = "https://nfhs-network.pxf.io/c/7957348/699473/10661?partnerpropertyid=9025280"


def affiliate(url):
    if not url or "nfhsnetwork.com" not in url or "pxf.io" in url:  # not NFHS, or already an affiliate link
        return url
    return f"{AFFILIATE}&u={urllib.parse.quote(url, safe='')}"


def curl(url, nonce=None):
    cmd = ["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "60"]
    if nonce:
        cmd += ["-H", f"X-WP-Nonce: {nonce}"]
    return subprocess.check_output(cmd + [url]).decode()


def mpssaa_results():
    """{(date, opponent): {res, gf, ga}} for Walkersville boys varsity."""
    nonce = re.search(r'"nonce":"([a-z0-9]+)"', curl("https://www.mpssaa.org/live-scores/")).group(1)
    out, off = {}, 0
    while True:
        d = json.loads(curl(f"{API}recent-results?sport=boys-soccer&limit=100&offset={off}&status=", nonce))
        for g in d["games"]:
            if US not in (g["school"], g["opponent"]):
                continue
            r = RES.get(g["result"])
            if not r:
                continue
            ours = g["school"] == US
            opp = g["opponent"] if ours else g["school"]
            gf, ga = (g["your_score"], g["opponent_score"]) if ours else (g["opponent_score"], g["your_score"])
            out[(g["game_date"], opp)] = dict(res=r if ours else FLIP[r], gf=gf, ga=ga,
                                              ff=g["result"].startswith("Forfeit"))
        off += d["count"]
        if d["count"] == 0 or off >= d["total"]:
            break
    return out


NFHS = "https://search-api.nfhsnetwork.com/search/events?school_key=da1a6a3363&size=100"  # Walkersville HS


def nfhs_broadcasts(season_start):
    """{(date, level): url} for boys soccer streams/replays on the NFHS Network."""
    out, cursor = {}, None
    for _ in range(20):
        d = json.loads(curl(NFHS + (f"&cursor={cursor}" if cursor else "")))
        for e in d["items"]:
            if e.get("sport") != "Soccer" or (e.get("gender") or "").lower() != "boys" or e.get("is_deleted"):
                continue
            date = (e.get("local_start_time") or e["start_time"])[:10]
            if date < season_start:
                continue
            level = "jv" if "junior" in (e.get("level") or "").lower() else "varsity"
            out[(date, level)] = dict(url=affiliate(e.get("site_url") or f"https://www.nfhsnetwork.com/events/{e['key']}"),
                                      status=e.get("status"))
        cursor = d.get("cursor")
        if not d["items"] or not cursor or min(e["start_time"] for e in d["items"])[:10] < season_start:
            break
    return out


def cells(fragment):
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", fragment, re.S):
        row = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if row:
            yield row


def opp_name(raw):
    """'Middletown (MD) High School' -> 'Middletown'."""
    n = re.sub(r"\s*\(MD\)|\s+High School$", "", raw).strip()
    return {"St. Johns Catholic Prep": "St. John's Catholic Prep"}.get(n, n)


def arbiter_games(page, year):
    """{(date, opp): game} from the schedule tab of an ArbiterLive team page."""
    out = {}
    for c in cells(page[page.index("<body"):page.index('id="tabTeamRoster"')]):
        m = re.match(r"\w{3} (\w{3}) (\d+)\s*(.*)", c[0])
        if not m or c[1] not in ("vs", "@"):
            continue
        date = datetime.datetime.strptime(f"{m[1]} {m[2]} {year}", "%b %d %Y").date().isoformat()
        res = next((re.match(r"([WLT]) (\d+)-(\d+)$", x) for x in c if re.match(r"[WLT] \d+-\d+$", x)), None)
        g = dict(date=date, opp=opp_name(c[2]), home=c[1] == "vs", time=m[3] if m[3] != "TBA" else None,
                 league="L" in c[4:], scrimmage="S" in c[4:], canceled="Canceled" in c,
                 result=dict(res=res[1], gf=int(res[2]), ga=int(res[3])) if res else None)
        key = (date, g["opp"])
        if key not in out or (g["result"] and not out[key]["result"]):  # Arbiter sometimes lists a game twice
            out[key] = g
    return out


def arbiter_team(page):
    """Players and coaches from an ArbiterLive team page's roster tab."""
    tab = page[page.index('id="tabTeamRoster"'):]
    tab = tab[:tab.index("</table>", tab.index("Title"))]
    players, coaches = [], []
    for c in cells(tab):
        if len(c) >= 3 and c[0].isdigit():
            last, _, first = c[1].partition(",")
            ht = c[4] if len(c) > 4 else ""
            if not re.fullmatch(r"[4-7]'\d{1,2}\"", ht):  # Arbiter has junk heights like 0'5"
                ht = ""
            players.append(dict(num=int(c[0]), name=f"{first.strip()} {last.strip()}".strip(),
                                grade=c[2] or None, pos=(c[3] if len(c) > 3 else "") or None, height=ht or None))
        elif len(c) == 2 and c[0] and not c[0].isdigit():
            coaches.append(dict(name=c[0], role=c[1]))
    return players, coaches


def main():
    sched = json.loads((DATA / "schedule.json").read_text())
    sched["links"] = {k: affiliate(v) for k, v in sched["links"].items()}
    cfg = json.loads((DATA / "roster.json").read_text())
    year = sched["season"]
    roster, coaches, by_level = {}, {}, {}
    for level, url in cfg["arbiter"].items():
        page = curl(url)
        if 'id="tabTeamRoster"' not in page:  # Arbiter down or changed: keep the last good site/data.js
            raise SystemExit(f"ArbiterLive {level} page didn't load; site/data.js left unchanged")
        players, staff = arbiter_team(page)
        players = cfg["players"][level]  # hand-maintained; Arbiter's roster has errors
        roster[level] = players
        by_level[level] = arbiter_games(page, year)
        for c in staff:
            coaches.setdefault(c["name"], dict(c, teams=[], bio=cfg["bios"].get(c["name"])))["teams"].append(level)
        print(f"{level}: {len(players)} players, {len(by_level[level])} games, coaches {[c['name'] for c in staff]}")
    for c in cfg.get("assistants", []):
        if c["name"] not in coaches:
            coaches[c["name"]] = dict(c, bio=cfg["bios"].get(c["name"]))
    roster["coaches"] = list(coaches.values())
    roster["arbiter"] = cfg["arbiter"]
    try:
        mpssaa = mpssaa_results()
    except Exception as e:  # keep building with Arbiter's scores alone
        print("MPSSAA fetch failed:", e)
        mpssaa = {}

    games = {}
    for level, gs in by_level.items():
        for key, g in gs.items():
            if g["date"] < sched["seasonStart"]:
                continue
            game = games.setdefault(key, dict(date=g["date"], opp=g["opp"], home=g["home"], league=g["league"], scrimmage=g["scrimmage"],
                                              time={}, varsity=None, jv=None, canceled={}))
            game["league"] |= g["league"]
            game["scrimmage"] &= g["scrimmage"]
            if g["time"]:
                game["time"][level] = g["time"]
            game[level] = g["result"]
            if g["canceled"]:
                game["canceled"][level] = True
    for g in sched.get("added", []):  # hand-entered games Arbiter doesn't list
        games.setdefault((g["date"], g["opp"]), dict(g, time={}, varsity=None, jv=None, canceled={}))
    try:
        streams = nfhs_broadcasts(sched["seasonStart"])
    except Exception as e:
        print("NFHS fetch failed:", e)
        streams = {}
    for g in games.values():
        g["watch"] = {lv: streams[(g["date"], lv)]["url"] for lv in ("varsity", "jv") if (g["date"], lv) in streams}
    print(f"NFHS: {len(streams)} boys soccer broadcasts")
    for key, r in mpssaa.items():
        if key in games and not games[key]["varsity"]:
            games[key]["varsity"] = r
        elif key not in games:
            print("MPSSAA game not on Arbiter:", key)
    for key, g in games.items():
        m = mpssaa.get(key)
        if m and g["varsity"] and (m["gf"], m["ga"]) != (g["varsity"]["gf"], g["varsity"]["ga"]):
            print("Score mismatch Arbiter vs MPSSAA:", key, g["varsity"], m)
        for k, v in sched.get("extras", {}).get(g["date"], {}).items():
            if k in ("varsity", "jv"):  # hand-entered score ("0-1", Walkersville first) when Arbiter has none
                if not g[k]:
                    gf, ga = (int(x) for x in v.split("-"))
                    g[k] = dict(res="W" if gf > ga else "L" if gf < ga else "T", gf=gf, ga=ga)
            else:
                g[k] = v
        if g["scrimmage"]:  # scrimmage scores aren't shown on the site
            g["varsity"] = g["jv"] = None
        if g["opp"] not in sched["opponents"]:
            print("No mascot/city for opponent:", g["opp"])
    sched["games"] = sorted(games.values(), key=lambda g: g["date"])
    for k in ("_comment", "added", "extras", "seasonStart"):
        sched.pop(k, None)
    photos = json.loads((DATA / "photos.json").read_text())
    # Full Drive folder per game & level (for "see all in Drive" links); count distinct shots (JPG+NEF pairs once)
    folders = json.loads((DATA / "photo_folders.json").read_text())
    drive = json.loads((ROOT / "scripts" / "cache" / "drive.json").read_text())
    drive_games = []
    for name, info in folders.items():
        if name.startswith("_") or "/" in name and not name.startswith("JV Pictures 2026/") or not info.get("folder"):
            continue  # skip edit subfolders; their photos live in the parent game folder
        if "split" in info:
            continue  # mixed folder spanning several games: no single game to link it to
        shots = {f["name"].rsplit(".", 1)[0].lower() for f in drive.get(name, [])
                 if f["name"].lower().endswith((".jpg", ".jpeg", ".png", ".nef"))}
        key = info["date"] or "x-" + re.sub(r"[^a-z0-9]+", "-", info["opp"].lower()).strip("-")
        drive_games.append(dict(key=key, level=info["level"], count=len(shots),
                                url=f"https://drive.google.com/drive/folders/{info['folder']}"))
    data = dict(updated=datetime.datetime.now().strftime("%b %-d, %Y"), schedule=sched, roster=roster, photos=photos,
                driveGames=drive_games)
    (ROOT / "site" / "data.js").write_text("window.DATA = " + json.dumps(data, separators=(",", ":")) + ";\n")
    # Link-preview text for each photo's own page (/photo/<id>, filled in by functions/photo/[id].js)
    rosters = {lv: {p["num"]: p["name"] for p in roster.get(lv, [])} for lv in ("varsity", "jv")}
    games = {g["date"]: g for g in sched["games"]}
    meta = {}
    for p in photos:
        g = games.get(p["date"])
        who = ", ".join(f"#{n} {rosters[p['level']].get(n, '')}".strip() for n in p["numbers"][:3])
        game = f"{'JV' if p['level'] == 'jv' else 'Varsity'} {'vs' if g and g['home'] else 'at'} {p['opp']}"
        when = datetime.date.fromisoformat(p["date"]).strftime("%b %-d") if p["date"] else ""
        meta[p["id"]] = dict(title=p["caption"] or who or game, image="/" + p["full"],
                             description=" · ".join(x for x in (game if (p["caption"] or who) else "", when, "Walkersville Lions boys soccer 2026") if x))
    (ROOT / "site" / "photo-meta.json").write_text(json.dumps(meta, separators=(",", ":")))
    # Cache-bust asset links so browsers pick up new data/code after a rebuild
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    for page in (ROOT / "site").glob("*.html"):
        page.write_text(re.sub(r'((?:href|src)="(?:styles\.css|data\.js|app\.js))(\?v=\d+)?"', rf'\1?v={stamp}"',
                               page.read_text()))
    for level in ("varsity", "jv"):
        rec = [g[level]["res"] for g in sched["games"] if g[level] and not g["scrimmage"]]
        print(f"{level} {rec.count('W')}-{rec.count('L')}-{rec.count('T')}", end="  ")
    print(f"{len(photos)} photos -> site/data.js")


if __name__ == "__main__":
    main()
