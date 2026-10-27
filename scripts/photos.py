#!/usr/bin/env python3
"""Download the curated photo picks from Google Drive and write data/photos.json.

Only the picks are fetched, at web size via Drive's thumbnail endpoint (never the
original RAW/NEF files), then saved as WebP:
  site/photos/full/<id>.webp   1600px long edge
  site/photos/thumb/<id>.webp   640px long edge

Inputs (scripts/cache/): drive.json (folder index from drive_index.py),
cand.json (contact-sheet tag -> photo), picks.txt (tag|numbers|caption|featured).
Folder -> game mapping lives in data/photo_folders.json. A cand.json entry with "local" (a file
in scripts/cache/local/) is used instead of Drive for photos shared some other way.

For the Download menu it also records each pick's full-size JPEG and RAW (NEF) links
with their byte sizes and pixel size (read from a ranged request, not a full
download); these are cached in scripts/cache/originals.json.

Needs Pillow:  python3 -m venv .venv && .venv/bin/pip install pillow
"""
import io, json, pathlib, re, subprocess, sys
from PIL import Image, ImageFile
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "scripts" / "cache"
OUT = ROOT / "site" / "photos"


def fetch(file_id, size):
    url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w{size}"
    return subprocess.check_output(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "90", url])


def probe(url, head=False):
    """Total size of a Drive file (and its pixel size if head) without downloading it all."""
    out = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "90", "-r", "0-262143" if head else "0-0",
                          "-D", "/dev/stderr", url], capture_output=True)
    total = re.findall(rb"(?im)^content-range:\s*bytes [^/]+/(\d+)", out.stderr)
    info = {"bytes": int(total[-1])} if total else {}
    if head:
        try:
            p = ImageFile.Parser(); p.feed(out.stdout)
            if p.image: info["w"], info["h"] = p.image.size
        except Exception:
            pass
    return info


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    cand = json.loads((CACHE / "cand.json").read_text())
    folders = json.loads((ROOT / "data" / "photo_folders.json").read_text())
    (OUT / "full").mkdir(parents=True, exist_ok=True)
    (OUT / "thumb").mkdir(parents=True, exist_ok=True)
    # originals for the Download button: camera JPGs/PNGs download as-is; a RAW (NEF) pick uses its JPG twin
    # from the same folder when there is one, else Drive's full-resolution JPEG render of the RAW
    # (served from lh3.googleusercontent.com, which allows the site to fetch it and save it as a file)
    drive = json.loads((CACHE / "drive.json").read_text())
    twin = {(folder, f["name"].rsplit(".", 1)[0].upper()): f["id"]
            for folder, files in drive.items() for f in files if f["name"].upper().endswith((".JPG", ".JPEG"))}

    raws = {(folder, f["name"].rsplit(".", 1)[0].upper()): f["id"]
            for folder, files in drive.items() for f in files if f["name"].upper().endswith(".NEF")}
    uc = "https://drive.google.com/uc?export=download&id={}".format

    def links(c):
        stem = (c["folder"], c["name"].rsplit(".", 1)[0].upper())
        if c.get("local"):  # photo shared outside Drive: only the web-size copy is offered
            return None, None
        if c["name"].upper().endswith(".NEF"):
            jid = twin.get(stem)
            full = dict(url=uc(jid), type="JPG", converted=False) if jid else \
                dict(url=f"https://lh3.googleusercontent.com/d/{c['id']}=w8000", type="JPG", converted=True)
            rid = c["id"]
        else:
            full = dict(url=uc(c["id"]), type=c["name"].rsplit(".", 1)[-1].upper().replace("JPEG", "JPG"), converted=False)
            rid = raws.get(stem)
        return full, (dict(url=uc(rid), type="NEF") if rid else None)

    sizes_path = CACHE / "originals.json"
    sizes = json.loads(sizes_path.read_text()) if sizes_path.exists() else {}

    def measure(url, head):
        if url not in sizes:
            sizes[url] = probe(url, head)
        return sizes[url]

    photos = []
    for line in (CACHE / "picks.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        tag, nums, caption, featured, crop, credit = (line.split("|") + ["", "", "", "", ""])[:6]
        c = cand[tag]
        info = folders[c["folder"]]
        if "split" in info:  # mixed folder: pick the game by file number
            num = int(re.search(r"\d+", c["name"]).group())
            info = {**info, **next(s for s in info["split"] if num <= s["upto"])}
        pid = f"{info['level']}-{slug(info['opp'])}-{c['name'].rsplit('.', 1)[0].lower()}"
        if any(x["id"] == pid for x in photos):  # same filename picked from two folders (e.g. an edits subfolder)
            sys.exit(f"duplicate photo id {pid} (pick {tag}); keep only one version in picks.txt")
        full, thumb = OUT / "full" / f"{pid}.webp", OUT / "thumb" / f"{pid}.webp"
        if not full.exists():
            if c.get("local"):  # file dropped in scripts/cache/local/ (e.g. a parent's phone photo)
                im = Image.open(CACHE / "local" / c["local"]).convert("RGB")
            else:
                im = Image.open(io.BytesIO(fetch(c["id"], 1600))).convert("RGB")
            if info.get("crop_bottom"):  # trim burned-in camera date stamps
                im = im.crop((0, 0, im.width, round(im.height * (1 - info["crop_bottom"]))))
            if crop:  # per-photo "top,bottom" fractions to trim, e.g. empty bleachers above a group shot
                top, bottom = map(float, crop.split(","))
                im = im.crop((0, round(im.height * top), im.width, round(im.height * (1 - bottom))))
            im.thumbnail((1600, 1600))  # full-res local files; Drive previews are already this size
            im.save(full, "WEBP", quality=80, method=6)
            im.thumbnail((640, 640))
            im.save(thumb, "WEBP", quality=74, method=6)
            print("saved", pid)
        w, h = Image.open(full).size
        photos.append(dict(
            id=pid, full=f"photos/full/{pid}.webp", thumb=f"photos/thumb/{pid}.webp", w=w, h=h,
            level=info["level"], opp=info["opp"], date=info["date"],
            numbers=[int(n) for n in nums.split(",") if n.strip()],
            caption=caption.strip() or None, featured=featured.strip() == "1",
            **({"credit": credit.strip()} if credit.strip() else {}),
            drive=c.get("id") and f"https://drive.google.com/file/d/{c['id']}/view", _links=links(c)))
    # sizes for the Download menu (cached; only new picks hit Drive)
    jobs = {l["url"]: l is p["_links"][0] for p in photos for l in p["_links"] if l}
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(lambda kv: measure(*kv), [kv for kv in jobs.items() if kv[0] not in sizes]))
    sizes_path.write_text(json.dumps(sizes, indent=0))
    for p in photos:
        full, raw = p.pop("_links")
        p["download"] = dict(web=dict(bytes=(ROOT / "site" / p["full"]).stat().st_size),
                             **({"full": {**full, **sizes.get(full["url"], {})}} if full else {}),
                             **({"raw": {**raw, **sizes.get(raw["url"], {})}} if raw else {}))
    (ROOT / "data" / "photos.json").write_text(json.dumps(photos, indent=1))
    print(f"{len(photos)} photos -> data/photos.json")


if __name__ == "__main__":
    sys.exit(main())
