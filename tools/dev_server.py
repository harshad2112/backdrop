"""Run Backdrop in a desktop browser - no TV, no build, no install.

usage: python tools/dev_server.py [--port 8800]
then open http://localhost:8800

The app uses Tizen APIs (files, downloads, ZIP, remote keys) that only exist on the TV.
tools/dev/tizen-shim.js stands in for them in the browser, and this server does the parts
a browser can't: it keeps "TV storage" on disk in dev-storage/ (so images and favorites
survive reloads), downloads images server-side (no CORS problems) and unzips ZIPs.
Your link and Unsplash key are filled in from config.local.json, as tools/build.py does.

Keyboard instead of the remote: arrows, Enter = OK, Space/P = Play/Pause,
Esc/Backspace = Back, I = INFO.

The tests (tests/) start this server with BACKDROP_STORAGE / BACKDROP_CONFIG pointing at temporary
files and BACKDROP_FAKE_NET=1, which answers image services with fake data (tools/dev/fakenet.py).
"""
import argparse
import http.server
import json
import mimetypes
import os
import re
import shutil
import sys
import urllib.parse
import zipfile

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build import inject_values  # noqa: E402  (same injection as the real build)

APP_DIR = os.path.join(ROOT, "app")
SHIM = os.path.join(ROOT, "tools", "dev", "tizen-shim.js")
# stands in for the TV's storage ("downloads/...")
STORAGE = os.path.abspath(os.environ.get("BACKDROP_STORAGE", os.path.join(ROOT, "dev-storage")))
CONFIG_FILE = os.environ.get("BACKDROP_CONFIG", os.path.join(ROOT, "config.local.json"))
FAKE_NET = os.environ.get("BACKDROP_FAKE_NET") == "1"
if FAKE_NET:
    sys.path.insert(0, os.path.join(ROOT, "tools", "dev"))
    import fakenet  # noqa: E402


def local_path(virtual):
    """Map a Tizen virtual path like 'downloads/backdrop-a/x.jpg' into dev-storage, safely."""
    path = os.path.normpath(os.path.join(STORAGE, virtual.strip("/")))
    if path != STORAGE and not path.startswith(STORAGE + os.sep):
        raise ValueError("path outside storage: " + virtual)
    return path


def page():
    with open(os.path.join(APP_DIR, "index.html"), encoding="utf-8") as f:
        src = f.read()
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)
    src = inject_values(src, config)
    # load the Tizen stand-in before the app's own script
    return src.replace('<script type="text/javascript">', '<script src="/dev/tizen-shim.js"></script>\n\t'
                       '<script type="text/javascript">', 1)


def fs(op, q):
    """File operations for the shim. Returns a JSON-able value or raises."""
    p = lambda name: local_path(q[name])
    if op == "stat":
        path = p("path")
        return {"exists": os.path.exists(path), "isDir": os.path.isdir(path)}
    if op == "list":
        path = p("path")
        return [{"name": n, "isFile": os.path.isfile(os.path.join(path, n)),
                 "size": os.path.getsize(os.path.join(path, n)) if os.path.isfile(os.path.join(path, n)) else 0}
                for n in sorted(os.listdir(path))]
    if op == "mkdir":
        path = p("path")
        existed = os.path.isdir(path)
        os.makedirs(path, exist_ok=True)
        return {"existed": existed}
    if op == "rm":
        os.remove(p("path"))
        return {}
    if op == "rmdir":
        shutil.rmtree(p("path"))
        return {}
    if op in ("move", "copy"):
        src, dst = p("from"), p("to")
        if os.path.exists(dst) and q.get("overwrite") != "true":
            raise FileExistsError(q["to"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        (shutil.move if op == "move" else shutil.copy2)(src, dst)
        return {}
    if op == "read":
        with open(p("path"), encoding="utf-8") as f:
            return {"text": f.read()}
    if op == "download":
        folder = p("dir")
        os.makedirs(folder, exist_ok=True)
        if FAKE_NET:
            content, served_name = fakenet.fetch(q["url"])
            name = q.get("name") or served_name
        else:
            resp = requests.get(q["url"], timeout=90, headers={"User-Agent": "Backdrop-dev"})
            resp.raise_for_status()
            content = resp.content
            # like the TV: the server's file name (Content-Disposition, e.g. Dropbox) or the URL's
            disposition = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', resp.headers.get("Content-Disposition", ""))
            name = (q.get("name") or (disposition and urllib.parse.unquote(disposition.group(1)))
                    or os.path.basename(urllib.parse.urlparse(resp.url).path) or "download")
        name = re.sub(r"[^\w.\-]", "_", name)
        with open(os.path.join(folder, name), "wb") as f:
            f.write(content)
        return {"name": name}
    if op == "unzip":
        dest = p("dest")
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(p("zip")) as z:
            for member in z.namelist():  # refuse paths that escape the destination
                target = os.path.normpath(os.path.join(dest, member))
                if not target.startswith(dest + os.sep):
                    raise ValueError("unsafe path in ZIP: " + member)
            z.extractall(dest)
        return {}
    raise ValueError("unknown op " + op)


class Handler(http.server.BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            return self.send(200, page(), "text/html; charset=utf-8")
        if url.path == "/dev/tizen-shim.js":
            with open(SHIM, encoding="utf-8") as f:
                return self.send(200, f.read(), "application/javascript; charset=utf-8")
        if url.path == "/fs":
            q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
            try:
                return self.send(200, json.dumps({"ok": True, "result": fs(q.pop("op"), q)}), "application/json")
            except Exception as e:
                return self.send(200, json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)}),
                                 "application/json")
        if FAKE_NET and url.path == "/__test/log":  # tests: which URLs were downloaded
            return self.send(200, json.dumps(fakenet.LOG), "application/json")
        if FAKE_NET and url.path == "/__test/reset":  # tests: empty storage and the log
            shutil.rmtree(STORAGE, ignore_errors=True)
            os.makedirs(os.path.join(STORAGE, "downloads"), exist_ok=True)
            del fakenet.LOG[:]
            return self.send(200, "{}", "application/json")
        if url.path.startswith("/files/"):  # what File.toURI() points at
            try:
                path = local_path(urllib.parse.unquote(url.path[len("/files/"):]))
            except ValueError:
                return self.send(403, "forbidden", "text/plain")
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    return self.send(200, f.read(), mimetypes.guess_type(path)[0] or "application/octet-stream")
            return self.send(404, "not found", "text/plain")
        # anything else from app/ (icon etc.)
        path = os.path.normpath(os.path.join(APP_DIR, url.path.lstrip("/")))
        if path.startswith(APP_DIR + os.sep) and os.path.isfile(path):
            with open(path, "rb") as f:
                return self.send(200, f.read(), mimetypes.guess_type(path)[0] or "application/octet-stream")
        return self.send(404, "not found", "text/plain")

    def log_message(self, fmt, *args):
        if "/fs?" not in (args[0] if args else ""):  # keep the console readable
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8800)
    args = parser.parse_args()
    os.makedirs(os.path.join(STORAGE, "downloads"), exist_ok=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Backdrop dev server: http://localhost:{args.port}  (storage: {STORAGE})")
    print("Keys: arrows, Enter = OK, Space/P = Play/Pause, Esc/Backspace = Back, I = INFO. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
