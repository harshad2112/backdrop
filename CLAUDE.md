# Working on Backdrop

- **Run the tests after every change**, before calling it done:
  `.venv\Scripts\python -m pytest tests` (about a minute; all must pass).
- When a change intentionally alters a feature, update that feature's tests in the same change, and add a
  test for every new feature or bug fix. Don't weaken a test just to make it pass.
- Try UI changes in the browser first (`.venv\Scripts\python tools\dev_server.py`, http://localhost:8800);
  install on the TV with `tools\build.py --install` only when asked (bump `version` in `app/config.xml`).
- Never put personal values (TV IP, image link, Unsplash key) in tracked files - they live in
  `config.local.json` and are injected at build time.
