"""Shared test setup.

Starts tools/dev_server.py in test mode (temporary storage and config, fake internet - see
tools/dev/fakenet.py) and gives each test a fresh headless browser page running the real app.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE_ZIP = "https://fake.test/images.zip"
DEFAULT_CONFIG = {"tv_ip": "", "image_url": FAKE_ZIP, "unsplash_key": "test-key"}


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def server():
    tmp = tempfile.mkdtemp(prefix="backdrop-test-")
    config_file = os.path.join(tmp, "config.json")
    port = _free_port()
    env = dict(os.environ, BACKDROP_STORAGE=os.path.join(tmp, "storage"), BACKDROP_CONFIG=config_file,
               BACKDROP_FAKE_NET="1")
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "dev_server.py"), "--port", str(port)],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(base + "/__test/log", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError("dev server did not start")
    yield {"base": base, "config_file": config_file, "storage": env["BACKDROP_STORAGE"]}
    proc.kill()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


class App:
    """The running app in a browser page, plus helpers for driving it like the remote does."""

    def __init__(self, server, page):
        self.server = server
        self.page = page

    # ----- setup -----

    def open(self, config=None, settings=None):
        """Start fresh: empty storage, the given config, optional saved settings (localStorage)."""
        with open(self.server["config_file"], "w") as f:
            json.dump(dict(DEFAULT_CONFIG, **(config or {})), f)
        urllib.request.urlopen(self.server["base"] + "/__test/reset")
        # save settings from a blank page on the same origin, before any app code runs
        self.page.goto(self.server["base"] + "/__test/log")
        self.page.evaluate("s => { localStorage.clear(); for (var k in s) localStorage.setItem(k, s[k]); }",
                           {k: v if isinstance(v, str) else json.dumps(v) for k, v in (settings or {}).items()})
        self.page.goto(self.server["base"] + "/")
        return self

    # ----- remote -----

    KEYS = {"ok": "Enter", "back": "Escape", "playpause": "Space", "up": "ArrowUp", "down": "ArrowDown",
            "left": "ArrowLeft", "right": "ArrowRight"}

    def press(self, *keys):
        for key in keys:
            self.page.keyboard.press(self.KEYS.get(key, key))
            self.page.wait_for_timeout(60)

    def open_settings_page(self, index):
        """Open settings and the index-th section of the main menu (0 Display, 1 Clock, 2 Images, 3 Favorites)."""
        self.press("playpause")
        self.press(*["down"] * index)
        self.press("ok")
        self.page.wait_for_timeout(300)

    # ----- state -----

    def js(self, expression, arg=None):
        return self.page.evaluate(expression, arg)

    def setting(self, key):
        return self.js("k => localStorage.getItem(k)", key)

    def manifest(self, source):
        return json.loads(self.setting("manifest_" + source) or "[]")

    def shown(self, source=None):
        """Names of the images currently in the slideshow (optionally of one source)."""
        return self.js("s => images.filter(i => !s || i.source === s).map(i => i.name)", source)

    def files(self, folder):
        path = os.path.join(self.server["storage"], "downloads", folder)
        return sorted(os.listdir(path)) if os.path.isdir(path) else []

    def download_log(self):
        return json.loads(urllib.request.urlopen(self.server["base"] + "/__test/log").read())

    def focused(self):
        return self.js("() => { var f = document.querySelector('#panel .focused');"
                       " return f && { action: f.getAttribute('data-action'), value: f.getAttribute('data-value'),"
                       " text: f.textContent }; }")

    def wait_for(self, expression, arg=None, timeout=15000):
        self.page.wait_for_function(expression, arg=arg, timeout=timeout)

    def wait_idle(self, settle=400):
        """Wait until no download/refresh is running (and stays so briefly)."""
        self.page.wait_for_timeout(settle)
        self.wait_for("() => !refreshing")
        self.page.wait_for_timeout(settle)
        self.wait_for("() => !refreshing")


@pytest.fixture
def app(server, browser):
    context = browser.new_context(viewport={"width": 1600, "height": 900})
    # no real internet: anything not on the dev server fails, like being offline
    context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(server["base"])
                  else route.abort())
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    yield App(server, page)
    context.close()
    assert not errors, "JavaScript errors in the page: " + "; ".join(errors)
