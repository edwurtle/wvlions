// /photo/<id>: the photos page opened on one photo, with that photo's title and image in the link-preview tags
// (Facebook, texts) so a shared link shows the picture. Per-photo text comes from /photo-meta.json (built by build.py).
export async function onRequest({ request, env, params }) {
  const url = new URL(request.url);
  const page = await env.ASSETS.fetch(new Request(new URL("/photos", url), request));
  const metaRes = await env.ASSETS.fetch(new Request(new URL("/photo-meta.json", url)));
  const m = metaRes.ok ? (await metaRes.json())[params.id] : null;
  if (!m) return page;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const image = new URL(m.image, url).href;
  const tags = [
    ["og:type", "article"], ["og:site_name", "WV Lions Soccer"], ["og:title", m.title],
    ["og:description", m.description], ["og:image", image], ["og:url", url.href],
  ].map(([k, v]) => `<meta property="${k}" content="${esc(v)}">`).join("") +
    `<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="${esc(image)}">`;
  return new HTMLRewriter()
    .on("title", { element(e) { e.setInnerContent(`${m.title} · WV Lions Soccer`); } })
    .on("head", { element(e) { e.append(tags, { html: true }); } })
    .transform(page);
}
