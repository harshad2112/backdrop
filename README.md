# Backdrop

A full-screen photo slideshow for Samsung Tizen TVs and Smart Monitors.

Backdrop downloads a ZIP of your images, keeps a copy on the TV so it works offline, and shows them full screen
with smooth transitions. A settings overlay - opened with the remote's Play/Pause button - lets you pick the
timing, the transition and which images to show.

Tested on a Samsung Smart Monitor M7 (2022, Tizen 6.5). It should work on other Samsung TVs from 2017 onward
(Tizen 3.0+) that support Developer Mode; see [Limitations](#limitations) for newer models.

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

## How it works

```
 your images ──zip──► cloud link (e.g. Dropbox) ──download──► TV: Backdrop
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
| Image hosting | Somewhere to put a ZIP with a direct-download link, e.g. Dropbox | [Dropbox: share a link](https://help.dropbox.com/share/create-and-share-link) |

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

### 3. Prepare your images

1. Put your images in a folder. Supported: JPG, PNG, GIF, WebP. 16:9 images (1920×1080 or 3840×2160) fill the
   screen best. Name them in the order you want: `01.jpg`, `02.jpg`, ...
2. Open the folder, select **all the image files** (Ctrl+A), right-click → **Compress to ZIP file**.
   Zip the files themselves - not the folder - or the images will be ignored.
3. Upload the ZIP to Dropbox, then **Share → Copy link** (anyone with the link can view).

Backdrop converts Dropbox share links to direct downloads automatically. Other hosts work if the link downloads
the ZIP file directly; Google Drive links usually don't, because they return a web page.

### 4. Create your local config

Copy `config.example.json` to `config.local.json` and fill in the TV's IP and your link:

```json
{
  "tv_ip": "192.168.1.50",
  "image_url": "https://www.dropbox.com/scl/fi/.../images.zip?rlkey=...&dl=0"
}
```

Or set and check the link with `.venv\Scripts\python tools\build.py --set-url "<link>"`.
`config.local.json` is ignored by git, so your TV's address and image link stay on your machine.

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

## Remote controls

| Button | Slideshow | Settings overlay |
|---|---|---|
| Play/Pause or INFO | open settings | close settings |
| Left / Right | previous / next image | move |
| Up / Down | - | move |
| OK | - | select |
| Back | hide Backdrop | close settings |

## Project layout

```
app/                  the TV app (Tizen web app; can be imported into Tizen Studio)
  config.xml          app ID, name, permissions
  index.html          slideshow, settings overlay, download + local copy
  service.js          background service (requests launch at boot; see Limitations)
  icon.png            app icon
tools/
  build.py            build, sign and install
  draw_icon.py        regenerate the icon: python tools\draw_icon.py app\icon.png 304
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

## Credits

Backdrop started from [**no-cover/wall**](https://github.com/no-cover/wall) by
[no-cover](https://github.com/no-cover), a Tizen TV app that downloads a ZIP of images and shows them as a
slideshow. That idea - and the download-and-extract approach - came from there; the app has since been
rewritten, adding the offline copy, settings overlay, transitions, image selection and build tooling.
Thanks to the original author.

## License

[MIT](LICENSE) - applies to the code in this repository.
