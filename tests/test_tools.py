"""tools/build.py and tools/dev_server.py - no browser needed."""
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build  # noqa: E402

SRC = "var DEFAULT_URL = '';\nvar UNSPLASH_KEY = '';\n"


def test_inject_fills_link_and_key():
    out = build.inject_values(SRC, {"image_url": "https://x/y.zip", "unsplash_key": "abc"})
    assert "var DEFAULT_URL = 'https://x/y.zip';" in out
    assert "var UNSPLASH_KEY = 'abc';" in out


def test_inject_skips_empty_values():
    assert build.inject_values(SRC, {"image_url": "", "unsplash_key": ""}) == SRC


def test_inject_escapes_quotes_and_backslashes():
    out = build.inject_values(SRC, {"image_url": "https://x/it's\\a.zip"})
    assert "var DEFAULT_URL = 'https://x/it\\'s\\\\a.zip';" in out


def test_dropbox_links_become_direct_downloads():
    assert build.normalise_url("https://www.dropbox.com/s/a/b.zip?dl=0").endswith("dl=1")
    assert build.normalise_url("https://www.dropbox.com/s/a/b.zip").endswith("?dl=1")
    assert build.normalise_url("https://example.com/b.zip") == "https://example.com/b.zip"


def test_app_source_has_no_personal_values():
    with open(os.path.join(ROOT, "app", "index.html"), encoding="utf-8") as f:
        src = f.read()
    assert re.search(r"var DEFAULT_URL = '';", src)
    assert re.search(r"var UNSPLASH_KEY = '';", src)


def test_dev_server_refuses_paths_outside_storage(server):
    with urllib.request.urlopen(server["base"] + "/fs?op=list&path=../..") as r:
        assert b'"ok": false' in r.read()
    try:
        urllib.request.urlopen(server["base"] + "/files/..%2F..%2Fconfig.json")
        assert False, "expected 403"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_dev_server_loads_shim_and_config(server):
    with open(server["config_file"], "w") as f:
        f.write('{"image_url": "", "unsplash_key": "test-key"}')
    html = urllib.request.urlopen(server["base"] + "/").read().decode()
    assert '<script src="/dev/tizen-shim.js"></script>' in html
    assert "var UNSPLASH_KEY = 'test-key';" in html
