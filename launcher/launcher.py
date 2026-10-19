"""Open Backdrop on the TV whenever it powers on.

Apps installed in Developer Mode can't start themselves at boot on consumer
Samsung TVs, so this runs on the PC: it watches the TV's remote-control API and
opens Backdrop after each power-on, keeping it in front while the TV's own
startup app (Samsung TV Plus) finishes loading.
"""
import json
import logging
import os
import time
import warnings
from logging.handlers import RotatingFileHandler

import requests
from samsungtvws import SamsungTVWS

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, "tv-token.txt")  # created on first connect; keep it private
CONFIG_FILE = os.path.join(os.path.dirname(HERE), "config.local.json")

with open(CONFIG_FILE, encoding="utf-8") as _f:
    HOST = json.load(_f)["tv_ip"]

APP_ID = "cl9IMZpNhA.Backdrop"
POLL_SECONDS = 5
GUARD_SECONDS = 60       # keep Backdrop in front this long after power-on
GUARD_CHECK_SECONDS = 4

log = logging.getLogger("backdrop")
log.setLevel(logging.INFO)
_handler = RotatingFileHandler(os.path.join(HERE, "launcher.log"), maxBytes=200_000, backupCount=1)
_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
log.addHandler(_handler)


def power_state():
    """'on', 'standby', or None when the TV isn't reachable."""
    try:
        device = requests.get(f"http://{HOST}:8001/api/v2/", timeout=3).json()["device"]
        return device.get("PowerState", "on")
    except Exception:
        return None


def keep_in_front():
    """Open Backdrop now, then reopen it if anything covers it during the guard window."""
    tv = SamsungTVWS(host=HOST, port=8002, token_file=TOKEN_FILE, timeout=10, name="BackdropLauncher")
    start = time.time()
    launches = 0
    while time.time() - start < GUARD_SECONDS:
        try:
            if not tv.rest_app_status(APP_ID).get("visible"):
                tv.rest_app_run(APP_ID)
                launches += 1
                log.info("opened Backdrop (%d) at +%.0fs", launches, time.time() - start)
        except Exception as e:
            # the API can lag a few seconds behind the network coming up
            log.info("not ready at +%.0fs: %s", time.time() - start, e)
        time.sleep(GUARD_CHECK_SECONDS)
    try:
        visible = tv.rest_app_status(APP_ID).get("visible")
    except Exception:
        visible = None
    log.info("guard done: visible=%s after %d launch(es)", visible, launches)


def main():
    log.info("launcher started")
    was_on = power_state() == "on"  # don't take over the screen if the TV is already on
    while True:
        is_on = power_state() == "on"
        if is_on and not was_on:
            log.info("TV powered on")
            keep_in_front()
        was_on = is_on
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
