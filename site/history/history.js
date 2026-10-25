/* History section behavior (pages built by scripts/history.py). Each block runs only if its page has the element. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  /* ---------- team photo lightbox ---------- */
  const lb = $("#h-lb");
  const closeLb = () => { lb.hidden = true; $("img", lb).src = ""; };
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-full]");
    if (b) { $("img", lb).src = b.dataset.full; $("p", lb).textContent = b.dataset.cap || ""; lb.hidden = false; return; }
    if (!lb.hidden && (e.target === lb || e.target.closest(".h-lb button"))) closeLb();
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !lb.hidden) closeLb(); });

  /* ---------- current season, live from ../data.js ---------- */
  const D = window.DATA;
  if (D && $("[data-live]")) {
    const gs = D.schedule.games.filter(g => !g.scrimmage && g.varsity);
    const c = k => gs.filter(g => g.varsity.res === k).length;
    const gf = gs.reduce((s, g) => s + g.varsity.gf, 0), ga = gs.reduce((s, g) => s + g.varsity.ga, 0);
    const rec = `${c("W")}-${c("L")}-${c("T")}`;
    $$('[data-live="record"]').forEach(el => { el.textContent = gs.length ? rec : "In progress"; });
    $$('[data-live="gfga"]').forEach(el => { el.textContent = `${gf} GF · ${ga} GA`; });
    const list = $('[data-live="games"]');
    if (list) list.innerHTML = gs.map(g => {
      const d = new Date(g.date + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });
      const r = g.varsity;
      return `<li><span class="d">${d}</span><span class="o">${g.home ? "" : "at "}${esc(g.opp)}</span><span class="res ${r.res}"><i>${r.res}</i>${r.gf}–${r.ga}</span></li>`;
    }).join("") || '<li><span class="o">No results yet</span></li>';
  }

  /* ---------- decade jump bar ---------- */
  const jump = $$(".jump a");
  if (jump.length) {
    const bar = $(".jump .wrap"), decades = $$(".decade");
    let target = null; // decade being scrolled to after a tap; the highlight stays on it until the scroll settles
    const mark = id => {
      jump.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + id));
      const on = jump.find(a => a.classList.contains("on"));
      // scroll only the bar sideways: scrollIntoView here would also cancel the page's own scroll
      if (on) bar.scrollTo({ left: on.offsetLeft - (bar.clientWidth - on.offsetWidth) / 2, behavior: "smooth" });
    };
    const offset = () => $(".top").offsetHeight + $(".jump").offsetHeight + 8;
    jump.forEach(a => a.addEventListener("click", e => {
      const d = $(a.getAttribute("href"));
      if (!d) return;
      e.preventDefault();
      target = d.id;
      mark(target);
      window.scrollTo({ top: d.getBoundingClientRect().top + scrollY - offset(), behavior: "smooth" });
      try { history.replaceState(null, "", "#" + d.id); } catch (err) {}
    }));
    let settle;
    window.addEventListener("scroll", () => {
      clearTimeout(settle);
      settle = setTimeout(() => { target = null; }, 150);
      if (target) return;
      const line = Math.max(offset() + 40, innerHeight * .35); // a decade counts as current once its heading reaches the upper third
      const cur = decades.filter(d => d.getBoundingClientRect().top <= line).pop() || decades[0];
      if (!jump.find(a => a.classList.contains("on") && a.getAttribute("href") === "#" + cur.id)) mark(cur.id);
    }, { passive: true });
  }

  /* ---------- win % chart tooltip ---------- */
  const box = $(".chartbox");
  if (box) {
    const tip = $(".tip", box);
    const show = el => {
      const r = el.getBoundingClientRect(), b = box.getBoundingClientRect();
      tip.textContent = el.dataset.tip;
      tip.hidden = false;
      tip.style.left = Math.min(Math.max(r.left + r.width / 2 - b.left, 90), b.width - 90) + "px";
      tip.style.top = (r.top - b.top + 10) + "px";
    };
    $$(".hit", box).forEach(h => {
      h.addEventListener("mouseenter", () => show(h));
      h.addEventListener("click", () => show(h));
      h.querySelector("title")?.remove(); // the custom tooltip replaces the browser's
    });
    box.addEventListener("mouseleave", () => { tip.hidden = true; });
  }

  /* ---------- head-to-head: sort + filter ---------- */
  const tbl = $("table.sortable");
  if (tbl) {
    const body = $("tbody", tbl);
    $$("th[data-k]", tbl).forEach(th => th.addEventListener("click", () => {
      const k = +th.dataset.k, asc = th.getAttribute("aria-sort") === "descending" ? true : k === 0 && th.getAttribute("aria-sort") !== "ascending";
      $$("th", tbl).forEach(x => x.removeAttribute("aria-sort"));
      th.setAttribute("aria-sort", asc ? "ascending" : "descending");
      const val = tr => { const v = tr.children[k].dataset.v; return k === 0 ? v.toLowerCase() : +v; };
      [...body.rows].sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * (asc ? 1 : -1)).forEach(r => body.append(r));
    }));
    const q = $(".h2h-q input");
    q && q.addEventListener("input", () => {
      const s = q.value.trim().toLowerCase();
      [...body.rows].forEach(r => { r.hidden = s && !r.dataset.opp.includes(s); });
    });
  }

  /* ---------- players search ---------- */
  const P = window.PLAYERS, out = $("#plist");
  if (P && out) {
    const input = $("#pq"), count = $("#pcount"), az = $("#paz");
    const last = n => n.split(" ").pop().toUpperCase();
    const hl = (s, q) => q ? esc(s).replace(new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>") : esc(s);
    const row = ([n, ys], q) => `<div class="pl"><b>${hl(n, q)}</b><span class="ys">${ys.map(([y, c, num]) =>
      `<a href="${y}"${c ? ' class="c" title="Captain"' : ""}>${y}${c ? " ©" : ""}</a>`).join("")}</span></div>`;
    const render = () => {
      const q = input.value.trim();
      const ql = q.toLowerCase();
      const hits = !q ? P : P.filter(([n, ys]) => n.toLowerCase().includes(ql) || ys.some(([y]) => String(y) === q));
      count.textContent = `${hits.length.toLocaleString()} ${hits.length === 1 ? "name" : "names"}`;
      if (!hits.length) { out.innerHTML = '<p class="noresults">No one by that name yet. Older rosters sometimes list only a first initial, so try just the last name.</p>'; az.hidden = true; return; }
      const groups = {};
      hits.forEach(p => { (groups[last(p[0])[0]] = groups[last(p[0])[0]] || []).push(p); });
      const letters = Object.keys(groups).sort();
      az.hidden = !!q;
      az.innerHTML = letters.map(l => `<a href="#L${l}">${l}</a>`).join("");
      out.innerHTML = letters.map(l => `<h2 id="L${l}">${l}</h2><div class="pgrid">${groups[l].map(p => row(p, q && !/^\d{4}$/.test(q) ? q : "")).join("")}</div>`).join("");
      try { history.replaceState(null, "", q ? "?q=" + encodeURIComponent(q) : location.pathname); } catch (e) {}
    };
    input.value = new URLSearchParams(location.search).get("q") || "";
    input.addEventListener("input", render);
    render();
  }
})();
