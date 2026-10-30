# EO1-Museum Legacy Installation Guide

_Firefox + MetBoot Browser-Based Architecture_

This guide describes how to set up **EO1-Museum** on a PC and prepare an
Electric Objects EO1 to display the gallery automatically.

The setup consists of two parts:

-   **PC** --- downloads and processes museum artworks and serves the
    local web gallery.
-   **EO1** --- runs Firefox and displays the gallery served by the PC.

Once the initial setup is complete, the EO1 requires only power and a
Wi-Fi connection for normal operation.

------------------------------------------------------------------------

## 1. Requirements

### PC

-   Windows PC
-   Python 3
-   Wi-Fi or local network connection
-   EO1-Museum files

### EO1

-   Electric Objects EO1
-   Wi-Fi connection
-   Micro-USB OTG adapter or hub
-   USB keyboard
-   USB mouse
-   Firefox 68.11.0 for Android
-   MetBoot APK

------------------------------------------------------------------------

## 2. Preparing the EO1

### 2.1 Connect a keyboard and mouse

Connect a USB OTG hub to the EO1's micro-USB port and attach a keyboard
and mouse.

Verify that both devices work correctly.

### 2.2 Open the Android browser

Use the keyboard shortcut:

``` text
Win + B
```

to open the Android browser.

### 2.3 Connect the EO1 to Wi-Fi

Connect the EO1 to the same local network as the PC that will run
EO1-Museum.

------------------------------------------------------------------------

## 3. Setting Up EO1-Museum on the PC

### 3.1 Download EO1-Museum

Download or clone the EO1-Museum repository to the PC.

Example:

``` text
C:\EO1-Museum
```

### 3.2 Install Python dependencies

Install Python 3 and make sure `python` is available from the Windows
command line. `make_gallery.py` uses Pillow; `START_EO1.bat` checks for
Pillow and attempts to install it automatically if necessary.

### 3.3 Start the local web server

Normally, use `START_EO1.bat` or `GET_MET_AND_START.bat`. Both start the
included `server.py` when needed. The server listens on port 8000,
supplies the correct MIME type for Android APK files, and sends
cache-control headers to reduce stale gallery data on the EO1 browser.

For a manual test:

``` text
python server.py
```

A successful start displays `Serving on port 8000`. Keep that window
open while the EO1 is using the gallery.

### 3.4 Test the connection from the EO1

Open the PC's local EO1-Museum address in the EO1 browser.

Example:

``` text
http://192.168.1.xxx:8000/
```

Verify that the EO1 can display a page served by the PC.

------------------------------------------------------------------------

## 4. Installing Firefox on the EO1

### 4.1 Download Firefox

The EO1 runs Android 4.4.2, so a compatible older version of Firefox is
required.

[Firefox 68.11.0 for Android
(ARM)](https://archive.mozilla.org/pub/mobile/releases/68.11.0/android-api-16/en-US/fennec-68.11.0.en-US.android-arm.apk)

### 4.2 Serve the Firefox APK from the PC

EO1-Museum includes a small Python HTTP server that provides the
appropriate MIME type for Android APK files.

Place the Firefox APK in the EO1-Museum directory and run
`python server.py`. Then open the APK from the EO1 browser through the
PC's local address, for example:

``` text
http://192.168.1.xxx:8000/firefox.apk
```

Replace the example IP address with the PC's actual local IPv4 address.

### 4.3 Install Firefox

Download the Firefox APK using the EO1 browser and install it.

Android may require installation from unknown sources to be enabled.

### 4.4 Configure the Firefox home page

Set the EO1-Museum local gallery URL as the Firefox home page.

Example:

``` text
http://192.168.1.xxx:8000/
```

Close and reopen Firefox to confirm that the setting is retained.

------------------------------------------------------------------------

## 5. Installing MetBoot

MetBoot is a small Android application created for EO1-Museum. It
launches Firefox automatically after Android finishes booting.

### 5.1 Install MetBoot

Download and install `MetBoot.apk` on the EO1.

Install `MetBoot.apk` on the EO1. It can be served from the PC in the
same way as the Firefox APK, for example:

``` text
http://192.168.1.xxx:8000/metboot.apk
```

### 5.2 Launch MetBoot manually once

After installation, launch MetBoot manually once before testing
automatic startup.

### 5.3 Test automatic startup

Power off or reboot the EO1.

The expected startup sequence is:

``` text
EO1 power on
    ↓
Android boots
    ↓
MetBoot
    ↓
Firefox
    ↓
EO1-Museum gallery
```

------------------------------------------------------------------------

## 6. Downloading Museum Artworks

### 6.1 Start the initial collection

Run:

``` text
GET_MET_AND_START.bat
```

### 6.2 Enter search keywords

EO1-Museum currently uses The Metropolitan Museum of Art Open Access
collection as its first museum data source.

Example searches:

``` text
renoir
van gogh
hokusai
```

Multiple search groups can be separated by commas.

Words separated by spaces are treated as AND conditions, while commas
separate alternative search groups (OR). For example:

``` text
renoir portrait
renoir, degas
renoir portrait, hokusai landscape
```

Leaving the search blank selects randomly from all eligible works. The
current version is focused on public-domain painting-related records.
See `SEARCH_EXAMPLES.md` for more examples.

### 6.3 Building the display gallery

Downloaded original images are stored separately from the images
prepared for the EO1 display.

Downloaded source images accumulate in `original/` as a local cache.
`met_metadata.json` records the current selection. `make_gallery.py`
prepares the current exhibition as 1080×1920 images in `display/`,
preserving aspect ratio and centering the artwork on a black canvas. It
also generates `images.js`, the list used by the web gallery.

------------------------------------------------------------------------

## 7. Normal Operation

After the initial setup, a keyboard and mouse are no longer required on
the EO1.

### Starting EO1-Museum

Run:

``` text
START_EO1.bat
```

Then power on the EO1.

### Changing the current exhibition

Run:

``` text
UPDATE_MET.bat
```

Enter new search keywords to download/select artworks and rebuild the
current gallery.

### Batch file summary

  -----------------------------------------------------------------------
  File                                Purpose
  ----------------------------------- -----------------------------------
  `START_EO1.bat`                     Rebuild the current exhibition and
                                      start the server

  `UPDATE_MET.bat`                    Select a new exhibition while the
                                      existing server keeps running

  `GET_MET_AND_START.bat`             Select a new exhibition, rebuild
                                      it, and start the server
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 8. Data and Directory Structure

The working directory will contain downloaded artwork, metadata, and
generated display images.

``` text
EO1-Museum/
├── README.md
├── INSTALL.md
├── SEARCH_EXAMPLES.md
├── index.html
├── GET_MET_ART_KEYWORD.py
├── make_gallery.py
├── server.py
├── GET_MET_AND_START.bat
├── START_EO1.bat
├── UPDATE_MET.bat
├── MetBoot/
├── original/
├── display/
├── MetObjects.csv
├── met_metadata.json
└── images.js
```

`MetObjects.csv`, `met_metadata.json`, `images.js`, downloaded files
under `original/`, and generated files under `display/` are
working/runtime data and are excluded from Git where appropriate. Empty
`original/` and `display/` directories are retained with `.gitkeep`.

------------------------------------------------------------------------

## 9. Troubleshooting

### EO1 cannot reach the PC

Check that the PC and EO1 are on the same local network, `server.py` is
running, the Firefox home page contains the current PC IPv4 address, and
Windows Firewall is not blocking the Python server. Use `ipconfig` on
the PC to check its current address.

### APK downloads but cannot be opened

Use the included `server.py` rather than `python -m http.server`.
EO1-Museum's server explicitly supplies
`application/vnd.android.package-archive` for `.apk` files.

### Firefox does not start automatically

Check that MetBoot and Firefox are installed and that MetBoot was
launched manually once after installation.

### Firefox starts but does not open the gallery

Check the Firefox home-page URL and confirm that the PC server is
running. If old or nonexistent image numbers are requested after an
exhibition change, restart the server and reboot the EO1. The current
server sends no-cache/no-store headers, and `index.html` uses a
cache-busting URL for `images.js`.

### The PC's IP address has changed

Run `ipconfig` again and update the Firefox home page on the EO1 to use
the new PC IPv4 address. A DHCP reservation on the router can reduce
future address changes.

------------------------------------------------------------------------

## 10. Unattended Operation

Once everything is working correctly, disconnect the USB keyboard,
mouse, and OTG hub from the EO1.

For everyday use:

1.  Start the EO1-Museum server on the PC.
2.  Power on the EO1.
3.  MetBoot launches Firefox automatically.
4.  Firefox opens the local museum gallery.

At this point, the EO1 functions as a dedicated network-connected museum
display.
