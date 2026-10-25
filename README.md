# Backdrop

A full-screen photo slideshow for Samsung Tizen TVs and Smart Monitors.

Backdrop shows your own photos - or free photos and wallpapers from the web - full screen with smooth
transitions, and keeps a copy on the TV so it works offline. A settings overlay - opened with the remote's
Play/Pause button - lets you pick the sources, timing, transition, clock and which images to show.

Tested on a Samsung Smart Monitor M7 (2022, Tizen 6.5). It should work on other Samsung TVs from 2017 onward
(Tizen 3.0+) that support Developer Mode; see [Limitations](#limitations) for newer models.

## Features

- **Full-screen slideshow** with fade, slide or no transition, in order or shuffled
- **Image sources** - use any combination:
  - **Custom link** - a ZIP of your own images (e.g. on Dropbox)
  - **Random photos** from [Lorem Picsum](https://picsum.photos/) - no setup
  - **Photos by theme** from [Unsplash](https://unsplash.com/) - pick themes such as Nature, Ocean, City, Space
    (needs a free [Unsplash access key](#optional-unsplash-photos-by-theme))
  - **Wallpapers** from [Wallhaven](https://wallhaven.cc/) - safe-for-work 4K 16:9 wallpapers, by category
    (General, Anime, People) and optional themes
- **Favorites** - press **OK** during the slideshow to keep the current image for good (♥ in the corner).
  Favorites are never refreshed or deleted automatically; **Settings → Favorites** shows them all, has
  **Favorites only**, and is the only place to delete one (mark, then confirm), so a stray press can't lose one.
- **Works offline** - every image is stored on the TV and never downloaded twice. Backdrop starts from the local
  copy immediately; online sources add a few new images every 6 hours or daily (or only when you ask) and drop
  the oldest beyond your limit. A new ZIP only replaces your images if it downloads and unpacks completely.
- **Themes that remember** - only images of the selected themes are shown, sharing your limit equally between
  them. Unselecting a theme hides its images without deleting them, so selecting it again is instant; anything
  missing downloads a moment after you change the selection. A source's **Reload** downloads a fresh set and
  then clears its older images, of any theme.
- **Storage stays bounded** - hidden images (unselected themes and categories) are capped at your limit per
  source, oldest first, at each scheduled update; Settings → Images → General shows how much space each source
  uses and has **Clear hidden images**. Favorites are never touched.
- **Settings menu** (Play/Pause or INFO on the remote), with a section for each area:
  - **Display** - time per image (5 s to 5 min, or manual), transition (fade, slide, none), a brightness
    slider, 10 % to 100 % (dims the picture in software - apps can't change the TV's backlight), order,
    and photo credits (the site's name in the corner, plus the photographer for Unsplash)
  - **Clock** - show/hide, 24-hour, date, seconds, size (small/medium/large), position (center/bottom/corner)
  - **Images** - a tab per source: **General** (status and storage of every source, how many images to keep, how
    often to get new ones, update all now, clear hidden images) and **Custom link / Picsum / Unsplash / Wallhaven** (turn the source on or off, its
    own options such as the ZIP link or themes, **Reload**, and select / unselect its images - new images are
    included automatically)
  - **Favorites** - see below
- **Remote control**: Left/Right to change image, Back to hide the app

## How it works

```
 your images ──zip──► cloud link (e.g. Dropbox) ──┐
 Picsum / Unsplash / Wallhaven ───────────────────┴──download──► TV: Backdrop
                                                                 ├─ keeps a local copy
                                                                 └─ slideshow + settings
```

You build the app on a PC and install it on the TV over your home network, using the TV's Developer Mode.

## What you need

| | What | Where to get it |
|---|---|---|
| TV | A Samsung Tizen TV or Smart Monitor with Developer Mode, on the same network as the PC | - |
| PC | Windows 10/11 (the steps below are for Windows) | - |
| Python | 3.9 or newer - tick **"Add python.exe to PATH"** in the installer | [python.org/downloads](https://www.python.org/downloads/) |
| Git | To download this project | [git-scm.com/downloads](https://git-scm.com/downloads) |
| Tizen Studio | Samsung/Tizen SDK, used to sign and install the app. The **CLI** installer (`web-cli_Tizen_Studio_<version>_windows-64.exe`) is enough. Install it to `C:\tizen-studio` (no spaces in the path); the installer asks for administrator rights. | [Tizen Studio download](https://developer.tizen.org/development/tizen-studio/download) · [all installers](https://download.tizen.org/sdk/Installer/) |
| Image hosting (optional) | For your own images: somewhere to put a ZIP with a direct-download link, e.g. Dropbox. Not needed if you only use the online sources. | [Dropbox: share a link](https://help.dropbox.com/share/create-and-share-link) |
| Unsplash key (optional) | Only for "Photos by theme" | [Unsplash developers](https://unsplash.com/developers) |

## Setup

All commands are for **PowerShell** or **Command Prompt**, run from the project folder unless stated otherwise.

### 1. Download the project and install the Python tools

```
git clone https://github.com/harshad2112/backdrop.git
cd backdrop
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Find the IP addresses

- **PC:** run `ipconfig` and note the **IPv4 Address** of your Wi-Fi or Ethernet adapter (e.g. `192.168.1.20`).
- **TV:** Settings → General → Network → **Network Status** → **IP Settings** (e.g. `192.168.1.50`).

Tip: reserve both addresses in your router (DHCP reservation) so they don't change later.

### 3. Prepare your images (optional)

Skip this if you only want online photos - Backdrop starts with random photos from Picsum when no link is set.

1. Put your images in a folder. Supported: JPG, PNG, GIF, WebP. 16:9 images (1920×1080 or 3840×2160) fill the
   screen best. Name them in the order you want: `01.jpg`, `02.jpg`, ...
2. Open the folder, select **all the image files** (Ctrl+A), right-click → **Compress to ZIP file**.
   Zip the files themselves - not the folder - or the images will be ignored.
3. Upload the ZIP to Dropbox, then **Share → Copy link** (anyone with the link can view).

Backdrop converts Dropbox share links to direct downloads automatically. Other hosts work if the link downloads
the ZIP file directly; Google Drive links usually don't, because they return a web page.

### 4. Create your local config

Copy `config.example.json` to `config.local.json` and fill in the TV's IP, and optionally your link and
Unsplash key (leave them empty if you don't use them):

```json
{
  "tv_ip": "192.168.1.50",
  "image_url": "https://www.dropbox.com/scl/fi/.../images.zip?rlkey=...&dl=0",
  "unsplash_key": ""
}
```

Or set and check the link with `.venv\Scripts\python tools\build.py --set-url "<link>"`.
`config.local.json` is ignored by git, so your TV's address, image link and key stay on your machine.

#### Optional: Unsplash photos by theme

1. Sign in at [unsplash.com/developers](https://unsplash.com/developers) → **Your apps** → **New Application**,
   accept the terms and give it a name.
2. Copy the **Access Key** (not the Secret key) into `"unsplash_key"`.

The free (demo) tier allows 50 requests an hour, far more than Backdrop needs - it makes one request per theme
when it fetches new photos. As Unsplash requires, Backdrop credits the photographer on screen
("Name · Unsplash", Display → Show photo credits) and reports each download to Unsplash.

### 5. Create a signing certificate

Samsung TVs only install signed apps. Create a free Tizen author certificate and a signing profile named `Backdrop`
(replace `<password>` and `<your name>`; the `tizen` tool is not on the PATH, so use its full path):

```
set TIZEN=C:\tizen-studio\tools\ide\bin\tizen.bat
%TIZEN% certificate -a Backdrop -p <password> -n "<your name>" -f backdrop-author
%TIZEN% security-profiles add -n Backdrop -a C:\tizen-studio-data\keystore\author\backdrop-author.p12 -p <password>
%TIZEN% cli-config "profiles.path=C:\tizen-studio-data\profile\profiles.xml"
```

(In PowerShell use `$TIZEN = "C:\tizen-studio\tools\ide\bin\tizen.bat"` and `& $TIZEN ...` instead.)

**Keep the `.p12` file and password safe, and never commit them.** Every later update must be signed with the
same certificate, or the TV will refuse it. More: [Samsung - Creating certificates](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/creating-certificates.html).

### 6. Turn on Developer Mode on the TV

1. On the TV, open **Apps**, scroll to the end of your installed apps and open the **settings gear**.
2. Type `1 2 3 4 5`. If your remote has no number keys, plug in a **USB keyboard** and type it there.
   Nothing appears while you type; the Developer Mode window opens after the last digit.
3. Turn **Developer mode** on, set **Host PC IP** to your PC's IP from step 2, and press OK.
4. Restart the TV by **holding the remote's power button until the Samsung logo appears**
   (a normal off/on is not enough).

If installing later fails with a connection error, turn Developer mode **off**, restart, turn it **on** again
with your PC's IP, and restart once more. Samsung's guide: [Connecting the TV](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html).

### 7. Build and install

```
.venv\Scripts\python tools\build.py --check-url --install
```

This checks your image link, builds and signs the app (a copy is kept in `dist\`), and installs it on the TV.
**Backdrop** then appears in the TV's Apps list. The first start downloads your images; after that it starts
from the local copy.

### Updating

After changing the code, increase `version` in `app/config.xml` (e.g. `2.0.0` → `2.0.1`) and run step 7 again.
Developer Mode must still point to your PC.

To change the images, replace the ZIP **at the same link** (in Dropbox: upload a file with the same name and
choose *Replace*). The TV picks it up within 6 hours, or immediately with **Refresh now** in settings.
For a new link: `build.py --set-url "<link>" --install`, or **Change URL** in settings.

### Uninstalling

```
C:\tizen-studio\tools\ide\bin\tizen.bat uninstall -p cl9IMZpNhA.Backdrop -s <tv_ip>:26101
```

## Developing in a browser

Installing on the TV takes a while, so for day-to-day changes run Backdrop in your desktop browser:

```
.venv\Scripts\python tools\dev_server.py
```

Open <http://localhost:8800>, edit `app/index.html`, and refresh the page. No build, signing or TV needed.

- The page renders at the TV's resolution (1920×1080), scaled to fit the window.
- `tools/dev/tizen-shim.js` stands in for the TV-only Tizen APIs (files, downloads, ZIP, remote keys). The dev
  server keeps the "TV storage" in `dev-storage/` (ignored by git), so downloaded images and favorites survive
  reloads, and it downloads images itself, so sites that block browser requests still work.
- Your link and Unsplash key come from `config.local.json`, as in the build.
- Keyboard instead of the remote: **arrows**, **Enter** = OK, **Space / P** = Play/Pause, **Esc / Backspace** =
  Back, **I** = INFO.
- Settings are kept in the browser's local storage for `localhost:8800`; clear the site data to start fresh.

When it looks right, install it on the TV with `build.py --install`. Behaviour that depends on the TV itself
(remote quirks, performance, the TV's own apps) still needs a check on the TV.

## Remote controls

| Button | Slideshow | Settings menu | Inside a section |
|---|---|---|---|
| Play/Pause or INFO | open settings | close settings | close settings |
| Up / Down | - | move | move |
| Left / Right | previous / next image | Right opens the section | move; adjust sliders and switches |
| OK | add to favorites | open the section | select / toggle |
| Back | hide Backdrop | close settings | back to the menu |

## Tests

Run the tests after every change - they check every feature and every bug fixed so far:

```
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python -m pytest tests
```

(The first two lines are one-time setup.) The tests run the real app in a headless Chromium through the dev
server, pressing the same keys as the remote. They never use the internet: in test mode the dev server answers
Picsum, Unsplash, Wallhaven and ZIP requests with fake data (`tools/dev/fakenet.py`), so the run is fast,
repeatable and doesn't touch your Unsplash quota. Each test starts with empty storage and settings.

| File | Covers |
|---|---|
| `tests/test_slideshow.py` | custom link, first start without a link, transitions under quick key presses, credits |
| `tests/test_settings.py` | menu and pages, panel size, focus not clipped, messages above the menu, tabs, brightness, clock, order |
| `tests/test_sources.py` | downloading to the limit, reuse after restart, themes and categories sharing the limit, hide-don't-delete, Reload, trimming, clean-up, hidden-image cap, clearing hidden images, storage display |
| `tests/test_favorites.py` | saving with OK, Custom link favorites shown once, OK never removes, two-step delete, survival across reloads |
| `tests/test_tools.py` | build-time injection of your link and key, Dropbox links, dev server path safety |

When a change is meant to alter a feature, update its test in the same change.

## Project layout

```
app/                  the TV app (Tizen web app; can be imported into Tizen Studio)
  config.xml          app ID, name, permissions
  index.html          slideshow, settings overlay, download + local copy
  service.js          background service (requests launch at boot; see Limitations)
  icon.png            app icon
tools/
  build.py            build, sign and install
  dev_server.py       run the app in a desktop browser (see Developing in a browser)
  dev/tizen-shim.js   browser stand-in for the TV's Tizen APIs (dev only, never packaged)
  dev/fakenet.py      fake image services for the tests
  draw_icon.py        regenerate the icon: python tools\draw_icon.py app\icon.png 304
tests/                automated tests (see Tests)
config.example.json   template for your config.local.json
```

To edit the app in Tizen Studio's IDE: **File → Import → General → Existing Projects into Workspace**, choose the
`app` folder, and leave *Copy projects into workspace* unticked.

## Troubleshooting

| Problem | Fix |
|---|---|
| `12345` does nothing | Enter it in the settings gear at the end of the Apps list; try a USB keyboard |
| Install: `connection refused` / SDB daemon error | Host PC IP on the TV must be this PC's IP; turn Developer Mode off and on, restart with a long press of power |
| Install: `Check certificate error` | The package isn't signed, or is signed with a different certificate than the installed version |
| `tizen` says *Tizen Studio is not installed properly* | The installer didn't finish. Re-run it, or create `C:\tizen-studio\sdk.info` with the two lines `TIZEN_SDK_INSTALLED_PATH=C:\tizen-studio` and `TIZEN_SDK_DATA_PATH=C:\tizen-studio-data` |
| Signing fails: profile not found | Run the `cli-config` command from step 5 |
| "Could not download images" | The link must download the ZIP directly; check it with `build.py --check-url` |
| Some images missing | They're inside a folder in the ZIP - zip the files themselves |
| New icon doesn't show | The TV caches icons; restart it with a long press of power |

## Limitations

- Needs Developer Mode; Samsung may turn it off after firmware updates.
- Tested on Tizen 6.5. Newer TVs (Tizen 7.0+, roughly 2023 models onward) may refuse apps signed with a Tizen
  certificate; they need a **Samsung** certificate, created in Tizen Studio's Certificate Manager with the
  *Samsung Certificate Extension* - see [Creating certificates](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/creating-certificates.html).
- **No automatic start after a power cut.** Consumer Samsung TVs only let partner-certified apps start themselves
  at boot, and they don't remember Developer Mode apps as the "last app". Turning the TV off and on with the
  remote is fine - Backdrop stays loaded in standby and comes back - but after unplugging or a power cut the TV
  starts its own default app and you open Backdrop from Apps.
- Built-in apps (e.g. Samsung TV Plus) can't be removed or replaced.

## Image licenses

Backdrop downloads images for display on your own TV. The images belong to their creators:

- **Lorem Picsum** - photos from Unsplash, under the [Unsplash License](https://unsplash.com/license).
- **Unsplash** - [Unsplash License](https://unsplash.com/license); use follows the
  [Unsplash API guidelines](https://help.unsplash.com/en/articles/2511245-unsplash-api-guidelines)
  (credit the photographer, report downloads).
- **Wallhaven** - user-uploaded wallpapers; the rights differ per image and many are not freely licensed.
  Fine for your own screen, but don't redistribute them. Only safe-for-work images are requested.

## Credits

Backdrop started from [**no-cover/wall**](https://github.com/no-cover/wall) by
[no-cover](https://github.com/no-cover), a Tizen TV app that downloads a ZIP of images and shows them as a
slideshow. That idea - and the download-and-extract approach - came from there; the app has since been
rewritten, adding the offline copy, settings overlay, transitions, image selection and build tooling.
Thanks to the original author.

## License

[MIT](LICENSE) - applies to the code in this repository.
