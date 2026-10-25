"""A fake internet for the tests: answers the image services Backdrop talks to with fixed data.

Used by tools/dev_server.py when BACKDROP_FAKE_NET=1, so tests are fast, repeatable, don't need
a network and don't use up anyone's Unsplash quota. Every request is logged (see LOG).

  ZIP          https://fake.test/images.zip?n=3         -> a ZIP of n images 01.jpg ... (default 3)
  Picsum       https://picsum.photos/v2/list?page=P      -> 100 wide photos, ids P*100 ... P*100+99
               https://picsum.photos/id/<id>/...          -> an image
  Unsplash     https://api.unsplash.com/photos/random?count=C&query=Q  -> C new photos for theme Q
               https://images.unsplash.com/...            -> an image
  Wallhaven    https://wallhaven.cc/api/v1/search?categories=010&q=Q   -> 24 new wallpapers of that
               category ("100" general, "010" anime, "001" people)
               https://w.wallhaven.cc/full/...            -> an image
"""
import io
import itertools
import json
import threading
import urllib.parse
import zipfile

from PIL import Image

LOG = []  # every URL requested, in order
_lock = threading.Lock()
_ids = itertools.count(1)


def _image(seed):
    """A small, valid JPEG (colour varies with seed so images differ)."""
    h = abs(hash(seed))
    img = Image.new("RGB", (32, 18), ((h >> 16) & 255, (h >> 8) & 255, h & 255))
    out = io.BytesIO()
    img.save(out, "JPEG")
    return out.getvalue()


def _json(data):
    return json.dumps(data).encode("utf-8")


def fetch(url):
    """Return (bytes, filename) for url, like a download would."""
    with _lock:
        LOG.append(url)
    u = urllib.parse.urlparse(url)
    q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
    name = u.path.rsplit("/", 1)[-1] or "download"

    if u.netloc == "fake.test":
        n = int(q.get("n", "3"))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for i in range(1, n + 1):
                z.writestr(f"{i:02d}.jpg", _image(f"zip{i}"))
        return out.getvalue(), name

    if u.netloc == "picsum.photos" and u.path == "/v2/list":
        page = int(q.get("page", "1"))
        photos = [{"id": str(page * 100 + i), "author": f"Author {page * 100 + i}", "width": 5000,
                   "height": 3333} for i in range(100)]
        return _json(photos), "list.json"
    if u.netloc in ("picsum.photos", "fastly.picsum.photos"):
        return _image(url), name

    if u.netloc == "api.unsplash.com":
        theme = q.get("query", "")
        photos = []
        for _ in range(int(q.get("count", "1"))):
            pid = f"{theme}{next(_ids)}"
            photos.append({
                "id": pid,
                "urls": {"raw": f"https://images.unsplash.com/photo-{pid}?ixid=x", "small": f"https://images.unsplash.com/small-{pid}"},
                "user": {"name": f"Photographer {pid}"},
                "links": {"download_location": f"https://api.unsplash.com/photos/{pid}/download?ixid=x"},
            })
        return _json(photos), "random.json"
    if u.netloc == "images.unsplash.com":
        return _image(url), name

    if u.netloc == "wallhaven.cc":
        bits = q.get("categories", "100")
        category = {"100": "general", "010": "anime", "001": "people"}.get(bits, "general")
        data = []
        for _ in range(24):
            wid = f"{category[:2]}{next(_ids)}"
            data.append({"id": wid, "category": category,
                         "path": f"https://w.wallhaven.cc/full/xx/wallhaven-{wid}.jpg",
                         "thumbs": {"small": f"https://th.wallhaven.cc/small/xx/{wid}.jpg"}})
        return _json({"data": data, "meta": {"total": 1000}}), "search.json"
    if u.netloc in ("w.wallhaven.cc", "th.wallhaven.cc"):
        return _image(url), name

    raise ConnectionError("fake net: no route for " + url)
