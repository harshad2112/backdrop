# Backdrop

A full-screen photo slideshow for Samsung Tizen TVs and Smart Monitors.

Backdrop downloads a ZIP of your images, keeps a copy on the TV so it works offline, and shows them full screen
with smooth transitions. A settings overlay - opened with the remote's Play/Pause button - lets you pick the
timing, the transition and which images to show.

Tested on a Samsung Smart Monitor M7 (2022, Tizen 6.5). It should work on other Samsung TVs from 2017 onward
(Tizen 3.0+) that support Developer Mode.

## Features

- **Full-screen slideshow** with fade, slide or no transition
- **Works offline** - images are stored on the TV; Backdrop starts from the local copy immediately and checks for
  new images on start and every 6 hours. A new set only replaces the current one if it downloads and unpacks
  completely.
- **Settings overlay** (Play/Pause or INFO on the remote)
  - time per image: 5 s, 10 s, 15 s, 30 s, 1 min, 5 min or manual
  - transition: fade, slide or none
  - select / unselect individual images (new images are included automatically)
  - refresh now, change the image URL
- **Remote control**: Left/Right to change image, Back to hide the app
- **Optional PC launcher** that opens Backdrop every time the TV turns on

## How it works

```
 your images ──zip──► cloud link (e.g. Dropbox) ──download──► TV: Backdrop
                                                              ├─ keeps a local copy
                                                              └─ slideshow + settings
 PC: launcher.py ──remote-control API──► opens Backdrop when the TV powers on
```

## Requirements

- A Samsung Tizen TV or Smart Monitor with **Developer Mode** available
- A Windows PC (macOS/Linux should work for building with small changes; the launcher is cross-platform)
- [Tizen Studio](https://developer.tizen.org/development/tizen-studio/download) (the CLI version is enough)
- Python 3.9+

## Setup

### 1. Clone and install the Python tools

```
git clone https://github.com/<your-username>/backdrop.git
cd backdrop
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 2. Create your local config

Copy `config.example.json` to `config.local.json` and fill in your values:

```json
{
  "tv_ip": "192.168.1.50",
  "image_url": "https://www.dropbox.com/scl/fi/.../images.zip?rlkey=...&dl=1"
}
```

`config.local.json` is ignored by git - your TV's address and image link stay on your machine.

### 3. Create a signing certificate

TVs only install signed apps. Create a free Tizen author certificate and a signing profile named `Backdrop`:

```
tizen certificate -a Backdrop -p <password> -n "<your name>" -f backdrop-author
tizen security-profiles add -n Backdrop -a <tizen-studio-data>\keystore\author\backdrop-author.p12 -p <password>
```

Keep the certificate and password safe and **out of the repository** - every future update must be signed with
the same certificate, or the TV will refuse it.

### 4. Enable Developer Mode on the TV

1. Open **Apps**, scroll to the end of your installed apps and open the **settings gear**.
2. Type `1 2 3 4 5` (a USB keyboard works if your remote has no number keys).
3. Turn **Developer mode** on and set **Host PC IP** to your computer's IP address.
4. Restart the TV by **holding the power button until the Samsung logo appears**.
   If the TV still refuses connections afterwards, turn Developer mode off, restart, turn it back on, and restart again.

### 5. Build and install

```
.venv\Scripts\python tools\build.py --check-url --install
```

Backdrop appears in your TV's Apps list. Increase `version` in `app/config.xml` before each new install.

## Your images

- Supported formats: JPG, PNG, GIF, WebP. 16:9 images (e.g. 1920×1080 or 3840×2160) fill the screen best.
- Put the image files **directly** in the ZIP - select the files themselves and compress them, not their folder.
- Images play in file-name order, so name them `01.jpg`, `02.jpg`, ...
- Share the ZIP with a direct-download link. Dropbox share links are converted automatically (`dl=0` → `dl=1`);
  Google Drive links usually don't work because they return a web page instead of the file.

To change the images, replace the ZIP **at the same link** (in Dropbox: upload with the same name and choose
*Replace*). The TV picks it up within 6 hours, or immediately with **Refresh now** in settings.

To use a different link: `python tools\build.py --set-url "<link>" --install`, or **Change URL** in settings.

## Remote controls

| Button | Slideshow | Settings overlay |
|---|---|---|
| Play/Pause or INFO | open settings | close settings |
| Left / Right | previous / next image | move |
| Up / Down | - | move |
| OK | - | select |
| Back | hide Backdrop | close settings |

## Opening Backdrop when the TV turns on (optional)

Consumer Samsung TVs only allow **partner-certified** apps to start themselves at boot, and they don't remember
Developer Mode apps as the "last app". `launcher/launcher.py` works around this from a PC on the same network:
it watches the TV's remote-control API and opens Backdrop each time the TV powers on. For the first 60 seconds
it keeps Backdrop in front, because the TV's own startup app (Samsung TV Plus) loads a few seconds later and
would cover it.

```
.venv\Scripts\python launcher\launcher.py
```

The first time, the TV asks you to **Allow** the connection; the access token is saved to `launcher/tv-token.txt`
(ignored by git). To run it automatically, create a Windows Task Scheduler task that starts
`.venv\Scripts\pythonw.exe launcher\launcher.py` at sign-in. The launcher only works while the PC is on.

## Project layout

```
app/                  the TV app (Tizen web app; can be imported into Tizen Studio)
  config.xml          app ID, name, permissions
  index.html          slideshow, settings overlay, download + local copy
  service.js          background service (requests launch at boot; see above)
  icon.png            app icon
tools/
  build.py            build, sign and install
  draw_icon.py        regenerate the icon
launcher/
  launcher.py         opens Backdrop when the TV powers on
config.example.json   template for your config.local.json
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `12345` does nothing | Enter it in the settings gear at the end of the Apps list; try a USB keyboard |
| Install: connection refused / SDB daemon error | Host PC IP must match this PC; turn Developer Mode off and on, restart with a long press of power |
| Install: `Check certificate error` | The package isn't signed, or is signed with a different certificate than the installed version |
| "Could not download images" | The link must download the ZIP directly; check it with `build.py --check-url` |
| Images missing | They're inside a folder in the ZIP - zip the files themselves |
| Icon looks stretched or blurry | The TV caches icons; restart it with a long press of power |

## Limitations

- Needs Developer Mode; Samsung may reset it after firmware updates.
- Auto-start at power-on requires the PC launcher (see above).
- Built-in apps (e.g. Samsung TV Plus) can't be removed or replaced.

## Credits

Backdrop started from [**no-cover/wall**](https://github.com/no-cover/wall) by
[no-cover](https://github.com/no-cover), a Tizen TV app that downloads a ZIP of images and shows them as a
slideshow. That idea - and the download-and-extract approach - came from there; the app has since been
rewritten, adding the offline copy, settings overlay, transitions, image selection, build tooling and the
PC launcher. Thanks to the original author.

## License

[MIT](LICENSE) - applies to the code in this repository.
