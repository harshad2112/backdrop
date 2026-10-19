"""Build, sign and (optionally) install the Backdrop app.

usage:
  python tools/build.py                 build + sign -> dist/Backdrop-<version>.wgt
  python tools/build.py --install       ... and install it on the TV
  python tools/build.py --set-url URL   save the image ZIP URL to config.local.json (checks it first)
  python tools/build.py --check-url     download the configured ZIP and check it

Settings come from config.local.json (copy config.example.json). The image URL is
written into the packaged app only; app/index.html itself never contains it.
The TV must be in Developer Mode with Host PC IP set to this PC to --install.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT, "app")
DIST_DIR = os.path.join(ROOT, "dist")
STAGE_DIR = os.path.join(DIST_DIR, "stage")
CONFIG_FILE = os.path.join(ROOT, "config.local.json")

TIZEN_HOME = os.environ.get("TIZEN_HOME", r"C:\tizen-studio")
TIZEN = os.path.join(TIZEN_HOME, "tools", "ide", "bin", "tizen.bat" if os.name == "nt" else "tizen")
SDB = os.path.join(TIZEN_HOME, "tools", "sdb.exe" if os.name == "nt" else "sdb")
SIGNING_PROFILE = os.environ.get("BACKDROP_SIGNING_PROFILE", "Backdrop")
SDB_PORT = 26101

APP_FILES = ("config.xml", "index.html", "service.js", "icon.png")
IMAGE_RE = re.compile(r"\.(jpg|jpeg|png|gif|webp)$", re.I)
URL_RE = re.compile(r"var DEFAULT_URL = '(.*?)';")


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def app_version():
    ns = {"w": "http://www.w3.org/ns/widgets"}
    root = ET.parse(os.path.join(APP_DIR, "config.xml")).getroot()
    return root.get("version"), root.find("w:name", ns).text


def normalise_url(url):
    # Dropbox share links open a preview page unless dl=1
    if "dropbox.com" in url:
        url = re.sub(r"([?&])dl=0", r"\1dl=1", url)
        if "dl=1" not in url and "raw=1" not in url:
            url += ("&" if "?" in url else "?") + "dl=1"
    return url


def check_url(url):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    try:
        names = zipfile.ZipFile(io.BytesIO(resp.content)).namelist()
    except zipfile.BadZipFile:
        sys.exit(f"URL did not return a ZIP ({resp.headers.get('content-type')})")
    images = [n for n in names if IMAGE_RE.search(n)]
    nested = [n for n in images if "/" in n]
    print(f"ZIP ok: {len(resp.content) / 1e6:.1f} MB, {len(images)} images")
    if not images:
        sys.exit("ZIP contains no images")
    if nested:
        print(f"WARNING: {len(nested)} images are inside folders and won't be shown, e.g. {nested[0]}")


def build(image_url):
    version, name = app_version()
    shutil.rmtree(STAGE_DIR, ignore_errors=True)
    os.makedirs(STAGE_DIR)
    for f in APP_FILES:
        shutil.copy2(os.path.join(APP_DIR, f), STAGE_DIR)

    if image_url:
        index = os.path.join(STAGE_DIR, "index.html")
        with open(index, encoding="utf-8") as f:
            src = f.read()
        escaped = image_url.replace("\\", "\\\\").replace("'", "\\'")
        src, n = URL_RE.subn(lambda m: f"var DEFAULT_URL = '{escaped}';", src, count=1)
        if n != 1:
            sys.exit("DEFAULT_URL not found in app/index.html")
        with open(index, "w", encoding="utf-8", newline="") as f:
            f.write(src)
    else:
        print("no image_url configured: the app will ask for one on first start")

    code, out = run([TIZEN, "package", "-t", "wgt", "-s", SIGNING_PROFILE, "--", STAGE_DIR])
    wgt = os.path.join(STAGE_DIR, f"{name}.wgt")
    if code != 0 or not os.path.exists(wgt):
        sys.exit("signing failed:\n" + out)

    target = os.path.join(DIST_DIR, f"{name}-{version}.wgt")
    shutil.copy2(wgt, target)
    print("built", target)
    return name


def install(name, tv_ip):
    target = f"{tv_ip}:{SDB_PORT}"
    run([SDB, "connect", target])
    code, out = run([TIZEN, "install", "-n", f"{name}.wgt", "-s", target, "--", STAGE_DIR])
    if "install completed" not in out:
        sys.exit("install failed:\n" + out)
    print("installed on", target)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--install", action="store_true", help="install on the TV after building")
    p.add_argument("--set-url", metavar="URL", help="save the image ZIP URL to config.local.json")
    p.add_argument("--check-url", action="store_true", help="check the configured image ZIP URL")
    args = p.parse_args()

    config = load_config()
    if config.get("image_url"):
        config["image_url"] = normalise_url(config["image_url"])
    if args.set_url:
        url = normalise_url(args.set_url)
        check_url(url)
        config["image_url"] = url
        save_config(config)
        print("image URL saved to config.local.json")
    elif args.check_url:
        if not config.get("image_url"):
            sys.exit("no image_url in config.local.json")
        check_url(config["image_url"])

    name = build(config.get("image_url", ""))
    if args.install:
        if not config.get("tv_ip"):
            sys.exit("set tv_ip in config.local.json to install")
        install(name, config["tv_ip"])


if __name__ == "__main__":
    main()
