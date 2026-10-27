/* Walkersville Lions boys soccer 2026 — renders index.html and photos.html from window.DATA (built by scripts/build.py). */
(() => {
  const D = window.DATA;
  const S = D.schedule;
  const $ = (s, el = document) => el.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  const day = iso => { const [y, m, d] = iso.split("-").map(Number); return new Date(y, m - 1, d); };
  const today = (() => { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); })();
  const fmtDate = (iso, long) => { const d = day(iso); return `${(long ? ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"] : DOW)[d.getDay()]}, ${MON[d.getMonth()]} ${d.getDate()}`; };
  const LEVELS = ["varsity", "jv"];
  const LABEL = { varsity: "Varsity", jv: "JV" };
  const firstTime = g => g.time.jv || g.time.varsity;  // JV kicks off first
  const timesText = g => g.time.jv && g.time.varsity ? `JV ${esc(g.time.jv)} · Varsity ${esc(g.time.varsity)}`
    : firstTime(g) ? esc(firstTime(g)) + (g.tentative ? " (tentative)" : "") : "Time TBA";
  const kickoff = g => {
    const d = day(g.date);
    const m = /(\d+):(\d+)\s*(AM|PM)/i.exec(firstTime(g) || "");
    if (m) d.setHours((+m[1] % 12) + (/pm/i.test(m[3]) ? 12 : 0), +m[2]);
    return d;
  };
  const opp = g => S.opponents[g.opp] || {};
  // site: neutral venue from schedule.json extras (e.g. a conference final), overrides home/away
  const venue = g => g.site ? `${g.site.name}, ${g.site.city}` : g.home ? S.homeVenue : `${g.opp} High School, ${opp(g).city || ""}`;
  const mapUrl = g => "https://www.google.com/maps/search/?api=1&query=" +
    encodeURIComponent(g.site ? `${g.site.name}, ${g.site.city}, MD` : g.home ? "Walkersville High School, 81 W Frederick St, Walkersville, MD" : `${g.opp} High School, ${opp(g).city}, MD`);
  const vsAt = g => g.home || g.site ? "vs" : "at";
  const where = g => g.site ? "Neutral" : g.home ? "Home" : "Away";
  const result = (g, level) => g[level];
  const isPast = g => day(g.date) < today || g.varsity || g.jv;
  const ticketUrl = g => g.tickets === false ? null : g.tickets || (g.home ? S.links.tickets : null);  // tickets: false = no GoFan event yet

  // root-relative image paths: the lightbox changes the URL to /photo/<id>, which would break relative ones
  const photos = D.photos.map(p => ({ ...p, full: "/" + p.full.replace(/^\//, ""), thumb: "/" + p.thumb.replace(/^\//, "") }));
  const gameKey = p => p.date ? p.date : "x-" + p.opp.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  const gameOn = date => date && S.games.find(x => x.date === date);
  // clean URLs: /photos[/varsity|jv][/<jersey #>][/<date>-<opponent>] for filters, /photo/<id> for one photo
  const slugify = s => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const gameSeg = date => { const g = gameOn(date); return g ? `${date}-${slugify(g.opp)}` : date; };
  const photosUrl = ({ level = "", num = null, game = "" } = {}) =>
    "/photos" + [level, num ?? "", game ? gameSeg(game) : ""].filter(x => x !== "").map(x => "/" + x).join("");
  const photoUrl = p => `/photo/${p.id}`;
  const photosFor = (date, level) => photos.filter(p => p.date === date && (!level || p.level === level));
  const sortPhotos = list => [...list].sort((a, b) => (b.featured - a.featured));
  // catalog: varsity before JV within a game, then featured, then the curated order from picks.txt
  const catalogSort = list => [...list].sort((a, b) => (a.level === "jv") - (b.level === "jv") || b.featured - a.featured);
  const playerByNum = (level, n) => (D.roster[level] || []).find(p => p.num === n);
  const who = p => p.numbers.map(n => { const pl = playerByNum(p.level, n); return pl ? `#${n} ${esc(pl.name)}` : `#${n}`; }).join(" · ");

  const ICON = {
    cam: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h3l2-3h6l2 3h3a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="4"/></svg>',
    ticket: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 8a2 2 0 0 0 0 4v4h18v-4a2 2 0 0 1 0-4V4H3z"/><path d="M13 4v16" stroke-dasharray="2 2"/></svg>',
    play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z"/></svg>',
    trophy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M7 6H4.5a.5.5 0 0 0-.5.5V8a3 3 0 0 0 3 3M17 6h2.5a.5.5 0 0 1 .5.5V8a3 3 0 0 1-3 3"/><path d="M12 14v3M8.5 20h7M9.5 17h5v3h-5z"/></svg>',
    pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.3-7-12a7 7 0 0 1 14 0c0 5.7-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/></svg>',
  };

  const resHtml = (r, past, short) => r
    ? `<span class="res ${r.res}"><i>${r.res}</i>${r.gf}–${r.ga}</span>`
    : `<span class="res none">${past ? (short ? "No score" : "Score not reported") : ""}</span>`;

  function record(level) {
    const rs = S.games.filter(g => !g.scrimmage).map(g => g[level]).filter(Boolean);
    const c = k => rs.filter(r => r.res === k).length;
    let streak = 0, kind = null;
    for (const r of [...rs].reverse()) { if (!kind) kind = r.res; if (r.res !== kind) break; streak++; }
    return { w: c("W"), l: c("L"), t: c("T"), gf: rs.reduce((s, r) => s + r.gf, 0), ga: rs.reduce((s, r) => s + r.ga, 0), n: rs.length, streak, kind };
  }
  const recStr = r => `${r.w}-${r.l}${r.t ? "-" + r.t : ""}`;

  /* ---------- analytics (GoatCounter): page views are automatic; taps on outside links, downloads and shares are events ---------- */
  const track = (path, title) => { try { window.goatcounter && window.goatcounter.count && window.goatcounter.count({ path, title, event: true }); } catch (e) {} };
  const clean = s => (s || "").replace(/\s+/g, " ").trim();
  document.addEventListener("click", e => {
    const a = e.target.closest("a[href], button[data-share], #ics"); if (!a) return;
    const href = a.getAttribute("href") || "", text = clean(a.textContent);
    const row = a.closest(".game"), where = row ? clean(row.querySelector(".opp")?.textContent).replace(/^(vs|at)/, "$1 ") + " · " + clean(row.querySelector(".when")?.textContent)
      : lb.classList.contains("open") && lbList[lbIdx] ? lbList[lbIdx].id : document.title;
    if (a.id === "ics") track("calendar", "Add games to calendar");
    else if (a.matches("[data-share]")) track("share", where);
    else if (a.closest(".dl-menu")) track("download/" + slugify(clean(a.querySelector("b")?.textContent)), where);
    else if (/pxf\.io|nfhsnetwork\.com/.test(href)) track(/replay/i.test(text) ? "nfhs/replay" : a.id === "watch" ? "nfhs/channel" : "nfhs/live", where);
    else if (/gofan\.co/.test(href)) track("tickets", where);
    else if (/google\.com\/maps/.test(href)) track("directions", where);
    else if (/drive\.google\.com/.test(href)) track("drive", text);
  }, true);

  /* ---------- shared: header links + lightbox ---------- */
  document.querySelectorAll("#nav-tickets").forEach(a => a.href = S.links.tickets);

  const lb = $("#lb");
  let lbList = [], lbIdx = 0, lbReturn = null;
  // tab title follows the open photo; /photo/<id> pages arrive with that photo's title, so fall back to the catalog's
  const pageTitle = location.pathname.startsWith("/photo/") ? "Photos · WV Lions Soccer 2026" : document.title;
  function openLb(list, idx, returnUrl) {
    lbList = list; lbIdx = idx;
    lbReturn = returnUrl || location.pathname + location.search + location.hash;
    lb.classList.add("open"); lb.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    drawLb();
  }
  // Download menu: only the versions this photo actually has, each labeled with file type, pixel size and file size
  const mb = n => n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`;
  function dlMenu(p) {
    const d = p.download || {};
    const opts = [
      { href: p.full, same: true, name: "Web size", type: "WebP", px: `${p.w}×${p.h}`, size: d.web && d.web.bytes, note: "quick to share" },
      d.full && { href: d.full.url, name: "Full size", type: d.full.type, px: d.full.w ? `${d.full.w}×${d.full.h}` : "", size: d.full.bytes,
        note: d.full.converted ? "made from the RAW file" : "original camera file",
        fetch: d.full.converted ? `${p.id}.jpg` : "" },
      d.raw && { href: d.raw.url, name: "RAW", type: d.raw.type, px: "", size: d.raw.bytes, note: "for photo-editing apps" },
    ].filter(Boolean);
    return `<details class="dl"><summary>Download<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><div class="dl-menu">${opts.map(o =>
      `<a href="${o.href}" ${o.same ? "download" : o.fetch ? `data-fetch="${o.fetch}"` : `target="_blank" rel="noopener"`}><b>${o.name}</b>
        <span>${[o.type, o.px, o.size && mb(o.size)].filter(Boolean).join(" · ")}</span><small>${o.note}</small></a>`).join("")}</div></details>`;
  }
  // Share: the phone's share sheet where there is one, else copy the photo's link
  async function sharePhoto(btn) {
    const p = lbList[lbIdx], url = location.origin + photoUrl(p);
    if (navigator.share) { try { await navigator.share({ title: p.caption || "WV Lions Soccer photo", url }); } catch (e) {} return; }
    try { await navigator.clipboard.writeText(url); btn.textContent = "Link copied"; } catch (e) { prompt("Copy this link:", url); }
    setTimeout(() => { btn.textContent = "Share"; }, 2000);
  }
  // Drive only shows RAW-made JPEGs in the browser, so fetch the image and save it as a file instead
  async function saveRemote(a) {
    const small = a.querySelector("small"), was = small.textContent;
    small.textContent = "Downloading…";
    try {
      const r = await fetch(a.href); if (!r.ok) throw new Error(r.status);
      const url = URL.createObjectURL(await r.blob());
      const t = document.createElement("a"); t.href = url; t.download = a.dataset.fetch;
      document.body.appendChild(t); t.click(); t.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      small.textContent = was;
    } catch (err) { window.open(a.href, "_blank", "noopener"); small.textContent = was; }
  }
  function closeLb() {
    if (lbReturn !== null) { history.replaceState(null, "", lbReturn); lbReturn = null; }
    document.title = pageTitle;
    lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); document.body.style.overflow = ""; }
  function drawLb() {
    const p = lbList[lbIdx];
    const g = gameOn(p.date);
    history.replaceState(null, "", photoUrl(p));
    const who = p.numbers.map(n => { const pl = playerByNum(p.level, n); return pl ? `#${n} ${pl.name}` : `#${n}`; }).join(", ");
    document.title = `${p.caption || who || `${LABEL[p.level]} ${g ? vsAt(g) + " " : ""}${p.opp}`} · WV Lions Soccer`;
    try { window.goatcounter && window.goatcounter.count && window.goatcounter.count({ path: photoUrl(p), title: document.title }); } catch (e) {}  // each viewed photo counts as a page view
    lb.innerHTML = `
      <div class="lb-top">
        <div><div class="t">${p.level === "jv" ? "JV" : "Varsity"} · ${g ? `${vsAt(g)} ${esc(p.opp)}` : esc(p.opp)}</div>
          <div class="s">${p.date ? fmtDate(p.date) : "2026 season"}${p.caption ? " · " + esc(p.caption) : ""}</div></div>
        <span class="sp"></span>
        <button data-share>Share</button>
        ${dlMenu(p)}
        <button data-close aria-label="Close">✕</button>
      </div>
      <div class="lb-stage">
        <button class="lb-nav prev" data-step="-1" aria-label="Previous"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>
        <img src="${p.full}" alt="">
        <button class="lb-nav next" data-step="1" aria-label="Next"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg></button>
      </div>
      <div class="lb-bot">${lbIdx + 1} / ${lbList.length}${who ? ` · In this photo: ${who.split(", ").map(w => `<a href="${photosUrl({ level: p.level, num: +w.match(/\d+/)[0] })}">${esc(w)}</a>`).join(" ")}` : ""}
        · <a href="${p.drive}" target="_blank" rel="noopener">Original in Drive</a></div>`;
    [lbIdx - 1, lbIdx + 1].forEach(i => { const q = lbList[(i + lbList.length) % lbList.length]; if (q) new Image().src = q.full; });
  }
  const step = n => { lbIdx = (lbIdx + n + lbList.length) % lbList.length; drawLb(); };
  lb.addEventListener("click", e => {
    const dl = lb.querySelector(".dl[open]"); if (dl && !e.target.closest(".dl")) { dl.open = false; return; }
    const f = e.target.closest("a[data-fetch]"); if (f) { e.preventDefault(); saveRemote(f); return; }
    const sh = e.target.closest("[data-share]"); if (sh) { sharePhoto(sh); return; }
    if (e.target.closest("[data-close]") || e.target.classList.contains("lb-stage")) closeLb();
    const s = e.target.closest("[data-step]"); if (s) step(+s.dataset.step);
  });
  document.addEventListener("keydown", e => {
    if (!lb.classList.contains("open")) return;
    const dl = lb.querySelector(".dl[open]");
    if (e.key === "Escape") { if (dl) dl.open = false; else closeLb(); }
    if (e.key === "ArrowRight") step(1);
    if (e.key === "ArrowLeft") step(-1);
  });
  let touchX = null;
  lb.addEventListener("touchstart", e => touchX = e.touches[0].clientX, { passive: true });
  lb.addEventListener("touchend", e => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
    touchX = null;
  });

  /* ---------- home ---------- */
  function home() {
    // hero: a random featured photo (varsity or JV) on every load, never the same one twice in a row
    const feat = photos.filter(p => p.featured);
    let lastHero = null; try { lastHero = localStorage.getItem("heroPhoto"); } catch (e) {}
    const pool = feat.length > 1 ? feat.filter(p => p.id !== lastHero) : feat;
    const hero = pool[Math.floor(Math.random() * pool.length)];
    try { if (hero) localStorage.setItem("heroPhoto", hero.id); } catch (e) {}
    if (hero) $("#hero-bg").style.backgroundImage = `url(${hero.full})`;

    const v = record("varsity"), jv = record("jv");
    const tile = (r, label) => `<div class="record"><span>${label}</span><b>${r.n ? recStr(r) : "0-0"}</b>
      <small>${r.kind === "W" && r.streak > 1 ? `${r.streak}-game win streak` : `${r.gf}–${r.ga} goals`}</small></div>`;
    $("#records").innerHTML = tile(v, "Varsity") + tile(jv, "JV");

    // next game
    const upcoming = S.games.filter(g => !isPast(g));
    const next = upcoming[0];
    const box = $("#next-game");
    if (!next) {
      box.innerHTML = `<div class="label"><span>Regular season</span></div><h2>Season complete</h2>
        <p class="where">Playoff games will be posted by MPSSAA. Thanks for cheering on the Lions!</p>`;
    } else {
      const t = ticketUrl(next);
      box.innerHTML = `
        <div class="label"><span>Next game</span><span class="pill ${next.home ? "" : "away"}">${where(next)}</span></div>
        <h2>${vsAt(next)} ${esc(next.opp)}<small>${[opp(next).mascot, next.note].filter(Boolean).map(esc).join(" · ")}</small></h2>
        <div class="when">${fmtDate(next.date, true)} · ${timesText(next)}</div>
        <div class="where"><a href="${mapUrl(next)}" target="_blank" rel="noopener">${esc(venue(next))}</a></div>
        ${!t && next.ticketNote ? `<div class="where">${esc(next.ticketNote)}</div>` : ""}
        <div class="countdown" id="cd"></div>
        <div class="actions">
          ${t ? `<a class="btn gold" href="${t}" target="_blank" rel="noopener">${ICON.ticket}Buy tickets</a>` : ""}
          <a class="btn ghost" href="${mapUrl(next)}" target="_blank" rel="noopener">${ICON.pin}Directions</a>
          <a class="btn ghost" href="${S.links.watch}" target="_blank" rel="noopener">▶ Watch</a>
        </div>
        ${upcoming[1] ? `<div class="also">After that: <b>${fmtDate(upcoming[1].date)} ${vsAt(upcoming[1])} ${esc(upcoming[1].opp)}</b>${firstTime(upcoming[1]) ? " · " + esc(firstTime(upcoming[1])) : ""}</div>` : ""}`;
      const cd = $("#cd");
      const tick = () => {
        const ms = Math.max(0, kickoff(next) - new Date());
        const parts = [[Math.floor(ms / 864e5), "days"], [Math.floor(ms / 36e5) % 24, "hrs"], [Math.floor(ms / 6e4) % 60, "min"], [Math.floor(ms / 1e3) % 60, "sec"]];
        cd.innerHTML = parts.map(([n, l]) => `<div><b>${n}</b><span>${l}</span></div>`).join("");
      };
      if (firstTime(next)) { tick(); setInterval(tick, 1000); } else cd.remove();  // no countdown to midnight while the time is TBA
    }

    // latest result + photos
    const played = S.games.filter(g => (g.varsity || g.jv) && !g.scrimmage);
    const last = played[played.length - 1];
    if (last) {
      const lv = LEVELS.filter(l => last[l]);
      const wins = lv.filter(l => last[l].res === "W");
      const headline = wins.length === 2 ? `Lions sweep ${esc(last.opp)}`
        : wins.length === 1 ? `${LABEL[wins[0]]} wins ${vsAt(last)} ${esc(last.opp)}`
        : lv.every(l => last[l].res === "T") ? `Draw ${vsAt(last)} ${esc(last.opp)}` : `Tough night ${vsAt(last)} ${esc(last.opp)}`;
      const pics = sortPhotos(photosFor(last.date));
      const shown = pics.slice(0, 5);
      const shownLv = LEVELS.filter(l => last[l] || !(last.time && !last.time[l]));  // drop a level that didn't play (e.g. the varsity-only CMC final)
      $("#highlight").innerHTML = `
        <div class="score-card${last.feature ? " champ" : ""}">
          <div class="eyebrow">${fmtDate(last.date, true)} · ${where(last)}</div>
          <h3 class="headline">${last.note ? `${last.feature ? `<span class="trophy" aria-hidden="true">${ICON.trophy}</span>` : ""}${esc(last.note)}<small>${headline}</small>` : headline}</h3>
          <div class="duo${shownLv.length === 1 ? " solo" : ""}">${shownLv.map(l => last[l] ? `
            <div class="lvl"><span>${LABEL[l]}</span><b>${last[l].gf}<em>–</em>${last[l].ga}</b><i class="${last[l].res}">${{ W: "Win", L: "Loss", T: "Tie" }[last[l].res]}</i></div>`
            : `<div class="lvl none"><span>${LABEL[l]}</span><b>—</b><i>${last.canceled[l] ? "Canceled" : "No score"}</i></div>`).join("")}
          </div>
          ${LEVELS.some(l => last.watch && last.watch[l]) ? `<div class="replays">${LEVELS.filter(l => last.watch[l]).map(l =>
            `<a href="${last.watch[l]}" target="_blank" rel="noopener">▶ Watch ${LABEL[l]} replay</a>`).join("")}</div>` : ""}
          <div class="meta">${esc(venue(last))}<br>${pics.length ? `${pics.length} photo${pics.length === 1 ? "" : "s"} from this game` : "Photos coming soon"}</div>
        </div>
        <div class="mosaic${shown[0] && shown[0].w / shown[0].h > 1.9 ? " wide" : ""}">${shown.length ? "" : `<div class="mosaic-empty">Photos from this game will be posted soon</div>`}${shown.map((p, i) => `
          <button data-i="${i}" aria-label="Open photo"><img src="${i ? p.thumb : p.full}" alt="" loading="lazy">
          ${i === shown.length - 1 && pics.length > shown.length ? `<span class="more">+${pics.length - shown.length + 1} more</span>` : ""}</button>`).join("")}
        </div>`;
      $("#highlight .mosaic").addEventListener("click", e => {
        const b = e.target.closest("button"); if (!b) return;
        if (b.querySelector(".more")) location.href = photosUrl({ game: last.date });
        else openLb(pics, +b.dataset.i);
      });
      // special games (e.g. Senior Night) get a pinned full-width card that stays for the rest of the season
      const special = played.slice(0, -1).filter(g => g.feature).reverse().map(g => {
        const cover = sortPhotos(photosFor(g.date, "varsity"))[0];
        const seniors = (D.roster.varsity || []).filter(p => p.grade === "Senior");
        return `<div class="special">
          <a class="ph" href="${photosUrl({ game: g.date })}" style="${cover ? `background-image:url(${cover.full})` : ""}" aria-label="${esc(g.note || g.opp)} photos"></a>
          <div class="body">
            <div class="ribbon">${esc(g.note || "")}</div>
            <div class="opp">${vsAt(g)} ${esc(g.opp)} · ${fmtDate(g.date, true)}</div>
            <div class="both">${LEVELS.map(l => `<span><small>${LABEL[l]}</small>${g[l] ? resHtml(g[l]) : `<span class="res none">—</span>`}</span>`).join("")}</div>
            ${g.note === "Senior Night" && seniors.length ? `<div class="honor"><small>Honoring our seniors</small>
              <div class="names">${seniors.map(p => `<a href="${photosUrl({ level: "varsity", num: p.num })}">#${p.num} ${esc(p.name)}</a>`).join("")}</div></div>` : ""}
            <a class="all" href="${photosUrl({ game: g.date })}">See all ${photosFor(g.date).length} photos →</a>
          </div></div>`;
      }).join("");
      $("#recent").innerHTML = special + `<div class="recent-grid">` + played.slice(0, -1).filter(g => !g.feature).reverse().slice(0, 4).map(g => {
        const cover = sortPhotos(photosFor(g.date, "varsity"))[0] || photosFor(g.date)[0];
        return `<a class="mini" href="${photosUrl({ game: g.date })}">
          <div class="ph" style="${cover ? `background-image:url(${cover.thumb})` : ""}"></div>
          <div class="body"><div class="opp">${vsAt(g)} ${esc(g.opp)}</div><div class="date">${fmtDate(g.date)}</div>
            <div class="both">${LEVELS.map(l => `<span><small>${LABEL[l]}</small>${g[l] ? resHtml(g[l]) : `<span class="res none">—</span>`}</span>`).join("")}</div></div></a>`;
      }).join("") + `</div>`;
    }

    // schedule + team (shared team toggle)
    const nextDate = next && next.date;
    const rec = $("#sched-sub");
    function schedule(level) {
      const r = record(level);
      rec.textContent = `${S.season} · ${S.classification}${r.n ? ` · ${level === "jv" ? "JV" : "Varsity"} ${recStr(r)}` : ""}`;
      // scoreboard rows: a colored block on the left (result, kickoff time or status), one line of links under the opponent
      $("#sched").innerHTML = S.games.map(g => {
        const d = day(g.date), past = isPast(g), r = g[level], n = photosFor(g.date, level).length, t = !past && ticketUrl(g);
        const time = g.time[level], watch = g.watch && g.watch[level];
        const block = g.canceled[level] ? `<div class="score off"><span>Canceled</span></div>`
          : g.scrimmage && past ? `<div class="score off"><span>Scrimmage</span></div>`
          : past ? (r ? `<div class="score ${r.res}"><span>${{ W: "Win", L: "Loss", T: "Tie" }[r.res]}</span><b>${r.gf}–${r.ga}</b></div>`
                      : `<div class="score off"><span>No score</span></div>`)
          : time ? `<div class="score up"><span>${g.tentative ? "Tentative" : "Kickoff"}</span><b>${esc(time.replace(/\s?[AP]M$/i, ""))}</b><span>${/AM$/i.test(time) ? "AM" : "PM"}</span></div>`
          : `<div class="score up"><span>Kickoff</span><b>TBA</b></div>`;
        const links = [
          `<a class="venue" href="${mapUrl(g)}" target="_blank" rel="noopener">${esc(venue(g))}</a>`,
          g.scrimmage && !past ? `<span>Scrimmage</span>` : "",
          g.note ? `<span>${esc(g.note)}</span>` : "",
          t ? `<a class="tix" href="${t}" target="_blank" rel="noopener">${ICON.ticket}Tickets</a>` : !past && g.ticketNote ? `<span>${esc(g.ticketNote)}</span>` : !past && !g.home ? `<span>Away tickets at the gate</span>` : "",
          watch ? `<a href="${watch}" target="_blank" rel="noopener">${ICON.play}${past ? "Replay" : "Watch live"}</a>` : "",
          n ? `<a href="${photosUrl({ game: g.date, level })}">${ICON.cam}${n} photo${n === 1 ? "" : "s"}</a>` : "",
        ].filter(Boolean).join("");
        return `<div class="game${g.date === nextDate ? " is-next" : ""}">${block}<div class="body">
          <div class="hd"><div class="opp"><span class="vs">${vsAt(g)}</span>${esc(g.opp)}</div><div class="when">${DOW[d.getDay()]}, ${MON[d.getMonth()]} ${d.getDate()}</div></div>
          <div class="links">${links}</div></div></div>`;
      }).join("");
    }
    function team(level) {
      const cs = D.roster.coaches.filter(c => c.teams.includes(level));
      $("#coaches").innerHTML = cs.map(c => `
        <div class="coach"><div class="avatar">${c.name.split(" ").map(w => w[0]).join("")}</div>
          <div><div class="role">${esc(c.role)}${c.teams.length > 1 ? " · Varsity &amp; JV" : ""}</div><h3>${esc(c.name)}</h3>${c.bio ? `<p>${esc(c.bio)}</p>` : ""}</div></div>`).join("");
      $("#roster-title").textContent = `${level === "jv" ? "JV" : "Varsity"} Roster`;
      const players = [...(D.roster[level] || [])].sort((a, b) => a.num - b.num);
      if (players.length) {
        $("#roster").innerHTML = `<div class="roster">${players.map(p => {
          const n = photos.filter(x => x.level === level && x.numbers.includes(p.num)).length;
          return `<a class="player" href="${photosUrl({ level, num: p.num })}"><div class="jersey">${p.num}</div>
            <div><div class="n">${esc(p.name)}</div><div class="m">${[p.grade, p.pos].filter(Boolean).map(esc).join(" · ")}${n ? ` · ${n} photo${n > 1 ? "s" : ""}` : ""}</div></div></a>`;
        }).join("")}</div>`;
      } else {
        const nums = [...new Set(photos.filter(p => p.level === level).flatMap(p => p.numbers))].sort((a, b) => a - b);
        $("#roster").innerHTML = `<div class="empty"><b>The 2026 ${level === "jv" ? "JV" : "varsity"} roster is coming soon.</b><br>
          In the meantime, find your player's photos by jersey number:
          <div class="numbers">${nums.map(n => `<a href="${photosUrl({ level, num: n })}">${n}</a>`).join("")}</div></div>`;
      }
    }
    function setLevel(level) {
      document.querySelectorAll("[data-team-toggle] button").forEach(b => b.setAttribute("aria-pressed", b.dataset.team === level));
      schedule(level); team(level);
    }
    document.querySelectorAll("[data-team-toggle]").forEach(el => el.addEventListener("click", e => {
      const b = e.target.closest("button"); if (b) setLevel(b.dataset.team);
    }));
    setLevel("varsity");

    $("#updated").textContent = D.updated;
    $("#watch").href = S.links.watch;
      document.querySelectorAll("[data-team-toggle] button").forEach(b => b.addEventListener("click", () => $("#arbiter").href = D.roster.arbiter[b.dataset.team]));
      $("#arbiter").href = D.roster.arbiter.varsity;
    $("#ics").addEventListener("click", downloadIcs);
  }

  function downloadIcs() {
    const pad = n => String(n).padStart(2, "0");
    const stamp = d => `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//WV Lions Soccer 2026//EN", "X-WR-CALNAME:WV Lions Boys Soccer"];
    S.games.filter(g => !isPast(g)).forEach(g => {
      const d = kickoff(g);
      const when = firstTime(g)
        ? [`DTSTART;TZID=America/New_York:${stamp(d)}T${pad(d.getHours())}${pad(d.getMinutes())}00`,
           `DTEND;TZID=America/New_York:${stamp(d)}T${pad(d.getHours() + 3)}${pad(d.getMinutes())}00`]
        : [`DTSTART;VALUE=DATE:${stamp(d)}`];
      lines.push("BEGIN:VEVENT", `UID:lions-${g.date}@lionssoccer`, `DTSTAMP:${stamp(new Date())}T000000Z`, ...when,
        `SUMMARY:Lions Soccer ${vsAt(g)} ${g.opp} (JV then Varsity)`, `LOCATION:${venue(g).replace(/,/g, "\\,")}`,
        `DESCRIPTION:${(ticketUrl(g) ? "Tickets: " + ticketUrl(g) + "\\n" : g.ticketNote ? g.ticketNote + "\\n" : "")}Watch: ${S.links.watch}`, "END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\r\n")], { type: "text/calendar" }));
    a.download = "wvlions-soccer-2026.ics";
    a.click();
  }

  /* ---------- custom dropdown ----------
     dropdown(el, {placeholder, search, onChange}) -> {setGroups([{label, items:[{value,label}]}]), setValue(v)}
     Keyboard: arrows move, Enter picks, Esc closes, typing filters when search is on. */
  function dropdown(el, opts) {
    el.classList.add("dd");
    el.innerHTML = `<button type="button" class="dd-btn" aria-haspopup="listbox" aria-expanded="false"><span class="dd-label"></span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></button>
      <div class="dd-panel" hidden>${opts.search ? `<input class="dd-search" type="text" placeholder="${esc(opts.search)}" autocomplete="off">` : ""}<div class="dd-list" role="listbox"></div></div>`;
    const btn = el.querySelector(".dd-btn"), panel = el.querySelector(".dd-panel"), list = el.querySelector(".dd-list"), search = el.querySelector(".dd-search");
    let groups = [], value = "", active = -1;
    const all = () => [{ value: "", label: opts.placeholder }, ...groups.flatMap(g => g.items)];
    const label = () => (all().find(i => i.value === value) || all()[0]).label;
    function render() {
      const q = search ? search.value.trim().toLowerCase() : "";
      const hit = i => !q || i.label.toLowerCase().includes(q);
      let k = 0;
      const row = i => `<div class="dd-opt${i.value === value ? " sel" : ""}" role="option" data-v="${esc(i.value)}" data-k="${k++}" aria-selected="${i.value === value}">${esc(i.label)}</div>`;
      list.innerHTML = (q ? "" : row({ value: "", label: opts.placeholder })) +
        groups.map(g => { const its = g.items.filter(hit); return its.length ? (g.label ? `<div class="dd-group">${esc(g.label)}</div>` : "") + its.map(row).join("") : ""; }).join("")
        || `<div class="dd-empty">No matches</div>`;
      highlight(Math.max(0, [...list.querySelectorAll(".dd-opt")].findIndex(o => o.dataset.v === value)));
    }
    function highlight(i) {
      const os = list.querySelectorAll(".dd-opt"); if (!os.length) return;
      active = (i + os.length) % os.length;
      os.forEach((o, j) => o.classList.toggle("act", j === active));
      os[active].scrollIntoView({ block: "nearest" });
    }
    const open = () => { panel.hidden = false; btn.setAttribute("aria-expanded", "true"); el.classList.add("open"); if (search) { search.value = ""; } render(); (search || btn).focus(); };
    const close = () => { panel.hidden = true; btn.setAttribute("aria-expanded", "false"); el.classList.remove("open"); };
    const pick = v => { value = v; btn.querySelector(".dd-label").textContent = label(); el.classList.toggle("on", !!v); close(); btn.focus(); opts.onChange(v); };
    btn.addEventListener("click", () => panel.hidden ? open() : close());
    list.addEventListener("click", e => { const o = e.target.closest(".dd-opt"); if (o) pick(o.dataset.v); });
    list.addEventListener("mousemove", e => { const o = e.target.closest(".dd-opt"); if (o && +o.dataset.k !== active) highlight(+o.dataset.k); });
    if (search) search.addEventListener("input", render);
    el.addEventListener("keydown", e => {
      if (panel.hidden) { if (["ArrowDown", "Enter", " "].includes(e.key) && e.target === btn) { e.preventDefault(); open(); } return; }
      if (e.key === "Escape") { e.preventDefault(); close(); btn.focus(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); highlight(active + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); highlight(active - 1); }
      else if (e.key === "Enter") { e.preventDefault(); const o = list.querySelectorAll(".dd-opt")[active]; if (o) pick(o.dataset.v); }
    });
    document.addEventListener("click", e => { if (!el.contains(e.target)) close(); });
    return {
      setGroups(g) { groups = g; btn.querySelector(".dd-label").textContent = label(); if (!panel.hidden) render(); },
      setValue(v) { value = v; btn.querySelector(".dd-label").textContent = label(); el.classList.toggle("on", !!v); },
    };
  }

  /* ---------- photo catalog ---------- */
  function catalog() {
    $("#drive-link").href = S.links.drive;
    const games = new Map();
    photos.forEach(p => { const k = gameKey(p); if (!games.has(k)) games.set(k, { key: k, opp: p.opp, date: p.date }); });
    const gameList = [...games.values()].sort((a, b) => (b.date || "0").localeCompare(a.date || "0"));
    const gameLabel = g => g.date ? `${MON[day(g.date).getMonth()]} ${day(g.date).getDate()} · ${vsAt(gameOn(g.date))} ${g.opp}` : g.opp;
    const gameDD = dropdown($("#game"), { placeholder: "All games", onChange: v => { state.game = v; writeUrl(); draw(); } });
    gameDD.setGroups([{ items: gameList.map(g => ({ value: g.key, label: gameLabel(g) })) }]);
    const playerDD = dropdown($("#player"), { placeholder: "All players", search: "Type a name or number…", onChange: v => {
      if (!v) state.num = null;
      else { const [l, n] = v.split(":"); state.level = l; state.num = +n; }
      writeUrl(); draw();
    } });
    $("#ph-sub").innerHTML = `A selection of ${photos.length} photos from ${gameList.length} games, drawn from the season's full collection.
      Tap any photo to view full size or download. <a href="${S.links.drive}" target="_blank" rel="noopener">See all photos in Google Drive →</a>
      <small class="tag-note">Player tags are matched from jersey numbers and may not always be accurate.</small>`;

    const state = { q: "", level: "", game: "", num: null };
    let openId = "", catalogFlat = [];
    const readUrl = () => {
      const segs = location.pathname.split("/").filter(Boolean);
      const old = new URLSearchParams(location.hash.slice(1));  // links from before clean URLs: #level=jv&num=3&game=…
      Object.assign(state, { level: "", game: "", num: null, q: new URLSearchParams(location.search).get("q") || old.get("q") || "" });
      if (segs[0] === "photos") for (const s of segs.slice(1)) {
        if (LEVELS.includes(s)) state.level = s;
        else if (/^\d{1,3}$/.test(s)) state.num = +s;
        else if (/^\d{4}-\d{2}-\d{2}/.test(s)) state.game = s.slice(0, 10);
      }
      if (old.has("level")) state.level = old.get("level");
      if (old.has("game")) state.game = old.get("game");
      if (old.has("num")) state.num = +old.get("num");
      openId = segs[0] === "photo" ? decodeURIComponent(segs[1] || "") : "";
      return old.toString() !== "";
    };
    const filterUrl = () => {
      const level = state.level || (state.num !== null ? LEVELS.find(l => playerByNum(l, state.num)) || "" : "");
      return photosUrl({ level, num: state.num, game: state.game }) + (state.q ? "?q=" + encodeURIComponent(state.q) : "");
    };
    const writeUrl = () => history.replaceState(null, "", filterUrl());

    const hay = p => {
      const g = gameOn(p.date);
      const names = p.numbers.map(n => playerByNum(p.level, n)?.name || "").join(" ");
      return [p.opp, p.caption, p.level === "jv" ? "jv junior varsity" : "varsity", g ? (g.home ? "home" : "away") : "", g && g.scrimmage ? "scrimmage" : "",
        p.date ? `${MON[day(p.date).getMonth()]} ${["january","february","march","april","may","june","july","august","september","october","november","december"][day(p.date).getMonth()]}` : "",
        p.numbers.map(n => `#${n}`).join(" "), names, S.opponents[p.opp]?.mascot].join(" ").toLowerCase();
    };
    const hays = new Map(photos.map(p => [p, hay(p)]));
    const matches = p => {
      if (state.level && p.level !== state.level) return false;
      if (state.game && gameKey(p) !== state.game) return false;
      if (state.num !== null && !p.numbers.includes(state.num)) return false;
      const toks = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      return toks.every(t => /^#?\d+$/.test(t) ? p.numbers.includes(+t.replace("#", "")) : hays.get(p).includes(t));
    };

    function draw() {
      document.querySelectorAll("#level button").forEach(b => b.setAttribute("aria-pressed", b.dataset.level === state.level));
      gameDD.setValue(state.game);
      // player picker: roster players who appear in at least one photo, grouped by team
      playerDD.setGroups(LEVELS.filter(l => !state.level || state.level === l).map(l => ({
        label: LABEL[l],
        items: [...(D.roster[l] || [])].filter(pl => photos.some(x => x.level === l && x.numbers.includes(pl.num)))
          .sort((a, b) => a.num - b.num).map(pl => ({ value: `${l}:${pl.num}`, label: `#${pl.num} ${pl.name}` })),
      })).filter(g => g.items.length));
      const lv = state.level || LEVELS.find(l => playerByNum(l, state.num));
      playerDD.setValue(state.num !== null ? `${lv}:${state.num}` : "");
      const active = state.level || state.game || state.num !== null || state.q;
      $("#clear").hidden = !active;

      const list = photos.filter(matches);
      $("#count").textContent = `${list.length} photo${list.length === 1 ? "" : "s"}`;
      if (!list.length) { $("#catalog").innerHTML = `<div class="noresults">No photos match these filters.<br><button class="btn ghost sm" data-clear>Show all photos</button></div>`; return; }
      const flat = [];
      $("#catalog").innerHTML = gameList.map(g => {
        const ps = catalogSort(list.filter(p => gameKey(p) === g.key));
        if (!ps.length) return "";
        const sg = gameOn(g.date);
        const levels = [...new Set(ps.map(p => p.level))];
        const html = `<div class="group"><h2>${sg ? `${vsAt(sg)} ` : ""}${esc(g.opp)}</h2>
          <span class="meta">${g.date ? fmtDate(g.date, true) : "Non-league / preseason"}${sg && sg.scrimmage ? " · Scrimmage" : ""}${sg ? LEVELS.filter(l => sg[l]).map(l => ` · ${LABEL[l]} ${sg[l].res} ${sg[l].gf}–${sg[l].ga}`).join("") : ""} · ${ps.length} photo${ps.length === 1 ? "" : "s"}${levels.length === 1 ? ` · ${levels[0] === "jv" ? "JV" : "Varsity"}` : ""}</span></div>
          <div class="grid">${ps.map(p => {
            flat.push(p);
            return `<button data-i="${flat.length - 1}" aria-label="Open photo"><span class="ph"><img src="${p.thumb}" alt="" loading="lazy"></span>
              ${p.level === "jv" ? `<span class="tags"><span>JV</span></span>` : ""}
              <span class="cap${p.numbers.length ? "" : " empty"}" title="${p.numbers.length ? who(p).replace(/"/g, "&quot;") : ""}">${p.numbers.length ? who(p) : (p.caption ? esc(p.caption) : "&nbsp;")}</span></button>`;
          }).join("")}</div>
          <div class="drive-links">${(D.driveGames || []).filter(d => d.key === g.key && (!state.level || d.level === state.level)).map(d =>
            `<a class="btn ghost sm" href="${d.url}" target="_blank" rel="noopener">See all ${d.count} ${d.level === "jv" ? "JV" : "Varsity"} photos from this game in Google Drive →</a>`).join("")}</div>`;
        return html;
      }).join("");
      catalogFlat = flat;
      $("#catalog").onclick = e => { const b = e.target.closest("button[data-i]"); if (b) openLb(flat, +b.dataset.i, filterUrl()); };
    }

    $("#level").addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b) return;
      state.level = b.dataset.level;
      if (state.level && state.num !== null && !photos.some(p => p.level === state.level && p.numbers.includes(state.num))) state.num = null;
      writeUrl(); draw();
    });
    const clearAll = () => { Object.assign(state, { q: "", level: "", game: "", num: null }); $("#q").value = ""; writeUrl(); draw(); };
    $("#clear").addEventListener("click", clearAll);
    $("#catalog").addEventListener("click", e => { if (e.target.closest("[data-clear]")) clearAll(); });
    let qt;
    $("#q").addEventListener("input", e => { clearTimeout(qt); qt = setTimeout(() => { state.q = e.target.value.trim(); writeUrl(); draw(); }, 150); });
    const sync = () => {
      const fromOldLink = readUrl();
      if ($("#q").value.trim() !== state.q) $("#q").value = state.q;
      draw();
      if (openId) {
        const i = catalogFlat.findIndex(p => p.id === openId);
        if (i >= 0) openLb(catalogFlat, i, filterUrl()); else writeUrl();
      } else if (fromOldLink) writeUrl();
    };
    window.addEventListener("popstate", sync);
    sync();
  }

  if (document.body.dataset.page === "home") home();
  if (document.body.dataset.page === "photos") catalog();
})();
